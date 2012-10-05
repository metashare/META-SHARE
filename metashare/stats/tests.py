import logging
import urllib2
from urllib import urlencode
import uuid
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.test.client import Client
from django.test.testcases import TestCase
from metashare import test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers
from metashare.repository.models import resourceInfoType_model
from metashare.settings import ROOT_PATH, STORAGE_PATH, LOG_HANDLER, DJANGO_BASE, STATS_SERVER_URL, DJANGO_URL
from metashare.storage.models import INGESTED
from metashare.stats.model_utils import update_usage_stats, UsageStats, saveLRStats, getLRLast, getLastQuery, \
    UPDATE_STAT, VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT
from metashare.stats.views import callServerStats

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
        owner = test_utils.create_manager_user(
            'manageruser', 'manager@example.com', 'secret',
            (_test_editor_group, _test_manager_group))       
        
        # load first resource
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        _result.editor_groups.add(_test_editor_group)
        _result.owners.add(owner)
        # load second resource
        _fixture = '{0}/repository/test_fixtures/ingested-corpus-AudioVideo-French.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        _result.editor_groups.add(_test_editor_group)
        _result.owners.add(owner)
        
        # create a normal user
        test_utils.create_user('user', 'user@example.com', 'mypasswd')
        
    
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
        
        for i in range(0, 2):
            resource = resourceInfoType_model.objects.get(pk=resources[i].pk)
            for action in (VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT):
                saveLRStats(resource, action)
                self.assertEqual(len(getLRLast(action, 10)), i+1)
 
    def test_visiting_stats(self):
        """
        Tries to load the visiting stats page of the META-SHARE website.
        Some user calls from 193.254.26.9 are used as example of Italian IP address
        """
        client = Client()
        client.login(username='manageruser', password='secret')
        client_user = Client(REMOTE_ADDR="193.254.26.9")
        client_user.login(username='user', password='secret')
        resources =  resourceInfoType_model.objects.all()
        for resource in resources:
            resource.storage_object.publication_status = INGESTED
            resource.storage_object.save()
            client.post(ADMINROOT, \
                {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id}, \
                follow=True)
            url = resource.get_absolute_url()
            response = client_user.get(url, follow = True)
            self.assertTemplateUsed(response,
                'repository/resource_view/lr_view.html')

        response = client_user.get('/{0}stats/top/?view=latestupdated'.format(DJANGO_BASE))
        self.assertNotContains(response, ">No data found<")
        
        response = client_user.get('/{0}stats/top/?view=topdownloaded'.format(DJANGO_BASE))
        self.assertContains(response, ">No data found<")
        
        response = client_user.get('/{0}stats/top/'.format(DJANGO_BASE))
        self.assertTemplateUsed(response, 'stats/topstats.html')
        self.assertContains(response, "META-SHARE node visits statistics")
        self.assertNotContains(response, ">No data found<")

        response = client_user.get('/{0}stats/top/?last=week'.format(DJANGO_BASE))
        self.assertNotContains(response, ">No data found<")

        response = client_user.get('/{0}stats/top/?country=IT'.format(DJANGO_BASE))
        self.assertNotContains(response, ">No data matched<")

        response = client_user.get('/{0}stats/top/?last=week&country=DE'.format(DJANGO_BASE))
        self.assertContains(response, ">No data matched<")
        
    def test_latest_queries(self):
        """
        Test whether there are latest queries
        """
        client = Client()
        response = client.get('/{0}repository/search/?q=italian'.format(DJANGO_BASE))
        response = client.get('/{0}repository/search/?q=italian&selected_facets=languageNameFilter_exact:Italian'.format(DJANGO_BASE))
        response = client.get('/{0}stats/top/?view=topqueries'.format(DJANGO_BASE))
        self.assertNotContains(response, ">No data found<")

        response = client.get('/{0}stats/top/?view=latestqueries'.format(DJANGO_BASE))
        self.assertNotContains(response, ">No data found<")
        latest_query = getLastQuery(2)
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
            response = callServerStats()
            self.assertEquals(True, response)

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
        client.login(username='manageruser', password='secret')
        resources =  resourceInfoType_model.objects.all()
        for resource in resources:
            resource.storage_object.publication_status = INGESTED
            resource.storage_object.save()
            client.post(ADMINROOT, \
                {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id}, \
                follow=True)
            
        # get stats days date 
        response = client.get('/{0}stats/days'.format(DJANGO_BASE))
        self.assertEquals(200, response.status_code)
        # get stats info of the node 
        response = client.get('/{0}stats/get'.format(DJANGO_BASE))
        self.assertEquals(200, response.status_code)
        self.assertContains(response, "lrcount")
        self.assertNotContains(response, "usagestats")
        # get full stats info of the node 
        response = client.get('/{0}stats/get/?statsid={1}'.format(DJANGO_BASE, str(uuid.uuid3(uuid.NAMESPACE_DNS, STORAGE_PATH))))
        self.assertEquals(200, response.status_code)
        self.assertContains(response, "usagestats")
    
    def test_my_resources(self):
        client = Client()
        client.login(username='manageruser', password='secret')
        resources =  resourceInfoType_model.objects.all()
        for resource in resources:
            resource.storage_object.publication_status = INGESTED
            resource.storage_object.save()
            client.post(ADMINROOT, \
                {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id}, \
                follow=True)
            url = resource.get_absolute_url()
            response = client.get(url, follow = True)
            self.assertTemplateUsed(response,
                'repository/resource_view/lr_view.html')
        
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(2, len(statsdata))

        response = client.get('/{0}stats/top/'.format(DJANGO_BASE))
        self.assertNotContains(response, ">No data found<")
        self.assertContains(response, ">My resources<")
        
        response = client.get('/{0}stats/mystats/'.format(DJANGO_BASE))
        self.assertTemplateUsed(response, 'stats/mystats.html')
        self.assertContains(response, "Resource name")

        
        # make sure delete a resource from storage_object.deleted may delete any part of its statistics:
        # delete the second resource
        resource = resourceInfoType_model.objects.all()[0]
        resource.delete_deep()        
        #resource.storage_object.delete()
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(1, len(statsdata))
        
        response = client.get('/{0}stats/usage/'.format(DJANGO_BASE))
        self.assertContains(response, "Metadata usage in 1 resource")

        #delete the first resource
        resource = resourceInfoType_model.objects.all()[0]
        resource.delete_deep()        
        statsdata = getLRLast(VIEW_STAT, 10)
        self.assertEqual(0, len(statsdata))

        response = client.get('/{0}stats/mystats/'.format(DJANGO_BASE))
        self.assertContains(response, ">No data found<")
        response = client.get('/{0}stats/top/'.format(DJANGO_BASE))
        self.assertContains(response, ">No data found<")
            
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
        self.assertContains(response, "Metadata usage in 2 resources")

        response = client.post('/{0}stats/usage/'.format(DJANGO_BASE), {'model': 'identificationInfoType_model',
                'class': 'identificationInfoType_model', 'field': 'resourceName'})
        self.assertContains(response, "div id=fieldvalues")
        
        # remove all usage stats and check if there is the updating automatically
        UsageStats.objects.all().delete()
        # the usage stats are build from scratch calling update_usage_stats
        # UsageThread threads does not work, it eraised a "database is locked" exception
        for resource in resources:
            if not UsageStats.objects.filter(lrid=resource.storage_object.identifier).exists():
                update_usage_stats(resource.storage_object.identifier, resource.export_to_elementtree())
        response = client.get('/{0}stats/usage/'.format(DJANGO_BASE))
        self.assertContains(response, "Metadata usage in 2 resources")

