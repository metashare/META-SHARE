#!/usr/bin/env python
"""
Created on 05.06.2012

@author: Joerg Steffen, DFKI <steffen@dfki.de>
@author: Christian Federmann <cfedermann@dfki.de>
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
    
    # Check that SOLR is running, or else all resources will stay at status INTERNAL:
    from metashare.repository import verify_at_startup
    verify_at_startup() # may raise Exception, which we don't want to catch.

    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = 'True'
    
    from metashare.storage.models import update_digests

    update_digests()
    
    from django.core.management import call_command
    call_command('rebuild_index', interactive=False)

