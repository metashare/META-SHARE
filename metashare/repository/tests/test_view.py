import shutil
import logging
from datetime import datetime

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags import humanize
from django.core.urlresolvers import reverse
from django.template.defaultfilters import urlizetrunc
from django.test import TestCase
from django.test.client import Client
from django.utils.encoding import smart_str
from django.utils.formats import date_format

from metashare import test_utils, settings, xml_utils
from metashare.accounts.models import UserProfile, EditorGroup, \
    EditorGroupManagers, Organization
from metashare.repository import views
from metashare.repository.models import resourceInfoType_model
from metashare.repository.supermodel import OBJECT_XML_CACHE
from metashare.settings import DJANGO_BASE, ROOT_PATH, LOG_HANDLER, \
    TEST_MODE_NAME
from metashare.test_utils import create_user
from metashare.utils import prettify_camel_case_string


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

def _import_resource(fixture_name, editor_group=None):
    """
    Imports the XML resource description with the given file name.
    
    The new resource is published and returned.
    """
    result = test_utils.import_xml('{0}/repository/fixtures/{1}'
                                    .format(ROOT_PATH, fixture_name))
    result.storage_object.published = True
    if not editor_group is None:
        result.editor_groups.add(editor_group)
        result.save()
    result.storage_object.save()
    return result


class FrontpageTest(TestCase):
    """
    Tests for the frontpage of a META-SHARE node.
    """
    editor_user = None
    editor_user_password = 'secret'
    frontpage_url = '/' + DJANGO_BASE

    @classmethod
    def setUpClass(cls):
        """
        Sets up this test case.
        """
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        FrontpageTest.editor_user = test_utils.create_editor_user('editoruser',
            'editor@example.com', FrontpageTest.editor_user_password,
            (EditorGroup.objects.create(name='test_editor_group'),))

    @classmethod
    def tearDownClass(cls):
        """
        Makes required cleanups after all tests have run.
        """
        test_utils.clean_user_db()
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def setUp(self):
        """
        Set up logic for each test.
        """
        self.client = Client()

    def test_frontpage_provides_login_button(self):
        """
        Verifies that the frontpage provides a login button for anonymous users
        (only).
        """
        # look for the login button as an anonymous user:
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertContains(response, ">Login<",
            msg_prefix="There must be a login button for anonymous users.")
        # look for the login button as an editor user:
        self.client.login(username=FrontpageTest.editor_user.username,
                          password=FrontpageTest.editor_user_password)
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertNotContains(response, ">Login<",
            msg_prefix="There must not be any login button for editor users.")

    def test_frontpage_provides_logout_button(self):
        """
        Verifies that the frontpage provides a logout button for logged in users
        (only).
        """
        # look for the logout button as an anonymous user:
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertNotContains(response, ">Logout<", msg_prefix="There must " \
                               "not be any logout button for anonymous users.")
        # look for the logout button as an editor user:
        self.client.login(username=FrontpageTest.editor_user.username,
                          password=FrontpageTest.editor_user_password)
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertContains(response, ">Logout<",
            msg_prefix="There must be a logout button for editor users.")

    def test_frontpage_provides_register_button(self):
        """
        Verifies that the frontpage provides an account register button for
        anonymous users (only).
        """
        # look for the register button as an anonymous user:
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertContains(response, ">Register<",
            msg_prefix="There must be a register button for anonymous users.")
        # look for the register button as an editor user:
        self.client.login(username=FrontpageTest.editor_user.username,
                          password=FrontpageTest.editor_user_password)
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertNotContains(response, ">Register<", msg_prefix="There must" \
                               " not be any register button for editor users.")

    def test_frontpage_provides_editor_button_for_staff_users(self):
        """
        Verifies that the frontpage provides an editor link for staff users
        (only).
        """
        # look for the editor button as an anonymous user:
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertNotContains(response, ">Manage Resources<",
            msg_prefix="there mustn't be any editor button for anonymous users")
        # look for the editor button as an editor user:
        self.client.login(username=FrontpageTest.editor_user.username,
                          password=FrontpageTest.editor_user_password)
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertContains(response, ">Manage Resources<",
            msg_prefix="There must be an editor button for editor users.")

    def test_frontpage_provides_search_button(self):
        """
        Verifies that the frontpage provides a search button for all kinds of
        users.
        """
        # look for the search button as an anonymous user:
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertContains(response, ">Search<",
            msg_prefix="There must be a search button for anonymous users.")
        # look for the search button as an editor user:
        self.client.login(username=FrontpageTest.editor_user.username,
                          password=FrontpageTest.editor_user_password)
        response = self.client.get(FrontpageTest.frontpage_url)
        self.assertContains(response, ">Search<",
            msg_prefix="There must be a search button for editor users.")


