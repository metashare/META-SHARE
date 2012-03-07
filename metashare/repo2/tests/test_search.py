from django.test import TestCase
from metashare import test_utils
from django.contrib.auth.models import User
from django.test.client import Client
from metashare.settings import DJANGO_BASE, ROOT_PATH
from metashare.repo2.models import resourceInfoType_model
from haystack.query import SearchQuerySet


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


class SearchTest(TestCase):
    """
    Test the search functionality
    """
    def setUp(self):
        """
        Set up the view
        """
        test_utils.setup_test_storage()
        _fixture = '{0}/repo2/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        self.resource_id = _result[0].id
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.resource_name = getattr(resource.identificationInfo, 'resourceName', None)
        # set up test users with and without staff permissions.
        # These will live in the test database only, so will not
        # pollute the "normal" development db or the production db.
        # As a consequence, they need no valuable password.
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
        Tries to load the Browse page
        """
        client = Client()
        response = client.get('/{0}repo2/browse/'.format(DJANGO_BASE))
        self.assertEqual('repo2/search2.html', response.templates[0].name)

# cfedermann: if  you want to comment out larger blocks of code that may not
# be functional at all (missing imports, methods, etc.), you can use '''...'''
# syntax but make sure to put the following PyLint command in front of the
# opening ''' to avoid raising unnecessary warnings.
#
# pylint: disable-msg=W0105
'''
    def testSearch(self):
        """
        Tries to load the Search page
        """
        client = Client()
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':'Appen'})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "matching your query", status_code=200)

    def testLanguageFilter(self):
        """
        Tries to load the Search page with language filtering
        """
        client = Client()
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'language':'Italian'})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "matching your query", status_code=200)

    def testResourceTypeFilter(self):
        """
        Tries to load the Search page with language filtering
        """
        client = Client()
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'resource_type':'corpus'})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "matching your query", status_code=200)

    def testMediaTypeFilter(self):
        """
        Tries to load the Search page with language filtering
        """
        client = Client()
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'media_type':'text'})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "matching your query", status_code=200)

    def testSearchWithDoubleQuotes(self):
        """
        Tries to load the Search page with double quotes in the search field
        """
        client = Client()
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':'"Appen"'})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "matching your query", status_code=200)


    def test_staff_user_sees_unpublished_LR(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':self.resource_name})
        self.assertEqual('repo2/browsee.html', response.templates[0].name)
        self.assertContains(response, "resource matching your query", status_code=200)

    def test_normal_user_doesnt_sees_unpublished_LR(self):
        client = Client()
        client.login(username='normaluser', password='secret')
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':self.resource_name})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "No results matching your query were found", status_code=200)

    def test_anonymous_doesnt_sees_unpublished_LR(self):
        client = Client()
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':self.resource_name})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "No results matching your query were found", status_code=200)

    def test_unpublished_LR_in_italics_for_staff_user(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':self.resource_name})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "resource matching your query", status_code=200)
        self.assertContains(response, "<i>")

class AdvancedSearchTest(django.test.TestCase):
    """
    Test the advanced functionality
    """
    def setUp(self):
        """
        Set up the advanced functionality
        """
        test_utils.setup_test_storage()
        _fixture = '{0}/repo2/fixtures/testfixture.xml'.format(ROOT_PATH)
        self.resource_id = test_utils.import_xml(_fixture)
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.resource_name = getattr(resource.identificationInfo, 'resourceName', None)
        # set up test users with and without staff permissions.
        # These will live in the test database only, so will not
        # pollute the "normal" development db or the production db.
        # As a consequence, they need no valuable password.
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

    def testAdvancedSearch(self):
        """
        Tries to load the Search page
        """
        client = Client()
        response = client.post('/{0}search/'.format(DJANGO_BASE), follow=True,
          data={'Resourcename':'"Appen"'})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "matching your query", status_code=200)

    def test_staff_user_sees_unpublished_LR(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':self.resource_name})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "resource matching your query", status_code=200)

    def test_normal_user_doesnt_sees_unpublished_LR(self):
        client = Client()
        client.login(username='normaluser', password='secret')
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':self.resource_name})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "No results matching your query were found", status_code=200)

    def test_anonymous_doesnt_sees_unpublished_LR(self):
        client = Client()
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':self.resource_name})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "No results matching your query were found", status_code=200)

    def test_unpublished_LR_in_italics_for_staff_user(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/'.format(DJANGO_BASE), follow=True,
          data={'keywords':self.resource_name})
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "resource matching your query", status_code=200)
        self.assertContains(response, "<i>")

class UnpublishedLRTest(django.test.TestCase):
    """
    Test the unpublished page for staff user
    """
    def setUp(self):
        """
        Set up the unpublished page for staff user
        """
        test_utils.setup_test_storage()
        _fixture = '{0}/repo2/fixtures/testfixture.xml'.format(ROOT_PATH)
        self.resource_id = test_utils.import_xml(_fixture)
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.resource_name = getattr(resource.identificationInfo, 'resourceName', None)
        # set up test users with and without staff permissions.
        # These will live in the test database only, so will not
        # pollute the "normal" development db or the production db.
        # As a consequence, they need no valuable password.
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

    def test_staff_user_sees_unpublished_LR(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/unpublished/True'.format(DJANGO_BASE), follow=True)
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "resource matching your query", status_code=200)

    def test_normal_user_doesnt_sees_unpublished_LR(self):
        client = Client()
        client.login(username='normaluser', password='secret')
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/unpublished/True'.format(DJANGO_BASE), follow=True)
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "No results matching your query were found", status_code=200)

    def test_anonymous_doesnt_sees_unpublished_LR(self):
        client = Client()
        from metashare.repo2 import models
        models.unpublish_LR(self.resource_id)
        response = client.post('/{0}repo2/unpublished/True'.format(DJANGO_BASE), follow=True)
        self.assertEqual('repo2/browse.html', response.templates[0].name)
        self.assertContains(response, "No results matching your query were found", status_code=200)
'''
