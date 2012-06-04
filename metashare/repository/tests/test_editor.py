from django.test import TestCase
import django.db.models
from django.contrib.auth.models import User, Group
from django.test.client import Client
from metashare.settings import DJANGO_BASE, ROOT_PATH
from metashare.repository import models
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.sites import LOGIN_FORM_KEY
from metashare.repository.models import languageDescriptionInfoType_model, \
    lexicalConceptualResourceInfoType_model, resourceInfoType_model
from metashare import test_utils

ADMINROOT = '/{0}editor/'.format(DJANGO_BASE)
TESTFIXTURE_XML = '{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
BROKENFIXTURE_XML = '{}/repository/fixtures/broken.xml'.format(ROOT_PATH)
TESTFIXTURES_ZIP = '{}/repository/fixtures/tworesources.zip'.format(ROOT_PATH)
BROKENFIXTURES_ZIP = '{}/repository/fixtures/onegood_onebroken.zip'.format(ROOT_PATH)
LEX_CONC_RES_XML = '{}/repository/test_fixtures/published-lexConcept-Text-FreEngGer.xml'.format(ROOT_PATH)


class EditorTest(TestCase):
    """
    Test the python/server side of the editor
    """
    # static variables to be initialized in setUpClass():
    staff_login = None
    normal_login = None
    editor_login = None
    testfixture = None

    @classmethod
    def import_test_resource(cls, path=TESTFIXTURE_XML):
        test_utils.setup_test_storage()
        result = test_utils.import_xml(path)
        resource = result[0]
        return resource

    @classmethod
    def setUpClass(cls):
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
        EditorTest.staff_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'staffuser',
            'password': 'secret',
        }

        EditorTest.normal_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'normaluser',
            'password': 'secret',
        }
        
        EditorTest.editor_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'editoruser',
            'password': 'secret',
        }
        
        EditorTest.testfixture = cls.import_test_resource()

    @classmethod
    def tearDownClass(cls):
        resourceInfoType_model.objects.all().delete()
        User.objects.all().delete()
    
    
    def client_with_user_logged_in(self, user_credentials):
        client = Client()
        client.get(ADMINROOT)
        response = client.post(ADMINROOT, user_credentials)
        if response.status_code != 302:
            raise Exception, 'could not log in user with credentials: {}\nresponse was: {}'\
                .format(user_credentials, response)
        return client

    
    def test_can_log_in_staff(self):
        client = Client()
        request = client.get(ADMINROOT)
        self.assertEqual(request.status_code, 200)
        login = client.post(ADMINROOT, EditorTest.staff_login)
        # successful login redirects (status 302), failed login gives a status of 200:
        self.assertNotContains(login, 'Please enter a correct username and password', status_code=302)
        self.assertRedirects(login, ADMINROOT)
        self.assertFalse(login.context)
        client.get(ADMINROOT+'logout/')
        
    def test_cannot_log_in_normal(self):
        client = Client()
        request = client.get(ADMINROOT)
        self.assertEqual(request.status_code, 200)
        login = client.post(ADMINROOT, EditorTest.normal_login)
        # successful login redirects (status 302), failed login gives a status of 200:
        self.assertContains(login, 'Please enter a correct username and password', status_code=200)
           
    def test_editor_can_see_model_list(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+'repository/')
        self.assertContains(response, 'Repository administration')
       
    def test_staff_cannot_see_model_list(self):
        client = self.client_with_user_logged_in(EditorTest.staff_login)
        response = client.get(ADMINROOT+'repository/')
        self.assertContains(response, 'Page not found', status_code=404)

    def test_editor_can_see_resource_add(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+"repository/resourceinfotype_model/add/", follow=True)
        self.assertContains(response, 'Add Resource')

    def test_staff_cannot_see_resource_add(self):
        client = self.client_with_user_logged_in(EditorTest.staff_login)
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/add/', follow=True)
        self.assertContains(response, 'User Authentication', status_code=200)

    def test_editor_can_see_corpus_add(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+"repository/corpusinfotype_model/add/", follow=True)
        self.assertEquals(200, response.status_code)

    def test_staff_cannot_see_corpus_add(self):
        client = self.client_with_user_logged_in(EditorTest.staff_login)
        response = client.get(ADMINROOT+'repository/corpusinfotype_model/add/')
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
        import metashare.repository.admin
        client = self.client_with_user_logged_in(EditorTest.editor_login)
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
                    # Avoid checking classes imported in metashare.repository from other modules
                    #   like StorageObject
                    if value.__module__.startswith('metashare.repository'):
                        # Check only registered models
                        if value in admin.site._registry:
                            model_url = key.lower()
                            url = ADMINROOT+"repository/{}/add/".format(model_url)
                            print "For class {}, trying to access page {} ...".format(cls_name, url)
                            response = client.get(url, follow=True)
                            self.assertEquals(200, response.status_code)
                            num = num + 1
                        else:
                            print 'Class {} has no registered admin form.'.format(cls_name)
                    print
        print 'Checked models: {0}'.format(num)


    def test_resource_list_contains_publish_action(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+"repository/resourceinfotype_model/", follow=True)
        self.assertContains(response, 'Publish selected ingested resources', msg_prefix='response: {0}'.format(response))
        

    def test_upload_single_xml(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(TESTFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded file')
        
    def test_upload_broken_xml(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(BROKENFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Import failed', msg_prefix='response: {0}'.format(response))
        
    def test_upload_single_xml_unchecked(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(TESTFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile }, follow=True)
        self.assertFormError(response, 'form', 'uploadTerms', 'This field is required.')
    
    def test_upload_zip(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 2 resource descriptions')
        self.assertNotContains(response, 'Import failed')
        # And verify that we have more than zero resources on the "my resources" page where we are being redirected:
        self.assertContains(response, "My Resources")
        self.assertNotContains(response, '0 Resources')

    def test_upload_broken_zip(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(BROKENFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 1 resource descriptions')
        self.assertContains(response, 'Import failed for 1 files')
        
    def test_identification_is_inline(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        # Resource name is a field of identification, so if this is present, identification is shown inline:
        self.assertContains(response, "Resource name:", msg_prefix='Identification is not shown inline')
        
    def test_one2one_distribution_is_hidden(self):
        """
        Asserts that a required OneToOneField referring to models that "contain"
        one2many fields is hidden, i.e., the model is edited in a popup/overlay.
        """
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'type="hidden" id="id_distributionInfo"',
                            msg_prefix='Required One-to-one field ' \
                                'distributionInfo" should have been hidden.')

    def test_one2one_distribution_uses_related_widget(self):
        """
        Asserts that a required OneToOneField referring to models that "contain"
        one2many fields is edited in a popup/overlay.
        """
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/' \
                              .format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'related-widget-wrapper-change-link" ' \
                                'id="edit_id_distributionInfo"',
                msg_prefix='Required One-to-one field ' \
                    '"distributionInfo" not rendered using related widget.')
        
    def test_one2one_usage_is_hidden(self):
        """
        Asserts that a recommended OneToOneField referring to models that
        "contain" one2many fields is hidden, i.e., the model is edited in a
        popup/overlay.
        """
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/' \
                              .format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'type="hidden" id="id_usageInfo"',
                            msg_prefix='Recommended One-to-one field ' \
                                '"usageInfo" should have been hidden.')

    def test_one2one_usage_uses_related_widget(self):
        """
        Asserts that a recommended OneToOneField referring to models that
        "contain" one2many fields is edited in a popup/overlay.
        """
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/' \
                              .format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'related-widget-wrapper-change-link" ' \
                                'id="edit_id_usageInfo"',
                msg_prefix='Recommended One-to-one field "usageInfo" not ' \
                    'rendered using related widget, although it contains ' \
                    'a One-to-Many field.')

    def test_licenceinfo_inline_is_present(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/distributioninfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.distributionInfo.id))
        self.assertContains(response, '<div class="inline-group" id="licenceinfotype_model_set-group">',
                            msg_prefix='expected licence info inline')
        

    def test_one2one_sizepervalidation_is_hidden(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'type="hidden" id="id_validationinfotype_model_set-0-sizePerValidation"',
                             msg_prefix='One-to-one field "sizePerValidation" should have been hidden')

    def test_one2one_sizepervalidation_uses_related_widget(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'related-widget-wrapper-change-link" id="edit_id_validationinfotype_model_set-0-sizePerValidation"',
                            msg_prefix='One-to-one field "sizePerValidation" not rendered using related widget')
        self.assertContains(response, 'id="id_validationinfotype_model_set-0-sizePerValidation"',
                            msg_prefix='One2one field in inline has unexpected "id" field -- popup save action probably cannot update field as expected')

    def test_backref_is_hidden(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        corpustextinfo = EditorTest.testfixture.resourceComponentType.corpusMediaType.corpustextinfotype_model_set.all()[0]
        response = client.get('{}repository/corpustextinfotype_model/{}/'.format(ADMINROOT, corpustextinfo.id))
        self.assertContains(response, 'type="hidden" name="back_to_corpusmediatypetype_model"',
                            msg_prefix='Back reference should have been hidden')

    def test_linguality_inline_is_present(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        corpustextinfo = EditorTest.testfixture.resourceComponentType.corpusMediaType.corpustextinfotype_model_set.all()[0]
        response = client.get('{}repository/corpustextinfotype_model/{}/'.format(ADMINROOT, corpustextinfo.id))
        self.assertContains(response, '<div class="form-row lingualityType">',
                            msg_prefix='expected linguality inline')

    def test_hidden_field_is_not_referenced_in_fieldset_label(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        resource = self.import_test_resource(LEX_CONC_RES_XML)
        response = client.get('{}repository/lexicalconceptualresourceinfotype_model/{}/'.format(ADMINROOT, resource.resourceComponentType.id))
        self.assertNotContains(response, ' Lexical conceptual resource media</',
                               msg_prefix='Hidden fields must not be visible in fieldset labels.')

    def test_validator_is_multiwidget(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, '<select onchange="javascript:createNewSubInstance($(this), &quot;add_id_validationinfotype_model_set',
                            msg_prefix='Validator is not rendered as a ChoiceTypeWidget')

    def test_resources_list(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/')
        self.assertContains(response, 'Resources')

    def test_myresources_list(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/my/')
        self.assertContains(response, 'Resources')

    def test_storage_object_is_hidden(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'type="hidden" name="storage_object"',
                            msg_prefix='Expected a hidden storage object')

    def test_editor_can_delete_annotationInfo(self):
        editoruser = User.objects.get(username='editoruser')
        self.assertTrue(editoruser.has_perm('repository.delete_annotationinfotype_model'))

    def test_editor_cannot_delete_actorInfo(self):
        editoruser = User.objects.get(username='editoruser')
        self.assertFalse(editoruser.has_perm('repository.delete_actorinfotype_model'))
       
    def test_can_edit_master_copy(self):        
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        resource = self.import_test_resource()
        resource.storage_object.master_copy = True
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, resource.storage_object.id))
        self.assertContains(response, "Change Resource", status_code=200)
        
    def test_cannot_edit_not_master_copy(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        resource = self.import_test_resource()
        resource.storage_object.master_copy = False
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, resource.storage_object.id))
        self.assertContains(response, "You will now be redirected", status_code=200)
        
