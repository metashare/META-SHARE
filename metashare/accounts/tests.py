'''
Created on 09.08.2011

@author: marc
'''
import django.test
from django.contrib.admin.sites import LOGIN_FORM_KEY
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test.client import Client

from metashare import test_utils
from metashare.accounts import views
from metashare.accounts.models import RegistrationRequest, ResetRequest, \
    EditorGroup, UserProfile, Organization
from metashare.settings import DJANGO_BASE


class ContactFormTest(django.test.TestCase):
    """
    A test case for tests around the node maintainer contact form page.
    """
    test_login = None
    
    @classmethod
    def setUpClass(cls):
        UserProfileTest.test_login = {
            REDIRECT_FIELD_NAME: '/{}'.format(DJANGO_BASE),
            LOGIN_FORM_KEY: 1,
            'username': 'editoruser',
            'password': 'secret',
        }
        User.objects.create_user(UserProfileTest.test_login['username'],
            'editor@example.com', UserProfileTest.test_login['password'])

    @classmethod
    def tearDownClass(cls):
        test_utils.clean_user_db()

    def test_contact_form_access(self):
        """
        Verifies that the contact form page is only accessible by registered users.
        """
        # verify that anonymous access is forbidden and we are redirected to the
        # login page
        client = Client()
        response = client.get(reverse(views.contact), follow=True)
        self.assertNotContains(response, 'Contact Node Maintainers')
        self.assertTemplateUsed(response, 'login.html')
        # verify that access with a normal/registered user is possible
        client = test_utils.get_client_with_user_logged_in(
            UserProfileTest.test_login)
        response = client.get(reverse(views.contact))
        self.assertContains(response, 'Contact Node Maintainers')
        self.assertTemplateUsed(response, 'accounts/contact_maintainers.html')

    def test_contact_form_sending(self):
        """
        Verifies that the submitting the contact form is possible.
        """
        # verify that submitting as an anonymous user is forbidden and we are
        # redirected to the login page
        client = Client()
        response = client.post(reverse(views.contact), data={'message':
                'This is a sufficiently long test message for the node '
                'maintainer contact form.', 'subject': 'Test Request'},
            follow=True)
        self.assertNotContains(response,
            'We have received your message and successfully sent it')
        self.assertTemplateUsed(response, 'login.html')
        # verify that submitting with a normal/registered user is possible
        client = test_utils.get_client_with_user_logged_in(
            UserProfileTest.test_login)
        response = client.post(reverse(views.contact), data={'message':
                'This is a sufficiently long test message for the node '
                'maintainer contact form.', 'subject': 'Test Request'},
            follow=True)
        self.assertContains(response,
            'We have received your message and successfully sent it')


