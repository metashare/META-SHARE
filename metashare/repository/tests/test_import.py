import os
import logging

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from metashare import test_utils
from metashare.accounts.models import EditorGroup
from metashare.repository.models import documentUnstructuredString_model, \
    documentInfoType_model
from metashare.settings import DJANGO_BASE, ROOT_PATH, LOG_HANDLER

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

class ImportTest(TestCase):
    """
    Tests the import procedure for resources
    """

    test_editor_group = None
    super_user = None
    
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
        Set up the import test
        """        
        test_utils.setup_test_storage()
        
        ImportTest.test_editor_group = EditorGroup.objects.create(
                                                    name='test_editor_group')

        ImportTest.super_user = User.objects.create_superuser('superuser', 'su@example.com', 'secret')
   
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

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

    def test_import_bug_1(self):
        """
        This constellation caused an import error with a Postgres DB backend.
        """
        self._test_import_dir(
          '{}/repository/test_fixtures/import-bug-1/'.format(ROOT_PATH))
        
    def test_import_bug_2(self):
        """
        This constellation caused an import error with a Postgres DB backend.
        """
        self._test_import_dir(
          '{}/repository/test_fixtures/import-bug-2/'.format(ROOT_PATH))

    def test_res_doc_info(self):
        """
        Check if resourceDocumentationInfo is imported correctly.
        """
        self._test_import_dir(
          '{}/repository/test_fixtures/resourceDocumentationInfo/'.format(ROOT_PATH))
        # check that there are 3 documentUnstructured 
        # and 1 documentInfo in the database
        self.assertEqual(len(documentUnstructuredString_model.objects.all()), 2)
        self.assertEqual(len(documentInfoType_model.objects.all()), 1)

    def test_imported_resource_get_user_default_editor_group(self):
        """
        Check if resource editor group is set to the default editor group of the user.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        ImportTest.super_user.get_profile().default_editor_groups \
            .add(ImportTest.test_editor_group)

        resourcefile = open('{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH))
        response = client.post('/{0}editor/upload_xml/'.format(DJANGO_BASE), \
          {'resource': resourcefile}, follow=True)
        self.assertNotContains(response, '<td>{}</td>'.format(ImportTest.test_editor_group.name),
          msg_prefix='expected the system to set an editor group to the resource.')

    def test_imported_resource_get_none_if_no_default_editor_group(self):
        """
        Check if resource editor group is set to None if the user do not have a default editor group.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        resourcefile = open('{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH))
        response = client.post('/{0}editor/upload_xml/'.format(DJANGO_BASE), \
          {'resource': resourcefile}, follow=True)
        self.assertNotContains(response, '<td>{}</td>'.format(ImportTest.test_editor_group.name),
          msg_prefix='expected the system to set None as editor group to the resource.')
