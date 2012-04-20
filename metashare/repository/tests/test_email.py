from django.test import TestCase
from metashare import test_utils
from metashare.settings import ROOT_PATH
from metashare.repository.models import resourceInfoType_model

class EmailPictureTest(TestCase):
    """
    Test the picture display instead of the email in plain text
    """
    def setUp(self):
        """
        Set up the email test
        """
        test_utils.setup_test_storage()
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        self.resource_id = _result[0].id
    
    def tearDown(self):
        """
        Clean up the test
        """
        resourceInfoType_model.objects.all().delete()

# pylint: disable-msg=W0105
'''
    def testEmailProtection(self):
        """
        Checks whether the computation of secure email addresses works.
        """
        client = Client()
        url = '/{0}repository/{1}/'.format(DJANGO_BASE, self.resource_id)
        response = client.get(url, follow = True)
        
        # Verify that the response does NOT contain any email addresses.
        self.assertNotContains(response, '@')

    def testEmailImageOrReplace(self):
        """
        Checks whether there is an image replacing an email address.
        """
        try:
            # pylint: disable-msg=W0612
            import Image, ImageDraw, ImageFont
            _pil_available = True
    
        except ImportError:
            _pil_available = False
    
        client = Client()
        url = '/{0}repository/{1}/'.format(DJANGO_BASE, self.resource_id)
        response = client.get(url, follow = True)

        # Verify that the response does NOT contain any email addresses.
        if _pil_available:
            self.assertRegexpMatches(response.content, r'.*\_.*\_.*\.jpg')
        else:
            self.assertContains(response, ' [at] ')
            self.assertContains(response, ' [dot] ')
'''
