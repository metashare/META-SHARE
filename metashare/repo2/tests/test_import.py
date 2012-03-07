import os
from django.test import TestCase
from metashare import test_utils
from metashare.settings import ROOT_PATH
from metashare.repo2.models import resourceInfoType_model

class ImportTest(TestCase):
    """
    Tests the import procedure for resources
    """
    def setUp(self):
        """
        Set up the import test
        """        
        test_utils.setup_test_storage()
        
    def tearDown(self):
        """
        Clean up the test
        """
        resourceInfoType_model.objects.all().delete()
    
    def testImportELRA(self):      
        """
        run tests on ELRA resources
        """
        _path = '{0}/../misc/testdata/ELRAResources/'.format(ROOT_PATH)
        
        _files = os.listdir(_path)
        for _file in _files:
            _currfile =  "%s%s" % (_path, _file)
            _result = test_utils.import_xml(_currfile)            
            self.assertNotEqual(_result[:2], (None, []))
            
        
        
        