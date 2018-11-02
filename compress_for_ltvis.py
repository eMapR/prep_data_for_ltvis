# -*- coding: utf-8 -*-
"""
Created on Tue Jul  3 09:29:54 2018

@author: braatenj
"""

import subprocess
import os
import sys

#raster = '/vol/v3/lt_stem_v3.1/models/biomassfiaald_20180708_0859/{year}/biomassfiaald_20180708_0859_{year}_mean.tif'
#startYear = 1984
#endYear = 2017
#noData = -9999
#ofType = 'Int16' 'Byte'
#outDir = '/vol/v2/archive/biomass/'
#method = 'deflate' or 'lzw', or 'packbits'

def main(raster, startYear, endYear, noData, ofType, outDir, method):
  for year in range(startYear, endYear+1):
    print(year)
    inFile = raster.format(year=str(year))
    if not os.path.exists(inFile):
      sys.exit('Error: file '+inFile+' does not exist')
    bname = os.path.splitext(os.path.basename(inFile))[0]+'_{method}.tif'
    bname = bname.format(method=method.lower())
    outFile = os.path.join(outDir, str(year), bname)
    if not os.path.exists(os.path.dirname(outFile)):
      os.makedirs(os.path.dirname(outFile)) 
  
    cmd = 'gdal_translate -co COMPRESS='+method.upper()+' -co BIGTIFF=YES -of GTIFF -tr 30 30 -a_nodata '+str(noData)+' -ot '+ofType+' '+inFile+' '+outFile  #

    subprocess.call(cmd, shell=True)
        
if __name__ == '__main__':
  raster = str(sys.argv[1])
  startYear = int(sys.argv[2])
  endYear =int( sys.argv[3])
  noData = int(sys.argv[4])
  ofType = str(sys.argv[5])
  outDir = str(sys.argv[6])
  method = str(sys.argv[7])

  sys.exit(main(raster, startYear, endYear, noData, ofType, outDir, method))