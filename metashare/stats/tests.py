import django.test
import urllib2
from urllib import urlencode
from django.test.client import Client
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.sites import LOGIN_FORM_KEY

from metashare import test_utils, settings
from metashare.accounts.models import EditorGroup, ManagerGroup
from metashare.repository.models import resourceInfoType_model
from metashare.settings import DJANGO_BASE, DJANGO_URL, ROOT_PATH
from metashare.stats.model_utils import _update_usage_stats, saveLRStats, \
    getLRLast, saveQueryStats, getLastQuery, UPDATE_STAT, VIEW_STAT, \
    RETRIEVE_STAT, DOWNLOAD_STAT
from metashare.stats.models import TogetherManager
from metashare.storage.models import PUBLISHED, INGESTED
from metashare.stats.recommendations import SessionResourcesTracker, Resource
from metashare.repository import views
import datetime
import shutil
from metashare.test_utils import create_user
from django.core.urlresolvers import reverse


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


def _import_resource(res_file_name):
    """
    Imports the resource with the given file name; looks for the file in
    the folder repository/fixtures/; sets publication status to
    PUBLISHED; returns the resource
    """
    res = test_utils.import_xml(
      '{0}/repository/fixtures/{1}'.format(ROOT_PATH, res_file_name))[0]
    res.storage_object.publication_status = PUBLISHED
    res.storage_object.save()
    res.storage_object.update_storage()
    return res


def _import_downloadable_resource(res_file_name):
    """
    Imports the resource with the given file name; looks for the file in
    the folder repository/fixtures/; sets publication status to
    PUBLISHED; adds a downloadable archive; returns the resource
    """
    res = _import_resource(res_file_name)
    res.storage_object.checksum = '3930f5022aff02c7fa27ffabf2eaaba0'
    res.storage_object.save()
    res.storage_object.update_storage()
    shutil.copyfile(
      '{0}/repository/fixtures/archive.zip'.format(settings.ROOT_PATH),
      '{0}/{1}/archive.zip'.format(
        settings.STORAGE_PATH, res.storage_object.identifier))
    return res
    
    
def _download_resource(client, resource):
    """
    Downloads the given resource for the given client;
    it is assumed that it is downloadable and has an AGPL license; 
    returns the http response
    """
    return client.post(reverse(views.download, args=(resource.storage_object.identifier,)),
      { 'in_licence_agree_form': 'True', 'licence_agree': 'True', 'licence': 'AGPL' },
        follow = True)
        

class SimpleTogetherManagerTest(django.test.TestCase):

    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    
    @classmethod
    def setUpClass(cls):
        test_utils.set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        test_utils.set_index_active(True)
    
    def setUp(self):
        """
        Import test fixtures and add resource pairs to TogetherManager
        """
        test_utils.setup_test_storage()
        self.res_1 = _import_resource('elra112.xml')
        self.res_2 = _import_resource('elra135.xml')
        self.res_3 = _import_resource('elra260.xml')
    
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_db()
        test_utils.clean_storage()
    

    def test_counts(self):
        """
        tests the addResourcePair and getTogetherCount methods of TogetherManager
        """
        man = TogetherManager.getManager(Resource.VIEW)
        self.assertEquals(0, man.getTogetherCount(self.res_1, self.res_2))
        man.addResourcePair(self.res_1, self.res_2)
        self.assertEquals(0, man.getTogetherCount(self.res_1, self.res_3))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        self.assertEquals(1, man.getTogetherCount(self.res_2, self.res_1))
        man.addResourcePair(self.res_1, self.res_3)
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_3))
        self.assertEquals(1, man.getTogetherCount(self.res_3, self.res_1))
        man.addResourcePair(self.res_1, self.res_2)
        self.assertEquals(2, man.getTogetherCount(self.res_1, self.res_2))
        self.assertEquals(2, man.getTogetherCount(self.res_2, self.res_1))


