#!/usr/bin/env python
"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import os
import sys

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
    
    # Check that SOLR is running, or else all resources will stay at status INTERNAL:
    from metashare.repo2 import verify_at_startup
    verify_at_startup() # may raise Exception, which we don't want to catch.

    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    
    successful_imports = []
    erroneous_imports = []
    from metashare.xml_utils import import_from_file
    from metashare.storage.models import PUBLISHED
    
    for filename in sys.argv[1:]:
        temp_file = open(filename, 'rb')
        success, failure = import_from_file(temp_file, filename, PUBLISHED)
        successful_imports += success
        erroneous_imports += failure
        temp_file.close()
    
    print "Done.  Successfully imported {0} files into the database, errors " \
      "occurred in {1} cases.".format(len(successful_imports), len(erroneous_imports))
    if len(erroneous_imports) > 0:
        print "The following files could not be imported:"
        for descriptor, exception in erroneous_imports:
            if isinstance(exception.args, basestring):
                print "\t{}: {}".format(descriptor, ' '.join(exception.args))
            else:
                print "\t{}: {}".format(descriptor, exception.args)
      
