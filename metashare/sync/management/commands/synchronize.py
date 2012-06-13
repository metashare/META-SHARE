"""
Management utility to trigger synchronization.
"""

from settings import CORE_NODES
from sync.sync_utils import login, get_inventory, get_full_metadata
from xml_utils import xml_compare
from StringIO import StringIO
from django.core.management.base import BaseCommand
from metashare.storage.models import StorageObject, MASTER

class Command(BaseCommand):
    # Get the list of the servers to be querried
    core_nodes = CORE_NODES
    print core_nodes
    for server in core_nodes.values():
        updatable_resources = []
        local_inventory = []
        # Login
        url = server['URL']
        user_name = server['USERNAME']
        password = server['PASSWORD']
        print url + "  " + user_name + "  " + password
        opener = login("{0}/login/".format(url), user_name, password)
        
        # Get the inventory list. 
        inventory = get_inventory(opener, "{0}/sync/".format(url))
        print "REMOTE INVENTORY: \n" + str(inventory)
        
        # Get a list of uuid's and digests from the local inventory
        non_master_storage_objects = StorageObject.objects.all() #.exclude(copy_status=MASTER)
        for item in non_master_storage_objects:
            local_inventory.append({'id':str(item.identifier), 'digest':str(item.digest_checksum)})
        print "LOCAL INVENTORY: \n" + str(local_inventory)
        
        # Get the items that need to be updated.
        # For each item in the inventory, compare them with existing resource.
        

        
#        for item in inventory:
#            if item.
            
            
#            uuid = item
            #storage_json, resource_xml_string = get_full_metadata(opener, "{0}/sync/{1}/metadata/".format(base_url, uuid))
        # If they have differences, add the item to the updateable list
            
        
    
        
        # For each updateable item:
            # Update item.
            # TODO: Error handling in case connection is lost.
            # TODO: Error handling in case item cannot be updated.
    
    
    
    # 
    
    
    
    
    
    
