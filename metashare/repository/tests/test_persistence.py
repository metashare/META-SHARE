'''
Created on 29.05.2012

@author: steffen
'''
from django.core.management import call_command
from django.test.testcases import TestCase
from metashare import settings, test_utils
from metashare.repository.models import resourceInfoType_model
from metashare.settings import ROOT_PATH
from metashare.storage.models import INGESTED, INTERNAL
import os.path

TESTFIXTURE_XML = '{}/repository/fixtures/ILSP10.xml'.format(ROOT_PATH)

class PersistenceTest(TestCase):
    """
    Tests persistence methods for saving data to the storage folder.
    """
    
    def setUp(self):
        # make sure the index does not contain any stale entries
        call_command('rebuild_index', interactive=False, using=settings.TEST_MODE_NAME)
        
    def tearDown(self):
        resourceInfoType_model.objects.all().delete()

    def test_save_metadata(self):
        """
        Tests that the metadata XML is not written to the storage folder for internal
        resources but only when the resource is ingested
        """
        # load test fixture; its initial status is 'internal'
        test_utils.setup_test_storage()
        _result = test_utils.import_xml(TESTFIXTURE_XML)
        resource = resourceInfoType_model.objects.get(pk=_result[0].id)
        # initial status is 'internal'
        self.assertTrue(resource.storage_object.publication_status == INTERNAL)
        # internal resource has no metadata XML stored in storage folder
        self.assertFalse(
          os.path.isfile('{0}/metadata.xml'.format(resource.storage_object._storage_folder())))
        # set status to ingested
        resource.storage_object.publication_status = INGESTED
        resource.save()
        # ingested resource has metadata XML stored in storage folder
        self.assertTrue(
          os.path.isfile('{0}/metadata.xml'.format(resource.storage_object._storage_folder())))
        