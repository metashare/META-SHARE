import os
from django.test import TestCase
from metashare import test_utils
from metashare.settings import ROOT_PATH
from metashare.repository.models import resourceInfoType_model

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
    
    if False:
        def testImportELRA(self):      
            """
            run tests on ELRA resources
            """
            _path = '{0}/../misc/testdata/ELRAResources/'.format(ROOT_PATH)
            
            _files = os.listdir(_path)
            for _file in _files:
                _currfile =  "%s%s" % (_path, _file)
                successes, failures = test_utils.import_xml_or_zip(_currfile)
                self.assertEqual(1, len(successes), 'Could not import file {}'.format(_currfile))
                self.assertEqual(0, len(failures), 'Could not import file {}'.format(_currfile))
            
    def test_import_xml(self):
        _currfile = '{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        successes, failures = test_utils.import_xml_or_zip(_currfile)
        self.assertEqual(1, len(successes), 'Could not import file {} -- successes is {}, failures is {}'.format(_currfile, successes, failures))
        self.assertEqual(0, len(failures), 'Could not import file {} -- successes is {}, failures is {}'.format(_currfile, successes, failures))

    def test_broken_xml(self):
        _currfile = '{}/repository/fixtures/broken.xml'.format(ROOT_PATH)
        successes, failures = test_utils.import_xml_or_zip(_currfile)
        self.assertEqual(0, len(successes), 'Should not have been able to import file {}'.format(_currfile))
        self.assertEqual(1, len(failures), 'Should not have been able to import file {}'.format(_currfile))
        
    def test_import_zip(self):
        _currfile = '{}/repository/fixtures/tworesources.zip'.format(ROOT_PATH)
        successes, failures = test_utils.import_xml_or_zip(_currfile)
        self.assertEqual(2, len(successes), 'Could not import file {}'.format(_currfile))
        self.assertEqual(0, len(failures), 'Could not import file {}'.format(_currfile))

    def test_import_broken_zip(self):
        _currfile = '{}/repository/fixtures/onegood_onebroken.zip'.format(ROOT_PATH)
        successes, failures = test_utils.import_xml_or_zip(_currfile)
        self.assertEqual(1, len(successes), 'Could not import file {} -- successes is {}, failures is {}'.format(_currfile, successes, failures))
        self.assertEqual(1, len(failures), 'Could not import file {} -- successes is {}, failures is {}'.format(_currfile, successes, failures))
        self.assertEquals('broken.xml', failures[0][0])
    
