import logging
from django.test import TestCase
from django.test.client import Client
from metashare import test_utils
from metashare.settings import ROOT_PATH, LOG_HANDLER

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

class EmailProtectionTest(TestCase):
    """
    Test the picture display instead of the email in plain text
    """
    
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
        Set up the email test
        """
        test_utils.setup_test_storage()
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        self.resource = test_utils.import_xml(_fixture)
        self.resource.storage_object.published = True
        self.resource.storage_object.save()
    
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()

    def testEmailProtection(self):
        """
        Checks whether the computation of secure email addresses works.
        """
        client = Client()
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)

        # Verify that the response contains an email field.
        # The response doesn't contain an Email field any more
        #self.assertContains(response, ">Email: <",
        #    msg_prefix="There must be an 'email' field to test.")
        # Verify that the response does NOT contain any email addresses.
        for person in self.resource.contactPerson.all():
            self.assertNotContains(response, person.communicationInfo.email)
