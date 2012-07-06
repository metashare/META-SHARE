"""
Management utility to trigger digest updating.
"""
from django.core.management.base import BaseCommand
from metashare import settings
from metashare.storage.models import PROXY, StorageObject, RemovedObject
from metashare.sync.sync_utils import remove_resource

class Command(BaseCommand):
    
    help = 'Checks for each proxy resource if its source node is still in the' \
      + 'in the proxied node list; if not removes the resource'
    
    def handle(self, *args, **options):
        
        # collect current proxy urls
        proxy_urls = []
        for proxy in settings.PROXIED_NODES:
            proxy_urls.append(settings.PROXIED_NODES[proxy]['URL'])   

        # iterate over proxy resources and check for each if its source url
        # is still listed in the proxied node list
        for proxy_res in StorageObject.objects.filter(copy_status=PROXY):
            if not proxy_res.source_url in proxy_urls:
                # delete the associated resource and create a RemovedObject
                # to let the other nodes know that the resource has been removed
                # when synchronizing
                rem_obj = RemovedObject.objects.create(identifier=proxy_res.identifier)
                rem_obj.save()
                remove_resource(proxy_res)

