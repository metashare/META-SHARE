from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from metashare import test_utils
from metashare.repository.models import resourceInfoType_model
from metashare.repository import views
from metashare.settings import DJANGO_BASE, ROOT_PATH
from metashare.test_utils import create_user
from django.shortcuts import get_object_or_404


def _import_resource(fixture_name):
    """
    Imports the XML resource description with the given file name.
    
    The new resource is published and the ID is returned.
    """
    _result = test_utils.import_xml('{0}/repository/fixtures/{1}'
                                    .format(ROOT_PATH, fixture_name))
    result = _result[0].id
    resource = resourceInfoType_model.objects.get(pk=result)
    resource.storage_object.published = True
    resource.storage_object.save()
    return result


class ViewTest(TestCase):
    """
    Test the detail view
    """
    def setUp(self):
        """
        Set up the detail view
        """
        test_utils.setup_test_storage()
        self.resource_id = _import_resource('testfixture.xml')
        self.resource = get_object_or_404(resourceInfoType_model, pk=self.resource_id)
        # set up test users with and without staff permissions.
        # These will live in the test database only, so will not
        # pollute the "normal" development db or the production db.
        # As a consequence, they need no valuable password.
        staffuser = create_user('staffuser', 'staff@example.com', 'secret')
        staffuser.is_staff = True
        staffuser.save()
        create_user('normaluser', 'normal@example.com', 'secret')

    def tearDown(self):
        """
        Clean up the test
        """
        resourceInfoType_model.objects.all().delete()
        User.objects.all().delete()

    def testView(self):
        """
        Tries to view a resource
        """
        client = Client()
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/lr_view.html')
        self.assertNotContains(response, "Edit")

    def test_staff_user_sees_editor(self):
        """
        Tests whether a staff user can edit a resource (in seeing the edit button)
        """
        client = Client()
        client.login(username='staffuser', password='secret')
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/lr_view.html')
        self.assertContains(response, "Editor")

    def test_normal_user_doesnt_see_editor(self):
        """
        Tests whether a normal user cannot edit a resource
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/lr_view.html')
        self.assertNotContains(response, "Editor")

    def test_anonymous_doesnt_see_editor(self):
        """
        Tests whether an anonymous user cannot edit a resource
        """
        client = Client()
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/lr_view.html')
        self.assertNotContains(response, "Editor")


class DownloadViewTest(TestCase):
    """
    Tests for the license selection, license agreement and download views.
    """
    def setUp(self):
        """
        Sets up some resources with which to test.
        """
        test_utils.setup_test_storage()
        # set up different test resources
        self.non_downloadable_resource_id = _import_resource('testfixture.xml')
        self.downloadable_resource_id_1 = \
            _import_resource('downloadable_1_license.xml')
        self.downloadable_resource_id_2 = \
            _import_resource('downloadable_3_licenses.xml')
        self.non_downloadable_resource = get_object_or_404(resourceInfoType_model, pk=self.non_downloadable_resource_id)
        self.downloadable_resource_1 = get_object_or_404(resourceInfoType_model, pk=self.downloadable_resource_id_1)
        self.downloadable_resource_2 = get_object_or_404(resourceInfoType_model, pk=self.downloadable_resource_id_2)
        # set up test users with and without staff permissions
        staffuser = create_user('staffuser', 'staff@example.com', 'secret')
        staffuser.is_staff = True
        staffuser.save()
        create_user('normaluser', 'normal@example.com', 'secret')

    def tearDown(self):
        """
        Cleans up the test environment.
        """
        resourceInfoType_model.objects.all().delete()
        User.objects.all().delete()

    def test_non_downloadable_resource(self):
        """
        Verifies that an information page is provided for resources which are
        not marked as downloadable.
        """
        # make sure a staff user gets the information page:
        client = Client()
        client.login(username='staffuser', password='secret')
        response = client.get(
            reverse(views.download, args=(self.non_downloadable_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/lr_not_downloadable.html')
        # make sure a normal user gets the information page, too:
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.get(
            reverse(views.download, args=(self.non_downloadable_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/lr_not_downloadable.html')

    def test_downloadable_resource_with_one_license(self):
        """
        Verifies that a resource with only one download license (possibly
        amongst various other distribution licenses) can be downloaded
        appropriately.
        """
        # test as staff user:
        client = Client()
        client.login(username='staffuser', password='secret')
        self._test_downloadable_resource_with_one_license(client)
        # test as normal user:
        client = Client()
        client.login(username='normaluser', password='secret')
        self._test_downloadable_resource_with_one_license(client)

    def _test_downloadable_resource_with_one_license(self, client):
        """
        Verifies that a resource with only one download license (possibly
        amongst various other distribution licenses) can be downloaded
        appropriately using the given client.
        """
        # make sure the license page is shown:
        response = client.get(
            reverse(views.download, args=(self.downloadable_resource_1.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response, 'licences/CC-BYNCSAv2.5.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # make sure the license agreement page is shown again if the license was
        # not accepted:
        response = client.post(
            reverse(views.download, args=(self.downloadable_resource_1.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'False',
              'licence': 'CC_BY-NC-SA' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response, 'licences/CC-BYNCSAv2.5.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # make sure the download was started after accepting the license:
        response = client.post(
            reverse(views.download, args=(self.downloadable_resource_1.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'CC_BY-NC-SA' },
            follow = True)
        self.assertTemplateNotUsed(response, 'repository/licence_agreement.html',
                            msg_prefix="a download should have been started")
        self.assertTemplateNotUsed(response, 'repository/licence_selection.html',
                            msg_prefix="a download should have been started")
        self.assertTemplateNotUsed(response, 'repository/lr_not_downloadable.html',
                            msg_prefix="a download should have been started")

    def test_downloadable_resource_with_multiple_licenses(self):
        """
        Verifies that a resource with multiple download licenses (possibly
        amongst various other distribution licenses) can be downloaded
        appropriately.
        """
        # TODO add assertions
        pass

    def test_locally_downloadable_resource(self):
        """
        Verifies that a resource which is locally downloadable can actually be
        downloaded appropriately.
        """
        # TODO add assertions
        pass

    def test_externally_downloadable_resource(self):
        """
        Verifies that a resource which is externally downloadable can actually
        be downloaded appropriately.
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.post(
            reverse(views.download, args=(self.downloadable_resource_1.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'CC_BY-NC-SA' },
            follow = True)
        self.assertIn(("http://www.example.org/dl1", 302),
                      response.redirect_chain,
                      msg="There should be a redirect to example.org.")

    def test_resource_download_as_anonymous_user(self):
        """
        Verifies that the anonymous user cannot download any resources.
        """
        # neither via GET ...
        response = Client().get(
            reverse(views.download, args=(self.non_downloadable_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'login.html')
        # ... nor via POST with no data ...
        response = Client().post(
            reverse(views.download, args=(self.non_downloadable_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'login.html')
        # ... nor via POST with a selected license ...
        response = Client().post(
            reverse(views.download, args=(self.non_downloadable_resource.storage_object.identifier,)),
            { 'licence': 'GPL' },
            follow = True)
        # ... nor via POST with an agreement to some license:
        response = Client().post(
            reverse(views.download, args=(self.non_downloadable_resource.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'GPL' },
            follow = True)
        self.assertTemplateUsed(response, 'login.html')

    def test_download_button_is_correct_with_staff_user(self):
        """
        Tests whether the link of the download button is the good one
        """
        client = Client()
        client.login(username='staffuser', password='secret')
        url = self.downloadable_resource_1.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/lr_view.html')
        self.assertContains(response, "repository/download/{0}".format(self.downloadable_resource_1.storage_object.identifier))

    def test_can_download_master_copy(self):        
        client = Client()
        client.login(username='staffuser', password='secret')
        self.downloadable_resource_1.storage_object.master_copy = True
        self.downloadable_resource_1.storage_object.save()
        response = client.get('/{0}repository/download/{1}/'
                              .format(DJANGO_BASE, self.downloadable_resource_1.storage_object.identifier))
        self.assertContains(response, "I agree to these licence terms")        
        
    def test_cannot_download_not_master_copy(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        self.downloadable_resource_1.storage_object.master_copy = False
        self.downloadable_resource_1.storage_object.save()
        response = client.get('/{0}repository/download/{1}/'
                              .format(DJANGO_BASE, self.downloadable_resource_1.storage_object.identifier))
        self.assertContains(response, "You will now be redirected")
