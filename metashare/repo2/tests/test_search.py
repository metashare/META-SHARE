from metashare import test_utils
from metashare.settings import DJANGO_BASE, ROOT_PATH
from metashare.repo2.models import resourceInfoType_model
from haystack.query import SearchQuerySet
from django.contrib.auth.models import User
from django.test.client import Client


class SearchIndexUpdateTests(test_utils.IndexAwareTestCase):
    """
    A test case for testing various aspects of the automatic reindexing on
    database changes.
    """
    # paths to XML files containing test resources
    RES_PATH_1 = "{0}/repo2/fixtures/roundtrip.xml".format(ROOT_PATH)
    RES_PATH_2 = "{0}/repo2/fixtures/testfixture.xml".format(ROOT_PATH)
    
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
        _fixture = '{0}/repo2/fixtures/testfixture.xml'.format(ROOT_PATH)
        # import a single resource and save it in the DB
        resource = test_utils.import_xml(_fixture)[0]
        resource.storage_object.publication_status = 'p'
        resource.storage_object.save()
        staffuser = User.objects.create_user('staffuser', 'staff@example.com',
          'secret')
        staffuser.is_staff = True
        staffuser.save()
        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

    def tearDown(self):
        """
        Clean up the test
        """
        resourceInfoType_model.objects.all().delete()

    def testBrowse(self):  
        """
       # Tries to load the Browse page
        """
        client = Client()
        response = client.get('/{0}repo2/browse/'.format(DJANGO_BASE))
        self.assertEqual(response.status_code, 404)


    def testSearch(self):        
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True,
          data={'q':'Italian'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
    
       
    def testSearchForNoResults(self):        
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True,
          data={'q':'querywhichwillgivenoresults'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "No results were found for search query", status_code=200)
           
        
    def testLanguageFacet(self):   
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'languageNameFilter_exact:Italian'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testLanguageFacetForNoResults(self):   
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'languageNameFilter_exact:English'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "No results were found for search query", status_code=200)
        
    def testResourceTypeFacet(self):   
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'resourceTypeFilter_exact:corpus'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testMediaTypeFacet(self):   
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'mediaTypeFilter_exact:audio'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testAvailabilityFacet(self):   
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'availabilityFilter_exact:available-restrictedUse'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        '''      
    def testLicenceFacet(self):   
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True, data={'selected_facets':'licenceFilter_exact:ELRA_END_USER'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        
    def testLicenceFacetForTwoLicences(self):   
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'licenceFilter_exact:ELRA_END_USER', 'selected_facets':'licenceFilter_exact:ELRA_EVALUATION'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)

    def testRestrictionsOfUseFacet(self):   
        client = Client()
        response = client.get('/{0}repo2/search2/'.format(DJANGO_BASE), follow=True, 
          data={'selected_facets':'restrictionsOfUseFilter_exact:academic-nonCommercialUse'})
        self.assertEqual('repo2/search.html', response.templates[0].name)
        self.assertContains(response, "1 Language Resource", status_code=200)
        '''