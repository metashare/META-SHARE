"""
Management utility to handle removed nodes.
"""
from django.core.management.base import BaseCommand
from metashare import settings
from metashare.storage.models import PROXY, StorageObject, RemovedObject
from metashare.sync.sync_utils import remove_resource
import logging

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)

class Command(BaseCommand):
    
    args = '<node_name node_name ...>'
    help = 'Removes all resources of the nodes with the given names; ' \
      + 'if node is a proxied node, propagates the removal'
    
    def handle(self, *args, **options):
        
        for node_name in args:
            LOGGER.info("checking node {}".format(node_name))
            remove_count = 0
            for res in StorageObject.objects.filter(source_node=node_name):
                remove_count += 1
                LOGGER.info("removing resource {}".format(res.identifier))
                if res.copy_status == PROXY:
                    # if there is already a RemoveObject, we just use that
                    rem_obj = RemovedObject.objects.get_or_create(identifier=res.identifier)[0]
                    rem_obj.save()
                    LOGGER.info("creating RemovedObject for resource {}".format(
                      res.identifier))
                remove_resource(res)
            LOGGER.info("removed {} resources of node {}".format(remove_count, node_name))

