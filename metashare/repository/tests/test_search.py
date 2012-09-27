import os
import logging

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.testcases import TestCase

from haystack.query import SearchQuerySet

from metashare import test_utils, settings
from metashare.repository import views
from metashare.settings import DJANGO_BASE, ROOT_PATH, LOG_HANDLER
from metashare.stats.models import LRStats
from metashare.storage.models import INGESTED, PUBLISHED
from metashare.test_utils import create_user

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

_SEARCH_PAGE_PATH = '/{0}repository/search/'.format(DJANGO_BASE)


class SearchIndexUpdateTests(test_utils.IndexAwareTestCase):
    """
    A test case for testing various aspects of the automatic reindexing on
    database changes.
    """
    # paths to XML files containing test resources
    RES_PATH_1 = "{0}/repository/fixtures/roundtrip.xml".format(ROOT_PATH)
    RES_PATH_2 = "{0}/repository/fixtures/testfixture.xml".format(ROOT_PATH)
    
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))
    
    def test_index_updates_on_import(self):
        """
        Verifies that the index is correctly updated when importing a resource.
        """
        self.assert_index_is_empty()
        # import a single resource and save it in the DB
        resource = test_utils.import_xml(SearchIndexUpdateTests.RES_PATH_1)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        # make sure the import has automatically changed the search index
        self.assertEqual(SearchQuerySet().count(), 1,
            "After the import of a resource the index must automatically " \
            "have changed and contain that resource.")
        # import another resource and save it in the DB
        resource = test_utils.import_xml(SearchIndexUpdateTests.RES_PATH_2)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        # make sure the import has automatically changed the search index
        self.assertEqual(SearchQuerySet().count(), 2,
            "After the import of a resource the index must automatically " \
            "have changed and contain that resource.")

    def test_index_updates_on_changes(self):
        """
        Verifies that the index is correctly updated when changing a resource.
        """
        resource = self.init_index_with_a_resource()
        added_name = "NEW DUMMY NAME"
        # make sure the name to add can't be found, yet
        self.assertEqual(
            SearchQuerySet().auto_query('"{0}"'.format(added_name)).count(), 0,
            "'{0}' was not expected to be found in the search index, yet. " \
            "There appears to be a bug in {1}."
            .format(added_name, SearchIndexUpdateTests.__class__.__name__))
        # change the names list of the imported resource
        resource.identificationInfo.resourceName['en-US'] = added_name
        resource.identificationInfo.save()
        resource.save()
        # make sure the change has automatically updated the search index
        self.assertEqual(
            SearchQuerySet().auto_query('"{0}"'.format(added_name)).count(), 1,
            "After adding a new name to a resource, the resource should be " \
            "searchable by this name.")

    def test_index_updates_on_deletion(self):
        """
        Verifies that the index is correctly updated when deleting a resource.
        """
        resource = self.init_index_with_a_resource()
        # now flag the resource as deleted
        resource.storage_object.deleted = True
        resource.storage_object.save()
        # make sure the deletion has automatically changed the search index
        self.assertEqual(SearchQuerySet().count(), 0,
            "After a resource is flagged to be deleted in the storage object," \
            " the index must automatically change.")
        # remove the deletion flag from the resource
        resource.storage_object.deleted = False
        resource.storage_object.save()
        # make sure the undeletion has automatically changed the search index
        self.assertEqual(SearchQuerySet().count(), 1,
            "After a resource is flagged to not be deleted in the storage " \
            "object, the index must automatically change.")
        # delete the resource itself
        resource.delete()
        # make sure the deletion has automatically changed the search index
        self.assertEqual(SearchQuerySet().count(), 0,
            "After a resource is deleted, the index must automatically change.")

    def assert_index_is_empty(self):
        """
        Asserts that the search index is empty.
        """
        self.assertEqual(SearchQuerySet().all().count(), 0,
          "The search index is expected to be empty at the start of the " \
          "test. There appears to be a bug in {0}." \
          .format(test_utils.IndexAwareTestCase.__class__.__name__))
    
    def init_index_with_a_resource(self):
        """
        Initializes an empty search index with a single resource.
        
        The imported resource is returned. Asserts that the index really only
        contains a single resource.
        """
        self.assert_index_is_empty()
        # import a single resource and save it in the DB
        resource = test_utils.import_xml(SearchIndexUpdateTests.RES_PATH_1)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        # make sure the import has automatically changed the search index
        self.assertEqual(SearchQuerySet().count(), 1,
          "After the import of a resource the index must automatically " \
          "have changed and contain that resource.")
        return resource
    