class ViewTest(TestCase):
    """
    Test the single resource view
    """
    test_editor = None
    
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))
        
    def setUp(self):
        """
        Set up the detail view
        """
        test_utils.setup_test_storage()
        create_user('normaluser', 'normal@example.com', 'secret')
        _test_editor_group = EditorGroup.objects.create(
                                                    name='test_editor_group')
        self.resource = _import_resource('testfixture.xml',
                                         _test_editor_group)
        ViewTest.test_editor = test_utils.create_editor_user('editoruser',
            'editor@example.com', 'secret', (_test_editor_group,))          
        test_utils.create_manager_user('manageruser', 'manager@example.com',
            'secret', (EditorGroupManagers.objects.create(
                            name='test_editor_group_manager',
                            managed_group=_test_editor_group),))

    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

    def test_editor_user_sees_editor(self):
        """
        Tests whether an editor user can edit a resource (in seeing the
        "Edit Resource" button)
        """
        client = Client()
        client.login(username='editoruser', password='secret')
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        self.assertContains(response, 'middle_button">Edit Resource<')
        self.assertNotContains(response, 'middle_gray_button">Edit Resource<')

    def test_normal_user_doesnt_see_editor(self):
        """
        Tests whether a normal user cannot edit a resource
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        self.assertNotContains(response, 'middle_button">Edit Resource<')
        self.assertContains(response, 'middle_gray_button">Edit Resource<')

    def test_anonymous_doesnt_see_editor(self):
        """
        Tests whether an anonymous user cannot edit a resource
        """
        client = Client()
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        self.assertNotContains(response, 'middle_button">Edit Resource<')
        self.assertContains(response, 'middle_gray_button">Edit Resource<')

    def testPageTitle(self):
        """
        Tests whether the title inside the header of the web page 
        is the name of the resource (SEO)
        """
        client = Client()
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        self.assertContains(response, '<title>Italian TTS Speech Corpus ' \
                            '(Appen) &ndash; META-SHARE</title>')

    def testResourceTitle(self):
        """
        Tests whether the resource title is correct 
        """
        client = Client()
        url = self.resource.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        self.assertContains(response, '<h2>Italian TTS Speech Corpus (Appen)')

    def test_owner_can_edit_resource(self):
        """
        Tests whether the link of the edit button is the good one
        """
        client = Client()
        client.login(username=ViewTest.test_editor.username, password='secret')
        self.resource.owners.add(ViewTest.test_editor)
        self.resource.save()
        response = client.get(self.resource.get_absolute_url())
        self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        self.assertContains(response,
            "repository/resourceinfotype_model/{0}/".format(self.resource.id))

    def test_normal_user_cannot_edit_resource(self):
        """
        Tests that there is no edit button link for an unauthorized user
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.get(self.resource.get_absolute_url())
        self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        self.assertNotContains(response,
            "repository/resourceinfotype_model/{0}/".format(self.resource.id))


