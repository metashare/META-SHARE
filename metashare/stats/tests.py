import django.test
import urllib2
import logging
from urllib import urlencode
from django.test.client import Client
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.sites import LOGIN_FORM_KEY

from metashare import test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers
from metashare.repository.models import resourceInfoType_model
from metashare.repository.editor.resource_editor import unpublish_resources, \
    ingest_resources
from metashare.settings import DJANGO_BASE, DJANGO_URL, ROOT_PATH, LOG_HANDLER
from metashare.stats.model_utils import _update_usage_stats, saveLRStats, \
    getLRLast, saveQueryStats, getLastQuery, UPDATE_STAT, VIEW_STAT, \
    RETRIEVE_STAT, DOWNLOAD_STAT

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

ADMINROOT = '/{0}editor/'.format(DJANGO_BASE)
TESTFIXTURES_ZIP = '{}/repository/fixtures/tworesources.zip'.format(ROOT_PATH)
PSP_XML = '{}/repository/test_fixtures/PSP/UIB-M10-9_v2.xml'.format(ROOT_PATH)

class StatsTest(django.test.TestCase):
    manager_login = None
    
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))
    
    def setUp(self):
        """
        Sets up some resources with which to test.
        """
        self.stats_server_url = "http://metastats.fbk.eu/"
        
        test_editor_group = EditorGroup.objects.create(name='test_editor_group')
        test_manager_group = EditorGroupManagers.objects.create(
            name='test_manager_group', managed_group=test_editor_group)
        test_utils.create_manager_user('manageruser', 'manager@example.com',
            'secret', (test_editor_group, test_manager_group))
        StatsTest.manager_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'manageruser',
            'password': 'secret',
        }
        
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
    
    def testStatActions(self):
        """
        Testing statistics functions about LR
        """
        client = test_utils.get_client_with_user_logged_in(StatsTest.manager_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        # And verify that we have more than zero resources on the page where we
        # are being redirected:
        self.assertContains(response, "My Resources")
        self.assertNotContains(response, '0 Resources')
        
        statsdata = getLRLast(UPDATE_STAT, 2)
        self.assertEqual(len(statsdata), 2)
        
        for action in (VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT):
            for item in statsdata:
                resource =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
                saveLRStats(resource, action)
            self.assertEqual(len(getLRLast(action, 10)), 2)
        
    def testTopStats(self):
        """
        Tries to load the top stats page of the META-SHARE website.
        """
        client = Client()
        response = client.get('/{0}stats/top/'.format(DJANGO_BASE))
        self.assertTemplateUsed(response, 'stats/topstats.html')
        self.assertContains(response,
                            "Statistics about visiting this META-SHARE node")

    def testLatestQueries(self):
        """
        Test whether there are latest queries
        """
        saveQueryStats("tesQuerytquery 001", "", 10)
        saveQueryStats("tesQuerytquery 002", "", 2)
        latest_query = getLastQuery(2)
        client = Client()
        _url = "/{0}stats/top/?view=latestqueries".format(DJANGO_BASE)
        response = client.get(_url)
        self.assertContains(response,
                            'Statistics about visiting this META-SHARE node')
        self.assertContains(response, 'http://')
        self.assertGreaterEqual(len(latest_query), 1)
        for item in latest_query:
            self.assertContains(response, item['query'])
            
 
    def testServerConnection(self):
        """
        checking if there is at least one resource report available
        from the META-SHARE statistics server.
        """
        LOGGER.info("Connecting ... %s", self.stats_server_url)
        try:
            response = urllib2.urlopen(self.stats_server_url)
            self.assertEquals(200, response.code)
        except urllib2.URLError:
            LOGGER.warn('Failed to contact statistics server on %s',
                        self.stats_server_url)

    def testAddNode(self):
        """
        checking if there is at least one resource report available
        from the META-SHARE statistics server.
        """
        LOGGER.info("Connecting ... %s", self.stats_server_url)
        try:
            response = urllib2.urlopen("{0}addnode?{1}".format(self.stats_server_url, urlencode({'url': DJANGO_URL})))
            self.assertEquals(200, response.code)
        except urllib2.URLError:
            LOGGER.warn('Failed to contact statistics server on %s',
                        self.stats_server_url)

    def testGetDailyStats(self):
        """
        checking if there are the statistics of the day
        """
        client = Client()
        response = client.get('/{0}stats/get'.format(DJANGO_BASE))
        self.assertEquals(200, response.status_code)
    
    def testMyResources(self):
        client = test_utils.get_client_with_user_logged_in(StatsTest.manager_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 2 resource descriptions')
        self.assertNotContains(response, 'Import failed')
        statsdata = getLRLast(UPDATE_STAT, 10)
        numstats = len(statsdata)
        self.assertEqual(numstats, 2)
        
        response = client.get(ADMINROOT+"repository/resourceinfotype_model/", follow=True)
        self.assertContains(response, 'Publish selected ingested resources', msg_prefix='response: {0}'.format(response))

        #publish the resources
        for i in range(1, 3):
            resource = resourceInfoType_model.objects.get(pk=i)
            resource.storage_object.published = True
            resource.storage_object.save()
            response = client.get(resource.get_absolute_url(), follow=True)
            self.assertTemplateUsed(response, 'repository/lr_view.html')
            self.assertContains(response, "Edit")

        response = client.get('/{0}stats/mystats/'.format(DJANGO_BASE))
        self.assertEquals(200, response.status_code)
        self.assertContains(response, 'My resources')
        self.assertContains(response, 'Last view:')
        
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(2, len(statsdata))
        
        #ingest the first resource
        resource = resourceInfoType_model.objects.get(pk=1)
        ingest_resources(None, None, (resource,))
        statsdata = getLRLast(UPDATE_STAT, 10)
        self.assertEqual(1, len(statsdata))
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(1, len(statsdata))
        
        #publish the second resource again
        resource.storage_object.published = True
        resource.storage_object.save()
        response = client.get(resource.get_absolute_url(), follow=True)
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(2, len(statsdata))
         
        #delete the second resource
        resource.delete_deep()        
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(1, len(statsdata))
        
        #unpublish the second resource
        resource = resourceInfoType_model.objects.get(pk=2)
        unpublish_resources(None, None, (resource,))
        statsdata = getLRLast(UPDATE_STAT, 10)
        self.assertEqual(0, len(statsdata))
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(0, len(statsdata))
        
    def client_with_user_logged_in(self, user_credentials):
        client = Client()
        client.get(ADMINROOT)
        response = client.post(ADMINROOT, user_credentials)
        if response.status_code != 302:
            raise Exception, 'could not log in user with credentials: {}\nresponse was: {}'\
                .format(user_credentials, response)
        return client


    
    def testUsage(self):
        # checking if there are the usage statistics
        
        client = test_utils.get_client_with_user_logged_in(StatsTest.manager_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        
        statsdata = getLRLast(UPDATE_STAT, 2)
        self.assertEqual(len(statsdata), 2)
        
        for item in statsdata:
            resource =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
            _update_usage_stats(resource.id, resource.export_to_elementtree())
            
        response = client.get('/{0}stats/usage'.format(DJANGO_BASE))
        self.assertContains(response, "identificationInfo")
