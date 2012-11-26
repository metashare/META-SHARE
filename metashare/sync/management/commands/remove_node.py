"""
Management utility to handle removed nodes.
"""
from django.core.management.base import BaseCommand
from metashare import settings
from metashare.storage.models import StorageObject
from metashare.sync.sync_utils import remove_resource
import logging
from metashare.utils import Lock


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)

class Command(BaseCommand):
    
    args = '<node_name node_name ...>'
    help = 'Removes all resources of the nodes with the given names'
    
    def handle(self, *args, **options):
        try:
            # before starting, make sure to lock the storage so that any other
            # processes with heavy/frequent operations on the storage don't get
            # in our way
            lock = Lock('storage')
            lock.acquire()

            for node_name in args:
                LOGGER.info("checking node {}".format(node_name))
                remove_count = 0
                for res in StorageObject.objects.filter(source_node=node_name):
                    remove_count += 1
                    LOGGER.info("removing resource {}".format(res.identifier))
                    remove_resource(res)
                LOGGER.info("removed {} resources of node {}" \
                        .format(remove_count, node_name))
        finally:
            lock.release()
