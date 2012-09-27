"""
Download GeoIP database from http://geolite.maxmind.com/
"""
import urllib2
import logging
import gzip
import os
from django.core.management.base import BaseCommand
from metashare import settings
from metashare.settings import ROOT_PATH, GEOIP_DATA_URL

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)

class Command(BaseCommand):

    help = 'Downloading GeoIP data'

    def handle(self, *args, **options):
        geogzfile = ROOT_PATH+'/stats/resources/GeoIP.dat.gz'
        geodatfile = ROOT_PATH+'/stats/resources/GeoIP.dat'
        try:
            urldoc = urllib2.urlopen(GEOIP_DATA_URL)
            with open(geogzfile, 'wb') as out_file_handle:
                out_file_handle.write(urldoc.read())

            if os.path.exists(geogzfile) and os.path.getsize(geogzfile) > 0:
                try:
                    with gzip.open(geogzfile, 'rb') as db_file_handle, \
                            open(geodatfile, 'wb') as datfile:
                        datfile.write(db_file_handle.read())
                    LOGGER.info("Updated the GeoIP database file at: %s",
                        geodatfile)
                except:
                    LOGGER.fatal("Gzip decompression failure on %s.", geogzfile,
                        exc_info=True)
        except:
            LOGGER.error("Downloading a new GeoIP database from %s failed. "
                    "Continuing to use the existing version.", GEOIP_DATA_URL,
                exc_info=True)
