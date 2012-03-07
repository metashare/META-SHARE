from django.test import TestCase
import django.db.models
from django.contrib.auth.models import User
from django.test.client import Client
from metashare.settings import DJANGO_BASE
from metashare.repo2 import models
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.sites import LOGIN_FORM_KEY

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
        #staffuser.is_staff = True
        staffuser.is_superuser = True
        staffuser.save()
        
        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

        # login POST dicts
        self.staff_login = {
            REDIRECT_FIELD_NAME: '/{0}admin/'.format(DJANGO_BASE),
            LOGIN_FORM_KEY: 1,
            'username': 'staffuser',
            'password': 'secret',
        }

        self.normal_login = {
            REDIRECT_FIELD_NAME: '/{0}admin/'.format(DJANGO_BASE),
            LOGIN_FORM_KEY: 1,
            'username': 'normaluser',
            'password': 'secret',
        }
        

    # TODO: These tests don't actually do anything.
    # They get stuck at the login page; for the moment I cannot 
    # get the approach to work that is used in Django itself:
    # https://code.djangoproject.com/browser/django/trunk/tests/regressiontests/admin_views/tests.py#L806
    

    if False:
        def test_can_log_in_normal(self):
            client = Client()
            #is_logged_in = client.login(username='normaluser', password='secret')
            #self.assertTrue(is_logged_in)
            request = client.get('/{0}admin/'.format(DJANGO_BASE))
            self.assertEqual(request.status_code, 200)
            login = client.post('/{0}admin/'.format(DJANGO_BASE), self.staff_login)
            print u'{}'.format(login)
            self.assertRedirects(login, '/{0}admin/'.format(DJANGO_BASE))
            self.assertFalse(login.context)
            client.get('/{0}admin/logout/'.format(DJANGO_BASE))
        
    def test_can_log_in_staff(self):
        client = Client()
        is_logged_in = client.login(username='staffuser', password='secret')
        self.assertTrue(is_logged_in)

    if False:
        def test_resource_list_contains_publish_action(self):
            client = Client()
            client.login(username='staffuser', password='secret')
            response = client.get("/{0}admin/repo2/resourceinfotype_model/".format(DJANGO_BASE), follow=True)
            self.assertContains(response, 'Publish selected resources', msg_prefix='response: {0}'.format(response))
        

    def test_can_see_resource_add(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        response = client.get("/{0}admin/repo2/resourceinfotype_model/add/".format(DJANGO_BASE), follow=True)
        self.assertEquals(200, response.status_code)

    def test_can_see_corpus_add(self):
        client = Client()
        client.login(username='staffuser', password='secret')
        response = client.get("/{0}admin/repo2/corpusinfotype_model/add/".format(DJANGO_BASE), follow=True)
        self.assertEquals(200, response.status_code)
        
    def test_can_see_models_add(self):
        # Make sure admin.site.register() is actually executed:
        # pylint: disable-msg=W0612
        import metashare.repo2.admin
        client = Client()
        client.login(username='staffuser', password='secret')
        items = models.__dict__.items()
        num = 0
        for key, value in items:
        #print key
        #print value
        # Check only classes
            if isinstance(value, type):
                #print type(value)
                #print 'issubclass = ' + unicode(issubclass(value, django.db.models.Model))
                # Check only subclasses of Django Model
                if issubclass(value, django.db.models.Model):
                    cls_name = value.__name__
                    print "class name = " + cls_name + ", module = " + value.__module__
                    #mod = value.__module__
                    #print "Module = " + mod
                    # Avoid checking classes imported in metashare.repo2 from other modules
                    #   like StorageObject
                    if value.__module__.startswith('metashare.repo2'):
                        # Check only registered models
                        if value in admin.site._registry:
                            #print 'Registered'
                            model_url = key.lower()
                            url = "/{0}admin/repo2/{1}/add/".format(DJANGO_BASE, model_url)
                            print "Getting page {0} ...".format(url)
                            response = client.get(url, follow=True)
                            self.assertEquals(200, response.status_code)
                            num = num + 1
                            #print 'url = ' + url
                print
        print 'Checked models: {0}'.format(num)
        self.assertTrue(True)

    
    
    
