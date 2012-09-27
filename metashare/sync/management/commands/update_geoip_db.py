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
            with open(geogzfile, 'wb') as db:
                db.write(urldoc.read())
                
            if os.path.exists(geogzfile) and os.path.getsize(geogzfile) > 0:
                try:
                    db = gzip.open(geogzfile, 'r:gz')
                    datfile = open(geodatfile, 'w')
                    datfile.write(db.read())
                    datfile.close()
                    LOGGER.info("Updated "+geodatfile+" file")
                except:
                    LOGGER.info("ERROR! Gzip decompression failure on "+geogzfile+".")
        except:
            LOGGER.info("ERROR! Download the GeoIP resource "+GEOIP_DATA_URL+" failed")

