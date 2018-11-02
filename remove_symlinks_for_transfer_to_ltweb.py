#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 10:54:39 2018

@author: braatenj
"""

import os

##########################################################################################################
fileTemplate = '/vol/v2/archive/symlinks/lt-stem_biomass_nbcd_v0.1/{year}/lt-stem_biomass_nbcd_v0.1_{year}_median.tif'
startYear = 1984
endYear = 2017
##########################################################################################################

for i, year in enumerate(range(startYear, endYear+1)):
  src = fileTemplate.format(year=str(year))
  if os.path.exists(src):
    os.remove(src)