class UserProfileTest(django.test.TestCase):
    """
    A test case for tests around the user profile page.
    """
    test_login = None
    test_organization_1 = None
    test_organization_2 = None
    test_editor_group_1 = None
    test_editor_group_2 = None
    ms_full_member_perm = None
    ms_assoc_member_perm = None
    
    @classmethod
    def setUpClass(cls):
        UserProfileTest.test_login = {
            REDIRECT_FIELD_NAME: '/{}'.format(DJANGO_BASE),
            LOGIN_FORM_KEY: 1,
            'username': 'editoruser',
            'password': 'secret',
        }
        # create some test organizations
        UserProfileTest.test_organization_1 = \
            Organization.objects.create(name='test_organization_1')
        UserProfileTest.test_organization_2 = \
            Organization.objects.create(name='test_organization_2')
        # create some test editor groups
        UserProfileTest.test_editor_group_1 = \
            EditorGroup.objects.create(name='test_editor_group_1')
        UserProfileTest.test_editor_group_2 = \
            EditorGroup.objects.create(name='test_editor_group_2')
        # get the two META-SHARE membership permissions
        _profile_ct = ContentType.objects.get_for_model(UserProfile)
        UserProfileTest.ms_full_member_perm = Permission.objects.get(
            content_type=_profile_ct, codename='ms_full_member')
        UserProfileTest.ms_assoc_member_perm = Permission.objects.get(
            content_type=_profile_ct, codename='ms_associate_member')

    @classmethod
    def tearDownClass(cls):
        test_utils.clean_user_db()

    def setUp(self):
        self.test_user = test_utils.create_editor_user(
            UserProfileTest.test_login['username'], 'editor@example.com',
            UserProfileTest.test_login['password'],
            (UserProfileTest.test_editor_group_1,))
        self.client = test_utils.get_client_with_user_logged_in(
            UserProfileTest.test_login)

    def test_verify_profile_is_editable(self):
        """
        Verifies that the user profile page can be edited.
        """
        _profile = self.test_user.get_profile()
        _profile.position = 'whatever'
        _profile.homepage = 'http://example.org'
        _profile.save()
        self.client.post(reverse(views.edit_profile), data={'affiliation':
                'test organization', 'homepage': 'http://www.example.com/new',
                'birthdate': '', 'position': 'whatever'},
            follow=True)
        # reload the profile from the database to work around Django bug #17750
        _profile = UserProfile.objects.get(user=self.test_user)
        self.assertEquals(_profile.affiliation, 'test organization')
        self.assertEquals(_profile.homepage, 'http://www.example.com/new')
        self.assertEquals(_profile.birthdate, None)
        self.assertEquals(_profile.position, 'whatever')

    def test_verify_ms_membership_shown(self):
        """
        Verifies that the current META-SHARE membership status is shown on the
        user profile page.
        """
        # verify that the user doesn't have any META-SHARE membership by default
        response = self.client.get(reverse(views.edit_profile))
        self.assertNotContains(response, 'META-SHARE Membership')
        # verify that an added META-SHARE associate membership is shown
        self.test_user.user_permissions.add(
            UserProfileTest.ms_assoc_member_perm)
        response = self.client.get(reverse(views.edit_profile))
        self.assertContains(response, 'META-SHARE Membership')
        self.assertContains(response, 'associate member')
        self.test_user.user_permissions.remove(
            UserProfileTest.ms_assoc_member_perm)
        response = self.client.get(reverse(views.edit_profile))
        self.assertNotContains(response, 'META-SHARE Membership')
        # verify that an added META-SHARE full membership is shown
        self.test_user.user_permissions.add(UserProfileTest.ms_full_member_perm)
        response = self.client.get(reverse(views.edit_profile))
        self.assertContains(response, 'META-SHARE Membership')
        self.assertContains(response, 'full member')
        self.test_user.user_permissions.remove(
            UserProfileTest.ms_full_member_perm)
        response = self.client.get(reverse(views.edit_profile))
        self.assertNotContains(response, 'META-SHARE Membership')

    def test_verify_editor_groups_shown(self):
        """
        Verifies that the current editor group memberships are shown on the user
        profile page.
        """
        # verify that the user is shown as belonging to editor group 1
        response = self.client.get(reverse(views.edit_profile))
        self.assertContains(response, 'Editor Group')
        self.assertContains(response, 'test_editor_group_1')
        # verify that the user is shown as belonging to editor groups 1 and 2
        # after adding editor group 2
        self.test_user.groups.add(UserProfileTest.test_editor_group_2)
        response = self.client.get(reverse(views.edit_profile))
        self.assertContains(response, 'Editor Group')
        self.assertContains(response, 'test_editor_group_1')
        self.assertContains(response, 'test_editor_group_2')
        # verify that the user is not shown as belonging to any editor groups
        # after removing group membership
        self.test_user.groups.clear()
        response = self.client.get(reverse(views.edit_profile))
        self.assertNotContains(response, 'Editor Group')

    def test_verify_organizations_shown(self):
        """
        Verifies that the current organization memberships are shown on the user
        profile page.
        """
        # verify that the user is not shown as belonging to any organizations by
        # default
        response = self.client.get(reverse(views.edit_profile))
        self.assertNotContains(response, 'Organization')
        # verify that the user is shown as belonging to organization 1 after
        # adding organization 1
        self.test_user.groups.add(UserProfileTest.test_organization_1)
        response = self.client.get(reverse(views.edit_profile))
        self.assertContains(response, 'Organization')
        self.assertContains(response, 'test_organization_1')
        # verify that the user is shown as belonging to organizations 1 and 2
        # after adding organization 2
        self.test_user.groups.add(UserProfileTest.test_organization_2)
        response = self.client.get(reverse(views.edit_profile))
        self.assertContains(response, 'Organization')
        self.assertContains(response, 'test_organization_1')
        self.assertContains(response, 'test_organization_2')


