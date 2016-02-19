import django
from os.path import abspath, dirname, join
from django.conf import settings
from metashare import settings as my_settings
import os, sys

parentdir = dirname(dirname(abspath(__file__)))

sys.path.insert(0, join(parentdir, 'git_zone', 'lib', 'python2.7', 'site-packages'))
sys.path.insert(0, join(parentdir, 'git_zone'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metashare.settings")

settings.configure(default_settings=my_settings, DEBUG=True)
django.setup()



