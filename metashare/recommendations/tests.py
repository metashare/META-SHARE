import datetime
import django.test
import shutil
import logging
from django.core.urlresolvers import reverse
from django.test.client import Client
from metashare import test_utils, settings
from metashare.recommendations.models import TogetherManager, ResourceCountPair, \
    ResourceCountDict
from metashare.recommendations.recommendations import Resource, \
    SessionResourcesTracker, get_more_from_same_creators,\
    get_more_from_same_projects
from metashare.repository import views
from metashare.settings import ROOT_PATH, LOG_HANDLER
from metashare.storage.models import PUBLISHED, INGESTED, StorageObject
from metashare.test_utils import create_user
from metashare.stats.models import LRStats, UsageStats
from metashare.sync.sync_utils import remove_resource
from metashare.stats.model_utils import saveLRStats, UPDATE_STAT
from django.db.utils import IntegrityError
from django.core.management import call_command
from metashare.repository.models import resourceInfoType_model

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

def _import_resource(res_file_name):
    """
    Imports the resource with the given file name; looks for the file in
    the folder recommendations/fixtures/; sets publication status to
    PUBLISHED; returns the resource
    """
    res = test_utils.import_xml(
      '{0}/recommendations/fixtures/{1}'.format(ROOT_PATH, res_file_name))
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
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))
    
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
        
    def test_delete_deep(self):
        """
        tests that deep deleting a resource removes it from the counts
        """
        man = TogetherManager.getManager(Resource.VIEW)
        self.assertEquals(0, man.getTogetherCount(self.res_1, self.res_2))
        man.addResourcePair(self.res_1, self.res_2)
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        self.assertEquals(2, len(ResourceCountPair.objects.all()))
        self.assertEquals(2, len(ResourceCountDict.objects.all()))
        self.res_1.delete_deep()
        # after deep deletion, only one instance remains:
        # the (empty) resource count dictionary of res_2            
        self.assertEquals(0, len(ResourceCountPair.objects.all()))
        self.assertEquals(1, len(ResourceCountDict.objects.all()))
        
    def test_delete_deep_with_keeping_recommendations(self):
        """
        tests that deep deleting a resource keeps the recommendations if requested
        """
        man = TogetherManager.getManager(Resource.VIEW)
        self.assertEquals(0, man.getTogetherCount(self.res_1, self.res_2))
        man.addResourcePair(self.res_1, self.res_2)
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        self.assertEquals(2, len(ResourceCountPair.objects.all()))
        self.assertEquals(2, len(ResourceCountDict.objects.all()))
        self.assertEquals(3, len(resourceInfoType_model.objects.all())) 
        self.assertEquals(3, len(StorageObject.objects.all())) 
        self.res_1.storage_object.delete()
        self.res_1.delete_deep(keep_stats=True)
        self.assertEquals(2, len(resourceInfoType_model.objects.all()))
        self.assertEquals(2, len(StorageObject.objects.all())) 
        # recommendations stay the same
        self.assertEquals(2, len(ResourceCountPair.objects.all()))
        self.assertEquals(2, len(ResourceCountDict.objects.all()))
        # recommendations are deleted after repairing them
        call_command('repair_recommendations', interactive=False)
        self.assertEquals(0, len(ResourceCountPair.objects.all()))
        self.assertEquals(1, len(ResourceCountDict.objects.all()))
        
    def test_unique_together_constraint(self):
        man = TogetherManager.getManager(Resource.VIEW)
        man.addResourcePair(self.res_1, self.res_2)
        res_count_dict = man.resourcecountdict_set.get(
          lrid=self.res_1.storage_object.identifier)
        try:
            res_count_dict.resourcecountpair_set.create(
              lrid = self.res_2.storage_object.identifier)
            self.fail("Should have raised an exception")
        except IntegrityError:
            # reset database connection; required for PostgreSQL
            from django import db
            db.close_connection()


class TogetherManagerTest(django.test.TestCase):
    
    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    res_4 = None
    
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

    def test_delete_deep(self):
        man = TogetherManager.getManager(Resource.VIEW)
        sorted_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(1, len(sorted_res))
        self.res_1.delete_deep()
        sorted_res = man.getTogetherList(self.res_2, 0)
        self.assertEqual(0, len(sorted_res))


