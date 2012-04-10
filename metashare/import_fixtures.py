#!/usr/bin/env python
"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import os
import sys
import traceback

try:
    import settings 

except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the " \
      "directory containing %r. It appears you've customized things.\n" \
      "You'll have to run django-admin.py, passing it your settings " \
      "module.\n(If the file settings.py does indeed exist, it's causing" \
      " an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
    sys.path.append(PROJECT_HOME)
    
    if len(sys.argv) > 1:
        print "\n\tusage: {0} \n".format(sys.argv[0])
        sys.exit(-1)
    
    settings.DEBUG = False
    
    SUCCESSFUL_IMPORTS = 0
    ERRONEOUS_IMPORTS = 0
    from zipfile import ZipFile, is_zipfile
    from xml.etree.ElementTree import fromstring
    from metashare.repository.models import resourceInfoType_model
    from metashare.stats.model_utils import saveLRStats, UPDATE_STAT
    
    PATH = os.path.normpath(os.getcwd() + "/repository/test_fixtures")
    
    for path, dirs, files in os.walk(PATH):
        for filename in files:
            fullpath = os.path.join(path, filename)  
            temp_file = open(fullpath, 'rb')
            temp_file.seek(0)

       
            try:
                print 'Importing XML file: "{0}"'.format(filename)
                tree = fromstring(temp_file.read())
                result = resourceInfoType_model.import_from_elementtree(tree)
                
                if result[0]:
                    resource = result[0]
                    
                    if "published" in filename:
                        resource.storage_object.publication_status = 'p'
                    elif "ingested" in filename:
                        resource.storage_object.publication_status = 'g'
                    else: #if internal (if no status given, status default is internal)
                        resource.storage_object.publication_status = 'i'
                    resource.storage_object.save()
                    
                    SUCCESSFUL_IMPORTS += 1

                    saveLRStats("", resource.storage_object.identifier, "", UPDATE_STAT)
    
            except:
                ERRONEOUS_IMPORTS += 1
                print 'Could not import XML file into database!'
                print traceback.format_exc()

            
            temp_file.close()
    
    print "Done.  Successfully import {0} files into the database, errors " \
      "occured in {1} cases.".format(SUCCESSFUL_IMPORTS, ERRONEOUS_IMPORTS)
      
      
