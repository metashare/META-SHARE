#!/usr/bin/env python
"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import os
import sys
import traceback

# Magic python path, based on http://djangosnippets.org/snippets/281/
from os.path import abspath, dirname, join
parentdir = dirname(dirname(abspath(__file__)))
# Insert our dependencies:
sys.path.insert(0, join(parentdir, 'lib', 'python2.7', 'site-packages'))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, parentdir)


try:
    import settings # Assumed to be in the same directory.

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
    
    # Check command line parameters first.
    if len(sys.argv) < 2:
        print "\n\tusage: {0} <file.xml|archive.zip> [<file.xml|archive." \
          "zip> ...]\n".format(sys.argv[0])
        sys.exit(-1)
    
    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    
    SUCCESSFUL_IMPORTS = 0
    ERRONEOUS_IMPORTS = 0
    from zipfile import ZipFile, is_zipfile
    from xml.etree.ElementTree import fromstring
    from metashare.repo2.models import resourceInfoType_model
    from metashare.stats.model_utils import saveLRStats, UPDATE_STAT
    
    for filename in sys.argv[1:]:
        temp_file = open(filename, 'rb')
        handling_zip_file = is_zipfile(temp_file)
        
        # Reset file handle for proper reading of the file contents.
        temp_file.seek(0)
        
        # cfedermann: use the following line in case of Python 2.6.x
        #             You should however, REALLY, install 2.7.x!
        #if not request.FILES['xml_file'].name.lower().endswith('zip'):
        if not handling_zip_file:
            try:
                print 'Importing XML file: "{0}"'.format(filename)
                tree = fromstring(temp_file.read())
                result = resourceInfoType_model.import_from_elementtree(tree)
                
                if result[0]:
                    resource = result[0]
                    
                    # Set published=True for new object.
                    resource.storage_object.published = True
                    resource.storage_object.save()
                    
                    # Increase number of successful imports.
                    SUCCESSFUL_IMPORTS += 1

                    # Update statistics
                    saveLRStats("", resource.storage_object.identifier, "", UPDATE_STAT)
    
            except:
                ERRONEOUS_IMPORTS += 1
                print 'Could not import XML file into database!'
                print traceback.format_exc()
        
        else:
            temp_zip = ZipFile(temp_file)
            
            print 'Importing ZIP file: "{0}"'.format(filename)
            for xml_name in temp_zip.namelist():
                try:
                    if xml_name.endswith('/') or xml_name.endswith('\\'):
                        continue
                    
                    print 'Importing XML file: "{0}"'.format(xml_name)
                    tree = fromstring(temp_file.read())
                    result = resourceInfoType_model.import_from_elementtree(tree)
                    
                    if result[0]:
                        resource = result[0]
                        
                        # Set published=True for new object.
                        resource.storage_object.published = True
                        resource.storage_object.save()

                        # Increase number of successful imports.
                        SUCCESSFUL_IMPORTS += 1

                        # Update statistics
                        saveLRStats("", resource.storage_object.identifier, "", UPDATE_STAT)
                
                except:
                    ERRONEOUS_IMPORTS += 1
                    print 'Could not import XML file into database!'
                    print traceback.format_exc()
        
        temp_file.close()
    
    print "Done.  Successfully import {0} files into the database, errors " \
      "occured in {1} cases.".format(SUCCESSFUL_IMPORTS, ERRONEOUS_IMPORTS)
      
