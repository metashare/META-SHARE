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

    def test_import_ELRA(self):      
        """
        Run tests on ELRA resources
        Representative xml files have been taken
        """
        self._test_import_dir('{0}/repository/test_fixtures/ELRA/'
                              .format(ROOT_PATH))

    def test_import_PSP(self):
        """
        Run tests on PSP resources
        Representative xml files from all PSP providers have been taken
        """
        self._test_import_dir('{0}/repository/test_fixtures/PSP/'
                              .format(ROOT_PATH))

    def test_import_METASHARE(self):
        """
        Run tests on META-SHARE resources
        Representative xml files from all META-SHARE partners have been taken
        """
        self._test_import_dir('{0}/repository/test_fixtures/META-SHARE/'
                              .format(ROOT_PATH))

    def _test_import_dir(self, path):
        """Asserts that all XML files in the given directory can be imported."""
        _files = os.listdir(path)
        for _file in _files:
            self._test_import_xml_file("%s%s" % (path, _file))

    def test_import_xml(self):
        """Asserts that a single XML file can be imported."""
        self._test_import_xml_file('{}/repository/fixtures/testfixture.xml'
                                   .format(ROOT_PATH))

    def _test_import_xml_file(self, xml_path):
        """Asserts that the given XML file can be imported."""
        successes, failures = test_utils.import_xml_or_zip(xml_path)
        self.assertEqual(1, len(successes),
            'Could not import file {} -- successes is {}, failures is {}'
                .format(xml_path, successes, failures))
        self.assertEqual(0, len(failures),
            'Could not import file {} -- successes is {}, failures is {}'
                .format(xml_path, successes, failures))

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
    
