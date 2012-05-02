import django.test
from django.test.client import Client
from django.contrib.auth.models import User, Group
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.sites import LOGIN_FORM_KEY
from metashare.settings import DJANGO_BASE, DJANGO_URL, ROOT_PATH
from metashare.stats.model_utils import saveLRStats, getLRLast, saveQueryStats, getLastQuery, UPDATE_STAT, VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT
import urllib2
from urllib import urlencode

ADMINROOT = '/{0}editor/'.format(DJANGO_BASE)
TESTFIXTURES_ZIP = '{}/repository/fixtures/tworesources.zip'.format(ROOT_PATH)

class StatsTest(django.test.TestCase):
    editor_login = None
    
    def setUp(self):
        """
        Sets up some resources with which to test.
        """
        self.stats_server_url = "http://metastats.fbk.eu/"
        editoruser = User.objects.create_user('editoruser', 'editor@example.com',
          'secret')
        editoruser.is_staff = True
        globaleditors = Group.objects.get(name='globaleditors')
        editoruser.groups.add(globaleditors)
        editoruser.save()
        
        StatsTest.editor_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'editoruser',
            'password': 'secret',
        }
        
    
    def testStatActions(self):
        """
        Testing statistics functions about LR
        """
        lrid = "00000000"
        for action in (UPDATE_STAT, VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT):
            saveLRStats("anonymous", lrid, "", action)
            self.assertEqual(len(getLRLast(action, 10)), 1)
        
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
        saveQueryStats("anonymous", "", "testquery 000", 1, 0)
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
        client = self.client_with_user_logged_in(StatsTest.editor_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 2 resource descriptions')
        self.assertNotContains(response, 'Import failed')
        
        response = client.get(ADMINROOT+"repository/resourceinfotype_model/", follow=True)
        self.assertContains(response, 'Publish selected ingested resources', msg_prefix='response: {0}'.format(response))
        
        url = '/{0}repository/browse/1/'.format(DJANGO_BASE)
        response = client.get(url, follow = True)
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

