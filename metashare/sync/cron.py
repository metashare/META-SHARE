import kronos
from metashare.settings import INTERVALS
from django.core.management import call_command

interval_settings = ""
# Get time interval settings
interval_settings += INTERVALS['MINUTE'] + " "
interval_settings += INTERVALS['HOUR'] + " " 
interval_settings += INTERVALS['DAY_OF_MONTH'] + " " 
interval_settings += INTERVALS['MONTH'] + " " 
interval_settings += INTERVALS['DAY_OF_WEEK']

@kronos.register(interval_settings)
def run_synchronization():
    call_command('synchronize', interactive=False)
    
