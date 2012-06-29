import django.test
import urllib2
from urllib import urlencode
from django.test.client import Client
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.sites import LOGIN_FORM_KEY

from metashare import test_utils
from metashare.accounts.models import EditorGroup, ManagerGroup
from metashare.repository.models import resourceInfoType_model
from metashare.settings import DJANGO_BASE, DJANGO_URL, ROOT_PATH
from metashare.stats.model_utils import _update_usage_stats, saveLRStats, \
    getLRLast, saveQueryStats, getLastQuery, UPDATE_STAT, VIEW_STAT, \
    RETRIEVE_STAT, DOWNLOAD_STAT


ADMINROOT = '/{0}editor/'.format(DJANGO_BASE)
TESTFIXTURES_ZIP = '{}/repository/fixtures/tworesources.zip'.format(ROOT_PATH)
PSP_XML = '{}/repository/test_fixtures/PSP/UIB-M10-9_v2.xml'.format(ROOT_PATH)

class StatsTest(django.test.TestCase):
    manager_login = None
    
    def setUp(self):
        """
        Sets up some resources with which to test.
        """
        self.stats_server_url = "http://metastats.fbk.eu/"
        
        test_editor_group = EditorGroup.objects.create(name='test_editor_group')
        test_manager_group = ManagerGroup.objects.create(
            name='test_manager_group', managed_group=test_editor_group)
        test_utils.create_manager_user('manageruser', 'manager@example.com',
            'secret', (test_editor_group, test_manager_group))
        StatsTest.manager_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'manageruser',
            'password': 'secret',
        }
        
    
    def testStatActions(self):
        """
        Testing statistics functions about LR
        """
        client = self.client_with_user_logged_in(StatsTest.manager_login)
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
        
    def testTop10(self):
        """
        Tries to load the top 10 page of the META-SHARE website
        """
        client = Client()
        response = client.get('/{0}stats/top/'.format(DJANGO_BASE))
        self.assertEqual('stats/topstats.html',
          response.templates[0].name)
            

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
        self.assertEquals(200, response.status_code)
        self.assertContains(response, 'Top 10')
        self.assertContains(response, 'http://')
        self.assertGreaterEqual(len(latest_query), 1)
        for item in latest_query:
            self.assertContains(response, item['query'])
            
 
    def testServerConnection(self):
        """
        checking if there is at least one resource report available
        from the META-SHARE statistics server.
        """
        print "Connecting... {0}".format(self.stats_server_url)
        try:
            response = urllib2.urlopen(self.stats_server_url)
            self.assertEquals(200, response.code)
        except urllib2.URLError:
            print 'WARNING! Failed contacting statistics server on %s' % self.stats_server_url
        
    def testAddNode(self):
        """
        checking if there is at least one resource report available
        from the META-SHARE statistics server.
        """
        print "Connecting... {0}".format(self.stats_server_url)
        try:
            response = urllib2.urlopen("{0}addnode?{1}".format(self.stats_server_url, urlencode({'url': DJANGO_URL})))
            self.assertEquals(200, response.code)
        except urllib2.URLError:
            print 'WARNING! Failed contacting statistics server on %s' % self.stats_server_url
        
    def testGet(self):
        """
        checking if there are the statistics of the day
        """
        client = Client()
        response = client.get('/{0}stats/get'.format(DJANGO_BASE))
        self.assertEquals(200, response.status_code)
    
    def testMyResources(self):
        client = self.client_with_user_logged_in(StatsTest.manager_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 2 resource descriptions')
        self.assertNotContains(response, 'Import failed')
        
        response = client.get(ADMINROOT+"repository/resourceinfotype_model/", follow=True)
        self.assertContains(response, 'Publish selected ingested resources', msg_prefix='response: {0}'.format(response))

        imported_res = resourceInfoType_model.objects.get(pk=1)
        imported_res.storage_object.published = True
        imported_res.storage_object.save()
        response = client.get(imported_res.get_absolute_url(), follow=True)
        self.assertTemplateUsed(response, 'repository/lr_view.html')
        self.assertContains(response, "Edit")

        response = client.get('/{0}stats/mystats/'.format(DJANGO_BASE))
        self.assertEquals(200, response.status_code)
        self.assertContains(response, 'My resources')
        self.assertContains(response, 'Last view:')

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
        
        client = self.client_with_user_logged_in(StatsTest.manager_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        
        statsdata = getLRLast(UPDATE_STAT, 2)
        self.assertEqual(len(statsdata), 2)
        
        for item in statsdata:
            resource =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
            _update_usage_stats(resource.id, resource.export_to_elementtree())
            
        response = client.get('/{0}stats/usage'.format(DJANGO_BASE))
        if response.status_code != 200:
            print Exception, 'could not get usage stats: {}'.format(response)
        else:
            self.assertContains(response, "identificationInfo")
    
