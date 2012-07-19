
import os
import sys
from fset import FILESETS, RES_ROOT

if __name__ == "__main__":
  errors = 0
  for fileset in FILESETS.keys():
    print fileset
    res_set = FILESETS[fileset]
    for res_files in res_set:
      #print res_files
      for res_file in res_files:
        full_name = '{0}/{1}'.format(RES_ROOT, res_file)
        print full_name
        if not os.path.exists(full_name):
          errors = errors + 1
          print 'WARNING: File {0} does not exist!!'.format(full_name)
  if errors > 0:
    print '{0} file(s) missing!'.format(errors)
    det_f = os.fdopen(3, 'w')
    det_f.write('FileNotFound')
    sys.exit(1)
  else:
    print 'All files have been found.'
    sys.exit(0)

