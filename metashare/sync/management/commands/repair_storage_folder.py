"""
Management utility to repair content of storage folder by forcing the recreation
of all files. Superfluous files are deleted."
"""
from django.core.management.base import BaseCommand
from metashare.storage.models import repair_storage_folder

class Command(BaseCommand):
    
    help = 'Repair content of storage folder by forcing the recreation of all ' + \
      'files. Superfluous files are deleted.'
    
    def handle(self, *args, **options):
        repair_storage_folder()