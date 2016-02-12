import django
from django.conf import settings
from metashare import settings as my_settings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metashare.settings")
settings.configure(default_settings=my_settings, DEBUG=True)
django.setup()



