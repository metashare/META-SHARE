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
from hashlib import md5
import os.path
import zipfile

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
        _storage_object = resource.storage_object
        _storage_object.update_storage()
        # initial status is 'internal'
        self.assertTrue(_storage_object.publication_status == INTERNAL)
        # internal resource has no metadata XML stored in storage folder
        self.assertFalse(
          os.path.isfile('{0}/metadata-{1:04d}.xml'.format(
                  _storage_object._storage_folder(), _storage_object.revision)))
        # set status to ingested
        _storage_object.publication_status = INGESTED
        _storage_object.update_storage()
        # ingested resource has metadata XML stored in storage folder
        self.assertTrue(
          os.path.isfile('{0}/metadata-{1:04d}.xml'.format(
            _storage_object._storage_folder(), _storage_object.revision)))
        # ingested resource has global part of storage object in storage folder
        self.assertTrue(
          os.path.isfile('{0}/storage-global.json'.format(
            _storage_object._storage_folder())))
        # ingested resource has local part of storage object in storage folder
        self.assertTrue(
          os.path.isfile('{0}/storage-local.json'.format(
            _storage_object._storage_folder())))
        # ingested resource has digest zip in storage folder
        self.assertTrue(
          os.path.isfile('{0}/resource.zip'.format(
            _storage_object._storage_folder())))
        # digest zip contains metadata.xml and storage-global.json
        _zf_name = '{0}/resource.zip'.format( _storage_object._storage_folder())
        _zf = zipfile.ZipFile(_zf_name, mode='r')
        self.assertTrue('metadata.xml' in _zf.namelist())
        self.assertTrue('storage-global.json' in _zf.namelist())
        # md5 of digest zip is stored in storage object
        _checksum = md5()
        with open(_zf_name, 'rb') as _zf_reader:
            _checksum.update(_zf_reader.read())
        self.assertEqual(_checksum.hexdigest(), _storage_object.digest_checksum)