class SessionResourcesTrackerTest(django.test.TestCase):
    
    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    res_4 = None
    
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


    def test_delete_deep(self):
        
        # test views:
        man = TogetherManager.getManager(Resource.VIEW)
        tracker = SessionResourcesTracker()
        tracker.add_view(self.res_1, datetime.datetime(2012, 7, 16, 18, 0, 0))
        tracker.add_view(self.res_2, datetime.datetime(2012, 7, 16, 18, 0, 1))
        # both resources have been viewed 'together'
        self.assertEquals(1, len(man.getTogetherList(self.res_1, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_2, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_1, self.res_2))
        # deep delete resource
        self.res_1.delete_deep()
        self.assertEquals(0, len(man.getTogetherList(self.res_2, 0)))
        
        # test downloads:
        man = TogetherManager.getManager(Resource.DOWNLOAD)
        tracker.add_download(self.res_3, datetime.datetime(2012, 7, 16, 18, 0, 0))
        tracker.add_download(self.res_4, datetime.datetime(2012, 7, 16, 18, 0, 1))
        # both resources have been downloaded 'together'
        self.assertEquals(1, len(man.getTogetherList(self.res_3, 0)))
        self.assertEquals(1, len(man.getTogetherList(self.res_4, 0)))
        self.assertEquals(1, man.getTogetherCount(self.res_3, self.res_4))
        # deep delete resource
        self.res_3.delete_deep()
        self.assertEquals(0, len(man.getTogetherList(self.res_4, 0)))
        

class SessionTest(django.test.TestCase):
    
    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    res_4 = None
    
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
        Import test fixtures and add resource pairs to TogetherManager
        """
        test_utils.setup_test_storage()
        test_utils.clean_stats()
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
        test_utils.clean_stats()
        
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
        
        # make sure that statistics are updated when a resource is 
        # completely removed
        saveLRStats(self.res_1, UPDATE_STAT)
        saveLRStats(self.res_2, UPDATE_STAT)
        saveLRStats(self.res_3, UPDATE_STAT)
        saveLRStats(self.res_4, UPDATE_STAT)
        self.assertEquals(9, len(LRStats.objects.all()))
        self.assertEquals(219, len(UsageStats.objects.all()))
        remove_resource(self.res_1.storage_object)
        self.assertEquals(7, len(LRStats.objects.all()))
        self.assertEquals(163, len(UsageStats.objects.all()))
        
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
        

class CreatorTest(django.test.TestCase):
    
    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    res_4 = None
    res_5 = None
    
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
        Import test fixtures and add resource pairs to TogetherManager
        """
        test_utils.setup_test_storage()
        self.res_1 = _import_downloadable_resource('creators-projects-1.xml')
        self.res_2 = _import_downloadable_resource('creators-projects-2.xml')
        self.res_3 = _import_downloadable_resource('creators-projects-3.xml')
        self.res_4 = _import_downloadable_resource('creators-projects-4.xml')
        self.res_5 = _import_downloadable_resource('creators-projects-5.xml')
        
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        
    def test_creator(self):
        self.assertEquals(2, len(get_more_from_same_creators(self.res_1)))
        self.assertEquals(1, len(get_more_from_same_creators(self.res_2)))
        self.assertEquals(1, len(get_more_from_same_creators(self.res_3)))
        self.assertEquals(0, len(get_more_from_same_creators(self.res_4)))
        self.assertEquals(0, len(get_more_from_same_creators(self.res_5)))
        
    def test_project(self):
        self.assertEquals(0, len(get_more_from_same_projects(self.res_1)))
        self.assertEquals(1, len(get_more_from_same_projects(self.res_2)))
        self.assertEquals(1, len(get_more_from_same_projects(self.res_3)))
        self.assertEquals(2, len(get_more_from_same_projects(self.res_4)))
        self.assertEquals(0, len(get_more_from_same_projects(self.res_5)))
        
    