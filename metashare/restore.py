#!/usr/bin/env python

import os
import sys

# Magic python path, based on http://djangosnippets.org/snippets/281/
from os.path import abspath, dirname, join
from json import loads
parentdir = dirname(dirname(abspath(__file__)))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(1, parentdir)


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
    
    # Check that SOLR is running, or else all resources will stay at status INTERNAL:
    from metashare.repository import verify_at_startup
    verify_at_startup() # may raise Exception, which we don't want to catch.

    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = 'True'
    
    successful_restored = []
    erroneous_restored = []
    from metashare.repository.supermodel import OBJECT_XML_CACHE
    from metashare.storage.models import restore_from_folder

    # Clean cache before starting the import process.
    OBJECT_XML_CACHE.clear()
    
    # iterate over storage folder content
    for folder_name in os.listdir(settings.STORAGE_PATH):
        folder_path = os.path.join(settings.STORAGE_PATH, folder_name)
        if os.path.isdir(folder_path):
            # skip empty folders; it is assumed that this is not an error
            if os.listdir(folder_path) == []:
                continue
            try:
                print 'restoring from folder: "{0}"'.format(folder_name)
                # only restore resources with global- and local-storage.json
                _storage_global_path = '{0}/storage-global.json'.format(folder_path)
                if not os.path.isfile(_storage_global_path):
                    print 'missing global json, skipping "{}"'.format(folder_name)
                    continue
                _storage_local_path = '{0}/storage-local.json'.format(folder_path)
                if not os.path.isfile(_storage_local_path):
                    print 'missing local json, skipping "{}"'.format(folder_name)
                    continue
                # get copy status from storage-local.json
                _copy_status = 'm'
                with open(_storage_local_path, 'rb') as _in:
                    json_string = _in.read()
                    _dict = loads(json_string)
                    if _dict['copy_status']:
                        _copy_status = _dict['copy_status']
                resource = restore_from_folder(folder_name, copy_status=_copy_status)
                successful_restored += [resource]
            # pylint: disable-msg=W0703
            except Exception as problem:
                erroneous_restored += [(folder_name, problem)]

    print "Done.  Successfully restored {0} files into the database, errors " \
      "occurred in {1} cases.".format(len(successful_restored), len(erroneous_restored))
    if len(erroneous_restored) > 0:
        print "The following resources could not be restored:"
        for descriptor, exception in erroneous_restored:
            print "{}: {}".format(descriptor, exception)
    
    # Be nice and cleanup cache...
    _cache_size = sum([len(x) for x in OBJECT_XML_CACHE.values()])
    OBJECT_XML_CACHE.clear()
    print "Cleared OBJECT_XML_CACHE ({} bytes)".format(_cache_size)
    
    from django.core.management import call_command
    call_command('rebuild_index', interactive=False)

