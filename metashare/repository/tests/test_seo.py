import logging

from django.test import TestCase
from django.test.client import Client

from metashare import test_utils
from metashare.settings import DJANGO_BASE, ROOT_PATH, DJANGO_URL, SITEMAP_URL, \
    LOG_HANDLER

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

class SEOTest(TestCase):
    """
    Check the sitemap's and robots.txt's format
    """

    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def test_sitemap(self):
        """
        Tests the correct appearance of the sitemap
        """
       
        imported_res = test_utils.import_xml('{}/repository/fixtures/'
          'testfixture.xml'.format(ROOT_PATH))
        imported_res.storage_object.published = True
        imported_res.storage_object.save()
        client = Client()
        
        # Assert that the sitemap page contains the xmlsn and the entry
        # of the imported resource.
        response = client.get(SITEMAP_URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        self.assertContains(response, 
          '{}/repository/browse/italian-tts-speech-corpus-appen/' \
          .format(DJANGO_URL))

    def test_robots_txt(self):
        """
        Tests the correct appearance of the robots.txt file
        """
        client = Client()
        if DJANGO_BASE == '':
            response = client.get('/{0}robots.txt'.format(DJANGO_BASE))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Disallow: /admin/')
            self.assertContains(response,
              'Sitemap: {}'.format(SITEMAP_URL))
        else:
            pass
