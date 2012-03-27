import django.test
from django.test.client import Client
from metashare.settings import DJANGO_BASE, DJANGO_URL, STATS_SERVER_URL
from metashare.stats.model_utils import saveLRStats, getLRLast, saveQueryStats, getLastQuery, UPDATE_STAT, VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT
import urllib2
from urllib import urlencode

class StatsTest(django.test.TestCase):
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
        saveQueryStats("anonymous", "testquery 000", 1, 0)
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
        print "Connecting... {0}".format(STATS_SERVER_URL)
        try:
            response = urllib2.urlopen(STATS_SERVER_URL)
            self.assertEquals(200, response.code)
        except urllib2.URLError:
            print 'WARNING! Failed contacting statistics server on %s' % STATS_SERVER_URL
        
    def testAddNode(self):
        """
        checking if there is at least one resource report available
        from the META-SHARE statistics server.
        """
        print "Connecting... {0}".format(STATS_SERVER_URL)
        try:
            response = urllib2.urlopen(STATS_SERVER_URL+"addnode?" + urlencode({'url': DJANGO_URL}))
            self.assertEquals(200, response.code)
        except urllib2.URLError:
            print 'WARNING! Failed contacting statistics server on %s' % STATS_SERVER_URL
        
    def testGet(self):
        """
        checking if there are the statistics of the day
        """
        client = Client()
        response = client.get('/{0}stats/get'.format(DJANGO_BASE))
        # cfedermann: Django's test Client does not use .code but .status_code!
        self.assertEquals(200, response.status_code)
            

