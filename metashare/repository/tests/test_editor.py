import django.db.models

from django.contrib import admin
from django.contrib.admin.sites import LOGIN_FORM_KEY
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from metashare import test_utils
from metashare.accounts.models import EditorGroup, ManagerGroup
from metashare.repository import models
from metashare.repository.models import languageDescriptionInfoType_model, \
    lexicalConceptualResourceInfoType_model, resourceInfoType_model
from metashare.settings import DJANGO_BASE, ROOT_PATH


ADMINROOT = '/{0}editor/'.format(DJANGO_BASE)
TESTFIXTURE_XML = '{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
TESTFIXTURE2_XML = '{}/repository/fixtures/ILSP10.xml'.format(ROOT_PATH)
TESTFIXTURE3_XML = '{}/repository/test_fixtures/META-SHARE/DFKI2.xml'.format(ROOT_PATH)
BROKENFIXTURE_XML = '{}/repository/fixtures/broken.xml'.format(ROOT_PATH)
TESTFIXTURES_ZIP = '{}/repository/fixtures/tworesources.zip'.format(ROOT_PATH)
BROKENFIXTURES_ZIP = '{}/repository/fixtures/onegood_onebroken.zip'.format(ROOT_PATH)
LEX_CONC_RES_XML = '{}/repository/test_fixtures/published-lexConcept-Text-FreEngGer.xml'.format(ROOT_PATH)


