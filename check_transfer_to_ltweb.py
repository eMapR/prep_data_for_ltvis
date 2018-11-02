#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 09:41:00 2018

@author: braatenj
"""


import os
import sys

##########################################################################################################
fileTemplate = '/data/maps/CONUS/lt-stem_landcover_v0.1/{year}/lt-stem_landcover_v0.1_{year}_vote.tif'
startYear = 1984
endYear = 2017
##########################################################################################################

sizes = []
for i, year in enumerate(range(startYear, endYear+1)):
  src = fileTemplate.format(year=str(year))
  if not os.path.exists(src):
    sys.exit('Error: file '+src+' does not exist')
  
  sizes.append(str(year)+': '+ str(os.path.getsize(src)))

print('\n'.join(sizes))



