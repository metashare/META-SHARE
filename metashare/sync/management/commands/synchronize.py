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
from metashare.storage.models import StorageObject, PROXY, REMOTE, \
    add_or_update_resource, RemovedObject
from django.core.exceptions import ObjectDoesNotExist

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
        server_name = server['NAME']
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
        LOGGER.info("Remote server {} contains {} resources".format(
          server_name, remote_inventory_count))
        
        # Get a list of uuid's and digests of resource from the local inventory
        # that stem from the remote server
        remote_storage_objects = StorageObject.objects.filter(source_node=server_name)
        for item in remote_storage_objects:
            local_inventory.append({'id':str(item.identifier), 'digest':str(item.digest_checksum)})
        local_inventory_count = len(local_inventory)
        sys.stdout.write("\nLocal node contains " + BOLD + str(local_inventory_count) \
          + " resources.\n" + RESET)
        LOGGER.info("Local server contains {} resources stemming from remote server {}".format(
          local_inventory_count, server_name))
        
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
                # make sure that the remote server does not try to add a resource
                # for which we now that it stems from ANOTHER node or OUR node 
                try:
                    local_so = StorageObject.objects.get(identifier=item_id)
                    source_node = local_so.source_node
                    if not source_node:
                        source_node = 'LOCAL SERVER'
                    LOGGER.warn(
                      "{} wants to add resource {} that we already know from {}".format(
                      server_name, item_id, source_node))
                except ObjectDoesNotExist:
                    new_resources.append(item)
            else:
                # Find the corresponding item in the local inventory
                # and compare digests
                for local_item in local_inventory:
                    if item_id == local_item['id']:
                        if item['digest'] != local_item['digest']:
                            resources_to_update.append(item)
                        break

        # Print informative messages to the user
        new_resources_count = len(new_resources)
        resources_to_update_count = len(resources_to_update)
        LOGGER.info("{} resources will be added".format(new_resources_count))
        LOGGER.info("{} resources will be updated".format(resources_to_update_count))          
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
            
            # Get the full xmls from remote inventory and update local inventory
            for resource in new_resources:
                res_obj = Command._get_remote_resource(resource, server, opener, _copy_status)
                LOGGER.info("adding resource {}".format(res_obj.storage_object.identifier))
                if not id_file is None:
                    id_file.write("--->RESOURCE_ID:{0};STORAGE_IDENTIFIER:{1}\n"\
                        .format(res_obj.id, res_obj.storage_object.identifier))
        
            for resource in resources_to_update:
                res_obj = Command._get_remote_resource(resource, server, opener, _copy_status)
                LOGGER.info("updating resource {}".format(res_obj.storage_object.identifier))
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
        LOGGER.info("Remote server {} lists {} resources as removed".format(
          server_name, remote_inventory_removed_count))
        
        # add to removed resources those that have silently disappeared; these
        # are resources that are not mentioned in either the inventory or the 
        # 'removed' list
        silently_removed = list(local_inventory_indexed)
        # remove the explicitly remove resources
        silently_removed = \
          [n for n in silently_removed if n not in remote_inventory_removed]
        # remove the remote inventory
        for item in remote_inventory_existing:
            item_id = item['id']
            if item_id in silently_removed:
                silently_removed.remove(item_id)
        LOGGER.info("{} resources have silently disappeared".format(
          len(silently_removed)))
        
        remote_inventory_removed.append(silently_removed)
        
        removed_count = 0
        for removed_id in remote_inventory_removed:
            if removed_id in local_inventory_indexed:
                # remove resource from this node;
                # if it is a PROXY copy, also create a corresponding removed
                # object, so that the removal is propagated to other
                # META-SHARE Managing Nodes (aka. inner nodes)
                sys.stdout.write("\nRemoving id {}...\n".format(removed_id))
                LOGGER.info("removing resource {}".format(removed_id))
                removed_count += 1
                _so_to_remove = StorageObject.objects.get(identifier=removed_id)
                if _so_to_remove.copy_status is PROXY:
                    _rem_obj = RemovedObject.objects.create(identifier=removed_id)
                    _rem_obj.save()
                remove_resource(_so_to_remove) 
                # also update the local inventory index
                local_inventory_indexed.remove(removed_id)
                
        sys.stdout.write("\n{} resources removed\n".format(removed_count))
        LOGGER.info("A total of {} resources have been removed".format(removed_count))
            

    @staticmethod
    def _get_remote_resource(digest_item, server, opener, copy_status):
        """
        retrieves from the given server the resource for the given inventory 
        item consisting of the resource id and its digest and add/update it at
        the current node with the given copy status using the given opener 
        """
        # Get the json storage object and the actual metadata xml
        storage_json, resource_xml_string = \
          get_full_metadata(opener, "{0}/sync/{1}/metadata/" \
                .format(server['URL'], digest_item['id']), digest_item['digest'])
        res_obj = add_or_update_resource(storage_json, resource_xml_string,
                        digest_item['digest'], copy_status, 
                        source_node=server['NAME'])
        return res_obj
        
