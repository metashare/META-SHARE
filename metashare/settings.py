"""
Project: META-SHARE prototype implementation
Author: Christian Federmann <cfedermann@dfki.de>
"""
from os.path import abspath, dirname, join
import subprocess
ROOT_PATH = abspath(dirname(__file__))

import os
import tempfile
import logging
from logging.handlers import RotatingFileHandler

# Logging settings for this Django project.
LOG_LEVEL = logging.INFO
LOG_FILENAME = join(tempfile.gettempdir(), "metashare.log")
LOG_FORMAT = "[%(asctime)s] %(name)s::%(levelname)s %(message)s"
LOG_DATE = "%m/%d/%Y @ %H:%M:%S"
LOG_FORMATTER = logging.Formatter(LOG_FORMAT, LOG_DATE)

# Allows to disable check for duplicate instances.
CHECK_FOR_DUPLICATE_INSTANCES = True

# work around a problem on non-posix-compliant platforms by not using any
# RotatingFileHandler there
if os.name == "posix":
    LOG_HANDLER = RotatingFileHandler(filename=LOG_FILENAME, mode="a",
        maxBytes=1024*1024, backupCount=5, encoding="utf-8")
else:
    LOG_HANDLER = logging.FileHandler(filename=LOG_FILENAME, mode="a",
        encoding="utf-8")
LOG_HANDLER.setLevel(level=LOG_LEVEL)
LOG_HANDLER.setFormatter(LOG_FORMATTER)

# Import local settings, i.e., DEBUG, TEMPLATE_DEBUG, TIME_ZONE,
# SECRET_KEY, DATABASE_* settings and ADMINS.
from local_settings import *

# If STORAGE_PATH does not exist, try to create it and halt if not possible.
from os.path import exists
if not exists(STORAGE_PATH):
    try:
        from os import mkdir
        mkdir(STORAGE_PATH)
    
    except:
        raise OSError, "STORAGE_PATH must exist and be writable!"

# If XDIFF_LOCATION was not set in local_settings, set a default here:
try:
    _ = XDIFF_LOCATION
except:
    XDIFF_LOCATION = None

# Perform some cleanup operations on the imported local settings.
if DJANGO_URL.strip().endswith('/'):
    DJANGO_URL = DJANGO_URL.strip()[:-1]

if not DJANGO_BASE.strip().endswith('/'):
    DJANGO_BASE = '{0}/'.format(DJANGO_BASE.strip())

if DJANGO_BASE.strip().startswith('/'):
    DJANGO_BASE = DJANGO_BASE.strip()[1:]

# Defines the maximal lifetime for SSO tokens in seconds.
MAX_LIFETIME_FOR_SSO_TOKENS = 30

# Pagination settings for this django project.
PAGINATION_ITEMS_PER_PAGE = 50

LOGIN_URL = '/{0}login/'.format(DJANGO_BASE)
LOGIN_REDIRECT_URL = '/{0}'.format(DJANGO_BASE)
LOGOUT_URL = '/{0}logout/'.format(DJANGO_BASE)

MANAGERS = ADMINS

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '{0}/media/'.format(ROOT_PATH)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/{0}site_media/'.format(DJANGO_BASE)

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX must use full URL or else our custom admin will not be used,
# cf. http://stackoverflow.com/questions/1081596/django-serving-admin-media-files
ADMIN_MEDIA_PREFIX = '{0}/site_media/admin/'.format(DJANGO_URL)


#ADMIN_MEDIA_ROOT = '{0}/media/admin/'.format(ROOT_PATH)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
# 'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'metashare.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '{0}/templates'.format(ROOT_PATH),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.media',
    'django.contrib.messages.context_processors.messages',
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

AUTH_PROFILE_MODULE = 'accounts.UserProfile'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'metashare.accounts.auth.SingleSignOnTokenBackend',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.humanize',

    'haystack',

    'metashare.accounts',
    'metashare.storage',
    
    'metashare.stats',

    'metashare.repository',
    'metashare.AdminTest',
)

# Continuous Integration support using django_jenkins: only add application
# if django_jenkins module can be imported properly.
try:
    import django_jenkins
    INSTALLED_APPS += ('django_jenkins',)

except ImportError:
    pass

# Apps for which to run tests in continuous integration django_jenkins:
PROJECT_APPS = (
    'metashare.repository',
    'metashare.accounts',
    'metashare.storage',
)

# basic Haystack search backend configuration
TEST_MODE_NAME = 'testing'
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': SOLR_URL,
        'SILENTLY_FAIL': False
    },
    TEST_MODE_NAME: {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': TESTING_SOLR_URL,
        'SILENTLY_FAIL': False
    },
}

# a custom test runner with the added value on top of the default Django test
# runner to automatically set up Haystack so that it uses a dedicated search
# backend for testing
TEST_RUNNER = 'metashare.test_runner.MetashareTestRunner'
JENKINS_TEST_RUNNER = 'metashare.test_runner.MetashareJenkinsTestRunner'

# we use a custom Haystack search backend router so that we can dynamically
# switch between the main/default search backend and the one for testing
HAYSTACK_ROUTERS = [ 'metashare.haystack_routers.MetashareRouter' ]

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.django_tests',
)

PYLINT_RCFILE = '{0}/test-config/pylint.rc'.format(ROOT_PATH)

# set display for Selenium tests
if 'DISPLAY' in os.environ:
    import re
    SELENIUM_DISPLAY = re.sub(r'[^\:]*(\:\d{1,2})(?:\.\d+)?', r'\1', 
      os.environ['DISPLAY'])
