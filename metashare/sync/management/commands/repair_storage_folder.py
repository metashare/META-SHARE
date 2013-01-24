"""
Management utility to repair content of storage folder by forcing the recreation
of all files. Superfluous files are deleted."
"""
from django.core.management.base import BaseCommand
from metashare.storage.models import repair_storage_folder
from metashare.utils import Lock


class Command(BaseCommand):
    
    help = 'Repair content of storage folder by forcing the recreation of all ' + \
      'files. Superfluous files are deleted.'
    
    def handle(self, *args, **options):
        try:
            # before starting to repair the storage folder, make sure to lock
            # the storage so that any other processes with heavy/frequent
            # operations on the storage don't get in our way
            lock = Lock('storage')
            lock.acquire()
            repair_storage_folder()
        finally:
            lock.release()
