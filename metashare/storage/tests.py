"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from time import sleep
from os.path import exists
from os import remove, rmdir
from django.core.exceptions import ValidationError
from django.test.client import Client
from django.utils import unittest
from metashare.storage.models import StorageObject, _validate_valid_xml
from metashare import settings, test_utils
from metashare.settings import DJANGO_BASE

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
        
        # The revision for our storage object should be 1, HTTP status 200.
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

    def test_delete(self):
        """
        Checks that pre_delete works for a storage object with binary data.
        """
        
        # Load storage object instance from database.
        storage_object = StorageObject.objects.get(pk=self.object_id)
        
        # Create dummy binary file inside storage folder.
        _dummy_zip = '{0}/archive.zip'.format(storage_object._storage_folder())
        with open(_dummy_zip, 'w') as dummy_zip:
            dummy_zip.write('DUMMY_ZIP')
        
        # Update storage object with checksum for dummy ZIP file.  Otherwise,
        #   the delete() method cannot know that there is a download attached.
        storage_object._compute_checksum()
        
        # Deleting the instance should result in a renamed storage folder.
        _renamed_folder = '{0}/DELETED-{1}'.format(settings.STORAGE_PATH,
          storage_object.identifier)
        storage_object.delete()
        
        # Check that the renamed folder exists.
        self.assertTrue(exists(_renamed_folder))
        
        # Then, clean up by deleting the dummy binary file and removing the
        # renamed storage folder from disk.
        _dummy_zip = '{0}/archive.zip'.format(_renamed_folder)
        remove(_dummy_zip)
        rmdir(_renamed_folder)

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
        
        # revision defaults to 1.
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
        
        # The storage folder should be None if master_copy is False.
        storage_object.master_copy = False
        storage_object.save()
        self.assertEqual(storage_object._storage_folder(), None)
        
        # Set master_copy again to allow cleanup of storage folder.
        storage_object.master_copy = True
        storage_object.save()
