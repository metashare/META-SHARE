import logging
from metashare.repository.forms import _extract_special_queries, \
    _process_special_query, MORE_FROM_SAME_CREATORS, MORE_FROM_SAME_PROJECTS
from metashare import test_utils
from metashare.recommendations.tests import _import_resource
import django.test
from django.test.client import Client
from metashare.settings import DJANGO_BASE, LOG_HANDLER

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

class SpecialQueryTest(django.test.TestCase):

    # test resources to be initialized in setup
    res_1 = None
    res_2 = None
    res_3 = None
    res_4 = None
    
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))
    
    def setUp(self):
        """
        Import test fixtures and add resource pairs to TogetherManager
        """
        test_utils.setup_test_storage()
        self.res_1 = _import_resource('creators-projects-1.xml')
        self.res_2 = _import_resource('creators-projects-2.xml')
        self.res_3 = _import_resource('creators-projects-3.xml')
        self.res_4 = _import_resource('creators-projects-4.xml')
    
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()

    
    def test_extraction(self):       
        query = "a b c {}:1234 d e f {}:4567".format(
          MORE_FROM_SAME_CREATORS, MORE_FROM_SAME_PROJECTS)
        special_queries, res_query = _extract_special_queries(query)
        self.assertEquals("a b c d e f", res_query)
        self.assertEquals(2, len(special_queries))


    def test_query_handling(self):
        query = "{}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_1.storage_object.identifier)
        self.assertEquals(2, len(_process_special_query(query)))
        query = "{}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_2.storage_object.identifier)
        self.assertEquals(1, len(_process_special_query(query)))
        query = "{}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_3.storage_object.identifier)
        self.assertEquals(1, len(_process_special_query(query)))
        query = "{}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_4.storage_object.identifier)
        self.assertEquals(0, len(_process_special_query(query)))
        
        query = "{}:{}".format(
          MORE_FROM_SAME_PROJECTS, self.res_1.storage_object.identifier)
        self.assertEquals(0, len(_process_special_query(query)))
        query = "{}:{}".format(
          MORE_FROM_SAME_PROJECTS, self.res_2.storage_object.identifier)
        self.assertEquals(1, len(_process_special_query(query)))
        query = "{}:{}".format(
          MORE_FROM_SAME_PROJECTS, self.res_3.storage_object.identifier)
        self.assertEquals(1, len(_process_special_query(query)))
        query = "{}:{}".format(
          MORE_FROM_SAME_PROJECTS, self.res_4.storage_object.identifier)
        self.assertEquals(2, len(_process_special_query(query)))
        
        
    def test_simple_search(self):
        """
        Tests usage of single special queries.
        """
        client = Client()
        
        query = "{}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_1.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
        
        query = "{}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_2.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
        query = "{}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_3.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
        query = "{}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_4.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "0 Language Resources", status_code=200)
        
        query = "{}:{}".format(
          MORE_FROM_SAME_PROJECTS, self.res_1.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "0 Language Resources", status_code=200)
        
        query = "{}:{}".format(
          MORE_FROM_SAME_PROJECTS, self.res_2.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
        query = "{}:{}".format(
          MORE_FROM_SAME_PROJECTS, self.res_3.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
        query = "{}:{}".format(
          MORE_FROM_SAME_PROJECTS, self.res_4.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
        
        
    def test_mixed_search(self):
        """
        Tests usage of single special queries together with other query terms.
        """
        client = Client()
        
        query = "{}:{} CINTIL".format(
          MORE_FROM_SAME_CREATORS, self.res_1.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
        query = "{}:{} foobar".format(
          MORE_FROM_SAME_CREATORS, self.res_1.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "0 Language Resources", status_code=200)


    def test_multiple_search(self):
        """
        Tests usage of multiple special queries.
        """
        client = Client()
        
        query = "{}:{} {}:{}".format(
          MORE_FROM_SAME_CREATORS, self.res_1.storage_object.identifier,
          MORE_FROM_SAME_PROJECTS, self.res_4.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
        
        
    def test_complex_search(self):
        """
        Tests usage of multiple special queries with other query term
        """
        client = Client()
        
        query = "{}:{} {}:{} CINTIL".format(
          MORE_FROM_SAME_CREATORS, self.res_1.storage_object.identifier,
          MORE_FROM_SAME_PROJECTS, self.res_4.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
        query = "{}:{} {}:{} foobar".format(
          MORE_FROM_SAME_CREATORS, self.res_1.storage_object.identifier,
          MORE_FROM_SAME_PROJECTS, self.res_4.storage_object.identifier)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': '{}'.format(query)})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "0 Language Resources", status_code=200)
