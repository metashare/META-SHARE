#!/usr/bin/env python

import os
import sys

# Magic python path, based on http://djangosnippets.org/snippets/281/
from os.path import abspath, dirname, join
parentdir = dirname(dirname(abspath(__file__)))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(1, parentdir)


try:
    from metashare import settings

except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the " \
      "directory containing %r. It appears you've customized things.\n" \
      "You'll have to run django-admin.py, passing it your settings " \
      "module.\n(If the file settings.py does indeed exist, it's causing" \
      " an ImportError somehow.)\n" % __file__)
    sys.exit(1)



def print_usage():
    print "\n\tusage: {0} [--id-file=idfile] <file.xml|archive.zip> [<file.xml|archive." \
      "zip> ...]\n".format(sys.argv[0])
    print "  --id-file=idfile : print identifier of imported resources in idfile"
    return

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'metashare.settings'
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
    sys.path.append(PROJECT_HOME)
    
    # Check command line parameters first.
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(-1)
    
    # Check command line options for --id-file
    id_filename = None
    arg_num=1
    if sys.argv[arg_num].startswith("--id-file="):
        opt_len = len("--id-file=")
        id_filename = sys.argv[arg_num][opt_len:]
        arg_num = arg_num + 1
        if len(id_filename) == 0:
            print "Incorrect option"
            print_usage()
            sys.exit(-1)
        if len(sys.argv) < 3:
            print_usage()
            sys.exit(-1)
        

    # Check that SOLR is running, or else all resources will stay at status INTERNAL:
    from metashare.repository import verify_at_startup
    verify_at_startup() # may raise Exception, which we don't want to catch.

    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = 'True'
    
    successful_imports = []
    erroneous_imports = []
    from metashare.xml_utils import import_from_file
    from metashare.storage.models import PUBLISHED, MASTER
    from metashare.repository.supermodel import OBJECT_XML_CACHE
    
    # Clean cache before starting the import process.
    OBJECT_XML_CACHE.clear()
    
    for filename in sys.argv[arg_num:]:
        temp_file = open(filename, 'rb')
        success, failure = import_from_file(temp_file, filename, PUBLISHED, MASTER)
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
    
    # Salvatore:
    # This is useful for tracking where the resource is stored.
    # It is used by some scripts for testing purposes
    if not id_filename is None:
        id_file = open(id_filename, 'w')
        for resource in successful_imports:
            id_file.write('--->RESOURCE_ID:{0};STORAGE_IDENTIFIER:{1}\n'\
                .format(resource.id, resource.storage_object.identifier))
        id_file.close()

    # Be nice and cleanup cache...
    _cache_size = sum([len(x) for x in OBJECT_XML_CACHE.values()])
    OBJECT_XML_CACHE.clear()
    print "Cleared OBJECT_XML_CACHE ({} bytes)".format(_cache_size)
    
    from django.core.management import call_command
    call_command('rebuild_index', interactive=False)
