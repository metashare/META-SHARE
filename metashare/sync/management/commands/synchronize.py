"""
Management utility to trigger synchronization.
"""

import getpass
import re
import sys
import urllib
import urllib2
import contextlib
import json

from metashare.settings import CORE_NODES
from zipfile import ZipFile
from StringIO import StringIO

from optparse import make_option
from django.contrib.auth.models import User, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    # Get the list of the servers to be querried
    for server in CORE_NODES:
         
    
    
    # Query each server. Add some error handling.
    # For each server:
        # Login

        # Get the inventory list. 
    
    

        # Get the items that need to be updated.
        
        # For each updateable item:
            # Update item.
            # TODO: Error handling in case connection is lost.
            # TODO: Error handling in case item cannot be updated.
    
    
    
    # 
    
    
    
    
    
    
