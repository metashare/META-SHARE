import kronos
from metashare.settings import SYNC_INTERVALS, UPDATE_INTERVALS
from django.core.management import call_command


# clean up the session database every Monday night
@kronos.register("12 4 * * 1")
def run_session_cleanup():
    call_command('cleanup', interactive=False)


sync_interval_settings = ""
# Get sync interval settings
sync_interval_settings = "{} {} {} {} {}".format( \
    SYNC_INTERVALS['MINUTE'],
    SYNC_INTERVALS['HOUR'],
    SYNC_INTERVALS['DAY_OF_MONTH'],
    SYNC_INTERVALS['MONTH'],
    SYNC_INTERVALS['DAY_OF_WEEK']
    )

@kronos.register(sync_interval_settings)
def run_synchronization():
    call_command('synchronize', interactive=False)


update_interval_settings = ""
# Get update interval settings
update_interval_settings = "{} {} {} {} {}".format( \
    UPDATE_INTERVALS['MINUTE'],
    UPDATE_INTERVALS['HOUR'],
    UPDATE_INTERVALS['DAY_OF_MONTH'],
    UPDATE_INTERVALS['MONTH'],
    UPDATE_INTERVALS['DAY_OF_WEEK']
    )

@kronos.register(update_interval_settings)
def run_digest_update():
    call_command('update_digests', interactive=False)
