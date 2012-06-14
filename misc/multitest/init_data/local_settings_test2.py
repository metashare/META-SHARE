"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import os
ROOT_PATH = os.getcwd()

# Path to the local svnversion binary.  If set, the SVN revision number will
# be shown in the footer section of the META-SHARE application.
#SVNVERSION = 'C:/Program Files/SlikSvn/bin/svnversion'

# The URL for this META-SHARE node django application
DJANGO_URL = 'http://localhost:{0}/metashare'.format(%%DJANGO_PORT%%)
DJANGO_BASE = 'metashare/'

# URL for the Metashare Knowledge Base
KNOWLEDGE_BASE_URL = 'http://localhost:8010/knowledgeBase/'


# Debug settings, setting DEBUG=True will give exception stacktraces.
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_JS = False

#STORAGE_PATH = ROOT_PATH + '/storageFolder'
STORAGE_PATH = '%%STORAGE_PATH%%'

# Configure administrators for this django project.  If DEBUG=False, errors
# will be reported as emails to these persons...
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql',
                                         # 'postgresql', 'sqlite3', 'oracle'.
        'NAME': '{0}'.format('%%DATABASE_FILE%%'),  # Or path to file if using sqlite3.
                                         # '{0}/development.db'.format(ROOT_PATH)
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost.
                                         # Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default.
                                         # Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Athens'

DATE_FORMAT = 'j N Y'
# Make this unique, and don't share it with anybody.
# You can generate a new SECRET_KEY like this:
#
# import string
# from random import choice
# alphabet = string.letters + string.digits + string.punctuation
# SECRET_KEY = ''.join([choice(alphabet) for i in range(50)])
# SECRET_KEY = '7h$+o^h4f%q#d$u7d^1!3s#a-+u5p*+p*lpz++z^q^9^+a5p--'
SECRET_KEY = 'l59!!!338zza+chi05qsey95cc8lobt!p4nc@+v59!rszoojac'

# Shared secret used for Single-Sign-On between META-SHARE core nodes.
SSO_SECRET_KEY = '6736d82b807811e0a1e51093e908621ab4e0e5225bde4fbcb1aa160fbd198e2a'

# Path to the local private key used for decryption of content.
PRIVATE_KEY_PATH = '/path/to/private/key'

STATS_SERVER_URL = "http://metastats.fbk.eu/"

# the URL of the Solr server which is used as a search backend
HAYSTACK_SOLR_URL = 'http://127.0.0.1:{0}/solr'.format(%%SOLR_PORT%%)

# the URL of the Solr server (or server core) which is used as a search backend
SOLR_URL = 'http://127.0.0.1:{0}/solr/main'.format(%%SOLR_PORT%%)
# the URL of the Solr server (or server core) which is used as a search backend
# when running tests
TESTING_SOLR_URL = 'http://127.0.0.1:{0}/solr/testing'.format(%%SOLR_PORT%%)

# List of external nodes with which the local node will be synchronized.
# Use this if you are a core node!
%%CORE_NODES%%

# User accounts with the permission to access synchronization information:
%%SYNC_USERS%%

