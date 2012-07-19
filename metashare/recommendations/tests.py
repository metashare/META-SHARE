from django.core.urlresolvers import reverse
from django.test.client import Client
from metashare import test_utils, settings
from metashare.recommendations.models import TogetherManager
from metashare.recommendations.recommendations import Resource, \
    SessionResourcesTracker
from metashare.repository import views
from metashare.settings import ROOT_PATH
from metashare.storage.models import PUBLISHED, INGESTED
from metashare.test_utils import create_user
import datetime
import django.test
import shutil


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
        test_utils.clean_resources_db()
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
        test_utils.clean_resources_db()
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
        test_utils.clean_resources_db()
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
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        
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