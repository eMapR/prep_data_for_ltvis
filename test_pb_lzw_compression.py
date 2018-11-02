#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 11 09:39:53 2018

@author: braatenj
"""

import subprocess
import json
from time import time
import pandas as pd
from osgeo import gdal
import numpy as np
import math
import seaborn as sns

def get_dims(fileName):
  src = gdal.Open(fileName)
  ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
  sizeX = src.RasterXSize
  sizeY = src.RasterYSize
  lrx = ulx + (sizeX * xres)
  lry = uly + (sizeY * yres)
  return [ulx,uly,lrx,lry,xres,-yres,sizeX,sizeY]

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

def getPoint(inRaster, x, y, minYear, maxYear):
  startTime = time()
  x = str(x) #
  y = str(y) #
  cmd = 'gdallocationinfo -valonly -wgs84'+' '+inRaster+' '+x+' '+y
  #subprocess.call(cmd, shell=True)
  
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
  output = [int(v) for v in proc.stdout.read().splitlines()]
  year = range(minYear,maxYear+1)
  print(json.dumps({"ts":output, "yr":year}))
  endTime = time()
  return(endTime - startTime)

def calcMean(fileName, trgtDim, nBands):
  for i in nBands:
    junk = np.mean(get_band(fileName, trgtDim, i))

def timeCalc(fileName, trgtDim, nBands):
  startTime = time()
  calcMean(fileName, trgtDim, nBands)
  endTime = time()
  return round((endTime - startTime), 4)

# read in all the bands of a spatial subset and return band mean
def getMeanAll(fn,trgtDim):
  startTime = time()
  offsets = get_offsets(fn, trgtDim)
  src = gdal.Open(fn)
  array = src.ReadAsArray(
            offsets[0],
            offsets[1],
            offsets[2],
            offsets[3])
  
  rs = array.reshape(array.shape[0], array.shape[1]*array.shape[2])
  means = np.mean(rs, axis=1)
  endTime = time()
  tDif = endTime-startTime
  return tDif


def getMeanBand(fn,trgtDim):
  startTime = time()
  offsets = get_offsets(fn, trgtDim)
  src = gdal.Open(fn)
  means = []
  for b in range(src.RasterCount):
    band = src.GetRasterBand(b+1)
    array = band.ReadAsArray(
            offsets[0],
            offsets[1],
            offsets[2],
            offsets[3])
    means.append(np.mean(array))
  endTime = time()
  tDif = endTime-startTime
  return tDif


  
########################################
  
packBitsFn = '/vol/v2/archive/biomass_time_series_packbits.vrt'
lzwFn = '/vol/v2/archive/biomass_time_series_lzw.vrt'
origFn = '/vol/v2/archive/biomass_time_series_original.vrt'
deflateFn = '/vol/v2/archive/biomass_time_series_deflate.vrt'

minYear = 1984
maxYear = 2017
x = -1097878
y = 2136060

########################################


sizeList = range(30, 300000, 15000)
sizeList = [sizeList[i]-30 for i in range(1,len(sizeList))]
sizeList = [30,90] + sizeList
km2 = [(i**2)/1000 for i in sizeList]


#packBitsTall = []
#lzwTall = []
#origTall = []
packBitsTband = []
lzwTband = []
origTband = []
deflateTband = []

size = []
nBands = list(range(1, ((maxYear-minYear)+1)+1))

for j in range(8): #range(len(sizeList)):
  #print(str(j+1)+'/'+str(len(sizeList)))
  print(str(j+1)+'/8')

  trgtDim = [x, y, x+sizeList[j], y-sizeList[j]]
  #for i in range(20):
  #origTall.append(getMeanAll(origFn,trgtDim))
  #packBitsTall.append(getMeanAll(packBitsFn,trgtDim))
  #lzwTall.append(getMeanAll(lzwFn,trgtDim))
  #origTband.append(getMeanBand(origFn,trgtDim))
  #packBitsTband.append(getMeanBand(packBitsFn,trgtDim))
  deflateTband.append(getMeanBand(deflateFn,trgtDim))
  lzwTband.append(getMeanBand(lzwFn,trgtDim))
  size.append(km2[j])


#origTall=origTall[0:7]
#packBitsTall=packBitsTall[0:7]
#lzwTall=lzwTall[0:7]

#origTband=origTband[0:7]
#packBitsTband=packBitsTband[0:7]
#lzwTband=lzwTband[0:7]
#deflateTband=deflateTband[0:7]
pixels = [i/30 for i in sizeList[0:8]]

df = pd.DataFrame({'nPixels':pixels, 'Uncompressed':origTband, 'Packbits':packBitsTband, 'LZW':lzwTband, 'Deflate':deflateTband})
dfPlot = df.drop([1])
tidyDf = pd.melt(dfPlot, id_vars=['nPixels'], value_vars=['Uncompressed', 'Packbits', 'LZW', 'Deflate'], var_name='Method', value_name='Seconds')
ax = sns.pointplot(x="nPixels", y="Seconds", hue="Method", data=tidyDf)


df = pd.DataFrame({'nPixels':pixels, 'LZW':lzwTband, 'Deflate':deflateTband})
dfPlot = df.drop([1])
tidyDf = pd.melt(dfPlot, id_vars=['nPixels'], value_vars=['LZW', 'Deflate'], var_name='Method', value_name='Seconds')
ax = sns.pointplot(x="nPixels", y="Seconds", hue="Method", data=tidyDf)





    














