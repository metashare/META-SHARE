
from django.core.management.base import BaseCommand
from metashare.repository.models import resourceInfoType_model

class Command(BaseCommand):
    def handle(self, *args, **options):
        for res in resourceInfoType_model.objects.all():
            sto_obj = res.storage_object
            if sto_obj.published:
                print "{1}:{2}".format(res.id, sto_obj.identifier, sto_obj.digest_checksum)
        return