class CreateViewTest(django.test.TestCase):
    def testCreateInitial(self):
        client = Client()
        response = client.get('/{0}accounts/create/'.format(DJANGO_BASE))
        self.assertEqual('accounts/create_account.html',
          response.templates[0].name)
        self.assertNotContains(response, "Please fill in all fields",
          status_code=200)

    def testCreatePost(self):
        client = Client()
        post_data = {'shortname':'test', 'first_name':'Test',
          'last_name':'Testson', 'email':'a@b.com', 'password':'test',
          'confirm_password': 'test'}
        response = client.post('/{0}accounts/create/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('frontpage.html', response.templates[0].name)
        self.assertNotContains(response, "Please fill in all fields",
          status_code=200)

    def testBrokenPost(self):
        client = Client()
        post_data = {'shortname':'test', 'first_name':'Test',
          'last_name':'Testson', 'password':'test',
          'confirm_password': 'test'}
        response = client.post('/{0}accounts/create/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('accounts/create_account.html',
          response.templates[0].name)
        self.assertFormError(response, 'form', 'email',
          'This field is required.')
        self.assertContains(response, "Please fill in all fields",
          status_code=200)

    def tearDown(self):
        test_utils.clean_user_db()

class RegistrationRequestTest(django.test.TestCase):

    def setUp(self):
        _user = User.objects.create_user('test', 'test@test.com', 'test')
        _user.first_name = 'Test'
        _user.last_name = 'Testson'
        _user.save()
        self.reg_request = RegistrationRequest.objects.create(user=_user)
        self.client = Client()

    def testRegistrationRequestionCorrect(self):
        self.assertEqual('<RegistrationRequest "test">',
          self.reg_request.__unicode__())
        self.assertEqual('test', self.reg_request.user.username)
        self.assertEqual('Test', self.reg_request.user.first_name)
        self.assertEqual('Testson', self.reg_request.user.last_name)
        self.assertEqual('test@test.com', self.reg_request.user.email)

    def testCanRetrieveFromDB(self):
        test_entry = RegistrationRequest.objects.get(pk=self.reg_request.pk)
        self.assertIsNotNone(test_entry)
        self.assertEqual(test_entry, self.reg_request)

    def testCanValidate(self):
        self.reg_request.full_clean()

    def testCanRegister(self):
        _prev_count = RegistrationRequest.objects.count()
        response = self.client.post(reverse(views.create),
            {'first_name': 'Test', 'last_name': 'Testson2', 'shortname': 'good',
             'email': 'ok@example.com', 'password': 'secret',
             'confirm_password': 'secret'}, follow=True)
        self.assertContains(response, 'received your registration data',
            msg_prefix="should have successfully created a registration")
        self.assertEquals(_prev_count + 1, RegistrationRequest.objects.count(),
            "should have successfully created an additional registration")

    def testValidateCatchesBrokenRequest1(self):
        response = self.client.post(reverse(views.create),
            {'first_name': 'Test', 'last_name': 'Testson',
             'email': 'broken1@test.com', 'password': 'test1',
             'confirm_password': 'test1'})
        self.assertContains(response, 'This field is required.',
            msg_prefix="should have shown an error due to missing user name")

    def testValidateCatchesBrokenRequest2(self):
        response = self.client.post(reverse(views.create),
            {'shortname': 'broken2', 'last_name': 'Testson',
             'email': 'broken2@test.com', 'password': 'test2',
             'confirm_password': 'test2'})
        self.assertContains(response, 'This field is required.',
            msg_prefix="should have shown an error due to missing first name")

    def testValidateCatchesBrokenRequest3(self):
        response = self.client.post(reverse(views.create),
            {'shortname': 'broken3', 'first_name': 'Test',
             'email': 'broken3@test.com', 'password': 'test3',
             'confirm_password': 'test3'})
        self.assertContains(response, 'This field is required.',
            msg_prefix="should have shown an error due to missing last name")

    def testValidateCatchesBrokenRequest4(self):
        response = self.client.post(reverse(views.create),
            {'shortname': 'broken4', 'first_name': 'Test',
             'last_name': 'Testson', 'email': 'not an email',
             'password': 'test4', 'confirm_password': 'test4'})
        self.assertContains(response, 'Enter a valid e-mail address.',
            msg_prefix="should have shown an error due to bad e-mail")

    def testValidateCatchesBrokenRequest5(self):
        response = self.client.post(reverse(views.create),
            {'shortname': 'broken5', 'first_name': 'Test',
             'last_name': 'Testson', 'password': 'test5',
             'confirm_password': 'test5'})
        self.assertContains(response, 'This field is required.',
            msg_prefix="should have shown an error due to missing e-mail")

    def testValidateCatchesBrokenRequest6(self):
        response = self.client.post(reverse(views.create),
            {'shortname': 'broken6', 'first_name': 'Test', 'email': 'x@bla.com',
             'last_name': 'Testson', 'confirm_password': 'test6'})
        self.assertContains(response, 'This field is required.',
            msg_prefix="should have shown an error due to missing password")

    def testValidateCatchesBrokenRequest7(self):
        response = self.client.post(reverse(views.create),
            {'shortname': 'broken7', 'first_name': 'Test', 'email': 'x@bla.com',
             'last_name': 'Testson', 'password': 'test7'})
        self.assertContains(response, 'This field is required.',
            msg_prefix="should have shown an error due to missing confirmation")

    def testValidateCatchesBrokenRequest8(self):
        response = self.client.post(reverse(views.create),
            {'shortname': 'broken8', 'first_name': 'Test', 'email': 'x@bla.com',
             'last_name': 'Testson', 'password': 'test8',
             'confirm_password': 'bad'})
        self.assertContains(response, "The two password fields did not match.",
            msg_prefix="should have shown an error due to bad confirmation")

    def testUniqueUserNameRegistration(self):
        response = self.client.post(reverse(views.create),
            {'shortname': self.reg_request.user.username, 'first_name': 'Test',
             'email': 'x@bla.com', 'last_name': 'Testson', 'password': 'test',
             'confirm_password': 'test'})
        self.assertContains(response, "account name already exists",
            msg_prefix="should have shown an error due to duplicate account")

    def testUniqueEmailRegistration(self):
        response = self.client.post(reverse(views.create),
            {'shortname': 'bla', 'first_name': 'Test',
             'email': self.reg_request.user.email, 'last_name': 'Testson',
             'password': 'test', 'confirm_password': 'test'})
        self.assertContains(response,
            "already an account registered with this e-mail address",
            msg_prefix="should have shown an error due to duplicate e-mail")

    def tearDown(self):
        test_utils.clean_user_db()


class ResetPasswordTest(django.test.TestCase):
    
    user = None
    
    def setUp(self):
        """
        Sets up some resources with which to test.
        """
        self.user = User.objects.create_user('normaluser', 'normal@example.com', 'secret')
        
        
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_user_db()
    
    
    def test_reset_requires_user_name_and_email(self):
        client = Client()
        # invalid user name
        post_data = {'username':'normaluserABC', 'email':'normal@example.com'}
        response = client.post('/{0}accounts/reset/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('accounts/reset_account.html', response.templates[0].name)
        self.assertContains(response, "Not a valid username-email combination",
          status_code=200)
        # invalid email
        post_data = {'username':'normaluser', 'email':'normal@example.comABC'}
        response = client.post('/{0}accounts/reset/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('accounts/reset_account.html', response.templates[0].name)
        self.assertContains(response, "Not a valid username-email combination",
          status_code=200)
        # invalid user name and email
        post_data = {'username':'normaluserABC', 'email':'normal@example.comABC'}
        response = client.post('/{0}accounts/reset/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('accounts/reset_account.html', response.templates[0].name)
        self.assertContains(response, "Not a valid username-email combination",
          status_code=200)
        # valid user name and email
        post_data = {'username':'normaluser', 'email':'normal@example.com'}
        response = client.post('/{0}accounts/reset/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('frontpage.html', response.templates[0].name)
        self.assertContains(
          response, 
          "We have received your reset request and sent you an email with further reset instructions",
          status_code=200)


    def test_reset_request_validation(self):
        client = Client()
        old_passwd = self.user.password
        post_data = {'username':'normaluser', 'email':'normal@example.com'}
        # create reset request
        client.post('/{0}accounts/reset/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertNotEqual(None, ResetRequest.objects.get(user=self.user))
        request = ResetRequest.objects.get(user=self.user)
        # confirm reset request
        response = client.get(
          '/{0}accounts/reset/{1}/'.format(DJANGO_BASE, request.uuid), 
          follow=True)
        self.assertEqual('frontpage.html', response.templates[0].name)
        self.assertContains(
          response, 
          "We have re-activated your user account and sent you an email with your personal password which allows you to login to the website.",
          status_code=200)
        # check that password has changed for user
        self.user = User.objects.get(username=self.user.username)
        self.assertNotEquals(old_passwd, self.user.password)
        # check that reset request is deleted
        self.assertEquals(0, len(ResetRequest.objects.all()))


class ChangePasswordTest(django.test.TestCase):
    
    user = None
    
    def setUp(self):
        """
        Sets up some resources with which to test.
        """
        self.user = User.objects.create_user('normaluser', 'normal@example.com', 'secret')
        
        
    def tearDown(self):
        """
        Clean up the test
        """
        test_utils.clean_user_db()
    
    def test_password_change(self):
        client = Client()
        client.login(username='normaluser', password='secret')
        old_passwd = self.user.password
        post_data = {'old_password':'secret', 'new_password1':'new_secret', 'new_password2':'new_secret'}
        response = client.post('/{0}accounts/profile/change_password/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('accounts/change_password_done.html', response.templates[0].name)
        self.assertContains(
          response, "Password change successful", status_code=200)
        # check that password has changed for user
        self.user = User.objects.get(username=self.user.username)
        self.assertNotEquals(old_passwd, self.user.password)
        
        