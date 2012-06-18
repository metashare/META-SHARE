import kronos
from metashare.settings import INTERVALS
from django.core.management import call_command

interval_settings = ""
# Get time interval settings
for item in INTERVALS.values():
    interval_settings += " " + str(item)
interval_settings = interval_settings.strip()

@kronos.register(interval_settings)
def run_synchronization():
    call_command('synchronize', interactive=False)
    
