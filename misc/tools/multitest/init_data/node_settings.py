# Node specific local settings

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# The URL for this META-SHARE node django application
DJANGO_URL = 'http://localhost:{0}/metashare'.format(%%DJANGO_PORT%%)

DJANGO_BASE = 'metashare/'

SECRET_KEY = 'fdklsc)dscdus8f7odc$slacud%%8so7cwp2fsFDASFWR/REFEsfjskdcjsdl3W'

#STORAGE_PATH = ROOT_PATH + '/storageFolder'
STORAGE_PATH = '%%STORAGE_PATH%%'

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

# the URL of the Solr server which is used as a search backend
HAYSTACK_SOLR_URL = 'http://127.0.0.1:{0}/solr'.format(%%SOLR_PORT%%)

# the URL of the Solr server (or server core) which is used as a search backend
SOLR_URL = 'http://127.0.0.1:{0}/solr/main'.format(%%SOLR_PORT%%)
# the URL of the Solr server (or server core) which is used as a search backend
# when running tests
TESTING_SOLR_URL = 'http://127.0.0.1:{0}/solr/testing'.format(%%SOLR_PORT%%)

# List of other META-SHARE Managing Nodes from which the local node imports
# resource descriptions. Any remote changes will later be updated
# ("synchronized"). Use this if you are a META-SHARE Managing Node!
%%CORE_NODES%%

# User accounts with the permission to access synchronization information on
# this node:
%%SYNC_USERS%%

# List of other META-SHARE Nodes from which the local node imports resource
# descriptions. Any remote changes will later be updated ("synchronized"). Any
# imported resource descriptions will also be shared with other nodes that
# synchronize with this local node, i.e., this node acts as a proxy for the
# listed nodes. This setting is meant to be used by META-SHARE Managing Nodes
# which make normal META-SHARE Node resource descriptions available on the
# META-SHARE Managing Nodes.
%%PROXIED_NODES%%

