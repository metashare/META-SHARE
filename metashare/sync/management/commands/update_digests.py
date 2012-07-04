"""
Management utility to trigger digest updating.
"""
from django.core.management.base import BaseCommand
from metashare.storage.models import update_digests

class Command(BaseCommand):
    
    help = 'Updates the resource digests if they are older than MAX_DIGEST_AGE / 2 seconds'
    
    def handle(self, *args, **options):
        """
        Update digests.
        """
        update_digests()

        