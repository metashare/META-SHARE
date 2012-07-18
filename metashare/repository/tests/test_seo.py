from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from metashare import test_utils, settings
from metashare.accounts.models import UserProfile
from metashare.repository import views
from metashare.settings import DJANGO_BASE, ROOT_PATH, DJANGO_URL


def _import_resource(fixture_name):
    """
    Imports the XML resource description with the given file name.
    
    The new resource is published and returned.
    """
    result = test_utils.import_xml('{0}/repository/fixtures/{1}'
                                    .format(ROOT_PATH, fixture_name))[0]
    result.storage_object.published = True
    result.storage_object.save()
    return result

class SitemapTest(TestCase):
    """
    Check the sitemap's format
    """
    
    @classmethod
    def set_up_class(cls):
        test_utils.set_index_active(False)
    
    @classmethod
    def tear_down_class(cls):
        test_utils.set_index_active(True)
        
    def set_up(self):
        """
        Set up the detail view
        """
        test_utils.setup_test_storage()
        self.resource = _import_resource('testfixture.xml')

    def tear_down(self):
        """
        Clean up the test
        """
        test_utils.clean_db()
        test_utils.clean_storage()
        User.objects.all().delete()

        
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
        response = client.get('/{0}sitemap.xml'.format(DJANGO_BASE),
          follow=True)
        self.assertContains(response, 
          '{}/repository/browse/italian-tts-speech-corpus-appen/' \
          .format(DJANGO_URL), status_code=200)
        self.assertContains(response, 
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', \
          status_code=200)

    def test_robots_txt(self):
        """
        Tests the correct appearance of the robots.txt file
        """
        if DJANGO_BASE == '':
            
        else:
			pass
        
        
        
    def test_title():
        """
        Tests whether the title of the resource is the resource name
        """
        
        
