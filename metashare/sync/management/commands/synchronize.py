"""
Management utility to trigger synchronization.
"""

from settings import CORE_NODES
from sync.sync_utils import login, get_inventory, get_full_metadata
from xml_utils import xml_compare
from StringIO import StringIO
from django.core.management.base import BaseCommand
from metashare.storage.models import StorageObject, MASTER, update_resource


class Command(BaseCommand):
    
    help = 'Synchronizes with a predefined list of META-SHARE nodes'
    
    def handle(self, *args, **options):
        # Get the list of the servers to be querried
        core_nodes = CORE_NODES
        print core_nodes
        
        for server in core_nodes.values():
            new_resources = []
            resources_to_update = []
            local_inventory = []

            # Login
            url = server['URL']
            user_name = server['USERNAME']
            password = server['PASSWORD']
            opener = login("{0}/login/".format(url), user_name, password)
            
            # Get the inventory list. 
            remote_inventory = get_inventory(opener, "{0}/sync/".format(url))
            print "REMOTE INVENTORY: \n" + str(remote_inventory)
            
            # Get a list of uuid's and digests from the local inventory
            non_master_storage_objects = StorageObject.objects.exclude(copy_status=MASTER)
            for item in non_master_storage_objects:
                local_inventory.append({'id':str(item.identifier), 'digest':str(item.digest_checksum)})
            print "\nLOCAL INVENTORY: \n" + str(local_inventory)
            
            
            # Create an list of ids to speed-up matching
            local_inventory_indexed = []
            for item in local_inventory:
                local_inventory_indexed.append(item['id'])
            print "\nINVENTORY LIST : \n" + str(local_inventory_indexed)
            
            # Create two lists:
            # 1. Containing items to be added - items that exist in the 
            # remote inventory and not in the local.
            # 2. Containing items to be updated - items that exist in both
            # inventories but the remote is different from the local
            for item in remote_inventory:
                item_id = item['id']
                if item_id not in local_inventory_indexed:
                    new_resources.append(item)
                else:
                    # Find the corresponding item in the local inventory
                    # and compare digests
                    for local_item in local_inventory:
                        if (item_id == local_item['id']) and (item['digest'] <> local_item['digest']):
                            resources_to_update.append(item)
                        
                
            print "\nNEW RESOURCES: \n" + str(new_resources)
            print "\nRESOURCES TO UPDATE: \n" + str(resources_to_update)


            for resource in new_resources:
                # Get the json storage object and the actual metadata xml
                storage_json, resource_xml_string = get_full_metadata(opener, "{0}/sync/{1}/metadata/".format(url, resource['id']))
                update_resource(storage_json, resource_xml_string)
            
            for resource in resources_to_update:
                # Get the json storage object and the actual metadata xml
                storage_json, resource_xml_string = get_full_metadata(opener, "{0}/sync/{1}/metadata/".format(url, resource['id']))
                update_resource(storage_json, resource_xml_string)
            
