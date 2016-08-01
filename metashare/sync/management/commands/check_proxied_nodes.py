"""
Management utility to handle removed proxy nodes.
"""
from django.core.management.base import BaseCommand
from metashare import settings
from metashare.storage.models import PROXY, StorageObject
from metashare.sync.sync_utils import remove_resource
import sys
import logging
from metashare.utils import Lock


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)

class Command(BaseCommand):
    
    help = 'Checks for each proxy resource if its source node is still in the ' \
      + 'proxied node list; if not removes the resource'
    
    def handle(self, *args, **options):
        try:
            # before starting, make sure to lock the storage so that any other
            # processes with heavy/frequent operations on the storage don't get
            # in our way
            lock = Lock('storage')
            lock.acquire()

            # collect current proxied node ids
            proxied_ids = [p for p in settings.PROXIED_NODES]
    
            # iterate over proxy resources and check for each if its source node
            # id is still listed in the proxied node id list
            remove_count = 0
            for proxy_res in StorageObject.objects.filter(copy_status=PROXY):
                if not proxy_res.source_node in proxied_ids:
                    # delete the associated resource
                    sys.stdout.write("\nremoving proxied resource {}\n" \
                        .format(proxy_res.identifier))
                    LOGGER.info("removing from proxied node {} resource {}" \
                        .format(proxy_res.source_node, proxy_res.identifier))
                    remove_count += 1
                    remove_resource(proxy_res)
            sys.stdout.write("\n{} proxied resources removed\n" \
                .format(remove_count))
            LOGGER.info("A total of {} resources have been removed" \
                .format(remove_count))
        finally:
            lock.release()
