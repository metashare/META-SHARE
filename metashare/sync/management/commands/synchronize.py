"""
Management utility to trigger synchronization.
"""

import sys
import logging
import traceback
from metashare import settings
from metashare.sync.sync_utils import login, get_inventory, get_full_metadata, \
    remove_resource
from django.core.management.base import BaseCommand
from optparse import make_option
from metashare.storage.models import StorageObject, MASTER, PROXY, REMOTE, \
    update_resource, RemovedObject

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)

# Constants to show bold-face fonts in standard output
BOLD = "\033[1m"
RESET = "\033[0;0m"

class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('-i', '--id-file', action='store', dest='id_filename',
                    default=None, help='file for IDs of new/modified resource'),
        make_option('-n', '--node', action='store', dest='node',
                    default=None, help='sync only with specified node'),
    )

    help = 'Synchronizes with a predefined list of META-SHARE nodes'
    
    def handle(self, *args, **options):
        """
        Synchronizes this META-SHARE node with the locally configured other
        META-SHARE nodes.
        """
        # Check for --id-file option
        id_filename = options.get('id_filename', None)
        id_file = None
        if not id_filename is None:
            if len(id_filename) > 0:
                try:
                    id_file = open(id_filename, 'w')
                except:
                    print "Impossible to open file {0}".format(id_filename)
                    print "  IDs will not be printed"
      
        node_name = options.get('node', None)
        if node_name is None:
            Command.sync_with_nodes(getattr(settings, 'CORE_NODES', {}), False, id_file)
            Command.sync_with_nodes(getattr(settings, 'PROXIED_NODES', {}), True, id_file)
        else:
            # Synchronize only with the given node
            node_list = {}
            core_nodes = getattr(settings, 'CORE_NODES', {})
            for key, value in core_nodes.items():
                if value['NAME'] == node_name:
                    node_list.update({key, value})
                    Command.sync_with_nodes(node_list, False, id_file)
                    break

            node_list = {}
            proxied_nodes = getattr(settings, 'PROXIED_NODES', {})
            for key, value in proxied_nodes.items():
                if value['NAME'] == node_name:
                    node_list.update({key, value})
                    Command.sync_with_nodes(node_list, True, id_file)
                    break

        # Close id file if used
        if not id_file is None:
            id_file.close()

    @staticmethod
    def sync_with_nodes(nodes, is_proxy, id_file=None):
        """
        Synchronizes this META-SHARE node with the given other META-SHARE nodes.
        
        `nodes` is a dict of dicts with synchronization settings for the nodes
            to synchronize with
        `is_proxy` must be True if this node is a proxy for the given nodes;
            it must be False if the given nodes are not proxied by this node
        """
        for server in nodes.values():
            LOGGER.info("syncing with server {} at {} ...".format(
              server['NAME'], server['URL']))
            try:
                Command.sync_with_server(server, is_proxy, id_file=id_file)
            except:
                LOGGER.error(traceback.format_exc())

    @staticmethod
    def sync_with_server(server, is_proxy, id_file=None):
        """
        Synchronizes this META-SHARE node with another META-SHARE node using
        the given server description.
        
        `nodes` is a dict of dicts with synchronization settings for the nodes
            to synchronize with
        `is_proxy` must be True if this node is a proxy for the given nodes;
            it must be False if the given nodes are not proxied by this node
        """
        
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
        
        # handle existing resources
        remote_inventory_existing = remote_inventory['existing']
        remote_inventory_count = len(remote_inventory_existing)
        sys.stdout.write("\nRemote node " + BOLD + url + RESET + " contains " \
          + BOLD + str(remote_inventory_count) + " resources.\n" + RESET)
        
        # Get a list of uuid's and digests from the local inventory
        non_master_storage_objects = StorageObject.objects.exclude(copy_status=MASTER)
        for item in non_master_storage_objects:
            local_inventory.append({'id':str(item.identifier), 'digest':str(item.digest_checksum)})
        local_inventory_count = len(local_inventory)
        sys.stdout.write("\nLocal node contains " + BOLD + str(local_inventory_count) \
          + " resources.\n" + RESET)
        
        # Create an list of ids to speed-up matching
        local_inventory_indexed = []
        for item in local_inventory:
            local_inventory_indexed.append(item['id'])
        
        # Create two lists:
        # 1. Containing items to be added - items that exist in the 
        # remote inventory and not in the local.
        # 2. Containing items to be updated - items that exist in both
        # inventories but the remote is different from the local
        for item in remote_inventory_existing:
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
            sys.stdout.write("\nThere are no resources marked" +\
              " for updating!\n")
        else:
            # If there are resources to add or update
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
                res_obj = update_resource(storage_json, resource_xml_string,
                                resource['digest'], _copy_status)
                if not id_file is None:
                    id_file.write("--->RESOURCE_ID:{0};STORAGE_IDENTIFIER:{1}\n"\
                        .format(res_obj.id, res_obj.storage_object.identifier))
        
            for resource in resources_to_update:
                # Get the json storage object and the actual metadata xml
                storage_json, resource_xml_string = \
                  get_full_metadata(opener, "{0}/sync/{1}/metadata/" \
                        .format(url, resource['id']), resource['digest'])
                res_obj = update_resource(storage_json, resource_xml_string,
                                resource['digest'], _copy_status)
                if not id_file is None:
                    id_file.write("--->RESOURCE_ID:{0};STORAGE_IDENTIFIER:{1}\n"\
                        .format(res_obj.id, res_obj.storage_object.identifier))
                    if resource['digest'] != res_obj.storage_object.digest_checksum:
                        id_file.write("Different digests!\n")
        
        sys.stdout.write("\n\n")
        
        # handle removed resources
        remote_inventory_removed = remote_inventory['removed']
        remote_inventory_removed_count = len(remote_inventory_removed)
        sys.stdout.write("\nRemote node " + BOLD + url + RESET + " lists " \
          + BOLD + str(remote_inventory_removed_count) + " resources as removed.\n" + RESET)
        
        removed_count = 0
        for removed_id in remote_inventory_removed:
            if removed_id in local_inventory_indexed:
                # remove resource from this node;
                # if it is a PROXY copy, also create a corresponding removed
                # object, so that the removal is propagated to other
                # META-SHARE Managing Nodes (aka. inner nodes)
                sys.stdout.write("\nRemoving id {}...\n".format(removed_id))
                removed_count += 1
                _so_to_remove = StorageObject.objects.get(identifier=removed_id)
                if _so_to_remove.copy_status is PROXY:
                    _rem_obj = RemovedObject.objects.create(identifier=removed_id)
                    _rem_obj.save()
                remove_resource(_so_to_remove) 
                
        sys.stdout.write("\n{} resources removed\n".format(removed_count))
