from django.test import TestCase
from django.test.client import Client

from metashare import test_utils
from metashare.settings import DJANGO_BASE, ROOT_PATH, DJANGO_URL, SITEMAP_URL


class SEOTest(TestCase):
    """
    Check the sitemap's and robots.txt's format
    """

    def test_sitemap(self):
        """
        Tests the correct appearance of the sitemap
        """
       
        imported_res = test_utils.import_xml('{}/repository/fixtures/'
          'testfixture.xml'.format(ROOT_PATH))[0]
        imported_res.storage_object.published = True
        imported_res.storage_object.save()
        client = Client()
        
        # assert that a two-token search finds a camelCase term:
        response = client.get(SITEMAP_URL)
        self.assertContains(response, 
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', \
          status_code=200)
        self.assertContains(response, 
          '{}/repository/browse/italian-tts-speech-corpus-appen/' \
          .format(DJANGO_URL), status_code=200)


    def test_robots_txt(self):
        """
        Tests the correct appearance of the robots.txt file
        """
        client = Client()
        if DJANGO_BASE == '':
            response = client.get('/{0}robots.txt'.format(DJANGO_BASE))
            self.assertContains(response, 
              'Disallow: /admin/', status_code=200)
            self.assertContains(response,
              'Sitemap: {}'.format(SITEMAP_URL), status_code=200)
        else:
            pass
