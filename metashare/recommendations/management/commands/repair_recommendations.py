"""
Management utility to check the recommendations for consistency and remove links
to invalid documents.
"""
from django.core.management.base import BaseCommand
from metashare.recommendations.recommendations import repair_recommendations

class Command(BaseCommand):
    
    help = 'Check the recommendations for consistency and remove links to invalid documents'
    
    def handle(self, *args, **options):
        """
        Repair recommendations.
        """
        repair_recommendations()

