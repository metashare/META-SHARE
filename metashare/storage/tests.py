"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from time import sleep
from django.core.exceptions import ValidationError
from django.test.client import Client
from django.utils import unittest
from metashare.storage.models import StorageObject, _validate_valid_xml, \
    update_resource, MASTER, REMOTE, PROXY, IllegalAccessException
from metashare import settings, test_utils
from metashare.settings import DJANGO_BASE
import json
import os
from metashare.repository.models import resourceInfoType_model, \
    personInfoType_model
from datetime import date
from metashare.test_utils import set_index_active

class StorageObjectTestCase(unittest.TestCase):
    """
    Test case that checks the StorageObject model implementation.
    """
    def setUp(self):
        """
        Creates a new storage object instance for testing.
        """
        test_utils.setup_test_storage()
        self.client = Client()
        self._minimal_xml = u"""<?xml version="1.0"?>\n<foo/>"""
        obj = StorageObject.objects.create(metadata=self._minimal_xml)
        self.object_id = obj.id

    def tearDown(self):
        """
        Removes the storage object instance from the database after testing.
        """
        # Load storage object instance from database.
        storage_object = StorageObject.objects.filter(pk=self.object_id)

        # Delete instance from database if still existing.
        if storage_object:
            storage_object[0].delete()


    def test_revision_view(self):
        """
        Checks that the get_latest_revision view is working correctly.
        """
        # Load storage object instance from database.
        storage_object = StorageObject.objects.get(pk=self.object_id)
        
        # The revision for our storage object should be 0, HTTP status 200.
        _url = '/{0}storage/revision/{1}/'.format(DJANGO_BASE, storage_object.identifier)
        response = self.client.get(_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.content), 1)
        
        # If we update the revision information for the object, this should
        # also produce an updated result for the current URL.
        storage_object.revision = 13
        storage_object.save()
        response = self.client.get(_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.content), 13)
        
        # If the storage object is not a master copy, the result should be 0.
        storage_object.master_copy = False
        storage_object.save()
        response = self.client.get(_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.content), 0)
        
        # Set master_copy again to allow cleanup of storage folder.
        storage_object.master_copy = True
        storage_object.save()
        
        # Using an unknown identifier should result in a '-1' response.
        _identifier = list(storage_object.identifier)
        _identifier.reverse()
        _url = '/{0}storage/revision/{1}/'.format(DJANGO_BASE, ''.join(_identifier))
        response = self.client.get(_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.content), -1)

    def test_validation(self):
        """
        Checks that no object without validating XML metadata can be created.
        """
        # Check that our minimal XML example validates.
        self.assertTrue(_validate_valid_xml(self._minimal_xml))
        
        # Then verify that no object can be created without validating XML.
        with self.assertRaises(ValidationError):
            _ = StorageObject.objects.create()

    def test_defaults(self):
        """
        Checks that a created object has correct default attributes set.
        """
        # Load storage object instance from database.
        storage_object = StorageObject.objects.get(pk=self.object_id)
        
        # revision defaults to 0.
        self.assertIs(storage_object.revision, 1)
                
        # master_copy defaults to True.
        self.assertTrue(storage_object.master_copy)
        
        # published defaults to False.
        self.assertFalse(storage_object.published)
        
        # deleted defaults to False.
        self.assertFalse(storage_object.deleted)
        
        # The new storage object should not have a download attached yet.
        self.assertFalse(storage_object.has_download())
        
        # The new object's metadata should be identical to _minimal_xml.
        self.assertEqual(storage_object.metadata, self._minimal_xml)
        
        # After saving the storage_object instance, the modified timestamp
        # should be different from the value stored inside created.
        # 
        # For more information on auto_now and auto_now_add, see the docs:
        # - https://docs.djangoproject.com/en/dev/ref/models/fields/#datetime
        sleep(0.01)
        storage_object.save()
        self.assertTrue(storage_object.created != storage_object.modified)

    def test_unicode(self):
        """
        Checks that the __unicode__ method works correctly.
        """
        # Load storage object instance from database.
        storage_object = StorageObject.objects.get(pk=self.object_id)
        
        self.assertEqual(unicode(storage_object), u'<StorageObject id="{0}">'.format(self.object_id))

    def test_storage_path(self):
        """
        Checks that the storage path is computed correctly.
        """
        # Load storage object instance from database.
        storage_object = StorageObject.objects.get(pk=self.object_id)
        
        _correct_path = '{0}/{1}'.format(settings.STORAGE_PATH,
          storage_object.identifier)
        self.assertEqual(storage_object._storage_folder(), _correct_path)
        
        # The storage folder should be None if master_copy is False
        # This has changed, the storage folder is now also available for
        # non-master copies
        storage_object.master_copy = False
        storage_object.save()
        self.assertEqual(storage_object._storage_folder(), _correct_path)
        
        # Set master_copy again to allow cleanup of storage folder.
        storage_object.master_copy = True
        storage_object.save()


