"""
Management utility to check the recommendations for consistency and remove links
to invalid documents.
"""
from django.core.management.base import BaseCommand
from metashare.recommendations.recommendations import repair_recommendations
from metashare.utils import Lock


class Command(BaseCommand):
    
    help = 'Check the recommendations for consistency and remove links to invalid documents'
    
    def handle(self, *args, **options):
        """
        Repair recommendations.
        """
        try:
            # before starting, make sure to lock the storage so that any other
            # processes with heavy/frequent operations on the storage don't get
            # in our way
            lock = Lock('storage')
            lock.acquire()

            repair_recommendations()
        finally:
            lock.release()
