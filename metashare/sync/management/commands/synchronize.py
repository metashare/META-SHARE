"""
Management utility to trigger synchronization.
"""

import sys
import logging

from metashare import settings
from metashare.sync.sync_utils import login, get_inventory, get_full_metadata, \
    remove_resource
from django.core.management.base import BaseCommand
from optparse import make_option
from metashare.storage.models import StorageObject, PROXY, REMOTE, add_or_update_resource
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
            core_nodes = getattr(settings, 'CORE_NODES', {})
            for key, value in core_nodes.items():
                if value['NAME'] == node_name:
                    Command.sync_with_nodes({key: value}, False, id_file)
                    break

            proxied_nodes = getattr(settings, 'PROXIED_NODES', {})
            for key, value in proxied_nodes.items():
                if value['NAME'] == node_name:
                    Command.sync_with_nodes({key: value}, True, id_file)
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
        for node_id, node in nodes.items():
            LOGGER.info("syncing with node {} at {} ...".format(
              node_id, node['URL']))
            try:
                Command.sync_with_single_node(
                  node_id, node, is_proxy, id_file=id_file)
            except:
                LOGGER.error('There was an error while trying to sync with '
                    'node "%s":', node_id, exc_info=True)

    @staticmethod
    def sync_with_single_node(node_id, node, is_proxy, id_file=None):
        """
        Synchronizes this META-SHARE node with another META-SHARE node using
        the given node description.
        
        `node_id` is the unique key under which the node settings are stored in 
            the dict
        `node` is a dict with synchronization settings for the node to
            synchronize with
        `is_proxy` must be True if this node is a proxy for the given nodes;
            it must be False if the given nodes are not proxied by this node
        """

        # login
        url = node['URL']
        user_name = node['USERNAME']
        password = node['PASSWORD']
        opener = login("{0}/login/".format(url), user_name, password)
        
        # create inventory url
        inv_url = "{0}/sync/?".format(url)
        # add sync protocols to url
        for index, _prot in enumerate(settings.SYNC_PROTOCOLS):
            inv_url = inv_url + "sync_protocol={}".format(_prot)
            if (index < len(settings.SYNC_PROTOCOLS) - 1):
                inv_url = inv_url + "&"
        
        # get the inventory list 
        remote_inventory = get_inventory(opener, inv_url)
        remote_inventory_count = len(remote_inventory)
        sys.stdout.write("\nRemote node " + BOLD + url + RESET + " contains " \
          + BOLD + str(remote_inventory_count) + " resources." + RESET + "\n")
        LOGGER.info("Remote node {} contains {} resources".format(
          node_id, remote_inventory_count))
        
        # create a dictionary of uuid's and digests of resource from the local 
        # inventory that stem from the remote node
        local_inventory = {}
        remote_storage_objects = StorageObject.objects.filter(source_node=node_id)
        for item in remote_storage_objects:
            local_inventory[item.identifier] = item.digest_checksum
        local_inventory_count = len(local_inventory)
        sys.stdout.write("\nLocal node contains " + BOLD + str(local_inventory_count) \
          + " resources." + RESET + "\n")
        LOGGER.info("Local node contains {} resources stemming from remote node {}".format(
          local_inventory_count, node_id))
        
        # create three lists:
        # 1. list of resources to be added - resources that exist in the remote
        # inventory but not in the local
        # 2. list of resources to be updated - resources that exist in both
        # inventories but the remote is different from the local
        # 3. list of resources to be removed - resources that exist in the local
        # inventory but not in the remote
        resources_to_add = []
        resources_to_update = []
        
        for remote_res_id, remote_digest in remote_inventory.iteritems():
            if remote_res_id in local_inventory:
                # compare checksums; if they differ, the resource has to be updated
                if remote_digest != local_inventory[remote_res_id]:
                    resources_to_update.append(remote_res_id)
                else:
                    # resources have the same checksum, nothing to do
                    pass
                # remove the resource from the local inventory; what is left
                # in the local inventory after this loop are the resources
                # to delete
                del local_inventory[remote_res_id]
            else:
                # resource exists in the remote inventory but not in the local;
                # make sure that the remote node does not try to add a resource
                # for which we now that it stems from ANOTHER node or OUR node 
                try:
                    local_so = StorageObject.objects.get(identifier=remote_res_id)
                    source_node = local_so.source_node
                    if not source_node:
                        source_node = 'LOCAL NODE'
                    LOGGER.warn(
                      "Node {} wants to add resource {} that we already know from node {}".format(
                      node_id, remote_res_id, source_node))
                except ObjectDoesNotExist:
                    resources_to_add.append(remote_res_id)
        # remaining local inventory resources are to delete
        resources_to_delete = local_inventory.keys()

        # print informative messages to the user
        resources_to_add_count = len(resources_to_add)
        resources_to_update_count = len(resources_to_update)
        resources_to_delete_count = len(resources_to_delete)
        LOGGER.info("{} resources will be added".format(resources_to_add_count))
        LOGGER.info("{} resources will be updated".format(resources_to_update_count))          
        LOGGER.info("{} resources will be deleted".format(resources_to_delete_count))          
        if ((resources_to_add_count == 0) and (resources_to_update_count == 0)):
            LOGGER.info("There are no resources marked for updating!")
        else:
            # if there are resources to add or update
            LOGGER.info("\n" + BOLD + \
              ("No" if resources_to_add_count == 0 \
              else str(resources_to_add_count)) + \
              " new resource" + ("" if resources_to_add_count == 1 else "s") \
              + RESET + " will be added to your repository.")
            LOGGER.info("\n" + BOLD + \
              ("No" if resources_to_update_count == 0 \
              else str(resources_to_update_count)) + \
              " resource" + ("" if resources_to_update_count == 1 else "s") \
              + RESET + " will be updated in your repository.")
            LOGGER.info("Importing and Indexing...\n")
        
        if is_proxy:
            _copy_status = PROXY
        else:
            _copy_status = REMOTE
        
        # add resources from remote inventory
        for res_id in resources_to_add:
            try:
                res_obj = Command._get_remote_resource(
                  res_id, remote_inventory[res_id], node_id, node, opener, _copy_status)
                LOGGER.info("adding resource {}".format(res_obj.storage_object.identifier))
                if not id_file is None:
                    id_file.write("--->RESOURCE_ID:{0};STORAGE_IDENTIFIER:{1}\n"\
                        .format(res_obj.id, res_obj.storage_object.identifier))
            except:
                LOGGER.error("Error while adding resource {}".format(res_id))
                sys.stdout.write("Error while adding resource {}".format(res_id))
        
        # update resources from remote inventory
        for res_id in resources_to_update:
            try:
                res_obj = Command._get_remote_resource(
                  res_id, remote_inventory[res_id], node_id, node, opener, _copy_status)
                LOGGER.info("updating resource {}".format(res_obj.storage_object.identifier))
                if not id_file is None:
                    id_file.write("--->RESOURCE_ID:{0};STORAGE_IDENTIFIER:{1}\n"\
                        .format(res_obj.id, res_obj.storage_object.identifier))
                    if remote_inventory[res_id] != res_obj.storage_object.digest_checksum:
                        id_file.write("Different digests!\n")
            except:
                LOGGER.error("Error while updating resource {}".format(res_id))
                sys.stdout.write("Error while updating resource {}\n".format(res_id))

        # delete resources from remote inventory
        resources_to_delete_count = len(resources_to_delete)
        LOGGER.info("\nRemote node " + BOLD + url + RESET + " lists " \
          + BOLD + str(resources_to_delete_count) + " resources " + RESET + "as removed." )
        
        removed_count = 0
        for res_id in resources_to_delete:
            try:
                sys.stdout.write("\nRemoving id {}...\n".format(res_id))
                LOGGER.info("removing resource {}".format(res_id))
                removed_count += 1
                _so_to_remove = StorageObject.objects.get(identifier=res_id)
                remove_resource(_so_to_remove) 
            except:
                LOGGER.error("Error while removing resource {}".format(res_id))
                sys.stdout.write("Error while removing resource {}\n".format(res_id))
                
        sys.stdout.write("\n{} resources removed\n\n\n".format(removed_count))
            

    @staticmethod
    def _get_remote_resource(resource_id, resource_digest, node_id, node, opener, copy_status):
        """
        Retrieves from the given node the resource for the given id and
        adds/updates it at the current node with the given copy status using the
        given opener 
        """
        # Get the json storage object and the actual metadata xml
        storage_json, resource_xml_string = \
          get_full_metadata(opener, "{0}/sync/{1}/metadata/" \
                .format(node['URL'], resource_id), resource_digest)
        res_obj = add_or_update_resource(storage_json, resource_xml_string,
                        resource_digest, copy_status, source_node=node_id)
        return res_obj