class DownloadViewTest(TestCase):
    """
    Tests for the license selection, license agreement and download views.
    """
    
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)
    
    @classmethod
    def tearDownClass(cls):
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))
        
    def setUp(self):
        """
        Sets up some resources with which to test.
        """
        test_utils.setup_test_storage()
        # set up different test resources
        self.non_downloadable_resource = _import_resource('ILSP10.xml')
        self.downloadable_resource_1 = \
            _import_resource('downloadable_1_license.xml')
        self.downloadable_resource_3 = \
            _import_resource('downloadable_3_licenses.xml')
        self.ms_commons_resource = \
            _import_resource('downloadable_ms_commons_license.xml')
        self.local_download_resource = \
            _import_resource('local_download.xml')
        # assign and copy downloadable resource
        self.local_download_resource.storage_object.checksum = \
            '3930f5022aff02c7fa27ffabf2eaaba0'
        self.local_download_resource.storage_object.save()
        self.local_download_resource.storage_object.update_storage()
        shutil.copyfile(
          '{0}/repository/fixtures/archive.zip'.format(settings.ROOT_PATH),
          '{0}/{1}/archive.zip'.format(
            settings.STORAGE_PATH, self.local_download_resource.storage_object.identifier))
        # set up test users with/without staff permissions and with/without
        # META-SHARE full membership
        staffuser = create_user('staffuser', 'staff@example.com', 'secret')
        staffuser.is_staff = True
        staffuser.save()
        create_user('normaluser', 'normal@example.com', 'secret')
        profile_ct = ContentType.objects.get_for_model(UserProfile)
        ms_full_member_perm = Permission.objects.get(content_type=profile_ct,
                                                     codename='ms_full_member')
        ms_member = create_user('fullmember', 'fm@example.com', 'secret')
        ms_member.user_permissions.add(ms_full_member_perm)
        ms_member.save()
        ms_member = create_user('associatemember', 'am@example.com', 'secret')
        ms_member.user_permissions.add(Permission.objects.get(
                    content_type=profile_ct, codename='ms_associate_member'))
        ms_member.save()
        # create a test organization with META-SHARE full membership
        test_organization_ms = Organization.objects.create(
                                                    name='test_organization_ms')
        test_organization_ms.permissions.add(ms_full_member_perm)
        test_organization_ms.save()
        test_utils.create_organization_member('organization_member_ms',
            'om_ms@example.com', 'secret', (test_organization_ms,))

    def tearDown(self):
        """
        Cleans up the test environment.
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

    def test_non_downloadable_resource(self):
        """
        Verifies that an information page is provided for resources which are
        not marked as downloadable.
        """
        # make sure a staff user gets the information page:
        client = Client()
        client.login(username='staffuser', password='secret')
        response = client.get(reverse(views.download, args=
                (self.non_downloadable_resource.storage_object.identifier,)),
            follow = True)
        self.assertContains(response, 'license terms for the download of the '
                'selected resource are not available')
        # make sure a normal user gets the information page, too:
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.get(reverse(views.download, args=
                (self.non_downloadable_resource.storage_object.identifier,)),
            follow = True)
        self.assertContains(response, 'license terms for the download of the '
                'selected resource are not available')

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
        response = client.get(reverse(views.download,
                args=(self.downloadable_resource_1.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response, 'licences/CC-BYNCSAv3.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # make sure the license agreement page is shown again if the license was
        # not accepted:
        response = client.post(reverse(views.download,
                args=(self.downloadable_resource_1.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'False',
              'licence': 'CC-BY-NC-SA' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response, 'licences/CC-BYNCSAv3.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # make sure the download was started after accepting the license:
        response = client.post(reverse(views.download,
                args=(self.downloadable_resource_1.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'CC-BY-NC-SA' },
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
        # test as anonymous user:
        self._test_downloadable_resource_with_multiple_licenses(Client())
        # test as staff user:
        client = Client()
        client.login(username='staffuser', password='secret')
        self._test_downloadable_resource_with_multiple_licenses(client)
        # test as normal user:
        client = Client()
        client.login(username='normaluser', password='secret')
        self._test_downloadable_resource_with_multiple_licenses(client)
        
    def _test_downloadable_resource_with_multiple_licenses(self, client):
        """
        Verifies that a resource with multiple download licenses (possibly
        amongst various other distribution licenses) can be downloaded
        appropriately using the given client.
        """
        # make sure the license selection page is shown:
        response = client.get(reverse(views.download,
                args=(self.downloadable_resource_3.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_selection.html',
                                "license selection page expected")
        self.assertContains(response, 'CC-BY-NC-SA',
                            msg_prefix="an expected license appears to not " \
                                "be shown")
        self.assertContains(response, 'GPL',
                            msg_prefix="an expected license appears to not " \
                                "be shown")
        self.assertContains(response, 'CC-BY-SA',
                            msg_prefix="an expected license appears to not " \
                                "be shown")
        # make sure the license selection page is shown again if no license is selected
        response = client.post(reverse(views.download,
                args=(self.downloadable_resource_3.storage_object.identifier,)),
            { 'licence': 'None' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_selection.html',
                                "license selection page expected")
        self.assertContains(response, 'CC-BY-NC-SA',
                            msg_prefix="an expected license appears to not " \
                                "be shown")
        self.assertContains(response, 'GPL',
                            msg_prefix="an expected license appears to not " \
                                "be shown")
        self.assertContains(response, 'CC-BY-SA',
                            msg_prefix="an expected license appears to not " \
                                "be shown")
        # make sure the license page is shown after selecting a license
        response = client.post(reverse(views.download,
                args=(self.downloadable_resource_3.storage_object.identifier,)),
            { 'licence': 'GPL' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response, 'licences/GNU_gpl-3.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")           
        # make sure the license agreement page is shown again if the license was
        # not accepted
        response = client.post(reverse(views.download,
                args=(self.downloadable_resource_3.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'False',
              'licence': 'GPL' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response, 'licences/GNU_gpl-3.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # make sure the download was started after accepting the license
        response = client.post(reverse(views.download,
                args=(self.downloadable_resource_3.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'GPL' },
            follow = True)
        self.assertTemplateNotUsed(response, 'repository/licence_agreement.html',
                            msg_prefix="a download should have been started")
        self.assertTemplateNotUsed(response, 'repository/licence_selection.html',
                            msg_prefix="a download should have been started")
        self.assertTemplateNotUsed(response, 'repository/lr_not_downloadable.html',
                            msg_prefix="a download should have been started")

    def test_locally_downloadable_resource(self):
        """
        Verifies that a resource which is locally downloadable can actually be
        downloaded appropriately.
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.post(reverse(views.download, args=
                (self.local_download_resource.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'AGPL' },
            follow = True)
        self.assertEquals(200, response.status_code)
        self.assertEquals('application/zip', response.__getitem__('Content-Type'))
        self.assertEquals('attachment; filename=archive.zip', response.__getitem__('Content-Disposition'))
        
    def test_externally_downloadable_resource(self):
        """
        Verifies that a resource which is externally downloadable can actually
        be downloaded appropriately.
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.post(reverse(views.download, args=
                (self.downloadable_resource_1.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'CC-BY-NC-SA' },
            follow = True)
        self.assertIn(("http://www.example.org", 302),
                      response.redirect_chain,
                      msg="There should be a redirect to example.org.")

    def test_download_button_is_correct_with_staff_user(self):
        """
        Tests whether the link of the download button is the good one
        """
        client = Client()
        client.login(username='staffuser', password='secret')
        url = self.downloadable_resource_1.get_absolute_url()
        response = client.get(url, follow = True)
        self.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        self.assertContains(response, "repository/download/{0}".format(
                        self.downloadable_resource_1.storage_object.identifier))

    def test_resource_download_as_unauthorized_user(self):
        """
        Verifies that a non-authorized user cannot download certain resources.
        """
        client = Client()
        client.login(username='associatemember', password='secret')
        # make sure the license page is shown on both a GET and a POST request
        # with no data:
        response = client.get(reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response,
                            'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        response = client.post(reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response,
                            'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # LR must not be downloadable via POST with just a selected license ...
        response = client.post(reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            { 'licence': 'MSCommons-BY-NC-SA' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response,
                            'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # ... nor via POST with an agreement to the license:
        response = client.post(reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'MSCommons-BY-NC-SA' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response,
                            'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")

    def test_downloadable_resource_for_ms_full_members(self):
        """
        Verifies that a resource with an MS Commons license can be downloaded by
        a META-SHARE full member.
        """
        client = Client()
        client.login(username='fullmember', password='secret')
        # make sure the license page is shown:
        response = client.get(reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response,
                            'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # make sure the license agreement page is shown again if the license was
        # not accepted:
        response = client.post(reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'False',
              'licence': 'MSCommons-BY-NC-SA' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response,
                            'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm',
                            msg_prefix="the correct license appears to not " \
                                "be shown in an iframe")
        # make sure the download was started after accepting the license:
        response = client.post(reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'MSCommons-BY-NC-SA' },
            follow = True)
        self.assertTemplateNotUsed(response, 'repository/licence_agreement.html',
                            msg_prefix="a download should have been started")
        self.assertTemplateNotUsed(response, 'repository/licence_selection.html',
                            msg_prefix="a download should have been started")
        self.assertTemplateNotUsed(response, 'repository/lr_not_downloadable.html',
                            msg_prefix="a download should have been started")

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

    def test_downloadable_resource_for_organization_ms_full_members(self):
        """
        Verifies that a resource with an MS Commons license can be downloaded by
        a user of an organization which has the META-SHARE full member
        permission.
        """
        client = Client()
        client.login(username='organization_member_ms', password='secret')
        # make sure the license page is shown:
        response = client.get(
            reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response,
            'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm', msg_prefix="the " \
                "correct license appears to not be shown in an iframe")
        # make sure the download is started after accepting the license:
        response = client.post(
            reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'MSCommons-BY-NC-SA' },
            follow = True)
        self.assertTemplateNotUsed(response,
            'repository/licence_agreement.html',
            msg_prefix="a download should have been started")
        self.assertTemplateNotUsed(response,
            'repository/licence_selection.html',
            msg_prefix="a download should have been started")
        self.assertTemplateNotUsed(response,
            'repository/lr_not_downloadable.html',
            msg_prefix="a download should have been started")

    def test_non_downloadable_resource_for_normal_organization_members(self):
        """
        Verifies that a resource with an MS Commons license cannot be downloaded
        by a user of an organization which does not have the META-SHARE full
        member permission.
        """
        test_passwd = 'secret'
        test_user = test_utils.create_organization_member(
            'organization_member_non_ms', 'om_non_ms@example.com', test_passwd,
            (Organization.objects.create(name='test_organization_non_ms'),))
        client = Client()
        client.login(username=test_user.username, password=test_passwd)
        # make sure the license page is shown:
        response = client.get(reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
                                "license agreement page expected")
        self.assertContains(response,
            'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm', msg_prefix="the " \
                "correct license appears to not be shown in an iframe")
        # make sure the download cannot be started:
        response = client.post(
            reverse(views.download,
                    args=(self.ms_commons_resource.storage_object.identifier,)),
            { 'in_licence_agree_form': 'True', 'licence_agree': 'True',
              'licence': 'MSCommons-BY-NC-SA' },
            follow = True)
        self.assertTemplateUsed(response, 'repository/licence_agreement.html',
            msg_prefix="a download should not have been started")


class FullViewTest(TestCase):
    """
    Defines a number of tests for the details of the single resource view
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Set up the test
        """
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
        # disable indexing during import
        test_utils.set_index_active(False)
        
        # import resources
        test_utils.setup_test_storage()
        OBJECT_XML_CACHE.clear()
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "partial-corpus.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-lang-description.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-lex-conceptual.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-corpus-text.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-corpus-image.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-corpus-audio.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-corpus-video.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-corpus-textngram.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-corpus-textnumerical.xml".format(ROOT_PATH))
        test_utils.import_xml_or_zip("{}/repository/fixtures/full-resources/"
                "full-tool-service.xml".format(ROOT_PATH))
                
        # enable indexing 
        test_utils.set_index_active(True)
    
        # update index
        from django.core.management import call_command
        call_command('rebuild_index', interactive=False, using=TEST_MODE_NAME)
        
    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up the test
        """
        LOGGER.info("finished '{}' tests".format(cls.__name__))
        
        # disable indexing during import
        test_utils.set_index_active(False)
        
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        OBJECT_XML_CACHE.clear()
        
        # enable indexing 
        test_utils.set_index_active(True)
    
        # update index
        from django.core.management import call_command
        call_command('rebuild_index', interactive=False, using=TEST_MODE_NAME)
        
    
    def testSingleResourceView(self):
        """
        Checks that each resource's single view is displayed correctly.
        """
        
        # disable indexing; we don't need stat updates for this test
        test_utils.set_index_active(False)
        
        queryset = resourceInfoType_model.objects.all()
        check_resource_view(queryset, self)

        # enable indexing 
        test_utils.set_index_active(True)


def path_to_root(element, parent_dict):
    """
    Returns the path to the given element using the given parent dictionary.
    """
    current = element
    ele_path = []
    ele_path.append(element.tag)
    while current in parent_dict:
        parent = parent_dict[current] 
        ele_path.append(parent.tag)
        current = parent
    ele_path.reverse()
    path = ""
    for ele in ele_path:
        path += ele
        path += "/"
    return path[:-1]
    

def check_resource_view(queryset, test_case):
    
    # paths elemenets for which the path is skipped
    skip_path_elements = (
      'email',
      'metaShareId',
      'downloadLocation',
      'executionLocation',
    )

    # path suffixes where to apply a URL transformation on the value
    url_paths = (
        '/url',
        '/downloadLocation',
        '/executionLocation',
        '/samplesLocation',
        '/targetResourceNameURI',
        '/documentation',
    )

    # path suffixes where to apply a number transformation on the value
    number_paths = (
      '/size',
      '/fee',
    )

    # path suffixes where to apply data transformation on the value
    date_paths = (
      '/metadataCreationDate',
      '/annotationStartDate',
      '/annotationEndDate',
      '/availabilityStartDate',
      '/availabilityEndDate',
      '/creationStartDate',
      '/creationEndDate',
      '/projectStartDate',
      '/projectEndDate',
      '/lastDateUpdated',
      '/metadataLastDateUpdated',
    )

    count = 0
    for _res in queryset:
        parent_dict = {}
        _res.export_to_elementtree(pretty=True, parent_dict=parent_dict)       

        count += 1
        LOGGER.info("calling {}. resource at {}".format(
          count, _res.get_absolute_url()))
        # always create a new client to force a new session
        client = Client()
        response = client.get(_res.get_absolute_url(), follow = True)
        test_case.assertEquals(200, response.status_code)
        test_case.assertTemplateUsed(response, 'repository/resource_view/lr_view.html')
        
        for _ele in parent_dict:
        
            if not _ele.text:
                continue
        
            path = path_to_root(_ele, parent_dict)
            text = smart_str(xml_utils.html_escape(_ele.text.strip()),
                response._charset)

            # skip boolean values, as they cannot reasonably be verified
            if text.lower() in ("true", "false"):
                continue

            # check if path should be skipped
            skip = False
            for path_ele in skip_path_elements:
                if path_ele in path:
                    skip = True
                    break
            if skip:
                continue    

            # apply number transformation if required
            for _np in number_paths:        
                if path.endswith(_np):
                    text = unicode(humanize.intcomma(text)).encode("utf-8")
                    if text == '0':
                        skip = True
                    break
            if skip:
                continue

            # apply URL transformation if required
            for _up in url_paths:
                if path.endswith(_up) and not path.endswith('identificationInfo/url'):
                    text = unicode(urlizetrunc(text, 23)).encode("utf-8")

            # apply date transformation if required
            for _dp in date_paths:
                if path.endswith(_dp):
                    date_object = datetime.strptime(text, '%Y-%m-%d')
                    text = unicode(
                      date_format(date_object, format='SHORT_DATE_FORMAT', use_l10n=True)).encode("utf-8")

            real_count = response.content.count(text)
            if real_count == 0:
                # try with beautified string
                beauty_real_count = response.content.count(
                  prettify_camel_case_string(text))
            if real_count == 0 and beauty_real_count == 0:
                test_case.fail(u"missing {}: {}".format(path, _ele.text))
