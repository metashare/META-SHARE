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
from metashare.sync.sync_utils import login
from zipfile import ZipFile
from StringIO import StringIO

from optparse import make_option
from django.contrib.auth.models import User, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    # Get the list of the servers to be querried
    core_nodes = CORE_NODES
    for server in core_nodes:
        # Login
        user_name = 'test_sync'
        password =  'test_sync123'
        opener = login("{0}/login/".format(server.URL), user_name, password)
        
        # Get the inventory list. 
        
        
        # Get the items that need to be updated.
        # For each item in the inventory, compare them
        # If they have differences, add the item to the updateable list
        
        
    
        
        # For each updateable item:
            # Update item.
            # TODO: Error handling in case connection is lost.
            # TODO: Error handling in case item cannot be updated.
    
    
    
    # 
    
    
    
    
    
    
