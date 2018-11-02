#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 11 11:02:55 2018

@author: braatenj
"""


import subprocess

def make_vrt(inputFiles, vrtFile):
  inputListFile = vrtFile.replace('.vrt', '_filelist.txt')
  inputList = open(inputListFile, 'w')
  for inputFile in inputFiles:
    inputList.write(inputFile+'\n')
  inputList.close()
  
  # create vrt
  cmd = 'gdalbuildvrt -separate -input_file_list '+inputListFile+' '+vrtFile
  print(cmd)
  subprocess.call(cmd, shell=True)


#############################

raster = '/vol/v2/archive/biomass_deflate/{year}/biomassfiaald_20180708_0859_{year}_mean_deflate.tif'
startYear = 1984
endYear = 2017
outFile = '/vol/v2/archive/biomass_time_series_deflate.vrt'


#############################

files = []
for year in range(startYear, endYear+1):
  files.append(raster.format(year=str(year)))

files.sort()
make_vrt(files, outFile)
