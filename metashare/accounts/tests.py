'''
Created on 09.08.2011

@author: marc
'''
import unittest
import django.test
from metashare.accounts.models import RegistrationRequest
from django.core.exceptions import ValidationError
from django.test.client import Client
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
        post_data = {'shortname':'test', 'firstname':'Test',
          'lastname':'Testson', 'email':'a@b.com'}
        response = client.post('/{0}accounts/create/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('frontpage.html', response.templates[0].name)
        self.assertNotContains(response, "Please fill in all fields",
          status_code=200)

    def testBrokenPost(self):
        client = Client()
        post_data = {'shortname':'test', 'firstname':'Test',
          'lastname':'Testson'}
        response = client.post('/{0}accounts/create/'.format(DJANGO_BASE),
          follow=True, data=post_data)
        self.assertEqual('accounts/create_account.html',
          response.templates[0].name)
        self.assertFormError(response, 'form', 'email',
          'This field is required.')
        self.assertContains(response, "Please fill in all fields",
          status_code=200)


class RegistrationRequestTest(unittest.TestCase):

    def setUp(self):
        self.reg_request = RegistrationRequest.objects.create(
          shortname='test', firstname='Test', lastname='Testson',
          email='test@b.com')
        self.broken_request1 = RegistrationRequest.objects.create(
          firstname='Test', lastname='Testson', email='broken1@b.com')
        self.broken_request2 = RegistrationRequest.objects.create(
          shortname='broken2',  lastname='Testson', email='broken2@b.com')
        self.broken_request3 = RegistrationRequest.objects.create(
          shortname='broken3', firstname='Test',  email='broken3@b.com')
        self.broken_request4 = RegistrationRequest.objects.create(
          shortname='broken4', firstname='Test', lastname='Testson',
          email='not an email')
        self.broken_request5 = RegistrationRequest.objects.create(
          shortname='broken5', firstname='Test', lastname='Testson')

    def testRegistrationRequestionCorrect(self):
        self.assertEqual('<RegistrationRequest "test">',
          self.reg_request.__unicode__())
        self.assertEqual('test', self.reg_request.shortname)
        self.assertEqual('Test', self.reg_request.firstname)
        self.assertEqual('Testson', self.reg_request.lastname)
        self.assertEqual('test@b.com', self.reg_request.email)

    def testCanRetrieveFromDB(self):
        test_entry = RegistrationRequest.objects.get(pk=self.reg_request.pk)
        self.assertIsNotNone(test_entry)
        self.assertEqual(test_entry, self.reg_request)

    def testCanValidate(self):
        self.reg_request.full_clean()

    def testValidateCatchesBrokenRequest1(self):
        try:
            self.broken_request1.full_clean()
            self.fail("Should have thrown a ValidationError due to missing " \
              "shortname")
        except ValidationError:
            pass

    def testValidateCatchesBrokenRequest2(self):
        try:
            self.broken_request2.full_clean()
            self.fail("Should have thrown a ValidationError due to missing " \
              "firstname")
        except ValidationError:
            pass

    def testValidateCatchesBrokenRequest3(self):
        try:
            self.broken_request3.full_clean()
            self.fail("Should have thrown a ValidationError due to missing " \
              "lastname")
        except ValidationError:
            pass

    def testValidateCatchesBrokenRequest4(self):
        try:
            self.broken_request4.full_clean()
            self.fail("Should have thrown a ValidationError due to wrong " \
              "email")
        except ValidationError:
            pass

    def testValidateCatchesBrokenRequest5(self):
        try:
            self.broken_request5.full_clean()
            self.fail("Should have thrown a ValidationError due to missing " \
              "email")
        except ValidationError:
            pass


    def tearDown(self):
        self.reg_request.delete()
        self.broken_request1.delete()
        self.broken_request2.delete()
        self.broken_request3.delete()
        self.broken_request4.delete()
        self.broken_request5.delete()

if __name__ == "__main__":
    unittest.main()
