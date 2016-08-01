
from django.core.management.base import BaseCommand
from metashare.repository.models import resourceInfoType_model
from optparse import make_option

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-x', '--extended', action='store_true', dest='extended',
                    default=None, help='print extended information'),
    )

    def handle(self, *args, **options):
        extended = options.get('extended', None)
        for res in resourceInfoType_model.objects.all():
            sto_obj = res.storage_object
            if sto_obj.published:
                extra_info = ''
                if extended:
                    extra_info = ':{}'.format(sto_obj.source_url)
                print "{1}:{2}{3}".format(res.id, sto_obj.identifier, sto_obj.digest_checksum, extra_info)
        return

