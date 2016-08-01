"""
Management utility to remove storage object for which no resourceinfotype_model
is set.
"""
from django.core.management.base import BaseCommand
from metashare.storage.models import repair_storage_objects
from metashare.utils import Lock


class Command(BaseCommand):
    
    help = 'Remove storage objects for which no resource is set.'
    
    def handle(self, *args, **options):
        try:
            # before starting to remove the storage objects, make sure to lock
            # the storage so that any other processes with heavy/frequent
            # operations on the storage don't get in our way
            lock = Lock('storage')
            lock.acquire()
            repair_storage_objects()
        finally:
            lock.release()
