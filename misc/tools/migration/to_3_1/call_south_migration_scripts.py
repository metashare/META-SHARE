import pip
import sys
from os.path import abspath, dirname
parentdir = dirname(dirname(abspath(__file__)))

# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, parentdir)

if __name__ == '__main__':
    
    pip.main(['install', 'django==1.4.19'])
    # Import my django project configuration settings
    from django.core.management import setup_environ, call_command
    import south_settings
    
    setup_environ(south_settings)
    
    call_command('syncdb', interactive=False)
    call_command('migrate', 'repository', '0001', fake=True, interactive=True)
    call_command('migrate', interactive=False)
    pip.main(['install', '--upgrade', 'django==1.7.11'])
    
