import logging
import urllib2
from urllib import urlencode

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.test.client import Client
from django.test.testcases import TestCase

from metashare import test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers
from metashare.repository.models import resourceInfoType_model
from metashare.settings import DJANGO_BASE, ROOT_PATH, LOG_HANDLER, STATS_SERVER_URL, DJANGO_URL
from metashare.storage.models import INGESTED
from metashare.stats.model_utils import saveLRStats, getLRLast, saveQueryStats, getLastQuery, \
    UPDATE_STAT, VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

ADMINROOT = '/{0}editor/repository/resourceinfotype_model/'.format(DJANGO_BASE)

class StatsTest(TestCase):

    resource_id = None
    
    @classmethod
    def setUpClass(cls):
        """
        Import a resource to test the workflow changes for
        """
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)        
        test_utils.setup_test_storage()
        _test_editor_group = \
            EditorGroup.objects.create(name='test_editor_group')
        _test_manager_group = \
            EditorGroupManagers.objects.create(name='test_manager_group',
                                               managed_group=_test_editor_group)            
        test_utils.create_manager_user(
            'manageruser', 'manager@example.com', 'secret',
            (_test_editor_group, _test_manager_group))
        
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        _result.editor_groups.add(_test_editor_group)
        #StatsTest.resource_id = _result.id      
        _fixture = '{0}/repository/test_fixtures/ingested-corpus-AudioVideo-French.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        _result.editor_groups.add(_test_editor_group)
        
    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def test_stats_actions(self):
        """
        Testing statistics functions about LR
        """
        statsdata = getLRLast(UPDATE_STAT, 2)
        self.assertEqual(len(statsdata), 0)
        
        resources =  resourceInfoType_model.objects.all()
        for resource in resources:
            for action in (VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT):
                saveLRStats(resource, action)
                self.assertEqual(len(getLRLast(action, 10)), 0)

        # change the status in published
        client = Client()
        client.login(username='manageruser', password='secret')
        resources =  resourceInfoType_model.objects.all()
        for resource in resources:
            resource.storage_object.publication_status = INGESTED
            resource.storage_object.save()
            client.post(ADMINROOT,
            {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        
        for i in range(1, 3):
            resource = resourceInfoType_model.objects.get(pk=i)
            for action in (VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT):
                saveLRStats(resource, action)
                self.assertEqual(len(getLRLast(action, 10)), i)
 
    def test_visiting_stats(self):
        """
        Tries to load the visiting stats page of the META-SHARE website.
        """
        client = Client()
        response = client.get('/{0}stats/top/'.format(DJANGO_BASE))
        self.assertTemplateUsed(response, 'stats/topstats.html')
        self.assertContains(response, "META-SHARE node visits statistics")

    def test_latest_queries(self):
        """
        Test whether there are latest queries
        """
        saveQueryStats("tesQuerytquery 001", "", 10)
        saveQueryStats("tesQuerytquery 002", "", 2)
        latest_query = getLastQuery(2)
        client = Client()
        _url = "/{0}stats/top/?view=latestqueries".format(DJANGO_BASE)
        response = client.get(_url)
        self.assertContains(response, 'META-SHARE node visits statistics')
        self.assertContains(response, 'http://')
        self.assertGreaterEqual(len(latest_query), 1)
        for item in latest_query:
            self.assertContains(response, item['query'])
            
 
    def test_stats_server(self):
        """
        checking if there is at least one resource report available
        from the META-SHARE statistics server.
        """
        LOGGER.info("Connecting ... %s", STATS_SERVER_URL)
        try:
            response = urllib2.urlopen(STATS_SERVER_URL)
            self.assertEquals(200, response.code)
        except urllib2.URLError:
            LOGGER.warn('Failed to contact statistics server on %s',
                        STATS_SERVER_URL)

    def test_add_new_node(self):
        """
        checking if there is at least one resource report available
        from the META-SHARE statistics server.
        """
        LOGGER.info("Connecting ... %s", STATS_SERVER_URL)
        try:
            response = urllib2.urlopen("{0}addnode?{1}".format(STATS_SERVER_URL, urlencode({'url': DJANGO_URL})))
            self.assertEquals(200, response.code)
        except urllib2.URLError:
            LOGGER.warn('Failed to contact statistics server on %s',
                        STATS_SERVER_URL)

    def test_daily_stats(self):
        """
        checking if there are the statistics of the day
        """
        client = Client()
        response = client.get('/{0}stats/get'.format(DJANGO_BASE))
        self.assertEquals(200, response.status_code)
    
    def test_my_resources(self):
        client = Client()
        client.login(username='manageruser', password='secret')
        resources =  resourceInfoType_model.objects.all()
        for resource in resources:
            resource.storage_object.publication_status = INGESTED
            resource.storage_object.save()
            client.post(ADMINROOT,
            {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
            url = resource.get_absolute_url()
            response = client.get(url, follow = True)
            self.assertTemplateUsed(response, 'repository/lr_view.html')
        
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(2, len(statsdata))
        
        #delete the second resource
        resource = resourceInfoType_model.objects.get(pk=1)
        resource.delete_deep()        
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(1, len(statsdata))
                
    
    def test_usage(self):
        # checking if there are the usage statistics
        client = Client()
        response = client.get('/{0}stats/top/'.format(DJANGO_BASE))
        self.assertTemplateUsed(response, 'stats/topstats.html')
        self.assertContains(response, "META-SHARE node visits statistics")
        self.assertNotContains(response, "identificationInfo")
        
        client.login(username='manageruser', password='secret')
        resources =  resourceInfoType_model.objects.all()
        for resource in resources:
            resource.storage_object.publication_status = INGESTED
            resource.storage_object.save()
            client.post(ADMINROOT,
            {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        
        statsdata = getLRLast(UPDATE_STAT, 2)
        self.assertEqual(len(statsdata), 2)
                        
        response = client.get('/{0}stats/usage/'.format(DJANGO_BASE))
        self.assertContains(response, "identificationInfo")
        

