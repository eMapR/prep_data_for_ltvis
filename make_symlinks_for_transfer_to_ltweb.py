
import os
import sys


def main(fileTemplate, startYear, endYear, outDir, outBaseTemplate):
  for i, year in enumerate(range(startYear, endYear+1)):
    src = fileTemplate.format(year=str(year))
    if not os.path.exists(src):
      sys.exit('Error: file '+src+' does not exist')
    
    thisDir = os.path.join(outDir,str(year))
    if not os.path.isdir(thisDir):
      os.makedirs(thisDir)
    
    dst = os.path.join(thisDir, outBaseTemplate.format(year=str(year)))
    os.symlink(src, dst)

if __name__ == '__main__':
  fileTemplate = str(sys.argv[1])
  startYear = int(sys.argv[2])
  endYear = int(sys.argv[3])
  outDir = str(sys.argv[4])
  outBaseTemplate = str(sys.argv[5])

  sys.exit(main(fileTemplate, startYear, endYear, outDir, outBaseTemplate))
  
"""
##########################################################################################################
fileTemplate = '/vol/v3/lt_stem_v3.1/models/biomassfiaald_20180708_0859/{year}/biomassfiaald_20180708_0859_{year}_median.tif'
startYear = 1984
endYear = 2017
outDir = '/vol/v2/archive/symlinks/lt-stem_biomass_nbcd_v0.1'
outBaseTemplate = 'lt-stem_biomass_nbcd_v0.1_{year}_median.tif'
##########################################################################################################
"""