class UpdateTests(unittest.TestCase):
    """
    Test case that checks the update mechanism used by the receiving end of synchronization.
    """

    @classmethod
    def setUpClass(cls):
        set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        set_index_active(True)

    def setUp(self):
        """
        Creates a new storage object instance for testing.
        """
        test_utils.setup_test_storage()
        folder = '{0}/storage/test_fixtures/updatetest'.format(settings.ROOT_PATH)
        with open('{0}/storage-global.json'.format(folder), 'rb') as storagein:
            self.storage_json = json.load(storagein)
        with open('{0}/metadata-before.xml'.format(folder), 'rb') as metadatain:
            self.metadata_before = metadatain.read()
        with open('{0}/metadata-modified.xml'.format(folder), 'rb') as metadatain:
            self.metadata_modified = metadatain.read()
        self.storage_id = self.storage_json['identifier']
        self.storage_digest = None

    
    def cleanup_storage(self):
        """
        Deletes the content of the storage folder.
        """
        for _folder in os.listdir(settings.STORAGE_PATH):
            for _file in os.listdir(os.path.join(settings.STORAGE_PATH, _folder)):
                os.remove(os.path.join(settings.STORAGE_PATH, _folder, _file))
            os.rmdir(os.path.join(settings.STORAGE_PATH, _folder))

    def tearDown(self):
        """
        Removes all storage object instances from the database after testing.
        """
        StorageObject.objects.all().delete()
        personInfoType_model.objects.all().delete()
        self.cleanup_storage()


    def test_update_new(self):
        """
        Simulate the case where synchronization brings a new storage object to be instantiated.
        """
        # Exercise
        update_resource(self.storage_json, self.metadata_before, self.storage_digest)
        # Verify
        self.assertEquals(1, StorageObject.objects.filter(identifier=self.storage_id).count())
        storage_object = StorageObject.objects.get(identifier=self.storage_id)
        self.assertEquals(self.metadata_before, storage_object.metadata)

    def test_update_existing(self):
        """
        Simulate update for already existing storage object
        """
        # helper
        def get_metadatacreationdate_for(storage_id):
            resource = resourceInfoType_model.objects.get(storage_object__identifier=self.storage_id)
            return resource.metadataInfo.metadataCreationDate
        
        # setup
        update_resource(self.storage_json, self.metadata_before, self.storage_digest)
        self.assertEquals(date(2005, 5, 12), get_metadatacreationdate_for(self.storage_id))
        self.assertEquals(REMOTE, StorageObject.objects.get(identifier=self.storage_id).copy_status)
        # exercise
        update_resource(self.storage_json, self.metadata_modified, self.storage_digest)
        self.assertEquals(date(2006, 12, 31), get_metadatacreationdate_for(self.storage_id))

    def test_update_refuse_mastercopy(self):
        """
        Refuse to replace a master copy with a non-master copy during update 
        """
        # setup
        update_resource(self.storage_json, self.metadata_before, self.storage_digest, MASTER)
        self.assertEquals(MASTER, StorageObject.objects.get(identifier=self.storage_id).copy_status)
        # exercise
        try:
            update_resource(self.storage_json, self.metadata_modified, self.storage_digest, REMOTE)
            self.fail("Should have raised an exception")
        except IllegalAccessException:
            pass # Expected exception

    def test_remote_copy(self):
        """
        Verify that reusable entities such as persons have copy status REMOTE
        after synchronization.
        """
        # exercise
        update_resource(self.storage_json, self.metadata_before, None, copy_status=REMOTE)
        # verify
        resource = resourceInfoType_model.objects.get(storage_object__identifier=self.storage_id)
        persons = resource.contactPerson.all()
        self.assertEquals(1, len(persons))
        contact_person = persons[0]
        self.assertEquals(REMOTE, contact_person.copy_status)
        
    def test_proxy_copy(self):
        """
        Verify that reusable entities such as persons have copy status PROXY
        after synchronization.
        """
        # exercise
        update_resource(self.storage_json, self.metadata_before, None, copy_status=PROXY)
        # verify
        resource = resourceInfoType_model.objects.get(storage_object__identifier=self.storage_id)
        persons = resource.contactPerson.all()
        self.assertEquals(1, len(persons))
        contact_person = persons[0]
        self.assertEquals(PROXY, contact_person.copy_status)
        
    def test_master_copy(self):
        """
        Verify that reusable entities such as persons have copy status MASTER
        after synchronization.
        """
        # exercise
        update_resource(self.storage_json, self.metadata_before, None, copy_status=MASTER)
        # verify
        resource = resourceInfoType_model.objects.get(storage_object__identifier=self.storage_id)
        persons = resource.contactPerson.all()
        self.assertEquals(1, len(persons))
        contact_person = persons[0]
        self.assertEquals(MASTER, contact_person.copy_status)
