import logging
from datetime import datetime, timedelta

import kronos

from django.conf import settings
from django.core.management import call_command

from metashare.accounts.models import RegistrationRequest


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)


# clean up the session database every Monday night
@kronos.register("12 4 * * 1")
def run_session_cleanup():
    LOGGER.info("Will now clean up the session database.")
    call_command('cleanup', interactive=False)


# every night remove account registration requests which are older than 3 days
@kronos.register("12 5 * * *")
def run_account_registration_request_cleanup():
    LOGGER.info("Will now clean up the account registration request database.")
    RegistrationRequest.objects.filter(
        created__lt=(datetime.now() - timedelta(days=3))).delete()


# periodically run the synchronization on META-SHARE Managing Nodes
if len(settings.CORE_NODES) or len(settings.PROXIED_NODES):
    sync_interval_settings = ""
    # Get sync interval settings
    sync_interval_settings = "{} {} {} {} {}".format( \
        settings.SYNC_INTERVALS['MINUTE'],
        settings.SYNC_INTERVALS['HOUR'],
        settings.SYNC_INTERVALS['DAY_OF_MONTH'],
        settings.SYNC_INTERVALS['MONTH'],
        settings.SYNC_INTERVALS['DAY_OF_WEEK']
        )
    
    @kronos.register(sync_interval_settings)
    def run_synchronization():
        call_command('synchronize', interactive=False)


update_interval_settings = ""
# Get update interval settings
update_interval_settings = "{} {} {} {} {}".format( \
    settings.UPDATE_INTERVALS['MINUTE'],
    settings.UPDATE_INTERVALS['HOUR'],
    settings.UPDATE_INTERVALS['DAY_OF_MONTH'],
    settings.UPDATE_INTERVALS['MONTH'],
    settings.UPDATE_INTERVALS['DAY_OF_WEEK']
    )

@kronos.register(update_interval_settings)
def run_digest_update():
    call_command('update_digests', interactive=False)
    
# update the GeoIP database every first day of the month
@kronos.register("12 4 1 * *")
def run_update_geoip_db():
    LOGGER.info("Will now update the GeoIP database.")
    call_command('update_geoip_db', interactive=False)

