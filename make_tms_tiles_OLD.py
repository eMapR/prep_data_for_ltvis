# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 14:21:43 2018

@author: braatenj
"""



from osgeo import gdal, ogr
import numpy as np
import math
import subprocess
from glob import glob
import os
from PIL import Image
import pandas as pd
import fnmatch
import shutil

def get_dims(fileName):
  src = gdal.Open(fileName)
  ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
  sizeX = src.RasterXSize
  sizeY = src.RasterYSize
  lrx = ulx + (sizeX * xres)
  lry = uly + (sizeY * yres)
  return [ulx,uly,lrx,lry,xres,-yres,sizeX,sizeY]

def make_geo_trans(fileName, trgtDim):
  src   = gdal.Open(fileName)
  ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
  return((trgtDim[0], xres, xskew, trgtDim[1], yskew, yres))

def get_intersec(files):
  ulxAll=[]
  ulyAll=[]
  lrxAll=[]
  lryAll=[]
  for fn in files:
    dim = get_dims(fn)
    ulxAll.append(dim[0])
    ulyAll.append(dim[1])
    lrxAll.append(dim[2])
    lryAll.append(dim[3])
  return([max(ulxAll),min(ulyAll),min(lrxAll),max(lryAll)])

def get_offsets(fileName, trgtDim):
  dim = get_dims(fileName)
  xoff = math.floor(abs(dim[0]-trgtDim[0])/dim[4])
  yoff = math.ceil(abs(dim[1]-trgtDim[1])/dim[4])
  xsize = abs(trgtDim[0]-trgtDim[2])/dim[4]
  ysize = abs(trgtDim[1]-trgtDim[3])/dim[4]
  return([int(i) for i in [xoff, yoff, xsize, ysize]])

def get_band(fileName, trgtDim, band):
  offsets = get_offsets(fileName, trgtDim)
  src = gdal.Open(fileName)
  band = src.GetRasterBand(band)
  array = band.ReadAsArray(
            offsets[0],
            offsets[1],
            offsets[2],
            offsets[3])
  return(array)

def write_img(outFile, refImg, trgtDim, nBands, dataType, of):
  convertDT = {
    'uint8': 1,
    'int8': 1,
    'uint16': 2,
    'int16': 3,
    'uint32': 4,
    'int32': 5,
    'float32': 6,
    'float64': 7,
    'complex64': 10,
    'complex128': 11
  }
  dataType = convertDT[dataType]
  geoTrans = make_geo_trans(refImg, trgtDim)
  proj = gdal.Open(refImg).GetProjection()
  dims = get_offsets(refImg, trgtDim)
  driver = gdal.GetDriverByName(of)
  driver.Register()
  outImg = driver.Create(outFile, dims[2], dims[3], nBands, dataType) # file, col, row, nBands, dataTypeCode
  outImg.SetGeoTransform(geoTrans)
  outImg.SetProjection(proj)
  return(outImg)


def scale_to_8bit_stdev(img, n_stdev):
  mean = np.mean(img)
  stdev = np.std(img)
  imin = mean-(stdev*n_stdev)
  imax = mean+(stdev*n_stdev)
  if imin < 0:
    imin = 0
  img[np.where(img < imin)] = imin
  img[np.where(img > imax)] = imax
  img = np.round(((img-imin)/(imax-imin+0.0))*255)     
  return img
  
  
def scale_to_8bit_minMax(img, minVal, maxVal, noData):
  noDataIndex = np.where(img == noData)
  img[np.where(img < minVal)] = minVal
  img[np.where(img > maxVal)] = maxVal
  img = np.round(((img-minVal)/(maxVal-minVal+0.0))*254)+1
  img[noDataIndex] = 0    
  return img


def scale_to_8bit_tc(img, tc):
  # standard TC stretch SR * 10000  
  n_stdev = 2  
  if tc == 'b':  
    imin = 3098-(1247*n_stdev)
    imax = 3098+(1247*n_stdev)
  if tc == 'g':
    imin = 1549-(799*n_stdev)
    imax = 1549+(799*n_stdev)
  if tc == 'w':  
    imin = -701-(772*n_stdev)
    imax = -701+(772*n_stdev)  
  
  img[np.where(img < imin)] = imin
  img[np.where(img > imax)] = imax
  img = np.round(((img-imin)/(imax-imin+0.0))*255)     
  return img


def write_rgb_bands(r, g, b, outFile, ref, trgtDim, noData=None):
  outImg = write_img(outFile, ref, trgtDim, 3, 'int8', 'GTIFF')
  outBand = outImg.GetRasterBand(1) 
  if noData is not None: 
    outBand.SetNoDataValue(noData)  
  outBand.WriteArray(r)
  outBand = outImg.GetRasterBand(2) 
  if noData is not None: 
    outBand.SetNoDataValue(noData) 
  outBand.WriteArray(g)
  outBand = outImg.GetRasterBand(3) 
  if noData is not None: 
    outBand.SetNoDataValue(noData) 
  outBand.WriteArray(b)
  outImg = None


def write_band(img, outFile, ref, trgtDim, dataType, of, noData=None):
  outImg = write_img(outFile, ref, trgtDim, 1, dataType, of)
  outBand = outImg.GetRasterBand(1) 
  if noData is not None: 
    outBand.SetNoDataValue(noData)
  outBand.WriteArray(img)
  outImg = None


  
def color_map_csv(inFile, colorTable, outFile, noData=None):
  trgtDim = get_intersec([inFile])
  img = get_band(inFile, trgtDim, 1)
  r = np.copy(img)
  g = np.copy(img)
  b = np.copy(img)
  
  l = colorTable.shape[0]
  for i in range(colorTable.shape[0]):
    print('working on class: '+str(i+1)+'/'+str(l))
    these = np.where(img == colorTable.iloc[i,0]) #ix
    r[these] = colorTable.iloc[i,1]
    g[these] = colorTable.iloc[i,2]
    b[these] = colorTable.iloc[i,3]
  
  write_rgb_bands(r, g, b, outFile, inFile, trgtDim, noData)


def color_map_dict(inFile, colorTable, outFile, noData=None):
  trgtDim = get_intersec([inFile])
  img = get_band(inFile, trgtDim, 1)
  r = np.copy(img)
  g = np.copy(img)
  b = np.copy(img)
  
  l = len(colorTable)
  keys = colorTable.keys()
  for i in range(l):
    print('working on class: '+str(i+1)+'/'+str(l))
    these = np.where(img == keys[i])
    r[these] = colorTable[keys[i]]['r']
    g[these] = colorTable[keys[i]]['g']
    b[these] = colorTable[keys[i]]['b']
  
  write_rgb_bands(r, g, b, outFile, inFile, trgtDim, noData)


def get_subset_bounds(ulxy, urxy, targetWidth, targetHeight):
    ulxAdj = math.ceil(ulxy[0] / 30.0) * 30
    if ulxAdj-ulxy[0] >= 15: 
        ulxAdj -= 30 + 15
    else:
        ulxAdj -= 15
    ulyAdj = round(ulxy[1] / 30.0) * 30 + 15
    ratio = targetHeight/(targetWidth + 0.0)   
    geoWidth = round((urxy[0] - ulxy[0]) / 30.0) * 30
    geoHeight = geoWidth * ratio
    lrxAdj = ulxAdj + geoWidth
    lryAdj = ulyAdj - geoHeight
                       
    return ([ulxAdj, ulyAdj],[lrxAdj, lryAdj]) #"{0} {1} {2} {3}".format(ulxAdj, lryAdj, lrxAdj, ulyAdj);  



def removeEmptyFolders(path, removeRoot=True):
  if not os.path.isdir(path):
    return

  # remove empty subfolders
  files = os.listdir(path)
  if len(files):
    for f in files:
      fullpath = os.path.join(path, f)
      if os.path.isdir(fullpath):
        removeEmptyFolders(fullpath)

  # if folder empty, delete it
  files = os.listdir(path)
  if len(files) == 0 and removeRoot:
    print "Removing empty folder:", path
    os.rmdir(path)




############################################################################
#fn = '/vol/v1/ftp/forestbiomass/mr200/biomass_summaries_crm/WAORCA_biomass_crm_mean.tif'
#outDir = '/vol/v1/general_files/user_files/justin/temp/biomass_tws'

fn = '/vol/v2/stem/caorwa/imperv/archive/default.vrt' # what files should be tiled
outDir = '/vol/v2/stem/caorwa/imperv/archive/tiles' # where do you want tiles to go


colorMap = '/vol/v2/stem/caorwa/tms_misc/nlcd_imperv_color_map.txt' # csv colorMap file path - could be NA if doing grey-scale
colorMode = 'interp'

minYear = 1990 #1990
maxYear = 2012 #2012
#minVal = 100
#maxValue = 2500
origNoData = 255 # if none, then: None      -9999
finalNodata = 255 # if none, then: None
grey = False

# these are expected to be in EPSG:3857
subset = False
"""
#inland test
xmin = -13796497 #-13830184  
ymax =  5648824 #5741212 
xmax = -13479942 #-13768169 
ymin = 5327991 #5665417 
"""
#coast test
xmin = -13830184  
ymax =  5741212 
xmax = -13768169 
ymin = 5665417 

clipFile = "/vol/v2/stem/caorwa/tms_misc/waorca_boundary_epsg3857_buffer1000m.shp"


############################################################################


years = [str(i) for i in range(minYear,maxYear+1)]
tempDir = os.path.join(outDir,'temp')
if not os.path.exists(tempDir):
  os.makedirs(tempDir)


for i, yr in enumerate(years):
  print(yr)
  i += 1
  
  #i = 1
  #yr = '1990'

  # subset the band
  # SUBSET THE AREA 
  bandFile = os.path.join(tempDir,yr+'.tif')
  cmd = 'gdal_translate -b '+str(i)+' -a_nodata '+str(origNoData)+' '+fn+' '+bandFile
  subprocess.call(cmd, shell=True)
  
  # warp the band  --- !!!! THIS NEEDS TO BE MODE OR NN IF CLASSES
  warpFile = os.path.join(tempDir,yr+'warp.tif')
  if subset:  
    te = '{} {} {} {}'.format(xmin, ymin, xmax, ymax)    
    cmd = 'gdalwarp -srcnodata '+str(origNoData)+' -dstnodata '+str(finalNodata)+' -t_srs EPSG:3857 -tr 30 30 -te '+te+' '+bandFile+' '+warpFile
  else:
    
    ext = str.lower(os.path.splitext(clipFile)[-1])
    drivers = {'.shp'    :'ESRI Shapefile', 
               '.geojson': 'GeoJSON'}           
    driver = ogr.GetDriverByName(drivers[ext])
    
    # read in the inShape file and get the extent
    inDataSource = driver.Open(clipFile, 0)
    extent = inDataSource.GetLayer().GetExtent()
    
    # format the exent as -projwin arguments for gdal translate
    te = '{} {} {} {}'.format(extent[0], extent[2], extent[1], extent[3])      
    
    # make cmd
    cmd = 'gdalwarp -srcnodata '+str(origNoData)+' -dstnodata '+str(finalNodata)+' -t_srs EPSG:3857 -tr 30 30 -te_srs EPSG:3857 -te '+te+' '+bandFile+' '+warpFile
  subprocess.call(cmd, shell=True)

  
  
  
  # STRETCH THE FILE TO 8BIT AND COLOR IT
  stretchFile = os.path.join(tempDir,yr+'8bit.tif')
  if colorMode == 'exact':
    cmd = 'gdaldem color-relief -of GTiff -alpha -nearest_color_entry '+warpFile+' '+colorMap+' '+stretchFile
  if colorMode == 'interp':
    cmd = 'gdaldem color-relief -of GTiff -alpha '+warpFile+' '+colorMap+' '+stretchFile

  subprocess.call(cmd, shell=True)




  """
  # these are expected to be in EPSG:3857
  subset = False
  xmin = -13830184  #-13796497 
  ymax = 5741212 #5648824
  xmax = -13768169 #-13479942
  ymin =  5665417 #5327991
  te = '{} {} {} {}'.format(xmin, ymax, xmax, ymin)
  bandFile = os.path.join(tempDir,'small8bit.tif')
  cmd = 'gdal_translate -projwin '+te+' '+stretchFile+' '+bandFile
  subprocess.call(cmd, shell=True)
  cmd = 'gdal2tiles.py -z 0-11 '+bandFile+' '+tileDir
  subprocess.call(cmd, shell=True)
  """


  """
  if grey:  
    # 8 bit stretch grey data
    trgtDim = get_intersec([warpFile])
    img = get_band(warpFile, trgtDim, 1)  
    img = scale_to_8bit_minMax(img, minVal, maxValue, origNoData)
    print(img[0,0])  
    stretchFile = os.path.join(tempDir,yr+'8bit.tif')
    write_band(img, stretchFile, warpFile, trgtDim, 'int8', 'GTIFF', finalNodata)
  else:
    # 8-bit stretch color data
    # read in the color nlcd table
    colorTable = pd.read_csv(colorMap)
    stretchFile = os.path.join(tempDir,yr+'8bit.tif')
    color_map_csv(warpFile, colorTable, stretchFile, finalNodata)
  """


  # MAKE TILES
  tileDir = os.path.join(outDir,yr)
  if not os.path.exists(tileDir):
    os.mkdir(tileDir)
  cmd = 'gdal2tiles.py -r near -z 0-11 '+stretchFile+' '+tileDir
  subprocess.call(cmd, shell=True)


  # GET RID OF BLANK TILES
  tiles = []  
  for root, dirnames, filenames in os.walk(tileDir):
    for filename in fnmatch.filter(filenames, '*.png'):    
      tiles.append(os.path.join(root, filename))
   
  for tile in tiles:
    im = Image.open(tile)
    good = np.any((np.asarray(im)[:,:,3]))
    if not good:
      os.remove(tile)
      
      
  #REMOVE EMPTY DIRECTORIES
  removeEmptyFolders(tileDir+'/')


  # REMOVE TEMP DATA
  tempFiles = glob(os.path.join(tempDir,'*'))
  for tempFile in tempFiles:
    os.remove(tempFile)  

  
  
  
  
  