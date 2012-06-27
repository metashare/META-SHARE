
import os
import sys

RES_ROOT = '{0}/misc/testdata/v2.1'.format(os.environ['METASHARE_SW_DIR'])
FILESETS={}

fileset = []

subset = []
subset.append('ELRAResources/elra20.xml')
subset.append('ELRAResources/elra30.xml')
subset.append('ELRAResources/elra40.xml')
fileset.append(subset)

subset = []
subset.append('ELRAResources/elra21.xml')
subset.append('ELRAResources/elra31.xml')
subset.append('ELRAResources/elra41.xml')
subset.append('ELRAResources/elra51.xml')
subset.append('ELRAResources/elra61.xml')
fileset.append(subset)

subset = []
subset.append('METASHAREResources/ILC-CNR/Estuari.xml')
fileset.append(subset)

subset = []
subset.append('METASHAREResources/ILSP/ILSP12.xml')
subset.append('METASHAREResources/ILSP/ILSP16.xml')
subset.append('METASHAREResources/ILSP/ILSP18.xml')
subset.append('METASHAREResources/ILSP/ILSP25.xml')
fileset.append(subset)

#subset = []
#subset.append('aaaa')
#subset.append('aaaa')
#subset.append('aaaa')
#subset.append('aaaa')
#subset.append('aaaa')
#subset.append('aaaa')
#subset.append('aaaa')
#subset.append('bbbb')
#fileset.append(subset)

FILESETS.update({'fileset1': fileset})

# fset.py filesetname node
if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(-1)
    
    try:
        key = sys.argv[1]
        index = int(sys.argv[2])
        for filename in FILESETS[key][index]:
            print '{0}/{1}'.format(RES_ROOT, filename)
    except:
        sys.exit(-2)

