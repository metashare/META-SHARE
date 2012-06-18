import kronos
#import os, sys
from django.core.management import call_command

@kronos.register('0 0 * * *')
def run_synchronization():
    call_command('synchronize', interactive=False)
    
