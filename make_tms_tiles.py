# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 14:21:43 2018

@author: braatenj
"""



from osgeo import ogr
import numpy as np
import subprocess
from glob import glob
import os
from PIL import Image
import fnmatch
import sys

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
    print("Removing empty folder:", path)
    os.rmdir(path)




############################################################################
#fileTemplate = '/vol/v3/lt_stem_v3.1/models/landcover_v1.1/{year}/landcover_v1.1_{year}_vote.tif'
#startYear = 1984
#endYear = 2017
#outDir = '/vol/v2/archive/tileTest' # where do you want tiles to go
#colorMap = '/vol/v1/general_files/script_library/prep_data_for_ltvis/color_maps/nlcd_lc_color_map.txt' 
#colorMode = 'exact' # 'interp' or 'exact' coloring 
#origNoData = 255
#finalNoData = 255
#extent = '/vol/v1/general_files/script_library/prep_data_for_ltvis/vector/tile_test_extent.shp' # a shapefile defining the extent to use (needs to be EPSG:3857) - if you want to use the whole raster, then enter 'all'
############################################################################


def main(fileTemplate, startYear, endYear, outDir, colorMap, colorMode, origNoData, finalNoData, extent):
  tempDir = os.path.join(outDir,'temp')
  if not os.path.exists(tempDir):
    os.makedirs(tempDir)
  
  for i, year in enumerate(range(startYear, endYear+1)):
    yr = str(year)
    fn = fileTemplate.format(year=yr)
    if not os.path.exists(fn):
      sys.exit('Error: file '+fn+' does not exist')
    
    warpFile = os.path.join(tempDir,yr+'_warp.tif')
    if extent == 'all':
      cmd = 'gdalwarp -srcnodata '+str(origNoData)+' -dstnodata '+str(finalNoData)+' -t_srs EPSG:3857 -te_srs EPSG:3857 -tr 30 30 '+fn+' '+warpFile 
    else: 
      # read in the inShape file and get the extent -  format as -te arguments for gdal warp
      driver = ogr.GetDriverByName('ESRI Shapefile')
      inDataSource = driver.Open(extent, 0)
      ext = inDataSource.GetLayer().GetExtent()
      te = '{} {} {} {}'.format(ext[0], ext[2], ext[1], ext[3])      
      cmd = 'gdalwarp -srcnodata '+str(origNoData)+' -dstnodata '+str(finalNoData)+' -t_srs EPSG:3857 -te_srs EPSG:3857 -tr 30 30 -te '+te+' '+fn+' '+warpFile 
    
    # run the command
    subprocess.call(cmd, shell=True)
    
    # STRETCH THE FILE TO 8BIT AND COLOR IT
    stretchFile = os.path.join(tempDir,yr+'_8bit_color.tif')
    if colorMode == 'exact':
      cmd = 'gdaldem color-relief -of GTiff -alpha -nearest_color_entry '+warpFile+' '+colorMap+' '+stretchFile
    if colorMode == 'interp':
      cmd = 'gdaldem color-relief -of GTiff -alpha '+warpFile+' '+colorMap+' '+stretchFile
  
    subprocess.call(cmd, shell=True)
  
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

if __name__ == '__main__':
  fileTemplate = str(sys.argv[1])
  startYear = int(sys.argv[2])
  endYear = int(sys.argv[3])
  outDir = str(sys.argv[4])
  colorMap = str(sys.argv[5])
  colorMode = str(sys.argv[6])
  origNoData = int(sys.argv[7])
  finalNoData = int(sys.argv[8])
  extent = str(sys.argv[9])

  sys.exit(main(fileTemplate, startYear, endYear, outDir, colorMap, colorMode, origNoData, finalNoData, extent))
  
  
  
  