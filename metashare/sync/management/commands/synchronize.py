"""
Management utility to trigger synchronization.
"""

import sys
from metashare import settings
from metashare.sync.sync_utils import login, get_inventory, get_full_metadata
from django.core.management.base import BaseCommand
from metashare.storage.models import StorageObject, MASTER, PROXY, REMOTE, \
    update_resource

# Constants to show bold-face fonts in standard output
BOLD = "\033[1m"
RESET = "\033[0;0m"

class Command(BaseCommand):
    
    help = 'Synchronizes with a predefined list of META-SHARE nodes'
    
    def handle(self, *args, **options):
        """
        Synchronizes this META-SHARE node with the locally configured other
        META-SHARE nodes.
        """
        Command.sync_with_nodes(getattr(settings, 'CORE_NODES', {}), False)
        Command.sync_with_nodes(getattr(settings, 'PROXIED_NODES', {}), True)


    @staticmethod
    def sync_with_nodes(nodes, is_proxy):
        """
        Synchronizes this META-SHARE node with the given other META-SHARE nodes.
        
        `nodes` is a dict of dicts with synchronization settings for the nodes
            to synchronize with
        `is_proxy` must be True if this node is a proxy for the given nodes;
            it must be False if the given nodes are not proxied by this node
        """
        for server in nodes.values():
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
            remote_inventory_count = len(remote_inventory)
            sys.stdout.write("\nRemote node " + BOLD + url + RESET + " contains " + BOLD + str(remote_inventory_count) + " resources.\n" + RESET)
            
            # Get a list of uuid's and digests from the local inventory
            non_master_storage_objects = StorageObject.objects.exclude(copy_status=MASTER)
            for item in non_master_storage_objects:
                local_inventory.append({'id':str(item.identifier), 'digest':str(item.digest_checksum)})
            local_inventory_count = len(local_inventory)
            sys.stdout.write("\nLocal node contains " + BOLD + str(local_inventory_count) + " resources.\n" + RESET)

            # Create an list of ids to speed-up matching
            local_inventory_indexed = []
            for item in local_inventory:
                local_inventory_indexed.append(item['id'])
            
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
                        if (item_id == local_item['id']) \
                          and not (item['digest'] == local_item['digest']):
                            resources_to_update.append(item)

 
            # Print informative messages to the user
            new_resources_count = len(new_resources)
            resources_to_update_count = len(resources_to_update)            
            if ((new_resources_count == 0) and (resources_to_update_count == 0)):
                sys.stdout.write("\nThere are no resources marked \
                  for updating!\n")
            else:           
                sys.stdout.write("\n" + BOLD + \
                  ("No" if new_resources_count == 0 \
                  else str(new_resources_count)) + \
                  " new resource" + ("" if new_resources_count == 1 else "s") \
                  + RESET + " will be added to your repository.\n")
                sys.stdout.write("\n" + BOLD + \
                  ("No" if resources_to_update_count == 0 \
                  else str(resources_to_update_count)) + \
                  " resource" + ("" if resources_to_update_count == 1 else "s") \
                  + RESET + " will be updated in your repository.\n")
                sys.stdout.write("\nImporting and Indexing...\n")

                if is_proxy:
                    _copy_status = PROXY
                else:
                    _copy_status = REMOTE
                
                # Get the full xmls from remore inventory and update local inventory
                for resource in new_resources:
                    # Get the json storage object and the actual metadata xml
                    storage_json, resource_xml_string = \
                      get_full_metadata(opener, "{0}/sync/{1}/metadata/" \
                            .format(url, resource['id']), resource['digest'])
                    update_resource(storage_json, resource_xml_string,
                                    resource['digest'], _copy_status)

                for resource in resources_to_update:
                    # Get the json storage object and the actual metadata xml
                    storage_json, resource_xml_string = \
                      get_full_metadata(opener, "{0}/sync/{1}/metadata/" \
                            .format(url, resource['id']), resource['digest'])
                    update_resource(storage_json, resource_xml_string,
                                    resource['digest'], _copy_status)

            sys.stdout.write("\n\n")
