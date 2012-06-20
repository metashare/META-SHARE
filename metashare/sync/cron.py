import kronos
from metashare.settings import INTERVALS
from django.core.management import call_command

interval_settings = ""
# Get time interval settings
interval_settings = "{0} {1} {2} {3} {4}".format( \
    INTERVALS['MINUTE'],
    INTERVALS['HOUR'],
    INTERVALS['DAY_OF_MONTH'],
    INTERVALS['MONTH'],
    INTERVALS['DAY_OF_WEEK']
    )

@kronos.register(interval_settings)
def run_synchronization():
    call_command('synchronize', interactive=False)
    
