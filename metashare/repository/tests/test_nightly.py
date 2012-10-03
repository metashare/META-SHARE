import logging
from zipfile import ZipFile
from django.test import TestCase
from django.test.client import Client
from metashare import test_utils, xml_utils
from metashare.settings import ROOT_PATH, LOG_HANDLER, TEST_MODE_NAME
from metashare.repository.supermodel import OBJECT_XML_CACHE
from metashare.repository.models import resourceInfoType_model
from metashare.repository.tests.test_view import check_resource_view

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

RESOURCES_ZIP_FILE = '{0}/../misc/testdata/v3.0/all.zip'.format(ROOT_PATH) 

class NightlyTests(TestCase):
    """
    Defines a number of tests for the nightly build.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Set up the test
        """
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
        # disable indexing during import
        test_utils.set_index_active(False)
        
        # import resources
        test_utils.setup_test_storage()
        OBJECT_XML_CACHE.clear()
        test_utils.import_xml_or_zip(RESOURCES_ZIP_FILE)

        # enable indexing 
        test_utils.set_index_active(True)
    
        # update index
        from django.core.management import call_command
        call_command('rebuild_index', interactive=False, using=TEST_MODE_NAME)
        
    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up the test
        """
        LOGGER.info("finished '{}' tests".format(cls.__name__))
        
        # disable indexing during import
        test_utils.set_index_active(False)
        
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        OBJECT_XML_CACHE.clear()
        
        # enable indexing 
        test_utils.set_index_active(True)
    
        # update index
        from django.core.management import call_command
        call_command('rebuild_index', interactive=False, using=TEST_MODE_NAME)

        
    def testSuccessfulImport(self):
        """
        Checks that all resources have been imported.
        """
        
        # count xml files in resources zip
        res_count = 0
        with ZipFile(RESOURCES_ZIP_FILE, 'r') as temp_zip:
            for _name in temp_zip.namelist():
                if _name.endswith('.xml'):
                    res_count += 1
        # check that every xml file is available as resource
        self.assertEqual(len(resourceInfoType_model.objects.all()), res_count)


    #TODO replace with next text when single resource view is complete
    def testSingleResourceView(self):
        """
        Checks that each resource's single view is displayed correctly.
        """
        
        # disable indexing; we don't need stat updates for this test
        test_utils.set_index_active(False)
        
        count = 0
        for _res in resourceInfoType_model.objects.all():
            count += 1
            LOGGER.info("calling {}. resource at {}".format(count, _res.get_absolute_url()))
            # always create a new client to force a new session
            client = Client()
            response = client.get(_res.get_absolute_url(), follow = True)
            self.assertEquals(200, response.status_code)
            self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
            self.assertContains(response, xml_utils.html_escape(_res.real_unicode_()))

        # enable indexing 
        test_utils.set_index_active(True)


    #TODO activate when single resource view is complete
    def deactivated_testSingleResourceViewAll(self):
        """
        Checks that each resource's single view is displayed correctly.
        """
        
        # disable indexing; we don't need stat updates for this test
        test_utils.set_index_active(False)
        
        queryset = resourceInfoType_model.objects.all()
        check_resource_view(queryset, self)

        # enable indexing 
        test_utils.set_index_active(True)
