import datetime
import os
import json
import logging

from xml.etree.ElementTree import fromstring
from StringIO import StringIO
from zipfile import ZipFile

from django.test.testcases import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission
from django.contrib.admin.sites import LOGIN_FORM_KEY
from django.core.management import call_command

from metashare import settings, test_utils
from metashare.repository.models import resourceInfoType_model
from metashare.storage.models import INGESTED, INTERNAL, StorageObject, \
    PUBLISHED, compute_digest_checksum, MASTER, PROXY
from metashare.settings import DJANGO_BASE, LOGIN_URL, LOG_HANDLER
from metashare.test_utils import set_index_active

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

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

    def assertValidInventory(self, json_inventory):
        # inventory contains pairs of resource ids and digests
        if len(json_inventory) == 0:
            raise Exception(
              'Not a valid inventory because it does not have any existing inventory items: {}'.format(json_inventory))

    def assertValidInventoryResponse(self, response):
        self.assertEquals(200, response.status_code)
        self.assertEquals('application/zip', response['Content-Type'])
        self.assertEquals(settings.METASHARE_VERSION, response['Metashare-Version'])
        with ZipFile(StringIO(response.content), 'r') as inzip:
            json_inventory = json.load(inzip.open('inventory.json'))
        self.assertNotEquals(0, len(json_inventory))

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


    @classmethod
    def import_test_resource(cls, filename, pub_status, \
      copy_status=MASTER, url=settings.DJANGO_URL, source_node=None):
        _fixture = '{0}/repository/fixtures/{1}'.format(settings.ROOT_PATH, filename)
        resource = test_utils.import_xml(_fixture)
        resource.storage_object.publication_status = pub_status
        resource.storage_object.copy_status = copy_status
        resource.storage_object.source_url = url
        resource.storage_object.source_node = source_node
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
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
        set_index_active(False)
        test_utils.setup_test_storage()
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
        
        testres = cls.import_test_resource('testfixture.xml', INGESTED)
        testres.storage_object.digest_modified = datetime.date(2012, 6, 1)
        testres.storage_object.save()
        
        cls.import_test_resource('roundtrip.xml', INTERNAL)
        
        pubres = cls.import_test_resource('ILSP10.xml', PUBLISHED)
        pubres.storage_object.digest_modified = datetime.date(2012, 1, 1)
        pubres.storage_object.save()


    @classmethod
    def tearDownClass(cls):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))
    

    def test_unprotected_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        client = Client()
        response = client.get(self.INVENTORY_URL + "?sync_protocol=1.0")
        self.assertValidInventoryResponse(response)

    def test_syncuser_get_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = test_utils.get_client_with_user_logged_in(self.syncuser_login)
        response = client.get(self.INVENTORY_URL + "?sync_protocol=1.0")
        self.assertValidInventoryResponse(response)

    def test_normaluser_cannot_reach_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = test_utils.get_client_with_user_logged_in(self.normal_login)
        response = client.get(self.INVENTORY_URL + "?sync_protocol=1.0")
        self.assertIsForbidden(response)

    def test_editoruser_cannot_reach_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        response = client.get(self.INVENTORY_URL + "?sync_protocol=1.0")
        self.assertIsForbidden(response)    

    def test_anonymous_cannot_reach_inventory(self):
        settings.SYNC_NEEDS_AUTHENTICATION = True
        client = Client()
        response = client.get(self.INVENTORY_URL + "?sync_protocol=1.0")
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
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
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
        response = client.get(self.INVENTORY_URL + "?sync_protocol=1.0")
        self.assertValidInventoryResponse(response)
        json_inventory = self.extract_inventory(response)
        self.assertEquals(2, len(json_inventory))
        for resource_id in json_inventory:
            storage_object = StorageObject.objects.get(identifier=resource_id)
            self.assertTrue(storage_object.publication_status in (INGESTED, PUBLISHED),
              "Resource {0} should not be included in inventory because it is not ingested or published".format(resource_id))

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
        # read zip file from response
        with ZipFile(StringIO(response.content), 'r') as inzip:
            with inzip.open('metadata.xml') as resource_xml:
                resource_xml_string = resource_xml.read()
            with inzip.open('storage-global.json') as storage_file:
                # should be a json object, not string
                storage_json_string = storage_file.read() 
        self.assertEquals(expected_digest, compute_digest_checksum(
          resource_xml_string, storage_json_string))

    def test_inventory_no_sync_protocol(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        response = Client().get(self.INVENTORY_URL)
        self.assertEquals(501, response.status_code)

    def test_inventory_no_matching_sync_protocol(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        response = Client().get(
          self.INVENTORY_URL + "?sync_protocol=3.0&sync_protocol=3.5&sync_protocol=4.0")
        self.assertEquals(501, response.status_code)
    
    def test_inventory_matching_sync_protocol(self):
        settings.SYNC_NEEDS_AUTHENTICATION = False
        response = Client().get(
          self.INVENTORY_URL + "?sync_protocol=1.0&sync_protocol=1.5&sync_protocol=2.0")
        self.assertEquals(200, response.status_code)
        self.assertEquals("1.0", response['Sync-Protocol'])
        inventory = self.extract_inventory(response)
        self.assertNotEquals(0, len(inventory))
     
    def test_proxy_check(self):
        
        # define proxied nodes
        proxied_nodes = {
            'proxied_node_1': {
                'NAME': 'Proxied Node 1',
                'DESCRIPTION': 'xxx',
                'URL': 'http://metashare.proxy1.org',
                'USERNAME': 'sync-user',
                'PASSWORD': 'sync-user-pass',
                },
            'proxied_node_2': {
                'NAME': 'Proxied Node 2',
                'DESCRIPTION': 'xxx',
                'URL': 'http://metashare.proxy2.org',
                'USERNAME': 'sync-user',
                'PASSWORD': 'sync-user-pass',
                },
        }
        settings.PROXIED_NODES = proxied_nodes
        
        # create 3 proxied resources, 2 from the first proxied node, 1 from the second
        res1 = MetadataSyncTest.import_test_resource(
          'downloadable_1_license.xml', PUBLISHED, copy_status=PROXY,
          url=proxied_nodes['proxied_node_1']['URL'],
          source_node='proxied_node_1')
        res2 = MetadataSyncTest.import_test_resource(
          'downloadable_3_licenses.xml', PUBLISHED, copy_status=PROXY,
          url=proxied_nodes['proxied_node_1']['URL'],
          source_node='proxied_node_1')
        res3 = MetadataSyncTest.import_test_resource(
          'downloadable_ms_commons_license.xml', PUBLISHED, copy_status=PROXY,
          url=proxied_nodes['proxied_node_2']['URL'],
          source_node='proxied_node_2')
        res1_folder = os.path.join(settings.STORAGE_PATH, res1.storage_object.identifier)
        res2_folder = os.path.join(settings.STORAGE_PATH, res2.storage_object.identifier)
        res3_folder = os.path.join(settings.STORAGE_PATH, res3.storage_object.identifier)
        self.assertEquals(3, StorageObject.objects.filter(copy_status=PROXY).count())
        self.assertTrue(os.path.isdir(res1_folder))
        self.assertTrue(os.path.isdir(res2_folder))
        self.assertTrue(os.path.isdir(res3_folder))
        
        # check proxied nodes
        call_command('check_proxied_nodes', interactive=False)
        # no proxied resource has been removed
        self.assertEquals(3, StorageObject.objects.filter(copy_status=PROXY).count())

        # remove proxied node
        del settings.PROXIED_NODES['proxied_node_1']
        # check proxied nodes
        call_command('check_proxied_nodes', interactive=False)
        # now, two proxied resources has been removed
        self.assertEquals(1, StorageObject.objects.filter(copy_status=PROXY).count())
        self.assertFalse(os.path.isdir(res1_folder))
        self.assertFalse(os.path.isdir(res2_folder))
        self.assertTrue(os.path.isdir(res3_folder))        
