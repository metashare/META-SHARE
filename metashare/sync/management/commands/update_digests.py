"""
Management utility to trigger digest updating.
"""
from django.core.management.base import BaseCommand
from metashare.storage.models import update_digests
from metashare.utils import Lock


class Command(BaseCommand):
    
    help = 'Updates the resource digests if they are older than MAX_DIGEST_AGE / 2 seconds'
    
    def handle(self, *args, **options):
        """
        Update digests.
        """
        try:
            # before starting the digest updating, make sure to lock the storage
            # so that any other processes with heavy/frequent operations on the
            # storage don't get in our way
            lock = Lock('storage')
            lock.acquire()
            update_digests()
        finally:
            lock.release()