class EditorTest(TestCase):
    """
    Test the python/server side of the editor
    """
    # static variables to be initialized in setUpClass():
    test_editor_group = None
    staff_login = None
    normal_login = None
    editor_login = None
    manager_login = None
    testfixture = None
    testfixture2 = None
    testfixture3 = None

    @classmethod
    def import_test_resource(cls, editor_group=None, path=TESTFIXTURE_XML):
        test_utils.setup_test_storage()
        result = test_utils.import_xml(path)
        resource = result[0]
        if not editor_group is None:
            resource.editor_groups.add(editor_group)
            resource.save()
        return resource
    
    @classmethod
    def setUp(cls):
        """
        set up test users with and without staff permissions.
        These will live in the test database only, so will not
        pollute the "normal" development db or the production db.
        As a consequence, they need no valuable password.
        """
        EditorTest.test_editor_group = EditorGroup.objects.create(
                                                    name='test_editor_group')
        EditorTest.test_manager_group = \
            ManagerGroup.objects.create(name='test_manager_group',
                                    managed_group=EditorTest.test_editor_group)

        staffuser = User.objects.create_user('staffuser', 'staff@example.com',
          'secret')
        staffuser.is_staff = True
        staffuser.save()
        
        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

        editoruser = test_utils.create_editor_user('editoruser',
            'editor@example.com', 'secret', (EditorTest.test_editor_group,))

        test_utils.create_manager_user(
            'manageruser', 'manager@example.com', 'secret',
            (EditorTest.test_editor_group, EditorTest.test_manager_group))

        User.objects.create_superuser('superuser', 'su@example.com', 'secret')

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
        
        EditorTest.manager_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'manageruser',
            'password': 'secret',
        }
        
        EditorTest.superuser_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'superuser',
            'password': 'secret',
        }
        
        EditorTest.testfixture = cls.import_test_resource(
                                                EditorTest.test_editor_group)
        # second resource which is only visible by the superuser
        EditorTest.testfixture2 = cls.import_test_resource(None,
                                                           TESTFIXTURE2_XML)
        # third resource which is owned by the editoruser
        EditorTest.testfixture3 = cls.import_test_resource(None,
                                                           TESTFIXTURE3_XML)
        EditorTest.testfixture3.owners.add(editoruser)
        EditorTest.testfixture3.save()


    @classmethod
    def tearDown(cls):
        resourceInfoType_model.objects.all().delete()
        User.objects.all().delete()
        EditorGroup.objects.all().delete()


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

    def test_manage_action_visibility(self):
        """
        Verifies that manage actions (delete/ingest/publish/unpublish/add groups/
        remove groups/add owners/remove owners) are only visible for authorized users.
        """
        # make sure the editor user cannot see the manage actions:
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT + 'repository/resourceinfotype_model/')
        self.assertNotContains(response, 'Ingest selected internal resources',
            msg_prefix='an editor user must not see the "ingest" action')
        self.assertNotContains(response, 'Publish selected ingested resources',
            msg_prefix='an editor user must not see the "publish" action')
        self.assertNotContains(response, 'Unpublish selected published',
            msg_prefix='an editor user must not see the "unpublish" action')
        self.assertNotContains(response, 'Delete selected Resources',
            msg_prefix='an editor user must not see the "delete" action')
        self.assertNotContains(response, 'Add Editor Groups',
            msg_prefix='an editor user must not see the "add groups" action')
        self.assertNotContains(response, 'Remove Editor Groups',
            msg_prefix='an editor user must not see the "remove groups" action')
        self.assertNotContains(response, 'Add Owners',
            msg_prefix='an editor user must not see the "add owners" action')
        self.assertNotContains(response, 'Remove Owners',
            msg_prefix='an editor user must not see the "remove owners" action')
        # make sure the manager user can see the manage actions:
        client = self.client_with_user_logged_in(EditorTest.manager_login)
        response = client.get(ADMINROOT + 'repository/resourceinfotype_model/')
        self.assertContains(response, 'Ingest selected internal resources',
            msg_prefix='a manager user should see the "ingest" action')
        self.assertContains(response, 'Publish selected ingested resources',
            msg_prefix='a manager user should see the "publish" action')
        self.assertContains(response, 'Unpublish selected published resources',
            msg_prefix='a manager user should see the "unpublish" action')
        self.assertContains(response, 'Delete selected Resources',
            msg_prefix='a manager user should see the "delete" action')
        self.assertNotContains(response, 'Add Editor Groups',
            msg_prefix='a manager user must not see the "add groups" action')
        self.assertNotContains(response, 'Remove Editor Groups',
            msg_prefix='a manager user must not see the "remove groups" action')
        self.assertNotContains(response, 'Add Owners',
            msg_prefix='a manager user must not see the "add owners" action')
        self.assertNotContains(response, 'Remove Owners',
            msg_prefix='a manager user must not see the "remove owners" action')
        # make sure the manager user can see the manage actions in 'my resources':
        responseMy = client.get(ADMINROOT + 'repository/resourceinfotype_model/my/')
        self.assertContains(responseMy, 'Add Editor Groups',
            msg_prefix='a manager user should see the "add groups" action')
        self.assertContains(responseMy, 'Remove Editor Groups',
            msg_prefix='a manager user should see the "remove groups" action')
        self.assertContains(responseMy, 'Add Owners',
            msg_prefix='a manager user should see the "add owners" action')
        self.assertContains(responseMy, 'Remove Owners',
            msg_prefix='a manager user should see the "remove owners" action')
        
        # make sure the superuser can see the manage actions:
        client = self.client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get(ADMINROOT + 'repository/resourceinfotype_model/')
        self.assertContains(response, 'Ingest selected internal resources',
            msg_prefix='a superuser should see the "ingest" action')
        self.assertContains(response, 'Publish selected ingested resources',
            msg_prefix='a superuser should see the "publish" action')
        self.assertContains(response, 'Unpublish selected published resources',
            msg_prefix='a superuser should see the "unpublish" action')
        self.assertContains(response, 'Delete selected Resources',
            msg_prefix='a superuser should see the "delete" action')
        self.assertContains(response, 'Add Editor Groups',
            msg_prefix='a superuser should see the "add groups" action')
        self.assertContains(response, 'Remove Editor Groups',
            msg_prefix='a superuser should see the "remove groups" action')
        self.assertContains(response, 'Add Owners',
            msg_prefix='a superuser should see the "add owners" action')
        self.assertContains(response, 'Remove Owners',
            msg_prefix='a superuser should see the "remove owners" action')
        

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
        # And verify that we have more than zero resources on the page where we
        # are being redirected:
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
        resource = self.import_test_resource(EditorTest.test_editor_group,
                                             LEX_CONC_RES_XML)
        response = client.get('{}repository/lexicalconceptualresourceinfotype_model/{}/'.format(ADMINROOT, resource.resourceComponentType.id))
        self.assertNotContains(response, ' Lexical conceptual resource media</',
                               msg_prefix='Hidden fields must not be visible in fieldset labels.')

    def test_validator_is_multiwidget(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, '<select onchange="javascript:createNewSubInstance($(this), &quot;add_id_validationinfotype_model_set',
                            msg_prefix='Validator is not rendered as a ChoiceTypeWidget')

    def test_resources_list(self):
        # test with editor user
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/')
        self.assertContains(response, '2 Resources')
        # test with superuser
        client = self.client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/')
        self.assertContains(response, '3 Resources')
        
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
        resource.storage_object.save()
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, resource.storage_object.id))
        self.assertContains(response, "Change Resource")        
        
    def test_cannot_edit_not_master_copy(self):
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        resource = self.import_test_resource()
        resource.storage_object.master_copy = False
        resource.storage_object.save()
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, resource.storage_object.id))
        self.assertContains(response, "You cannot edit the metadata")

    def test_editor_can_change_own_resource_and_parts(self):
        """
        Verifies that the editor user can change his own resources and parts
        thereof.
        """
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        # (1) editor is owner of the resource
        self._test_user_can_change_resource_and_parts(client,
                                                      EditorTest.testfixture3)
        # (2) resource belongs to an editor group of the editor
        self._test_user_can_change_resource_and_parts(client,
                                                      EditorTest.testfixture)

    def _test_user_can_change_resource_and_parts(self, client, res):
        """
        Verifies that the logged in user in the given client can change the
        given resource and parts thereof.
        """
        # make sure the editor may change the resource:
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, res.id))
        self.assertContains(response, '>Change Resource<', msg_prefix=
            'expected the user to be allowed to change the resource')
        # make sure the editor may change some part of the resource:
        response = client.get('{}repository/distributioninfotype_model/{}/'
                .format(ADMINROOT, res.distributionInfo.id))
        self.assertContains(response, '>Change Distribution<', msg_prefix=
            'expected the user to be allowed to change parts of the resource')

    def test_editor_cannot_change_non_owned_resource_and_parts(self):
        """
        Verifies that the editor user can neither change non-owned resources nor
        parts thereof.
        """
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        # make sure the editor may not change the resource:
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, EditorTest.testfixture2.id))
        self.assertIn(response.status_code, (403, 404), msg=
            'expected the editor to not be allowed to change the resource')
        # make sure the editor may not change some part of the resource:
        response = client.get('{}repository/distributioninfotype_model/{}/'
                .format(ADMINROOT, EditorTest.testfixture2.distributionInfo.id))
        self.assertIn(response.status_code, (403, 404), msg=
            'expected the editor to not be allowed to change resource parts')

    def test_editor_cannot_delete_any_resources_or_parts(self):
        """
        Verifies that the editor user can neither delete any resources nor any
        parts thereof.
        """
        client = self.client_with_user_logged_in(EditorTest.editor_login)
        # make sure the editor may not delete any resources:
        response = client.get('{}repository/resourceinfotype_model/{}/delete/'
                              .format(ADMINROOT, EditorTest.testfixture2.id))
        self.assertIn(response.status_code, (403, 404), msg=
            'expected the editor to not be allowed to delete the resource')
        # make sure the editor may not delete any part of a resource:
        response = client.get(
            '{}repository/distributioninfotype_model/{}/delete/'
                .format(ADMINROOT, EditorTest.testfixture2.distributionInfo.id))
        self.assertIn(response.status_code, (403, 404), msg=
            'expected the editor to not be allowed to delete resource parts')

    def test_superuser_can_change_all_resources_and_their_parts(self):
        """
        Verifies that the superuser can change all resources and their parts,
        irrespective of ownership.
        """
        client = self.client_with_user_logged_in(EditorTest.superuser_login)
        self._test_user_can_change_resource_and_parts(client,
                                                      EditorTest.testfixture)
        self._test_user_can_change_resource_and_parts(client,
                                                      EditorTest.testfixture2)
        self._test_user_can_change_resource_and_parts(client,
                                                      EditorTest.testfixture3)

    def test_superuser_can_delete_all_resources_and_their_parts(self):
        """
        Verifies that the superuser can delete all resources and their parts,
        irrespective of ownership.
        """
        client = self.client_with_user_logged_in(EditorTest.superuser_login)
        self._test_superuser_can_delete_resource_and_its_parts(client,
                                                        EditorTest.testfixture)
        self._test_superuser_can_delete_resource_and_its_parts(client,
                                                        EditorTest.testfixture2)
        self._test_superuser_can_delete_resource_and_its_parts(client,
                                                        EditorTest.testfixture3)

    def _test_superuser_can_delete_resource_and_its_parts(self, client, res):
        """
        Verifies that the superuser logged into the given client can delete the
        given resource and its parts.
        """
        # make sure the superuser may delete any resources:
        response = client.get('{}repository/resourceinfotype_model/{}/delete/'
                              .format(ADMINROOT, res.id))
        self.assertContains(response, 'Are you sure?', msg_prefix=
            'expected the superuser to be allowed to delete the resource')
        # make sure the superuser may delete any part of a resource:
        response = client.get(
            '{}repository/distributioninfotype_model/{}/delete/'
                .format(ADMINROOT, res.id))
        self.assertContains(response, 'Are you sure?', msg_prefix=
            'expected the superuser to be allowed to delete resource parts')  