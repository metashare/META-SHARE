from metashare import test_utils
from metashare.settings import DJANGO_BASE, ROOT_PATH
from metashare.repository.models import resourceInfoType_model
from haystack.query import SearchQuerySet
from django.contrib.auth.models import User
from django.test.client import Client
import os


class SearchIndexUpdateTests(test_utils.IndexAwareTestCase):
    """
    A test case for testing various aspects of the automatic reindexing on
    database changes.
    """
    # paths to XML files containing test resources
    RES_PATH_1 = "{0}/repository/fixtures/roundtrip.xml".format(ROOT_PATH)
    RES_PATH_2 = "{0}/repository/fixtures/testfixture.xml".format(ROOT_PATH)
    
    def test_index_updates_on_import(self):
        """
        Verifies that the index is correctly updated when importing a resource.
        """
        self.assert_index_is_empty()
        # import a single resource and save it in the DB
        resource = test_utils.import_xml(SearchIndexUpdateTests.RES_PATH_1)[0]
        resource.storage_object.save()
        # make sure the import has automatically changed the search index
        self.assertEqual(SearchQuerySet().count(), 1,
            "After the import of a resource the index must automatically " \
            "have changed and contain that resource.")
        # import another resource and save it in the DB
        resource = test_utils.import_xml(SearchIndexUpdateTests.RES_PATH_2)[0]
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
        resource.identificationInfo.resourceName.append(added_name)
        resource.identificationInfo.save()
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
        resource = test_utils.import_xml(SearchIndexUpdateTests.RES_PATH_1)[0]
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
    def setUp(self):
        """
        Set up the view
        """
        test_utils.setup_test_storage()                        
     
        staffuser = User.objects.create_user('staffuser', 'staff@example.com',
          'secret')
        staffuser.is_staff = True
        staffuser.save()
        normaluser =  User.objects.create_user('normaluser', 'normal@example.com', 'secret')
        normaluser.save()

    def tearDown(self):
        """
        Clean up the test
        """
        resourceInfoType_model.objects.all().delete()                 
                
    def importOneFixture(self):
        _currfile = '{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        test_utils.import_xml_or_zip(_currfile)
        
    def importPublishedFixtures(self):
        _path = '{}/repository/test_fixtures/pub/'.format(ROOT_PATH)
        files = os.listdir(_path)   
        for filename in files:
            fullpath = os.path.join(_path, filename)  
            test_utils.import_xml_or_zip(fullpath)
         
    def importIngestedFixtures(self):
        _path = '{}/repository/test_fixtures/ingested/'.format(ROOT_PATH)
        files = os.listdir(_path)   
        for filename in files:
            fullpath = os.path.join(_path, filename)  
            successes, failures = test_utils.import_xml_or_zip(fullpath)
            if successes:                
                successes[0].storage_object.publication_status = 'g'
                successes[0].storage_object.save()    
            if failures:
                print failures    
    #def importInternalFixtures(self):
    #   _path = '{}/repository/test_fixtures/internal/'.format(ROOT_PATH)
    #   files = os.listdir(_path)   
    #   for filename in files:
    #       fullpath = os.path.join(_path, filename)  
    #       test_utils.import_xml_or_zip(fullpath)
    #       if successes:                
    #           successes[0].storage_object.publication_status = 'i'
    #           successes[0].storage_object.save()   

    def test_case_insensitive_search(self):
        """
        Asserts that case-insensitive searching is done.
        """
        imported_res = test_utils.import_xml('{}/repository/test_fixtures/'
                        'internal-corpus-Text-EngPers.xml'.format(ROOT_PATH))[0]
        imported_res.storage_object.published = True
        imported_res.storage_object.save()
        client = Client()
        # assert that a lower case search for an upper case term succeeds:
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
                              follow=True, data={'q': 'fixture'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that an upper case search for a lower case term succeeds:
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
                              follow=True, data={'q': 'ORIGINALLY'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that a lower case search for a mixed case term succeeds:
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
                              follow=True, data={'q': 'unicode'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that a mixed case search for an upper case term succeeds:
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
                              follow=True, data={'q': 'FiXTuRe'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that a camelCase search for an upper case term succeeds:
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
                              follow=True, data={'q': 'fixTure'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that an all lower case search finds a camelCase term:
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
                              follow=True, data={'q': 'speechsynthesis'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)

    def test_camel_case_aware_search(self):
        """
        Asserts that the search engine is camelCase-aware.
        """
        imported_res = test_utils.import_xml('{}/repository/test_fixtures/'
                        'internal-corpus-Text-EngPers.xml'.format(ROOT_PATH))[0]
        imported_res.storage_object.published = True
        imported_res.storage_object.save()
        client = Client()
        # assert that a two-token search finds a camelCase term:
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
                              follow=True, data={'q': 'speech synthesis'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        # assert that a camelCase search term also finds the camelCase term:
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
                              follow=True, data={'q': 'speechSynthesis'})
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
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True,
          data={'q':'Italian'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
    
     
    def testSearchForNoResults(self):        
        client = Client()
        self.importOneFixture()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True,
          data={'q':'querywhichwillgivenoresults'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "No results were found for search query", status_code=200)
          
    def testLanguageFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'languageNameFilter_exact:Chinese'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        print response
        self.assertContains(response, "2 Language Resources", status_code=200)
             
    def testLanguageFacetForNoResults(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'languageNameFilter_exact:Italian'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "No results were found for search query", status_code=200)
        
    def testResourceTypeFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'resourceTypeFilter_exact:corpus'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testMediaTypeFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'mediaTypeFilter_exact:audio'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
     
    def testAvailabilityFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'availabilityFilter_exact:available-unrestrictedUse'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
              
    def testLicenceFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'licenceFilter_exact:ELRA_END_USER'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
    
    
    #def testLicenceFacetForTwoLicences(self):   
    #   client = Client()
    #   self.importPublishedFixtures()
    #   response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
    #     data={'selected_facets':'licenceFilter_exact:ELRA_END_USER', 'selected_facets':'licenceFilter_exact:ELRA_VAR'})
    #   self.assertEqual('repository/search.html', response.templates[0].name)
    #   print response
    #   self.assertContains(response, "1 Language Resource", status_code=200)
    
    
    def testRestrictionsOfUseFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'restrictionsOfUseFilter_exact:academic-nonCommercialUse'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
      
    def testValidatedFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'validatedFilter_exact:true'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
        
    def testForeseenUseFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'foreseenUseFilter_exact:nlpApplications'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
     
    def testUseNlpSpecificFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'useNlpSpecificFilter_exact:speechRecognition'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
      
    def testLingualityTypeFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'lingualityTypeFilter_exact:monolingual'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
        
    def testMultilingualityTypeFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'multilingualityTypeFilter_exact:comparable'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testModalityTypeFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'modalityTypeFilter_exact:other'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testMimeTypeFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'mimeTypeFilter_exact:audio mime type'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
    
    def testDomainFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'domainFilter_exact:science'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "2 Language Resources", status_code=200)
      
    def testGeographicCoverageFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'geographicCoverageFilter_exact:European Union'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)          
         
    def testCombinedSearchAndFacet(self):   
        client = Client()
        self.importPublishedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'q':'recordingFree', 'selected_facets':'languageNameFilter_exact:Chinese'})
        # print response
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)  

    def test_staff_user_sees_ingested_LR(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        self.importIngestedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'q':'INGESTED'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def test_normal_user_doesnt_see_ingested_LR(self):
        client = Client()
        client.login(username='normaluser', password='secret')
        self.importIngestedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'q':'INGESTED'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "No results were found for search query", status_code=200)
           
    def test_anonymous_doesnt_sees_ingested_LR(self):
        client = Client()
        self.importIngestedFixtures()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE), follow=True, 
          data={'q':'INGESTED'})
        self.assertEqual('repository/search.html', response.templates[0].name)
        self.assertContains(response, "No results were found for search query", status_code=200)
        
