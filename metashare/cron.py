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

# update the GeoIP database every first day of the month
@kronos.register("12 4 1 * *")
def run_update_geoip_db():
    LOGGER.info("Will now update the GeoIP database.")
    call_command('update_geoip_db', interactive=False)