class TogetherManagerTest(django.test.TestCase):
    
    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    res_4 = None
    
    @classmethod
    def setUpClass(cls):
        test_utils.set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        test_utils.set_index_active(True)
    
    def setUp(self):
        """
        Import test fixtures and add resource pairs to TogetherManager
        """
        test_utils.setup_test_storage()
        self.res_1 = _import_resource('elra112.xml')
        self.res_2 = _import_resource('elra135.xml')
        self.res_3 = _import_resource('elra260.xml')
        self.res_4 = _import_resource('elra295.xml')
        man = TogetherManager.getManager(Resource.VIEW)
        count = 0
        while (count < 5):
            man.addResourcePair(self.res_1, self.res_2)
            count += 1
        count = 0
        while (count < 10):
            man.addResourcePair(self.res_1, self.res_3)
            count += 1
        count = 0
        while (count < 3):
            man.addResourcePair(self.res_1, self.res_4)
            count += 1
        man = TogetherManager.getManager(Resource.DOWNLOAD)
        count = 0
        while (count < 15):
            man.addResourcePair(self.res_1, self.res_2)
            count += 1
        count = 0
        while (count < 10):
            man.addResourcePair(self.res_1, self.res_3)
            count += 1
        count = 0
        while (count < 5):
            man.addResourcePair(self.res_1, self.res_4)
            count += 1
        
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_db()
        test_utils.clean_storage()
    

    def test_sorting(self):
        man = TogetherManager.getManager(Resource.VIEW)
        sorted_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(3, len(sorted_res))
        self.assertEquals(self.res_3, sorted_res[0])
        self.assertEquals(self.res_2, sorted_res[1])
        self.assertEquals(self.res_4, sorted_res[2])
        
    def test_threshold_filter(self):
        man = TogetherManager.getManager(Resource.VIEW)
        sorted_res = man.getTogetherList(self.res_1, 5)
        self.assertEqual(2, len(sorted_res))
        self.assertEquals(self.res_3, sorted_res[0])
        self.assertEquals(self.res_2, sorted_res[1])
        
    def test_publication_status_filter(self):
        self.res_3.storage_object.publication_status = INGESTED
        self.res_3.storage_object.save()
        self.res_3.storage_object.update_storage()
        man = TogetherManager.getManager(Resource.VIEW)
        sorted_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(2, len(sorted_res))
        self.assertEquals(self.res_2, sorted_res[0])
        self.assertEquals(self.res_4, sorted_res[1])
        
    def test_deleted_filter(self):
        self.res_2.storage_object.deleted = True
        self.res_2.storage_object.save()
        self.res_2.storage_object.update_storage()
        man = TogetherManager.getManager(Resource.VIEW)
        sorted_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(2, len(sorted_res))
        self.assertEquals(self.res_3, sorted_res[0])
        self.assertEquals(self.res_4, sorted_res[1])


