#!/usr/bin/env python

import sys
import os
from os.path import abspath, dirname, join
parentdir = dirname(dirname(abspath(__file__)))

# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, parentdir)
try:
    import settings # Assumed to be in the same directory.

except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the " \
      "directory containing %r. It appears you've customized things.\n" \
      "You'll have to run django-admin.py, passing it your settings " \
      "module.\n(If the file settings.py does indeed exist, it's causing" \
      " an ImportError somehow, for example if you shouldn't have created a " \
      "custom 'local_settings.py' file.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    # MS, 21.03.2012: Add a fail-early verification "hook"
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
