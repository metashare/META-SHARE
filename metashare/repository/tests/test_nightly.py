'''
Created on 27.08.2012

@author: steffen
'''

from django.test import TestCase
from metashare import test_utils, xml_utils
from metashare.settings import ROOT_PATH
from metashare.repository.supermodel import OBJECT_XML_CACHE
from metashare.repository.models import resourceInfoType_model
from zipfile import ZipFile
from django.test.client import Client

RESOURCES_ZIP_FILE = '{0}/../misc/testdata/v2.1/metashare_resources_v2.1.zip'.format(ROOT_PATH) 

class NightlyTests(TestCase):
    """
    Defines a number of tests for the nightly build.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Set up the test
        """
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
        call_command('rebuild_index', interactive=False)
        
    
    @classmethod
    def tearDown(cls):
        """
        Clean up the test
        """
        # disable indexing during import
        test_utils.set_index_active(False)
        
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        OBJECT_XML_CACHE.clear()
        
        # enable indexing 
        test_utils.set_index_active(True)
    
        # update index
        from django.core.management import call_command
        call_command('rebuild_index', interactive=False)

        
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
    
    
    def testSingleResourceView(self):
        """
        Checks that each resource's single view is displayed correctly.
        """
        
        # disable indexing; we don't need stat updates for this test
        test_utils.set_index_active(False)
        
        client = Client()
        for _res in resourceInfoType_model.objects.all():
            response = client.get(_res.get_absolute_url(), follow = True)
            self.assertEquals(200, response.status_code)
            self.assertTemplateUsed(response, 'repository/lr_view.html')
            self.assertContains(response, xml_utils.html_escape(_res.real_unicode_()))

        # enable indexing 
        test_utils.set_index_active(True)