class SessionResourcesTrackerTest(django.test.TestCase):
    
    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    res_4 = None
    
    @classmethod
    def setUpClass(cls):
        test_utils.set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        test_utils.set_index_active(True)
    
    def setUp(self):
        """
        Import test fixtures and add resource pairs to TogetherManager
        """
        test_utils.setup_test_storage()
        self.res_1 = _import_resource('elra112.xml')
        self.res_2 = _import_resource('elra135.xml')
        self.res_3 = _import_resource('elra260.xml')
        self.res_4 = _import_resource('elra295.xml')
        self.max_view_interval_backup = settings.MAX_VIEW_INTERVAL
        settings.MAX_VIEW_INTERVAL = 5
        self.max_download_interval_backup = settings.MAX_DOWNLOAD_INTERVAL
        settings.MAX_DOWNLOAD_INTERVAL = 10
    
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_db()
        test_utils.clean_storage()
        settings.MAX_VIEW_INTERVAL = self.max_view_interval_backup
        settings.MAX_DOWNLOAD_INTERVAL = self.max_download_interval_backup 
        
    def test_usage(self):
        
        # test views:
        man = TogetherManager.getManager(Resource.VIEW)
        tracker = SessionResourcesTracker()
        tracker.add_view(self.res_1, datetime.datetime(2012, 7, 16, 18, 0, 0))
        tracker.add_view(self.res_2, datetime.datetime(2012, 7, 16, 18, 0, 1))
        # both resources have been viewed 'together'
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        # viewing the same resource again does NOT increase the count
        tracker.add_view(self.res_2, datetime.datetime(2012, 7, 16, 18, 0, 2))
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        # viewing a resource after the max view interval changes nothing
        tracker.add_view(self.res_3, datetime.datetime(2012, 7, 16, 18, 0, 10))
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        self.assertEquals(0, len(man.getTogetherList(self.res_3, 0)))
        # add another resource
        tracker.add_view(self.res_4, datetime.datetime(2012, 7, 16, 18, 0, 12))
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        self.assertEquals(1, len(man.getTogetherList(self.res_3, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_4, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_3, self.res_4))
        
        # test downloads:
        man = TogetherManager.getManager(Resource.DOWNLOAD)
        tracker.add_download(self.res_1, datetime.datetime(2012, 7, 16, 18, 0, 0))
        tracker.add_download(self.res_2, datetime.datetime(2012, 7, 16, 18, 0, 1))
        # both resources have been downloaded 'together'
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        # downloading the same resource again does NOT increase the count
        tracker.add_download(self.res_2, datetime.datetime(2012, 7, 16, 18, 0, 2))
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        # downloading a resource after the max download interval changes nothing
        tracker.add_download(self.res_3, datetime.datetime(2012, 7, 16, 18, 0, 20))
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        self.assertEquals(0, len(man.getTogetherList(self.res_3, 0)))
        # add another resource
        tracker.add_download(self.res_4, datetime.datetime(2012, 7, 16, 18, 0, 22))
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        self.assertEquals(1, len(man.getTogetherList(self.res_3, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_4, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_3, self.res_4))


class SessionTest(django.test.TestCase):
    
    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    res_4 = None
    
    @classmethod
    def setUpClass(cls):
        test_utils.set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        test_utils.set_index_active(True)
    
    def setUp(self):
        """
        Import test fixtures and add resource pairs to TogetherManager
        """
        test_utils.setup_test_storage()
        self.res_1 = _import_downloadable_resource('elra112.xml')
        self.res_2 = _import_downloadable_resource('elra135.xml')
        self.res_3 = _import_downloadable_resource('elra260.xml')
        self.res_4 = _import_downloadable_resource('elra295.xml')
        create_user('normaluser', 'normal@example.com', 'secret')
        create_user('normaluser2', 'normal2@example.com', 'secret')
        
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_db()
        test_utils.clean_storage()
        
    def test_views(self):
        # client 1 views all 4 resources
        client_1 = Client()
        man = TogetherManager.getManager(Resource.VIEW)
        response = client_1.get(self.res_1.get_absolute_url(), follow = True)
        self.assertEquals(200, response.status_code)
        view_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(0, len(view_res))
        
        response = client_1.get(self.res_2.get_absolute_url(), follow = True)
        self.assertEquals(200, response.status_code)
        view_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(1, len(view_res))
        view_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(1, len(view_res))
        self.assertEqual(1, man.getTogetherCount(self.res_1, self.res_2))
        
        response = client_1.get(self.res_3.get_absolute_url(), follow = True)
        self.assertEquals(200, response.status_code)
        view_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(2, len(view_res))
        view_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(2, len(view_res))
        view_res = man.getTogetherList(self.res_3, 0)
        self.assertEqual(2, len(view_res))
        
        response = client_1.get(self.res_4.get_absolute_url(), follow = True)
        self.assertEquals(200, response.status_code)
        view_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(3, len(view_res))
        view_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(3, len(view_res))
        view_res = man.getTogetherList(self.res_3, 0)
        self.assertEqual(3, len(view_res))
        view_res = man.getTogetherList(self.res_4, 0)
        self.assertEqual(3, len(view_res))
        
        # another client views 2 of the resources, counts are increased
        client_2 = Client()
        response = client_2.get(self.res_1.get_absolute_url(), follow = True)
        self.assertEquals(200, response.status_code)
        view_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(3, len(view_res))
        
        response = client_2.get(self.res_2.get_absolute_url(), follow = True)
        self.assertEquals(200, response.status_code)
        view_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(3, len(view_res))
        view_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(3, len(view_res))
        # counts of res_1 and res_2 appearing together is increased
        self.assertEqual(2, man.getTogetherCount(self.res_1, self.res_2))
        
        # make sure that downloads are no touched
        man = TogetherManager.getManager(Resource.DOWNLOAD)
        download_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(0, len(download_res))
        
    def test_downloads(self):
        # client 1 downloads all 4 resources
        client_1 = Client()
        client_1.login(username='normaluser', password='secret')
        man = TogetherManager.getManager(Resource.DOWNLOAD)
        response = _download_resource(client_1, self.res_1)
        self.assertEquals(200, response.status_code)
        download_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(0, len(download_res))
        
        response = _download_resource(client_1, self.res_2)
        self.assertEquals(200, response.status_code)
        download_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(1, len(download_res))
        download_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(1, len(download_res))
        self.assertEqual(1, man.getTogetherCount(self.res_1, self.res_2))
        
        response = _download_resource(client_1, self.res_3)
        self.assertEquals(200, response.status_code)
        download_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(2, len(download_res))
        download_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(2, len(download_res))
        download_res = man.getTogetherList(self.res_3, 0)
        self.assertEqual(2, len(download_res))
        
        response = _download_resource(client_1, self.res_4)
        self.assertEquals(200, response.status_code)
        download_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(3, len(download_res))
        download_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(3, len(download_res))
        download_res = man.getTogetherList(self.res_3, 0)
        self.assertEqual(3, len(download_res))
        download_res = man.getTogetherList(self.res_4, 0)
        self.assertEqual(3, len(download_res))
        
        # another client downloads 2 of the resources, counts are increased
        client_2 = Client()
        client_2.login(username='normaluser2', password='secret')
        response = _download_resource(client_2, self.res_1)
        self.assertEquals(200, response.status_code)
        download_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(3, len(download_res))
        
        response = _download_resource(client_2, self.res_2)
        self.assertEquals(200, response.status_code)
        download_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(3, len(download_res))
        download_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(3, len(download_res))
        # counts of res_1 and res_2 appearing together is increased
        self.assertEqual(2, man.getTogetherCount(self.res_1, self.res_2))

        # make sure that views are no touched;
        # in the web interface, the resource has of course to be viewed first
        # before it could be downloaded 
        man = TogetherManager.getManager(Resource.VIEW)
        view_res = man.getTogetherList(self.res_1, 0)
        self.assertEqual(0, len(view_res))