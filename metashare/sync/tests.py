from django.test.testcases import TestCase
from django.test.client import Client
from metashare.settings import DJANGO_BASE, LOGIN_URL
from django.contrib.auth.models import User, Group, Permission
from django.contrib.admin.sites import LOGIN_FORM_KEY
import json
from StringIO import StringIO
from zipfile import ZipFile


class MetadataSyncTest (TestCase):
    SYNC_BASE = "/{0}sync/".format(DJANGO_BASE)
    INVENTORY_URL = SYNC_BASE
    
    # static variables to be initialized in setUpClass():
    syncuser_login = None
    normal_login = None
    editor_login = None

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
            raise Exception("Not a valid inventory becuase it doesn't have any inventory items: {}".format(json_inventory))


    def client_with_user_logged_in(self, user_credentials):
        client = Client()
        response = client.post(LOGIN_URL, user_credentials)
        if response.status_code != 302:
            raise Exception, 'could not log in user with credentials: {}\nresponse was: {}'\
                .format(user_credentials, response)
        return client

    @classmethod
    def setUpClass(cls):
        """
        set up test users with and without sync permissions.
        These will live in the test database only, so will not
        pollute the "normal" development db or the production db.
        As a consequence, they need no valuable password.
        """
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
        

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    
    def test_syncuser_can_reach_inventory(self):
        client = self.client_with_user_logged_in(self.syncuser_login)
        response = client.get(self.INVENTORY_URL)
        self.assertEquals(200, response.status_code)
        self.assertEquals('application/zip', response['Content-Type'])
        self.assertEquals('2.2-SNAPSHOT', response['Metashare-Version'])
        with ZipFile(StringIO(response.content), 'r') as inzip:
            json_inventory = json.load(inzip.open('inventory.json'))
        self.assertValidInventory(json_inventory)

    def test_normaluser_cannot_reach_inventory(self):
        client = self.client_with_user_logged_in(self.normal_login)
        response = client.get(self.INVENTORY_URL)
        self.assertIsForbidden(response)

    def test_editoruser_cannot_reach_inventory(self):
        client = self.client_with_user_logged_in(self.editor_login)
        response = client.get(self.INVENTORY_URL)
        self.assertIsForbidden(response)