class SearchTest(test_utils.IndexAwareTestCase):
    """
    Test the search functionality
    """
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))
        
    def setUp(self):
        """
        Set up the view
        """
        test_utils.setup_test_storage()                        
        normaluser =  create_user('normaluser', 'normal@example.com', 'secret')
        normaluser.save()

    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

    def importOneFixture(self):
        _currfile = '{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        test_utils.import_xml_or_zip(_currfile)

    def test_view_count_visible_and_updated_in_search_results(self):
        """
        Verifies that the view count of a resource is visible and updated in
        the search results list.
        """
        test_res = test_utils.import_xml('{}/repository/test_fixtures/'
                        'internal-corpus-Text-EngPers.xml'.format(ROOT_PATH))
        test_res.storage_object.published = True
        test_res.storage_object.save()
        client = Client()
        # to be on the safe side, clear any existing stats
        LRStats.objects.all().delete()
        # assert that the download/view counts are both zero at first:
        response = client.get(_SEARCH_PAGE_PATH)
        self.assertContains(response, 'title="Number of downloads" />&nbsp;0')
        self.assertContains(response, 'title="Number of views" />&nbsp;0')
        # view the resource, then go back to the browse page and assert that the
        # view count has changed:
        client.get(test_res.get_absolute_url())
        response = client.get(_SEARCH_PAGE_PATH)
        self.assertContains(response, 'title="Number of downloads" />&nbsp;0')
        self.assertContains(response, 'title="Number of views" />&nbsp;1')
        # log in, view the resource again, go back to the browse page and then
        # assert that the view count has changed again:
        client.login(username='normaluser', password='secret')
        client.get(test_res.get_absolute_url())
        response = client.get(_SEARCH_PAGE_PATH)
        self.assertContains(response, 'title="Number of downloads" />&nbsp;0')
        self.assertContains(response, 'title="Number of views" />&nbsp;2')

    def test_download_count_visible_and_updated_in_search_results(self):
        """
        Verifies that the download count of a resource is visible and updated in
        the search results list.
        """
        test_res = test_utils.import_xml('{}/repository/fixtures/'
                'downloadable_1_license.xml'.format(ROOT_PATH))
        test_res.storage_object.published = True
        test_res.storage_object.save()
        client = Client()
        client.login(username='normaluser', password='secret')
        # to be on the safe side, clear any existing stats
        LRStats.objects.all().delete()
        # assert that the download/view counts are both zero at first:
        response = client.get(_SEARCH_PAGE_PATH)
        self.assertContains(response, 'title="Number of downloads" />&nbsp;0')
        self.assertContains(response, 'title="Number of views" />&nbsp;0')
        # view the resource, download it, go back to the browse page and then
        # assert that both view and download counts have changed:
        client.get(test_res.get_absolute_url())
        client.post(
            reverse(views.download, args=(test_res.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'CC-BY-NC-SA' })
        response = client.get(_SEARCH_PAGE_PATH)
        self.assertContains(response, 'title="Number of downloads" />&nbsp;1')
        self.assertContains(response, 'title="Number of views" />&nbsp;1')

    def test_case_insensitive_search(self):
        """
        Asserts that case-insensitive searching is done.
        """
        imported_res = test_utils.import_xml('{}/repository/test_fixtures/'
                        'internal-corpus-Text-EngPers.xml'.format(ROOT_PATH))
        imported_res.storage_object.published = True
        imported_res.storage_object.save()
        client = Client()
        # assert that a lower case search for an upper case term succeeds:
        response = client.get(_SEARCH_PAGE_PATH,
                              follow=True, data={'q': 'fixture'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that an upper case search for a lower case term succeeds:
        response = client.get(_SEARCH_PAGE_PATH,
                              follow=True, data={'q': 'ORIGINALLY'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that a lower case search for a mixed case term succeeds:
        response = client.get(_SEARCH_PAGE_PATH,
                              follow=True, data={'q': 'unicode'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that a mixed case search for an upper case term succeeds:
        response = client.get(_SEARCH_PAGE_PATH,
                              follow=True, data={'q': 'FiXTuRe'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that a camelCase search for an upper case term succeeds:
        response = client.get(_SEARCH_PAGE_PATH,
                              follow=True, data={'q': 'fixTure'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that an all lower case search finds a camelCase term:
        response = client.get(_SEARCH_PAGE_PATH,
                              follow=True, data={'q': 'camelcasetest'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)

    def test_camel_case_aware_search(self):
        """
        Asserts that the search engine is camelCase-aware.
        """
        imported_res = test_utils.import_xml('{}/repository/test_fixtures/'
                        'internal-corpus-Text-EngPers.xml'.format(ROOT_PATH))
        imported_res.storage_object.published = True
        imported_res.storage_object.save()
        client = Client()
        # assert that a three-token search finds a camelCase term:
        response = client.get(_SEARCH_PAGE_PATH,
                              follow=True, data={'q': 'camel case test'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that a camelCase search term also finds the camelCase term:
        response = client.get(_SEARCH_PAGE_PATH,
                              follow=True, data={'q': 'camelCaseTest'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)

    def testBrowse(self):  
        """
       # Tries to load the Browse page
        """
        client = Client()
        response = client.get('/{0}repository/browse/'.format(DJANGO_BASE))
        self.assertEqual(response.status_code, 404)

    def testSearch(self):        
        client = Client()
        self.importOneFixture()
        response = client.get(_SEARCH_PAGE_PATH, follow=True,
          data={'q':'Italian'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)

    def testSearchForNoResults(self):        
        client = Client()
        self.importOneFixture()
        response = client.get(_SEARCH_PAGE_PATH, follow=True,
          data={'q':'querywhichwillgivenoresults'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "No results were found for search query", status_code=200)

    def test_ingested_LRs_are_not_indexed(self):
        test_res = test_utils.import_xml('{}/repository/test_fixtures/ingested/'
            'ingested-corpus-AudioVideo-French.xml'.format(ROOT_PATH))
        test_res.storage_object.publication_status = INGESTED
        test_res.storage_object.save()
        response = Client().get(_SEARCH_PAGE_PATH, data={'q': 'INGESTED'})
        self.assertTemplateUsed(response, 'repository/search.html')
        self.assertContains(response, "No results were found for search query")


class SearchTestPublishedResources(TestCase):
    """
    Test the search functionality, importing a set of published resources to be used in all tests.
    """
    @classmethod
    def importPublishedFixtures(cls):
        _path = '{}/repository/test_fixtures/pub/'.format(ROOT_PATH)
        files = os.listdir(_path)   
        for filename in files:
            fullpath = os.path.join(_path, filename)  
            test_utils.import_xml_or_zip(fullpath)

    @classmethod
    def setUpClass(cls):
        """
        Set up the view
        """
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.setup_test_storage()                        
        # Make sure the index does not contain any stale entries:
        call_command('rebuild_index', interactive=False, using=settings.TEST_MODE_NAME)
        cls.importPublishedFixtures()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def testLanguageFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH,
            data={'selected_facets':'languageNameFilter_exact:Chinese'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
             
    def testLanguageFacetForNoResults(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH,
            data={'selected_facets':'languageNameFilter_exact:Italian'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "No results were found for search query", status_code=200)
        
    def testResourceTypeFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH,
            data={'selected_facets':'resourceTypeFilter_exact:corpus'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testMediaTypeFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH,
            data={'selected_facets':'mediaTypeFilter_exact:audio'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
     
    def testAvailabilityFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':
                'availabilityFilter_exact:Available - Unrestricted Use'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
              
    def testLicenceFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH,
            data={'selected_facets':'licenceFilter_exact:ELRA_END_USER'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
    
    
    #def testLicenceFacetForTwoLicences(self):   
    #   client = Client()
    #   response = client.get(_SEARCH_PAGE_PATH, follow=True, 
    #     data={'selected_facets':'licenceFilter_exact:ELRA_END_USER', 'selected_facets':'licenceFilter_exact:ELRA_VAR'})
    #   self.assertEqual('repository/search.html', response.templates[0].name)
    #   self.assertContains(response, "1 Language Resource", status_code=200)
    
    
    def testRestrictionsOfUseFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':
                'restrictionsOfUseFilter_exact:Academic - Non Commercial Use'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
      
    def testValidatedFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':'validatedFilter_exact:true'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
        
    def testForeseenUseFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':'foreseenUseFilter_exact:Nlp Applications'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
     
    def testUseNlpSpecificFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':
                'useNlpSpecificFilter_exact:Speech Recognition'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
      
    def testLingualityTypeFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':'lingualityTypeFilter_exact:Monolingual'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
        
    def testMultilingualityTypeFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':'multilingualityTypeFilter_exact:Comparable'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testModalityTypeFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':'modalityTypeFilter_exact:Other'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testMimeTypeFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':'mimeTypeFilter_exact:audio mime type'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
    
    def testDomainFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':'domainFilter_exact:science'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
      
    def testGeographicCoverageFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'selected_facets':'geographicCoverageFilter_exact:European Union'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)          
         
    def testCombinedSearchAndFacet(self):   
        client = Client()
        response = client.get(_SEARCH_PAGE_PATH, follow=True, 
          data={'q':'recordingFree', 'selected_facets':'languageNameFilter_exact:Chinese'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)  
