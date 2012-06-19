from django.test.testcases import TestCase
from django.test.client import Client
from metashare.settings import DJANGO_BASE, LOGIN_URL
from django.contrib.auth.models import User, Group, Permission
from django.contrib.admin.sites import LOGIN_FORM_KEY
import json
from StringIO import StringIO
from zipfile import ZipFile
from metashare import settings, test_utils
from metashare.repository.models import resourceInfoType_model
from xml.etree.ElementTree import fromstring
from metashare.storage.models import INGESTED, INTERNAL, StorageObject, \
    PUBLISHED, compute_checksum
from metashare.test_utils import set_index_active
import datetime




class MetadataSyncTest (TestCase):
    SYNC_BASE = "/{0}sync/".format(DJANGO_BASE)
    INVENTORY_URL = SYNC_BASE
    
    # static variables to be initialized in setUpClass():
    syncuser_login = None
    normal_login = None
    editor_login = None

    def extract_inventory(self, response):
        with ZipFile(StringIO(response.content), 'r') as inzip:
            return json.load(inzip.open('inventory.json'))

    def assertIsRedirectToLogin(self, response):
        self.assertEquals(302, response.status_code)
        self.assertTrue(LOGIN_URL in response['Location'])

    def assertIsForbidden(self, response):
        self.assertContains(response, "Forbidden", status_code=403)

    def assertValidInventoryItem(self, entry):
        if not (entry['id'] and entry['digest']):
            raise Exception('Inventory item does not have "id" and "digest" key-value pairs: {}'.format(entry))
        
    def assertValidInventory(self, json_inventory):
        is_empty = True
        for entry in json_inventory:
            is_empty = False
            self.assertValidInventoryItem(entry)
        if is_empty:
            raise Exception("Not a valid inventory because it doesn't have any inventory items: {}".format(json_inventory))

    def assertValidInventoryResponse(self, response):
        self.assertEquals(200, response.status_code)
        self.assertEquals('application/zip', response['Content-Type'])
        self.assertEquals(settings.METASHARE_VERSION, response['Metashare-Version'])
        json_inventory = self.extract_inventory(response)
        self.assertValidInventory(json_inventory)

    def assertValidFullMetadataResponse(self, response):
        self.assertEquals(200, response.status_code)
        self.assertEquals('application/zip', response['Content-Type'])
        self.assertEquals(settings.METASHARE_VERSION, response['Metashare-Version'])
        with ZipFile(StringIO(response.content), 'r') as inzip:
            with inzip.open('storage-global.json') as storage_file:
                storage_content = storage_file.read()
                self.assertIsNotNone(storage_content)
            with inzip.open('metadata.xml') as resource_xml:
                resource_xml_string = resource_xml.read()
                root = fromstring(resource_xml_string)
                self.assertIsNotNone(root)


    def client_with_user_logged_in(self, user_credentials):
        client = Client()
        response = client.post(LOGIN_URL, user_credentials)
        if response.status_code != 302:
            raise Exception, 'could not log in user with credentials: {}\nresponse was: {}'\
                .format(user_credentials, response)
        return client

    @classmethod
    def import_test_resource(cls, filename, status):
        test_utils.setup_test_storage()
        _fixture = '{0}/repository/fixtures/{1}'.format(settings.ROOT_PATH, filename)
        result = test_utils.import_xml(_fixture)
        resource = result[0]
        resource.storage_object.publication_status = status
        resource.storage_object.save()
        resource.storage_object.update_storage()
        return resource

    @classmethod
    def setUpClass(cls):
        """
        set up test users with and without sync permissions.
        These will live in the test database only, so will not
        pollute the "normal" development db or the production db.
        As a consequence, they need no valuable password.
        """
        set_index_active(False)
        syncuser = User.objects.create_user('syncuser', 'staff@example.com',
          'secret')
        syncpermission = Permission.objects.get(codename='can_sync')
        syncuser.user_permissions.add(syncpermission)
        syncuser.save()
        
        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

        editoruser = User.objects.create_user('editoruser', 'editor@example.com',
          'secret')
        editoruser.is_staff = True
        globaleditors = Group.objects.get(name='globaleditors')
        editoruser.groups.add(globaleditors)
        editoruser.save()


        # login POST dicts
        MetadataSyncTest.syncuser_login = {
            LOGIN_FORM_KEY: 1,
            'username': 'syncuser',
            'password': 'secret',
        }

        MetadataSyncTest.normal_login = {
            LOGIN_FORM_KEY: 1,
            'username': 'normaluser',
            'password': 'secret',
        }
        
        MetadataSyncTest.editor_login = {
            LOGIN_FORM_KEY: 1,
            'username': 'editoruser',
            'password': 'secret',
        }
        
        StorageObject.objects.all().delete()
        testres = cls.import_test_resource('testfixture.xml', INGESTED)
        testres.storage_object.digest_modified = datetime.date(2012, 6, 1)
        testres.storage_object.save()
        
        cls.import_test_resource('roundtrip.xml', INTERNAL)
        
        pubres = cls.import_test_resource('ILSP10.xml', PUBLISHED)
        pubres.storage_object.digest_modified = datetime.date(2012, 1, 1)
        pubres.storage_object.save()

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        test_utils.clean_db()
        test_utils.clean_storage()
        set_index_active(True)
    

    def test_unprotected_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        response = client.get(self.INVENTORY_URL)
        self.assertValidInventoryResponse(response)

    def test_syncuser_get_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = self.client_with_user_logged_in(self.syncuser_login)
        response = client.get(self.INVENTORY_URL)
        self.assertValidInventoryResponse(response)

    def test_normaluser_cannot_reach_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = self.client_with_user_logged_in(self.normal_login)
        response = client.get(self.INVENTORY_URL)
        self.assertIsForbidden(response)

    def test_editoruser_cannot_reach_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = self.client_with_user_logged_in(self.editor_login)
        response = client.get(self.INVENTORY_URL)
        self.assertIsForbidden(response)    

    def test_anonymous_cannot_reach_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = Client()
        response = client.get(self.INVENTORY_URL)
        self.assertIsForbidden(response)
        
    def test_unprotected_full_metadata(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        resource = resourceInfoType_model.objects.all()[0]
        resource_uuid = resource.storage_object.identifier
        response = client.get('{0}{1}/metadata/'.format(self.SYNC_BASE, resource_uuid))
        self.assertValidFullMetadataResponse(response)
        
    def test_anonymous_cannot_reach_full_metadata(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = Client()
        resource = resourceInfoType_model.objects.all()[0]
        resource_uuid = resource.storage_object.identifier
        response = client.get('{0}{1}/metadata/'.format(self.SYNC_BASE, resource_uuid))
        self.assertIsForbidden(response)

    def test_editoruser_cannot_reach_full_metadata(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = self.client_with_user_logged_in(self.editor_login)
        resource = resourceInfoType_model.objects.all()[0]
        resource_uuid = resource.storage_object.identifier
        response = client.get('{0}{1}/metadata/'.format(self.SYNC_BASE, resource_uuid))
        self.assertIsForbidden(response)
    
    def test_wrong_uuid_causes_404(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        response = client.get('{0}0000000000000000000000000000000000000000000000000000000000000000/metadata/'.format(self.SYNC_BASE))
        self.assertEquals(404, response.status_code)


    def test_inventory_doesnt_include_internal(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        response = client.get(self.INVENTORY_URL)
        self.assertValidInventoryResponse(response)
        with ZipFile(StringIO(response.content), 'r') as inzip:
            json_inventory = json.load(inzip.open('inventory.json'))
        self.assertEquals(2, len(json_inventory))
        for struct in json_inventory:
            storage_object = StorageObject.objects.get(identifier=struct['id'])
            self.assertTrue(storage_object.publication_status in (INGESTED, PUBLISHED),
                            "Resource {0} should not be included in inventory because it is not ingested or published".format(struct['id']))

    def test_can_get_ingested_metadata(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        storage_object = StorageObject.objects.filter(publication_status = INGESTED)[0]
        resource_uuid = storage_object.identifier
        response = client.get('{0}{1}/metadata/'.format(self.SYNC_BASE, resource_uuid))
        self.assertValidFullMetadataResponse(response)

    def test_can_get_published_metadata(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        storage_object = StorageObject.objects.filter(publication_status = PUBLISHED)[0]
        resource_uuid = storage_object.identifier
        response = client.get('{0}{1}/metadata/'.format(self.SYNC_BASE, resource_uuid))
        self.assertValidFullMetadataResponse(response)

    def test_cannot_reach_internal_metadata(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        storage_object = StorageObject.objects.filter(publication_status = INTERNAL)[0]
        resource_uuid = storage_object.identifier
        response = client.get('{0}{1}/metadata/'.format(self.SYNC_BASE, resource_uuid))
        self.assertIsForbidden(response)

    def test_metadata_digest(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        resource = resourceInfoType_model.objects.all()[0]
        resource_uuid = resource.storage_object.identifier
        expected_digest = resource.storage_object.digest_checksum
        response = client.get('{0}{1}/metadata/'.format(self.SYNC_BASE, resource_uuid))
        self.assertEquals(expected_digest, compute_checksum(StringIO(response.content)))
    
    def test_inventory_undated(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        response = Client().get(self.INVENTORY_URL)
        inventory = self.extract_inventory(response)
        self.assertEquals(2, len(inventory))

    def test_inventory_veryolddate(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        response = Client().get(self.INVENTORY_URL+"?from=2011-01-01")
        inventory = self.extract_inventory(response)
        self.assertEquals(2, len(inventory))

    def test_inventory_mediumdate(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        response = Client().get(self.INVENTORY_URL+"?from=2012-02-01")
        inventory = self.extract_inventory(response)
        self.assertEquals(1, len(inventory))

    def test_inventory_toorecentdate(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        response = Client().get(self.INVENTORY_URL+"?from=2013-01-01")
        inventory = self.extract_inventory(response)
        self.assertEquals(0, len(inventory))
