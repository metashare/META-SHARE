'''
Created on 09.08.2011

@author: marc
'''
import django.test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client

from metashare import test_utils
from metashare.accounts import views
from metashare.accounts.models import RegistrationRequest
from metashare.settings import DJANGO_BASE


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
