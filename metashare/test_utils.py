"""
Project: META-SHARE
Utility functions for unit tests useful across apps.
"""
import os
from metashare import settings
from metashare.repository.models import resourceInfoType_model
from django.test.testcases import TestCase
from django.core.management import call_command
from metashare.xml_utils import import_from_file
from metashare.storage.models import PUBLISHED
from django.contrib.auth.models import User

def setup_test_storage():
    settings.STORAGE_PATH = '{0}/test-tmp'.format(settings.ROOT_PATH)
    try:
        os.mkdir(settings.STORAGE_PATH)
    except:
        pass
    
    
def create_user(username, email, password):
    User.objects.all().filter(username=username).delete()
    return User.objects.create_user(username, email, password)

def import_xml(filename):
    _xml = open(filename)
    _xml_string = _xml.read()
    _xml.close()
    result = resourceInfoType_model.import_from_string(_xml_string)
    return result

def import_xml_or_zip(filename):
    _xml = open(filename, 'rb')
    return import_from_file(_xml, filename, PUBLISHED)

def set_index_active(is_active):
    """
    A helper allowing tests to disable the index if it is not needed,
    e.g. for tests that have no front-facing UI component.
    """
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = str(bool(not is_active))

class IndexAwareTestCase(TestCase):
    """
    A Django `TestCase` which makes sure to always rebuild the search index
    before and after every test so that it always matches the current database
    state.
    """
    def _fixture_setup(self):
        result = super(IndexAwareTestCase, self)._fixture_setup()
        call_command('rebuild_index', interactive=False,
                     using=settings.TEST_MODE_NAME)
        return result

    def _fixture_teardown(self):
        result = super(IndexAwareTestCase, self)._fixture_teardown()
        call_command('rebuild_index', interactive=False,
                     using=settings.TEST_MODE_NAME)
        return result
