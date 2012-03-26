from django.test import TestCase
import django.db.models
from django.contrib.auth.models import User, Group
from django.test.client import Client
from metashare.settings import DJANGO_BASE, ROOT_PATH
from metashare.repo2 import models
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.sites import LOGIN_FORM_KEY
from metashare.repo2.models import languageDescriptionInfoType_model, \
    lexicalConceptualResourceInfoType_model, resourceInfoType_model
from metashare import test_utils

ADMINROOT = '/{0}editor/'.format(DJANGO_BASE)
TESTFIXTURE_XML = '{}/repo2/fixtures/testfixture.xml'.format(ROOT_PATH)
BROKENFIXTURE_XML = '{}/repo2/fixtures/broken.xml'.format(ROOT_PATH)
TESTFIXTURES_ZIP = '{}/repo2/fixtures/tworesources.zip'.format(ROOT_PATH)
BROKENFIXTURES_ZIP = '{}/repo2/fixtures/onegood_onebroken.zip'.format(ROOT_PATH)

class EditorTest(TestCase):
    """
    Test the python/server side of the editor
    """

    #fixtures = ['testfixture.json']
    

    def setUp(self):
        """
        set up test users with and without staff permissions.
        These will live in the test database only, so will not
        pollute the "normal" development db or the production db.
        As a consequence, they need no valuable password.
        """
        staffuser = User.objects.create_user('staffuser', 'staff@example.com',
          'secret')
        staffuser.is_staff = True
        staffuser.save()
        
        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

        editoruser = User.objects.create_user('editoruser', 'editor@example.com',
          'secret')
        editoruser.is_staff = True
        globaleditors = Group.objects.get(name='globaleditors')
        editoruser.groups.add(globaleditors)
        editoruser.save()


        # login POST dicts
        self.staff_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'staffuser',
            'password': 'secret',
        }

        self.normal_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'normaluser',
            'password': 'secret',
        }
        
        self.editor_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'editoruser',
            'password': 'secret',
        }
        
    def tearDown(self):
        resourceInfoType_model.objects.all().delete()
    
    
    def client_with_user_logged_in(self, user_credentials):
        client = Client()
        client.get(ADMINROOT)
        response = client.post(ADMINROOT, user_credentials)
        if response.status_code != 302:
            raise Exception, 'could not log in user with credentials: {}\nresponse was: {}'\
                .format(user_credentials, response)
        return client

    def import_test_resource(self):
        test_utils.setup_test_storage()
        test_utils.import_xml(TESTFIXTURE_XML)
        

    def test_can_log_in_staff(self):
        client = Client()
        request = client.get(ADMINROOT)
        self.assertEqual(request.status_code, 200)
        login = client.post(ADMINROOT, self.staff_login)
        # successful login redirects (status 302), failed login gives a status of 200:
        self.assertNotContains(login, 'Please enter a correct username and password', status_code=302)
        self.assertRedirects(login, ADMINROOT)
        self.assertFalse(login.context)
        client.get(ADMINROOT+'logout/')
        
    def test_cannot_log_in_normal(self):
        client = Client()
        request = client.get(ADMINROOT)
        self.assertEqual(request.status_code, 200)
        login = client.post(ADMINROOT, self.normal_login)
        # successful login redirects (status 302), failed login gives a status of 200:
        self.assertContains(login, 'Please enter a correct username and password', status_code=200)
            
    def test_editor_can_see_resource_list(self):
        client = self.client_with_user_logged_in(self.editor_login)
        response = client.get(ADMINROOT+'repo2/')
        self.assertContains(response, 'Repo2 administration')
        
    def test_staff_cannot_see_resource_list(self):
        client = self.client_with_user_logged_in(self.staff_login)
        response = client.get(ADMINROOT+'repo2/')
        self.assertContains(response, 'Page not found', status_code=404)

    def test_editor_can_see_resource_add(self):
        client = self.client_with_user_logged_in(self.editor_login)
        response = client.get(ADMINROOT+"repo2/resourceinfotype_model/add/", follow=True)
        self.assertContains(response, 'Add Resource')

    def test_staff_cannot_see_resource_add(self):
        client = self.client_with_user_logged_in(self.staff_login)
        response = client.get(ADMINROOT+'repo2/resourceinfotype_model/add/', follow=True)
        self.assertContains(response, 'User Authentication', status_code=200)

    def test_editor_can_see_corpus_add(self):
        client = self.client_with_user_logged_in(self.editor_login)
        response = client.get(ADMINROOT+"repo2/corpusinfotype_model/add/", follow=True)
        self.assertEquals(200, response.status_code)

    def test_staff_cannot_see_corpus_add(self):
        client = self.client_with_user_logged_in(self.staff_login)
        response = client.get(ADMINROOT+'repo2/corpusinfotype_model/add/')
        self.assertContains(response, 'Permission denied', status_code=403)


    def test_editor_can_see_models_add(self):
        # We don't expect the following add forms to work, because the editor
        # always and exclusively uses the change form for these:
        models_not_expected_to_work = (
            languageDescriptionInfoType_model,
            lexicalConceptualResourceInfoType_model,
        )
        
        
        # Make sure admin.site.register() is actually executed:
        # pylint: disable-msg=W0612
        import metashare.repo2.admin
        client = self.client_with_user_logged_in(self.editor_login)
        items = models.__dict__.items()
        num = 0
        for key, value in items:
            if value in models_not_expected_to_work:
                continue
            # Check only classes
            if isinstance(value, type):
                # Check only subclasses of Django Model
                if issubclass(value, django.db.models.Model):
                    cls_name = value.__name__
                    # Avoid checking classes imported in metashare.repo2 from other modules
                    #   like StorageObject
                    if value.__module__.startswith('metashare.repo2'):
                        # Check only registered models
                        if value in admin.site._registry:
                            model_url = key.lower()
                            url = ADMINROOT+"repo2/{}/add/".format(model_url)
                            print "For class {}, trying to access page {} ...".format(cls_name, url)
                            response = client.get(url, follow=True)
                            self.assertEquals(200, response.status_code)
                            num = num + 1
                        else:
                            print 'Class {} has no registered admin form.'.format(cls_name)
                    print
        print 'Checked models: {0}'.format(num)


    def test_resource_list_contains_publish_action(self):
        self.import_test_resource()
        client = self.client_with_user_logged_in(self.editor_login)
        response = client.get(ADMINROOT+"repo2/resourceinfotype_model/", follow=True)
        self.assertContains(response, 'Publish selected ingested resources', msg_prefix='response: {0}'.format(response))
        

    def test_upload_single_xml(self):
        client = self.client_with_user_logged_in(self.editor_login)
        xmlfile = open(TESTFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded file')
        
    def test_upload_broken_xml(self):
        client = self.client_with_user_logged_in(self.editor_login)
        xmlfile = open(BROKENFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Import failed', msg_prefix='response: {0}'.format(response))
        
    def test_upload_single_xml_unchecked(self):
        client = self.client_with_user_logged_in(self.editor_login)
        xmlfile = open(TESTFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile }, follow=True)
        self.assertFormError(response, 'form', 'uploadTerms', 'This field is required.')
    
    def test_upload_zip(self):
        client = self.client_with_user_logged_in(self.editor_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 2 resource descriptions')
        self.assertNotContains(response, 'Import failed')
        # And verify that we have more than zero resources on the "my resources" page where we are being redirected:
        self.assertContains(response, "My Resources")
        self.assertNotContains(response, '0 Resources')

    def test_upload_broken_zip(self):
        client = self.client_with_user_logged_in(self.editor_login)
        xmlfile = open(BROKENFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 1 resource descriptions')
        self.assertContains(response, 'Import failed for 1 files')
        