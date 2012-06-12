"""
Management utility to trigger synchronization.
"""

from local_settings import CORE_NODES
from sync.sync_utils import login, get_full_metadata
from xml_utils import xml_compare
from zipfile import ZipFile
from StringIO import StringIO


class Command(BaseCommand):
    # Get the list of the servers to be querried
    core_nodes = CORE_NODES
    for server in core_nodes:
        updatable_resources = []
                
        # Login
        user_name = core_nodes.username
        password = core_nodes.password
        opener = login("{0}/login/".format(server.URL), user_name, password)
        
        # Get the inventory list. 
        inventory = get_inventory(opener, "{0}/sync/".format(server.URL))
        
        # Get the items that need to be updated.
        # For each item in the inventory, compare them with existing resource.
        
        for item in inventory:
            uuid = item
            storage_json, resource_xml_string = get_full_metadata(opener, "{0}/sync/{1}/metadata/".format(base_url, uuid))
        # If they have differences, add the item to the updateable list
            
        
    
        
        # For each updateable item:
            # Update item.
            # TODO: Error handling in case connection is lost.
            # TODO: Error handling in case item cannot be updated.
    
    
    
    # 
    
    
    
    
    
    
