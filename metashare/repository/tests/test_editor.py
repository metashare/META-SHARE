# -*- coding: utf-8 -*-
import logging
import shutil
import django.db.models

from django.contrib import admin
from django.contrib.admin.sites import LOGIN_FORM_KEY
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.utils.encoding import force_unicode
from metashare import test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers, \
    EditorGroupApplication, Organization, OrganizationManagers, \
    OrganizationApplication
from metashare.repository import models
from metashare.repository.editor.lookups import PersonLookup, ActorLookup, \
    DocumentationLookup, DocumentLookup, ProjectLookup, OrganizationLookup, \
    TargetResourceLookup
from metashare.repository.models import languageDescriptionInfoType_model, \
    lexicalConceptualResourceInfoType_model, personInfoType_model,\
    resourceInfoType_model
from metashare.settings import DJANGO_BASE, ROOT_PATH, LOG_HANDLER
from metashare.storage.models import PUBLISHED, INGESTED, INTERNAL, REMOTE, \
    StorageObject
from selectable.views import get_lookup

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

ADMINROOT = '/{0}editor/'.format(DJANGO_BASE)
TESTFIXTURE_XML = '{}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
TESTFIXTURE2_XML = '{}/repository/fixtures/ILSP10.xml'.format(ROOT_PATH)
TESTFIXTURE3_XML = '{}/repository/test_fixtures/META-SHARE/DFKI2.xml'.format(ROOT_PATH)
TESTFIXTURE4_XML = '{}/repository/test_fixtures/META-SHARE/FBK16.xml'.format(ROOT_PATH)
BROKENFIXTURE_XML = '{}/repository/fixtures/broken.xml'.format(ROOT_PATH)
TESTFIXTURES_ZIP = '{}/repository/fixtures/tworesources.zip'.format(ROOT_PATH)
BROKENFIXTURES_ZIP = '{}/repository/fixtures/onegood_onebroken.zip'.format(ROOT_PATH)
LEX_CONC_RES_XML = '{}/repository/test_fixtures/published-lexConcept-Audio-EnglishGerman.xml'.format(ROOT_PATH)
DATA_UPLOAD_ZIP = '{}/repository/fixtures/data_upload_test.zip'.format(ROOT_PATH)
DATA_UPLOAD_ZIP_2 = '{}/repository/fixtures/data_upload_test_2.zip'.format(ROOT_PATH)
COMPLETION_XML = '{}/repository/fixtures/completiontestfixture.xml'.format(ROOT_PATH)


def _import_test_resource(editor_group=None, path=TESTFIXTURE_XML,
                          pub_status=INGESTED):
    resource = test_utils.import_xml(path)
    if not editor_group is None:
        resource.editor_groups.add(editor_group)
        resource.save()
    resource.storage_object.publication_status = pub_status
    resource.storage_object.save()
    return resource


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
    superuser_login = None
    testfixture = None
    testfixture2 = None
    testfixture3 = None
    testfixture4 = None
    
    @classmethod
    def setUpClass(cls):
        """
        set up test users with and without staff permissions.
        These will live in the test database only, so will not
        pollute the "normal" development db or the production db.
        As a consequence, they need no valuable password.
        """
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)
        test_utils.setup_test_storage()

        EditorTest.test_editor_group = EditorGroup.objects.create(
                                                    name='test_editor_group')
        
        EditorTest.test_editor_group_manager = \
            EditorGroupManagers.objects.create(name='test_editor_group_manager',
                                    managed_group=EditorTest.test_editor_group)
        EditorGroupManagers.objects.create(name='test_editor_group_manager_2', managed_group=
                EditorGroup.objects.create(name='test_editor_group_2'))

        staffuser = User.objects.create_user('staffuser', 'staff@example.com',
          'secret')
        staffuser.is_staff = True
        staffuser.save()
        
        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

        editoruser = test_utils.create_editor_user('editoruser',
            'editor@example.com', 'secret', (EditorTest.test_editor_group,))

        test_utils.create_manager_user(
            'manageruser', 'manager@example.com', 'secret',
            (EditorTest.test_editor_group, EditorTest.test_editor_group_manager))

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
        
        EditorTest.testfixture = _import_test_resource(
                                                EditorTest.test_editor_group)
        # second resource which is only visible by the superuser
        EditorTest.testfixture2 = _import_test_resource(None, TESTFIXTURE2_XML)
        # third resource which is owned by the editoruser
        EditorTest.testfixture3 = _import_test_resource(None, TESTFIXTURE3_XML,
                                                        pub_status=PUBLISHED)
        EditorTest.testfixture3.owners.add(editoruser)
        EditorTest.testfixture3.save()
        # fourth test resource which is owned by the editor user
        EditorTest.testfixture4 = _import_test_resource(
            EditorTest.test_editor_group, TESTFIXTURE4_XML, pub_status=INTERNAL)
        EditorTest.testfixture4.owners.add(editoruser)
        EditorTest.testfixture4.save()


    @classmethod
    def tearDownClass(cls):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))


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
        self.assertContains(login, 'Please enter the correct username and password', status_code=200)
           
    def test_editor_can_see_model_list(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+'repository/')
        self.assertContains(response, 'Repository administration')
       
    def test_staff_cannot_see_model_list(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.staff_login)
        response = client.get(ADMINROOT+'repository/')
        self.assertContains(response, 'Page not Found', status_code=404)

    def test_editor_can_see_resource_add(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+"repository/resourceinfotype_model/add/", follow=True)
        self.assertContains(response, 'Add Resource')

    def test_staff_cannot_see_resource_add(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.staff_login)
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/add/', follow=True)
        self.assertContains(response, 'User Authentication', status_code=200)

    def test_editor_can_see_corpus_add(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+"repository/corpusinfotype_model/add/", follow=True)
        self.assertEquals(200, response.status_code)

    def test_staff_cannot_see_corpus_add(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.staff_login)
        response = client.get(ADMINROOT+'repository/corpusinfotype_model/add/')
        self.assertContains(response, '403 Forbidden', status_code=403)

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
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
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
                            LOGGER.debug("For class %s, trying to access page "
                                         "%s ...", cls_name, url)
                            response = client.get(url, follow=True)
                            self.assertEquals(200, response.status_code)
                            num = num + 1
                        else:
                            LOGGER.debug('Class %s has no registered admin '
                                         'form.', cls_name)
        LOGGER.debug('Checked models: %d', num)

    def test_manage_action_visibility(self):
        """
        Verifies that manage actions (delete/ingest/publish/unpublish/add groups/
        remove groups/add owners/remove owners) are only visible for authorized users.
        """
        # make sure the editor user cannot see the manage actions:
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT + 'repository/resourceinfotype_model/')
        self.assertNotContains(response, 'Ingest selected internal resources',
            msg_prefix='an editor user must not see the "ingest" action')
        self.assertNotContains(response, 'Publish selected ingested resources',
            msg_prefix='an editor user must not see the "publish" action')
        self.assertNotContains(response, 'Unpublish selected published',
            msg_prefix='an editor user must not see the "unpublish" action')
        self.assertNotContains(response, 'Mark selected resources as deleted',
            msg_prefix='an editor user must not see the "delete" action')
        self.assertNotContains(response, 'value="add_group">Add editor groups',
            msg_prefix='an editor user must not see the "add groups" action')
        self.assertNotContains(response,
            'value="remove_group">Remove editor groups from selected',
            msg_prefix='an editor user must not see the "remove groups" action')
        self.assertNotContains(response, 'Add owners',
            msg_prefix='an editor user must not see the "add owners" action')
        self.assertNotContains(response, 'Remove owners',
            msg_prefix='an editor user must not see the "remove owners" action')
        # make sure the manager user can see the manage actions in 'my resources':
        response_my = client.get(ADMINROOT + 'repository/resourceinfotype_model/my/')
        self.assertContains(response_my, 'Add editor groups',
            msg_prefix='a manager user should see the "add groups" action')
        self.assertContains(response_my, 'Add owners',
            msg_prefix='a manager user should see the "add owners" action')
        # make sure the manager user can see the manage actions:
        client = test_utils.get_client_with_user_logged_in(EditorTest.manager_login)
        response = client.get(ADMINROOT + 'repository/resourceinfotype_model/')
        self.assertContains(response, 'Ingest selected internal resources',
            msg_prefix='a manager user should see the "ingest" action')
        self.assertContains(response, 'Publish selected ingested resources',
            msg_prefix='a manager user should see the "publish" action')
        self.assertContains(response, 'Unpublish selected published resources',
            msg_prefix='a manager user should see the "unpublish" action')
        self.assertContains(response, 'Mark selected resources as deleted',
            msg_prefix='a manager user should see the "delete" action')
        self.assertNotContains(response, 'value="add_group">Add editor groups',
            msg_prefix='a manager user must not see the "add groups" action')
        self.assertNotContains(response, 
            'value="remove_group">Remove editor groups from selected',
            msg_prefix='a manager user must not see the "remove groups" action')
        self.assertNotContains(response, 'Add owners',
            msg_prefix='a manager user must not see the "add owners" action')
        self.assertNotContains(response, 'Remove owners',
            msg_prefix='a manager user must not see the "remove owners" action')
        # make sure the editor user can see the relevant manage actions in 'my
        # 'resources':
        self.assertContains(response_my, 'Add owners',
            msg_prefix='an editor user should see the "add owners" action')
        # make sure the superuser can see the manage actions:
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get(ADMINROOT + 'repository/resourceinfotype_model/')
        self.assertContains(response, 'Ingest selected internal resources',
            msg_prefix='a superuser should see the "ingest" action')
        self.assertContains(response, 'Publish selected ingested resources',
            msg_prefix='a superuser should see the "publish" action')
        self.assertContains(response, 'Unpublish selected published resources',
            msg_prefix='a superuser should see the "unpublish" action')
        self.assertContains(response, 'Mark selected resources as deleted',
            msg_prefix='a superuser should see the "delete" action')
        self.assertContains(response, 'value="add_group">Add editor groups',
            msg_prefix='a superuser should see the "add groups" action')
        self.assertContains(response, 
            'value="remove_group">Remove editor groups from selected',
            msg_prefix='a superuser should see the "remove groups" action')
        self.assertContains(response, 'Add owners',
            msg_prefix='a superuser should see the "add owners" action')
        self.assertContains(response, 'Remove owners',
            msg_prefix='a superuser should see the "remove owners" action')

    def test_enough_editing_time_before_session_expiry(self):
        """
        Verifies that a user always has enough time for editing a resource or
        reusable entity before there is a session timeout.
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        # test that there is enough time when adding a shared object
        self._test_enough_editing_time_before_session_expiry(client,
            'organizationinfotype_model/add/',
            'A user must have more than one day time for adding an entity.')
        # test that there is enough time when editing a shared object
        self._test_enough_editing_time_before_session_expiry(client,
            'personinfotype_model/{}/'.format(
                EditorTest.testfixture3.contactPerson.all()[0].id),
            'A user must have more than one day time for editing an entity.')
        # test that there is enough time when adding a (tool/service) resource
        _session = client.session
        _session.set_expiry(5)
        _session.save()
        # when accessing the (actual) resource editor, the expiration time for
        # the session is expected to be a lot higher again than one day
        client.post('{}repository/resourceinfotype_model/add/'
                    .format(ADMINROOT), {'resourceType': 'toolservice'})
        self.assertLess(86400, client.session.get_expiry_age(),
            'A user must have more than one day time for adding a resource.')
        # test that there is enough time when editing a resource
        self._test_enough_editing_time_before_session_expiry(client,
            'resourceinfotype_model/{}/'.format(EditorTest.testfixture3.id),
            'A user must have more than one day time for editing a resource.')

    def _test_enough_editing_time_before_session_expiry(self, client, url_tail,
                                                        fail_msg):
        """
        Verifies that the user logged in with the given client always has more
        than one day time for editing the model instance with the editor URL
        ending in the given `url_tail`.
        
        The given failure message is used if the test fails.
        """
        # set an expiration time for the session of just 5 seconds
        _session = client.session
        _session.set_expiry(5)
        _session.save()
        # when accessing the editor, the expiration time for the session is
        # expected to be a lot higher again (i.e., more than one day)
        client.get('{}repository/{}'.format(ADMINROOT, url_tail))
        self.assertLess(86400, client.session.get_expiry_age(), fail_msg)

    def test_upload_single_xml(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(TESTFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded file')
        
    def test_upload_broken_xml(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(BROKENFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Import failed', msg_prefix='response: {0}'.format(response))
        
    def test_upload_single_xml_unchecked(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(TESTFIXTURE_XML)
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile }, follow=True)
        self.assertFormError(response, 'form', 'uploadTerms', 'This field is required.')
    
    def test_upload_zip(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(TESTFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 2 resource descriptions')
        self.assertNotContains(response, 'Import failed')
        # And verify that we have more than zero resources on the page where we
        # are being redirected:
        self.assertContains(response, "My Resources")
        self.assertNotContains(response, '0 Resources')

    def test_upload_broken_zip(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        xmlfile = open(BROKENFIXTURES_ZIP, 'rb')
        response = client.post(ADMINROOT+'upload_xml/', {'description': xmlfile, 'uploadTerms':'on' }, follow=True)
        self.assertContains(response, 'Successfully uploaded 1 resource descriptions')
        self.assertContains(response, 'Import failed for 1 files')
        
    def test_identification_is_inline(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        # Resource name is a field of identification, so if this is present, identification is shown inline:
        self.assertContains(response, "Resource name:", msg_prefix='Identification is not shown inline')
        
    def test_one2one_distribution_is_hidden(self):
        """
        Asserts that a required OneToOneField referring to models that "contain"
        one2many fields is hidden, i.e., the model is edited in a popup/overlay.
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
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
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
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
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
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
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/' \
                              .format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'related-widget-wrapper-change-link" ' \
                                'id="edit_id_usageInfo"',
                msg_prefix='Recommended One-to-one field "usageInfo" not ' \
                    'rendered using related widget, although it contains ' \
                    'a One-to-Many field.')

    def test_licenceinfo_inline_is_present(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/distributioninfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.distributionInfo.id))
        self.assertContains(response, '<div class="inline-group" id="licenceinfotype_model_set-group">',
                            msg_prefix='expected licence info inline')
        

    def test_one2one_sizepervalidation_is_hidden(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'type="hidden" id="id_validationinfotype_model_set-0-sizePerValidation"',
                             msg_prefix='One-to-one field "sizePerValidation" should have been hidden')

    def test_one2one_sizepervalidation_uses_related_widget(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'related-widget-wrapper-change-link" id="edit_id_validationinfotype_model_set-0-sizePerValidation"',
                            msg_prefix='One-to-one field "sizePerValidation" not rendered using related widget')
        self.assertContains(response, 'id="id_validationinfotype_model_set-0-sizePerValidation"',
                            msg_prefix='One2one field in inline has unexpected "id" field -- popup save action probably cannot update field as expected')

    def test_backref_is_hidden(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        corpustextinfo = EditorTest.testfixture.resourceComponentType.corpusMediaType.corpustextinfotype_model_set.all()[0]
        response = client.get('{}repository/corpustextinfotype_model/{}/'.format(ADMINROOT, corpustextinfo.id))
        self.assertContains(response, 'type="hidden" name="back_to_corpusmediatypetype_model"',
                            msg_prefix='Back reference should have been hidden')

    def test_linguality_inline_is_present(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        corpustextinfo = EditorTest.testfixture.resourceComponentType.corpusMediaType.corpustextinfotype_model_set.all()[0]
        response = client.get('{}repository/corpustextinfotype_model/{}/'.format(ADMINROOT, corpustextinfo.id))
        self.assertContains(response, '<div class="form-row lingualityType">',
                            msg_prefix='expected linguality inline')

    def test_hidden_field_is_not_referenced_in_fieldset_label(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        resource = _import_test_resource(EditorTest.test_editor_group,
                                         LEX_CONC_RES_XML)
        response = client.get('{}repository/lexicalconceptualresourceinfotype_model/{}/'.format(ADMINROOT, resource.resourceComponentType.id))
        self.assertNotContains(response, ' Lexical conceptual resource media</',
                               msg_prefix='Hidden fields must not be visible in fieldset labels.')

    def test_validator_is_multiwidget(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, '<select onchange="javascript:createNewSubInstance($(this), &quot;add_id_validationinfotype_model_set',
                            msg_prefix='Validator is not rendered as a ChoiceTypeWidget')

    def test_resources_list(self):
        # test with editor user
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/')
        self.assertContains(response, '3 Resources')
        # test with superuser
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/')
        self.assertContains(response, '4 Resources')
        
    def test_myresources_list(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)            
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/my/')            
        self.assertContains(response, '2 Resource')

    def test_storage_object_is_hidden(self):
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        response = client.get('{}repository/resourceinfotype_model/{}/'.format(ADMINROOT, EditorTest.testfixture.id))
        self.assertContains(response, 'type="hidden" name="storage_object"',
                            msg_prefix='Expected a hidden storage object')

    def test_editor_can_delete_annotationInfo(self):
        editoruser = User.objects.get(username='editoruser')
        self.assertTrue(editoruser.has_perm('repository.delete_annotationinfotype_model'))

    def test_editor_cannot_delete_actorInfo(self):
        editoruser = User.objects.get(username='editoruser')
        self.assertFalse(editoruser.has_perm('repository.delete_actorinfotype_model'))

    def test_can_edit_resource_master_copy(self):        
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        resource = _import_test_resource(EditorTest.test_editor_group)
        resource.storage_object.master_copy = True
        resource.storage_object.save()
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, resource.id))
        self.assertContains(response, "Change Resource")        
        self.assertContains(response, "Italian TTS Speech Corpus")
        
    def test_can_edit_reusable_entity_master_copy(self):        
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        _import_test_resource(EditorTest.test_editor_group)
        response = client.get('{}repository/personinfotype_model/{}/'
                              .format(ADMINROOT, personInfoType_model.objects.all()[0].id))
        self.assertContains(response, "Change Person")    
    
    def test_editor_can_change_own_resource_and_parts(self):
        """
        Verifies that the editor user can change his own resources and parts
        thereof.
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
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
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
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

    def test_editor_cannot_delete_any_parts_or_non_internal_resources(self):
        """
        Verifies that the editor user can neither delete any non-internal
        resources nor any parts of any resources.
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.editor_login)
        # make sure the editor may not delete any ingested resources:
        response = client.get('{}repository/resourceinfotype_model/{}/delete/'
                              .format(ADMINROOT, EditorTest.testfixture2.id))
        self.assertIn(response.status_code, (403, 404), msg='expected that ' \
                'the editor is not allowed to delete an ingested resource')
        # make sure the editor may not delete any published resources:
        response = client.get('{}repository/resourceinfotype_model/{}/delete/'
                              .format(ADMINROOT, EditorTest.testfixture3.id))
        self.assertIn(response.status_code, (403, 404), msg='expected that ' \
                'the editor is not allowed to delete a published resource')
        # make sure the editor may not delete any part of non-internal resources
        response = client.get(
            '{}repository/distributioninfotype_model/{}/delete/'
                .format(ADMINROOT, EditorTest.testfixture2.distributionInfo.id))
        self.assertIn(response.status_code, (403, 404), msg='expected the ' \
                'editor to not be allowed to delete any resource parts')
        # make sure the editor may not delete any part of internal resources:
        response = client.get(
            '{}repository/distributioninfotype_model/{}/delete/'
                .format(ADMINROOT, EditorTest.testfixture4.distributionInfo.id))
        self.assertIn(response.status_code, (403, 404), msg="expected the " \
                "editor to not be allowed to delete internal resource' parts")

    def test_superuser_can_change_all_resources_and_their_parts(self):
        """
        Verifies that the superuser can change all resources and their parts,
        irrespective of ownership.
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
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
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
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

    def test_editor_can_delete_owned_internal_resources(self):
        """
        Verifies that an editor user can delete owned resources that have
        "internal" as publication status.
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        # make sure the superuser may delete any resources:
        response = client.get('{}repository/resourceinfotype_model/{}/delete/'
                              .format(ADMINROOT, EditorTest.testfixture4.id))
        self.assertContains(response, 'Are you sure?', msg_prefix='expected ' \
                'that the editor user may delete his own internal resource')

    def test_only_superuser_sees_editor_groups_list(self):
        """
        Verifies that only a superuser sees the editor groups list (with all
        editor groups).
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get('{}accounts/editorgroup/'.format(ADMINROOT))
        self.assertContains(response, '0 of 2 selected',
            msg_prefix='expected the superuser to see all editor groups')
        client = test_utils.get_client_with_user_logged_in(EditorTest.manager_login)
        response = client.get('{}accounts/editorgroup/'.format(ADMINROOT))
        self.assertIn(response.status_code, (403, 404),
            'expected that a manager user does not see the editor groups list')

    def test_superuser_sees_editor_group_manage_actions(self):
        """
        Verifies that a superuser sees all editor group manage actions.
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get('{}accounts/editorgroup/'.format(ADMINROOT))
        self.assertContains(response, 'Add users to selected editor groups',
            msg_prefix='a superuser must see the add editor group action')
        self.assertContains(response, 'Delete selected editor groups',
            msg_prefix='a superuser must see the delete editor group action')
        self.assertContains(response, 'Remove users from selected editor group',
            msg_prefix='a superuser must see the remove editor group action')

    def test_superuser_allowed_to_delete_editor_group(self):
        """
        Verifies that an editor group is removed from all relevant resources
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get('{}accounts/editorgroup/{}/delete/'
                              .format(ADMINROOT, EditorTest.test_editor_group.id))
        self.assertContains(response, 'Are you sure?', msg_prefix=
            'expected the superuser to be allowed to delete editor')

    def test_only_superuser_sees_editor_group_managers_list(self):
        """
        Verifies that only a superuser sees the editor group managers list (with
        all editor group managers).
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get('{}accounts/editorgroupmanagers/'.format(ADMINROOT))
        self.assertContains(response, '0 of 2 selected',
            msg_prefix='expected the superuser to see all editor group managers')
        client = test_utils.get_client_with_user_logged_in(EditorTest.manager_login)
        response = client.get('{}accounts/editorgroupmanagers/'.format(ADMINROOT))
        self.assertIn(response.status_code, (403, 404),
            'expected that a manager user does not see the editor group managers list')

    def test_superuser_sees_editor_group_manager_manage_actions(self):
        """
        Verifies that a superuser sees all editor group manager manage actions.
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get('{}accounts/editorgroupmanagers/'.format(ADMINROOT))
        self.assertContains(response, 'Add users to selected editor group managers',
            msg_prefix='a superuser must see the add editor group manager action')
        self.assertContains(response, 'Delete selected editor group managers',
            msg_prefix='a superuser must see the delete editor group manager action')
        self.assertContains(response, 'Remove users from selected editor group manager',
            msg_prefix='a superuser must see the remove editor group manager action')

    def test_superuser_allowed_to_delete_editor_group_manager(self):
        """
        Verifies that an editor group manager is removed from all relevant users
        """
        client = test_utils.get_client_with_user_logged_in(EditorTest.superuser_login)
        response = client.get('{}accounts/editorgroupmanagers/{}/delete/'
                              .format(ADMINROOT, EditorTest.test_editor_group_manager.id))
        self.assertContains(response, 'Are you sure?', msg_prefix=
            'expected the superuser to be allowed to delete manager')

class LookupTest(TestCase):
    """
    Test the lookup functionalities
    """
    # static variables to be initialized in setUpClass():
    editor_login = None
    testfixture = None
    client = None
    
    @classmethod
    def setUpClass(cls):
        """
        set up test editor user with staff permissions.
        These will live in the test database only, so will not
        pollute the "normal" development db or the production db.
        As a consequence, they need no valuable password.
        """
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)
        test_utils.setup_test_storage()

        test_editor_group = EditorGroup.objects.create(name='test_editor_group')
        
        EditorGroupManagers.objects.create(name='test_editor_group_manager',
          managed_group=test_editor_group)

        test_utils.create_editor_user('editoruser',
            'editor@example.com', 'secret', (test_editor_group,))

        LookupTest.editor_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'editoruser',
            'password': 'secret',
        }
        
        LookupTest.testfixture = _import_test_resource(test_editor_group, COMPLETION_XML)

        LookupTest.client = test_utils.get_client_with_user_logged_in(LookupTest.editor_login)

    @classmethod
    def tearDownClass(cls):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def test_editor_autocompletion_for_person(self):
        """
        Verifies that the auto-completion works for PersonLookup.
        """
        lookup = PersonLookup
        test_term = "val"
        # now the manual auto-completion lookup call with a test term:
        response = LookupTest.client.get(reverse(get_lookup, args=(force_unicode(lookup.name()),)), {'term': test_term})
        self.assertContains(response, 'Valérie Mapelli',
            msg_prefix='a superuser must see the lookup for Person.')

    def test_editor_autocompletion_for_actor(self):
        """
        Verifies that the auto-completion works for ActorLookup.
        """
        lookup = ActorLookup
        test_term = "val"
        # now the manual auto-completion lookup call with a test term:
        response = LookupTest.client.get(reverse(get_lookup, args=(force_unicode(lookup.name()),)), {'term': test_term})
        self.assertContains(response, 'Valérie Mapelli',
            msg_prefix='a superuser must see the lookup for Actor.')

    def test_editor_autocompletion_for_documentation(self):
        """
        Verifies that the auto-completion works for DocumentationLookup.
        """
        lookup = DocumentationLookup
        test_term = "SMP"
        # now the manual auto-completion lookup call with a test term:
        response = LookupTest.client.get(reverse(get_lookup, args=(force_unicode(lookup.name()),)), {'term': test_term})
        self.assertContains(response, 'SMP_E0021_TRS_AUTO.pdf',
            msg_prefix='a superuser must see the lookup for Documentation.')

    def test_editor_autocompletion_for_document(self):
        """
        Verifies that the auto-completion works for DocumentLookup.
        """
        lookup = DocumentLookup
        test_term = "SMP"
        # now the manual auto-completion lookup call with a test term:
        response = LookupTest.client.get(reverse(get_lookup, args=(force_unicode(lookup.name()),)), {'term': test_term})
        self.assertContains(response, 'SMP_E0021_TRS_AUTO.pdf',
            msg_prefix='a superuser must see the lookup for Document.')

    def test_editor_autocompletion_for_project(self):
        """
        Verifies that the auto-completion works for ProjectLookup.
        """
        lookup = ProjectLookup
        test_term = "ver"
        # now the manual auto-completion lookup call with a test term:
        response = LookupTest.client.get(reverse(get_lookup, args=(force_unicode(lookup.name()),)), {'term': test_term})
        self.assertContains(response, 'Verbmobil II',
            msg_prefix='a superuser must see the lookup for Project.')

    def test_editor_autocompletion_for_Organization(self):
        """
        Verifies that the auto-completion works for OrganizationLookup.
        """
        lookup = OrganizationLookup
        test_term = "lan"
        # now the manual auto-completion lookup call with a test term:
        response = LookupTest.client.get(reverse(get_lookup, args=(force_unicode(lookup.name()),)), {'term': test_term})
        self.assertContains(response, 'Evaluations and Language Resources Distribution Agency',
            msg_prefix='a superuser must see the lookup for Organization.')
            
    def test_editor_autocompletion_for_targetresource(self):
        """
        Verifies that the auto-completion works for TargetResourceLookup.
        """
        lookup = TargetResourceLookup
        test_term = "proj"
        # now the manual auto-completion lookup call with a test term:
        response = LookupTest.client.get(reverse(get_lookup, args=(force_unicode(lookup.name()),)), {'term': test_term})
        self.assertContains(response, 'Nice project',
            msg_prefix='a superuser must see the lookup for TargetResource.')


class DataUploadTests(TestCase):
    """
    Tests related to uploading actual resource data for a pure resource
    description.
    """
    # static variables to be initialized in setUpClass():
    test_editor_group = None
    editor_user = None
    editor_login = None
    superuser_login = None
    testfixture = None
    testfixture2 = None
    testfixture3 = None
    testfixture4 = None
    
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)

        DataUploadTests.test_editor_group = \
            EditorGroup.objects.create(name='test_editor_group')

        # test user accounts
        DataUploadTests.editor_user = test_utils.create_editor_user(
            'editoruser', 'editor@example.com', 'secret',
            (DataUploadTests.test_editor_group,))
        superuser = User.objects.create_superuser(
            'superuser', 'su@example.com', 'secret')

        # login POST dicts
        DataUploadTests.editor_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': DataUploadTests.editor_user.username,
            'password': 'secret',
        }
        DataUploadTests.superuser_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': superuser.username,
            'password': 'secret',
        }

    @classmethod
    def tearDownClass(cls):
        test_utils.clean_user_db()
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def setUp(self):
        test_utils.setup_test_storage()
        # first test resource
        DataUploadTests.testfixture = \
            _import_test_resource(DataUploadTests.test_editor_group)
        # second test resource which is only visible by the superuser
        DataUploadTests.testfixture2 = \
            _import_test_resource(None, TESTFIXTURE2_XML)
        # third test resource which is owned by the editoruser
        DataUploadTests.testfixture3 = \
            _import_test_resource(None, TESTFIXTURE3_XML, pub_status=PUBLISHED)
        DataUploadTests.testfixture3.owners.add(DataUploadTests.editor_user)
        DataUploadTests.testfixture3.save()
        # fourth test resource which is owned by the editor user
        DataUploadTests.testfixture4 = _import_test_resource(
            DataUploadTests.test_editor_group, TESTFIXTURE4_XML,
            pub_status=INTERNAL)
        DataUploadTests.testfixture4.owners.add(DataUploadTests.editor_user)
        DataUploadTests.testfixture4.save()

    def tearDown(self):
        # we have to clean up both the resources DB and the storage folder as
        # uploads change the storage folder
        test_utils.clean_resources_db()
        test_utils.clean_storage()

    def test_superuser_can_always_upload_data(self):
        """
        Verifies that a superuser may upload actual resource data to any
        resource.
        """
        client = test_utils.get_client_with_user_logged_in(
            DataUploadTests.superuser_login)
        for res in (DataUploadTests.testfixture, DataUploadTests.testfixture2,
                    DataUploadTests.testfixture3, DataUploadTests.testfixture4):
            self.assertFalse(res.storage_object.get_download(),
                "the test LR must not have a local download before the test")
            _data_upload_url = "{}repository/resourceinfotype_model/{}/" \
                "upload-data/".format(ADMINROOT, res.id)
            response = client.get(_data_upload_url)
            self.assertEquals(200, response.status_code, "expected that a " \
                              "superuser may always upload resource data")
            with open(DATA_UPLOAD_ZIP, 'rb') as _fhandle:
                response = client.post(_data_upload_url,
                    {'uploadTerms': 'on', 'resource': _fhandle}, follow=True)
                self.assertContains(response, "was changed successfully.")
            # refetch the storage object from the data base to make sure we have
            # the latest version
            _so = StorageObject.objects.get(pk=res.storage_object.pk)
            self.assertTrue(_so.get_download(),
                "uploaded LR data must be available as a local download")

    def test_editor_can_upload_data(self):
        """
        Verifies that an editor user may upload actual resource data to owned
        resources and to resources that are in her editor group.
        """
        client = test_utils.get_client_with_user_logged_in(
            DataUploadTests.editor_login)
        # make sure data can be uploaded to owned resources:
        self.assertFalse(DataUploadTests.testfixture3.storage_object \
                .get_download(),
            "the test LR must not have a local download before the test")
        _data_upload_url = "{}repository/resourceinfotype_model/{}/" \
            "upload-data/".format(ADMINROOT, DataUploadTests.testfixture3.id)
        response = client.get(_data_upload_url)
        self.assertEquals(200, response.status_code, "expected that an " \
                          "editor may upload resource data to owned resources")
        with open(DATA_UPLOAD_ZIP, 'rb') as _fhandle:
            response = client.post(_data_upload_url,
                {'uploadTerms': 'on', 'resource': _fhandle}, follow=True)
            self.assertContains(response, "was changed successfully.")
        # refetch the storage object from the data base to make sure we have
        # the latest version
        _so = StorageObject.objects.get(
            pk=DataUploadTests.testfixture3.storage_object.pk)
        self.assertTrue(_so.get_download(),
            "expected that uploaded LR data is available as a local download")
        # make sure data can be uploaded to editable resources:
        self.assertFalse(
            DataUploadTests.testfixture.storage_object.get_download(),
            "the test LR must not have a local download before the test")
        _data_upload_url = "{}repository/resourceinfotype_model/{}/" \
            "upload-data/".format(ADMINROOT, DataUploadTests.testfixture.id)
        response = client.get(_data_upload_url)
        self.assertEquals(200, response.status_code, "expected that an " \
            "editor may upload resource data to resources of her editor group")
        with open(DATA_UPLOAD_ZIP, 'rb') as _fhandle:
            response = client.post(_data_upload_url,
                {'uploadTerms': 'on', 'resource': _fhandle}, follow=True)
            self.assertContains(response, "was changed successfully.")
        # refetch the storage object from the data base to make sure we have
        # the latest version
        _so = StorageObject.objects.get(
            pk=DataUploadTests.testfixture.storage_object.pk)
        self.assertTrue(_so.get_download(),
            "expected that uploaded LR data is available as a local download")

    def test_editor_can_update_own_upload_data(self):
        """
        Verifies that an editor user may update actual resource data by
        re-uploading to owned resources.
        """
        client = test_utils.get_client_with_user_logged_in(
            DataUploadTests.editor_login)
        # add resource data first which can be updated later:
        shutil.copy(DATA_UPLOAD_ZIP, u'{}/archive.zip'.format(
                DataUploadTests.testfixture3.storage_object._storage_folder()))
        DataUploadTests.testfixture3.storage_object.compute_checksum()
        DataUploadTests.testfixture3.storage_object.save()
        # make sure that there is really resource data stored now:
        _so = StorageObject.objects.get(
            pk=DataUploadTests.testfixture3.storage_object.pk)
        _old_checksum = _so.checksum
        self.assertNotEqual(None, _old_checksum)
        # vreify that the resource data update works:
        _data_upload_url = "{}repository/resourceinfotype_model/{}/" \
            "upload-data/".format(ADMINROOT, DataUploadTests.testfixture3.id)
        response = client.get(_data_upload_url)
        self.assertContains(response,
            DataUploadTests.testfixture3.storage_object.get_download())
        with open(DATA_UPLOAD_ZIP_2, 'rb') as _fhandle:
            response = client.post(_data_upload_url,
                {'uploadTerms': 'on', 'resource': _fhandle}, follow=True)
            self.assertContains(response, "was changed successfully.")
        _so = StorageObject.objects.get(
            pk=DataUploadTests.testfixture3.storage_object.pk)
        self.assertNotEqual(_so.checksum, _old_checksum)

    def test_editor_cannot_upload_data_to_invisible_resources(self):
        """
        Verifies that an editor user must not upload actual resource data to
        resources that do not belong to her editor group and which are not hers.
        """
        client = test_utils.get_client_with_user_logged_in(
            DataUploadTests.editor_login)
        response = client.get("{}repository/resourceinfotype_model/{}/" \
            "upload-data/".format(ADMINROOT, DataUploadTests.testfixture2.id))
        self.assertIn(response.status_code, (403, 404), "expected that an " \
            "editor must not upload resource data to invisible resources")


class DestructiveTests(TestCase):
    """
    Test case for tests that are in some way 'destructive' with regard to the
    test data.
    
    This test case is separate from the `EditorTest` above as it requires setup
    and teardown methods per test.
    """
    
    # static variables to be initialized in setUpClass():
    superuser_login = None
    editor_login = None
    manager_login = None

    @classmethod
    def setUpClass(cls):
        
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
        # login POST dict
        DestructiveTests.superuser_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'superuser',
            'password': 'secret',
        }
        DestructiveTests.editor_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'editoruser',
            'password': 'secret',
        }
        DestructiveTests.manager_login = {
            REDIRECT_FIELD_NAME: ADMINROOT,
            LOGIN_FORM_KEY: 1,
            'username': 'manageruser',
            'password': 'secret',
        }

    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def setUp(self):
        """
        Sets up test users with and without staff permissions.
        """
        test_utils.setup_test_storage()

        self.test_editor_group = EditorGroup.objects.create(
                                                    name='test_editor_group')
        self.test_editor_group_manager = \
            EditorGroupManagers.objects.create(name='test_editor_groupmanager',
                                        managed_group=self.test_editor_group)

        self.test_editor = test_utils.create_editor_user('editoruser',
            'editor@example.com', 'secret', (self.test_editor_group,))
        self.test_manager = test_utils.create_manager_user(
            'manageruser', 'manager@example.com', 'secret',
            (self.test_editor_group, self.test_editor_group_manager))

        User.objects.create_superuser('superuser', 'su@example.com', 'secret')

        self.testfixture = _import_test_resource(self.test_editor_group,
                                                 pub_status=PUBLISHED)

    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()

    def test_editor_user_can_add_editor_group_to_own_resources_only(self):
        """
        Verifies that an editor user can add one of his editor groups to his own
        resources.
        """
        # create some test objects first:
        test_res = _import_test_resource(None, TESTFIXTURE3_XML)
        test_res.owners.add(self.test_editor)
        test_res.save()
        test_eg = EditorGroup.objects.create(name='a_test_eg')
        self.test_editor.groups.add(test_eg)
        # run the actual test:
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        response = client.post(
            '{}repository/resourceinfotype_model/my/'.format(ADMINROOT),
            {"action": "add_group", admin.ACTION_CHECKBOX_NAME: test_res.id})
        self.assertContains(response,
            "Add editor groups to the following resource:", msg_prefix=
                "expected to be on the page for adding an editor group")
        for group in self.test_editor.groups.filter(
                name__in=EditorGroup.objects.values_list('name', flat=True)):
            self.assertContains(response, group.name, msg_prefix=
                "expected to see all own editor groups as possible selections")
        response = client.post(
            '{}repository/resourceinfotype_model/my/'.format(ADMINROOT),
            {"multifield": test_eg.id, "add_editor_group": "Add", "action":
             "add_group", admin.ACTION_CHECKBOX_NAME: test_res.id},
            follow=True)
        self.assertContains(response, test_eg.name, msg_prefix="the resource " \
                            "is expected to be member of another editor group")
        self.assertTrue(test_res.editor_groups.filter(
                name=test_eg.name).count() == 1,
            "the resource is expected to be member of another editor group")

    def test_editor_user_cannot_add_editor_group_to_non_owned_resources(self):
        """
        Verifies that an editor user cannot add one of her editor groups to
        resources which are not her own.
        """
        # create a test object first:
        test_eg = EditorGroup.objects.create(name='a_test_eg')
        self.test_editor.groups.add(test_eg)
        # run the actual test:
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        response = client.post(
            '{}repository/resourceinfotype_model/my/'.format(ADMINROOT),
            {"action": "add_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "Add editor groups to the following resource", msg_prefix=
                "expected to be on the page for adding an editor group")
        for group in self.test_editor.groups.filter(
                name__in=EditorGroup.objects.values_list('name', flat=True)):
            self.assertContains(response, group.name, msg_prefix=
                "expected to see all own editor groups as possible selections")
        response = client.post(
            '{}repository/resourceinfotype_model/my/'.format(ADMINROOT),
            {"multifield": test_eg.id, "add_editor_group": "Add", "action":
             "add_group", admin.ACTION_CHECKBOX_NAME: self.testfixture.id},
            follow=True)
        self.assertTrue(self.testfixture.editor_groups.filter(
                name=test_eg.name).count() == 0,
            "the resource is expected to not be member of another editor group")

    def test_manager_user_can_add_editor_group_to_own_resources(self):
        """
        Verifies that a manager user can add one of his managed editor groups to
        his own resources.
        """
        # create some test objects first:
        test_res = _import_test_resource(None, TESTFIXTURE3_XML)
        test_res.owners.add(self.test_manager)
        test_res.save()
        test_eg = EditorGroup.objects.create(name='a_test_eg')
        self.test_manager.groups.add(EditorGroupManagers.objects.create(
                name='a_test_mg', managed_group=test_eg))
        # run the actual test:
        client = test_utils.get_client_with_user_logged_in(self.manager_login)
        response = client.post(
            '{}repository/resourceinfotype_model/my/'.format(ADMINROOT),
            {"action": "add_group", admin.ACTION_CHECKBOX_NAME: test_res.id})
        self.assertContains(response,
            "Add editor groups to the following resource:", msg_prefix=
                "expected to be on the page for adding an editor group")
        for group in self.test_manager.groups.filter(
                name__in=EditorGroup.objects.values_list('name', flat=True)):
            self.assertContains(response, group.name, msg_prefix=
                "expected to see all own editor groups as possible selections")
        for group in EditorGroup.objects.filter(name__in=
                self.test_manager.groups.values_list(
                    'editorgroupmanagers__managed_group__name', flat=True)):
            self.assertContains(response, group.name, msg_prefix=
                "expected to see all managed groups as possible selections")
        response = client.post(
            '{}repository/resourceinfotype_model/my/'.format(ADMINROOT),
            {"multifield": test_eg.id, "add_editor_group": "Add", "action":
             "add_group", admin.ACTION_CHECKBOX_NAME: test_res.id},
            follow=True)
        self.assertContains(response, test_eg.name, msg_prefix="the resource " \
                            "is expected to be member of another editor group")
        self.assertTrue(test_res.editor_groups.filter(
                name=test_eg.name).count() == 1,
            "the resource is expected to be member of another editor group")

    def test_manager_user_cannot_add_editor_group_to_non_owned_resources(self):
        """
        Verifies that a manager user cannot add one of her managed editor groups
        to resources which are not her own.
        """
        # create a test object first:
        test_eg = EditorGroup.objects.create(name='a_test_eg')
        self.test_manager.groups.add(EditorGroupManagers.objects.create(
                name='a_test_mg', managed_group=test_eg))
        # run the actual test:
        client = test_utils.get_client_with_user_logged_in(self.manager_login)
        response = client.post(
            '{}repository/resourceinfotype_model/my/'.format(ADMINROOT),
            {"action": "add_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "Add editor groups to the following resource", msg_prefix=
                "expected to be on the page for adding an editor group")
        for group in self.test_manager.groups.filter(
                name__in=EditorGroup.objects.values_list('name', flat=True)):
            self.assertContains(response, group.name, msg_prefix=
                "expected to see all own editor groups as possible selections")
        for group in EditorGroup.objects.filter(name__in=
                self.test_manager.groups.values_list(
                    'editorgroupmanagers__managed_group__name', flat=True)):
            self.assertContains(response, group.name, msg_prefix=
                "expected to see all managed groups as possible selections")
        response = client.post(
            '{}repository/resourceinfotype_model/my/'.format(ADMINROOT),
            {"multifield": test_eg.id, "add_editor_group": "Add", "action":
             "add_group", admin.ACTION_CHECKBOX_NAME: self.testfixture.id},
            follow=True)
        self.assertTrue(self.testfixture.editor_groups.filter(
                name=test_eg.name).count() == 0,
            "the resource is expected to not be member of another editor group")

    def test_superuser_can_add_any_editor_group_to_any_resource(self):
        """
        Verifies that a superuser can add any editor groups to any resources.
        """
        # create a test object first:
        test_eg = EditorGroup.objects.create(name='some_editor_group')
        # run the actual test:
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        response = client.post(
            '{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "add_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "Add editor groups to the following resource:", msg_prefix=
                "expected to be on the page for adding an editor group")
        response = client.post(
            '{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"multifield": test_eg.id, "add_editor_group": "Add", "action":
             "add_group", admin.ACTION_CHECKBOX_NAME: self.testfixture.id},
            follow=True)
        self.assertContains(response, test_eg.name, msg_prefix="the resource " \
                            "is expected to be member of another editor group")
        self.assertTrue(self.testfixture.editor_groups.filter(
                name=test_eg.name).count() == 1,
            "the resource is expected to be member of another editor group")

    def test_editor_user_cannot_remove_editor_group_from_any_resource(self):
        """
        Verifies that an editor user cannot remove any editor groups from any
        resources.
        """
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        response = client.post(
            '{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "remove_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        if response.status_code == 200:
            self.assertNotContains(response, "<h3>Remove editor groups", 200,
                "an editor user must not remove any editor groups")
        else:
            self.assertEqual(response.status_code, 403,
                "an editor user must not remove any editor groups")

    def test_manager_user_cannot_remove_editor_group_from_any_resource(self):
        """
        Verifies that a manager user cannot remove any editor groups from any
        resources.
        """
        client = test_utils.get_client_with_user_logged_in(self.manager_login)
        response = client.post(
            '{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "remove_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        if response.status_code == 200:
            self.assertNotContains(response, "<h3>Remove editor groups", 200,
                "a manager user must not remove any editor groups")
        else:
            self.assertEqual(response.status_code, 403,
                "a manager user must not remove any editor groups")

    def test_superuser_can_remove_editor_group_from_any_resource(self):
        """
        Verifies that a superuser can remove any editor group from any resource.
        """
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        response = client.post(
            '{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "remove_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "Remove editor groups from the following resource:", msg_prefix=
                "expected to be on the page for removing an editor group")
        response = client.post(
            '{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"multifield": self.test_editor_group.id,
             "remove_editor_group": "Remove", "action": "remove_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id}, follow=True)
        self.assertNotContains(response, self.test_editor_group.name,
            msg_prefix="the resource is expected to not be member of the " \
                "editor group anymore")
        self.assertTrue(self.testfixture.editor_groups.filter(
                name=self.test_editor_group.name).count() == 0, "the " \
            "resource is expected to not be member of the editor group anymore")

    def test_superuser_can_add_user_to_editor_group(self):
        """
        Verifies that a superuser can add a user to an editor group.
        """
        test_user = User.objects.create_user('normaluser', 'normal@example.com',
                                             'secret')
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        response = client.post('{}accounts/editorgroup/'.format(ADMINROOT),
            {"action": "add_user_to_editor_group",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group.id})
        self.assertContains(response,
            "Add a user to the following editor group:", msg_prefix=
                "expected to be on the action page for adding an editor group")
        response = client.post('{}accounts/editorgroup/'.format(ADMINROOT),
            {"users": test_user.userprofile.id, "add_user_profile_to_editor_group": "Add",
             "action": "add_user_to_editor_group", admin.ACTION_CHECKBOX_NAME:
             self.test_editor_group.id}, follow=True)
        self.assertContains(response, "normaluser", msg_prefix=
                "the user is expected to be member of the editor group now")
        self.assertTrue(test_user.groups.filter(
                name=self.test_editor_group.name).count() == 1,
            "the user is expected to be member of the editor group now")

    def test_superuser_can_remove_user_from_editor_group(self):
        """
        Verifies that a superuser can remove a user from an editor group.
        """
        test_user = test_utils.create_editor_user('ex_editoruser',
            'ex_editor@example.com', 'secret', (self.test_editor_group,))
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        response = client.post('{}accounts/editorgroup/'.format(ADMINROOT),
            {"action": "remove_user_from_editor_group",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group.id})
        self.assertContains(response,
            "Remove a user from the following editor group:", msg_prefix=
                "expected to be on the page for removing an editor group")
        response = client.post('{}accounts/editorgroup/'.format(ADMINROOT),
            {"users": test_user.userprofile.id, "remove_user_profile_from_editor_group":
                "Remove", "action": "remove_user_from_editor_group",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group.id},
            follow=True)
        self.assertNotContains(response, test_user.username, msg_prefix=
            "the user is expected to not be member of the editor group anymore")
        self.assertTrue(test_user.groups.filter(
                name=self.test_editor_group.name).count() == 0,
            "the user is expected to not be member of the editor group anymore")

    def test_deleted_editor_group_is_removed_from_all_relevant_resources(self):
        """
        Verifies that an editor group is removed from all relevant resources
        """
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        EditorGroup.objects.filter(id=self.test_editor_group.id).delete()
        self.assertEquals(self.testfixture.editor_groups.all().count(), 0)
        response = client.get('{}repository/resourceinfotype_model/'.format(ADMINROOT))
        self.assertNotContains(response, 'editoruser', msg_prefix=
            'expected the editor group to be removed from the resources')
        
    def test_deleted_editor_group_is_removed_from_all_relevant_users(self):
        """
        Verifies that an editor group is removed from all relevant users
        """
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        EditorGroup.objects.filter(id=self.test_editor_group.id).delete()
        editoruser = User.objects.get(username='editoruser')
        self.assertEquals(editoruser.groups.filter(name=self.test_editor_group.name).count(), 0)
        response = client.get('{}auth/user/{}/'.format(ADMINROOT, editoruser.id))
        self.assertNotContains(response, 'editoruser</option>', msg_prefix=
            'expected the editor group to be removed from the users')

    def test_superuser_can_add_user_to_editor_group_manager(self):
        """
        Verifies that a superuser can add a user to an editor group manager.
        """
        test_user = User.objects.create_user('normaluser', 'normal@example.com',
                                             'secret')
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        response = client.post('{}accounts/editorgroupmanagers/'.format(ADMINROOT),
            {"action": "add_user_to_editor_group_managers",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group_manager.id})
        self.assertContains(response,
            "Add a user to the following editor group manager group", msg_prefix=
                "expected to be on the action page for adding an editor group manager")
        response = client.post('{}accounts/editorgroupmanagers/'.format(ADMINROOT),
            {"users": test_user.userprofile.id, "add_user_profile_to_editor_group_managers": "Add",
             "action": "add_user_to_editor_group_managers", admin.ACTION_CHECKBOX_NAME:
             self.test_editor_group_manager.id}, follow=True)
        self.assertContains(response, "normaluser", msg_prefix=
                "the user is expected to be member of the editor group manager now")
        self.assertTrue(test_user.groups.filter(
                name=self.test_editor_group_manager.name).count() == 1,
            "the user is expected to be member of the editor group manager now")

    def test_superuser_can_remove_user_from_editor_group_manager(self):
        """
        Verifies that a superuser can remove a user from an editor group manager.
        """
        test_user = test_utils.create_manager_user('ex_manageruser',
            'ex_manager@example.com', 'secret', (self.test_editor_group_manager,))
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        response = client.post('{}accounts/editorgroupmanagers/'.format(ADMINROOT),
            {"action": "remove_user_from_editor_group_managers",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group_manager.id})
        self.assertContains(response,
            "Remove a user from the following editor group manager group", msg_prefix=
                "expected to be on the page for removing an editor group manager")
        response = client.post('{}accounts/editorgroupmanagers/'.format(ADMINROOT),
            {"users": test_user.userprofile.id, "remove_user_profile_from_editor_group_managers":
                "Remove", "action": "remove_user_from_editor_group_managers",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group_manager.id},
            follow=True)
        self.assertNotContains(response, test_user.username, msg_prefix=
            "the user is expected to not be an editor group manager member anymore")
        self.assertTrue(test_user.groups.filter(
                name=self.test_editor_group_manager.name).count() == 0,
            "the user is expected to not be an editor group manager member anymore")

    def test_deleted_editor_group_manager_is_removed_from_all_relevant_users(self):
        """
        Verifies that an editor group manager is removed from all relevant users
        """
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        EditorGroupManagers.objects.filter(id=self.test_editor_group_manager.id).delete()
        manageruser = User.objects.get(username='manageruser')
        self.assertEquals(manageruser.groups.filter(name=self.test_editor_group_manager.name).count(), 0)
        response = client.get('{}auth/user/{}/'.format(ADMINROOT, manageruser.id))
        self.assertNotContains(response, 'manageruser</option>', msg_prefix=
            'expected the editor group manager to be removed from the users')
        
    def test_delete_editor_group_remove_from_all_its_managing_groups(self):
        """
        Verifies that when an editor group is removed, all its managing groups are removed
        """
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        EditorGroup.objects.filter(id=self.test_editor_group.id).delete()
        self.assertEquals(EditorGroupManagers.objects.filter(managed_group=self.test_editor_group).count(), 0)
        response = client.get('{}accounts/editorgroupmanagers/'.format(ADMINROOT))
        self.assertNotContains(response, 'editoruser', msg_prefix=
            'expected the editor group manager to be removed when its editor group is removed')
    
    def test_cannot_edit_resource_non_master_copy(self):
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        resource = _import_test_resource(self.test_editor_group)
        resource.storage_object.master_copy = False
        resource.storage_object.save()
        response = client.get('{}repository/resourceinfotype_model/{}/'
                              .format(ADMINROOT, resource.id))
        self.assertContains(response, "You will now be redirected to the " \
            "META-SHARE node where the resource")
        self.assertContains(response, "You will now be redirected")
        
    def test_cannot_edit_reusable_entity_non_master_copy(self):
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        _import_test_resource(self.test_editor_group)
        personInfoType_model.objects.all().update(copy_status=REMOTE)
        response = client.get('{}repository/personinfotype_model/{}/'
                              .format(ADMINROOT, personInfoType_model.objects.all()[0].id))
        self.assertContains(response,
            "The metadata for this entity was originally created")
        self.assertNotContains(response, "You will now be redirected")

    def test_editor_user_cannot_see_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        self._test_user_cannot_see_deleted_resource(client)
        
    def test_super_user_cannot_see_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        self._test_user_cannot_see_deleted_resource(client)
        
    def _test_user_cannot_see_deleted_resource(self, client):
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/')
        self.assertContains(response, '1 Resource')
        self.testfixture.storage_object.deleted = True
        self.testfixture.storage_object.save()
        response = client.get(ADMINROOT+'repository/resourceinfotype_model/')
        self.assertContains(response, '0 Resources')
        
    def test_editor_user_cannot_edit_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        self._test_user_cannot_edit_deleted_resource(client)
        
    def test_super_user_cannot_edit_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        self._test_user_cannot_edit_deleted_resource(client)

    def _test_user_cannot_edit_deleted_resource(self, client):
        response = client.get(
          ADMINROOT+'repository/resourceinfotype_model/{}/'.format(self.testfixture.id))
        self.assertContains(response, 'Change Resource')
        self.testfixture.storage_object.deleted = True
        self.testfixture.storage_object.save()
        response = client.get(
          ADMINROOT+'repository/resourceinfotype_model/{}/'.format(self.testfixture.id))
        self.assertContains(response, 'Page not Found', status_code=404)
        
    def test_editor_user_cannot_export_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        self._test_user_cannot_export_deleted_resource(client)
        
    def test_super_user_cannot_export_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        self._test_user_cannot_export_deleted_resource(client)
    
    def _test_user_cannot_export_deleted_resource(self, client):
        response = client.get(
          ADMINROOT+'repository/resourceinfotype_model/{}/export-xml/'.format(self.testfixture.id))
        self.assertEquals(200, response.status_code)
        self.assertEquals('text/xml', response.__getitem__('Content-Type'))
        self.assertEquals('attachment; filename=resource-{}.xml'.format(self.testfixture.id), 
          response.__getitem__('Content-Disposition'))
        self.testfixture.storage_object.deleted = True
        self.testfixture.storage_object.save()
        response = client.get(
          ADMINROOT+'repository/resourceinfotype_model/{}/export-xml/'.format(self.testfixture.id))
        self.assertContains(response, 'Page not Found', status_code=404)

    def test_editor_user_cannot_browse_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        self._test_user_cannot_browse_deleted_resource(client)
        
    def test_super_user_cannot_browse_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        self._test_user_cannot_browse_deleted_resource(client)
    
    def _test_user_cannot_browse_deleted_resource(self, client):
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE))
        self.assertContains(response, '1 Language Resource')
        self.testfixture.storage_object.deleted = True
        self.testfixture.storage_object.save()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE))
        self.assertContains(response, '0 Language Resources')
        
    def test_editor_user_cannot_search_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.editor_login)
        self._test_user_cannot_search_deleted_resource(client)
        
    def test_super_user_cannot_search_deleted_resource(self):
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        self._test_user_cannot_search_deleted_resource(client)
    
    def _test_user_cannot_search_deleted_resource(self, client):
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': 'italian'})
        self.assertContains(response, '1 Language Resource')
        self.testfixture.storage_object.deleted = True
        self.testfixture.storage_object.save()
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE),
          follow=True, data={'q': 'reveal'})
        self.assertContains(response, 'No results were found')
        
    def test_reimporting_deleted_resource_unsets_deleted_flag(self):
        # one resource in db
        self.assertEqual(len(StorageObject.objects.all()), 1)
        self.assertEqual(len(resourceInfoType_model.objects.all()), 1)
        client = test_utils.get_client_with_user_logged_in(self.superuser_login)
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE))
        self.assertContains(response, '1 Language Resource')
        # resource still in db after setting the deleted flag
        self.testfixture.storage_object.deleted = True
        self.testfixture.storage_object.save()
        self.assertEqual(len(StorageObject.objects.all()), 1)
        self.assertEqual(len(resourceInfoType_model.objects.all()), 1)
        # but not visible
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE))
        self.assertContains(response, '0 Language Resources')
        # reimport the same resource
        self.testfixture = _import_test_resource(pub_status=PUBLISHED)
        # still only one resource in db
        self.assertEqual(len(StorageObject.objects.all()), 1)   
        self.assertEqual(len(resourceInfoType_model.objects.all()), 1)
        # but it is undeleted now
        self.assertFalse(self.testfixture.storage_object.deleted)
        # and visible again
        response = client.get('/{0}repository/search/'.format(DJANGO_BASE))
        self.assertContains(response, '1 Language Resource')


class EditorGroupApplicationTests(TestCase):
    """
    Test case for the user application to one or several Editors of various model instances.
    """
    
    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def setUp(self):
        """
        Sets up test users with and without staff permissions.
        """
        test_utils.set_index_active(False)
        test_utils.setup_test_storage()

        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

        self.test_editor_group = EditorGroup.objects.create(
                                                    name='test_editor_group')
        self.test_editor_group2 = EditorGroup.objects.create(
                                                    name='test_editor_group2')
        self.test_editor_group3 = EditorGroup.objects.create(
                                                    name='test_editor_group3')

        self.test_editor_group_manager = \
            EditorGroupManagers.objects.create(name='test_editor_group_manager',
                                        managed_group=self.test_editor_group)
        self.test_editor_group_manager2 = \
            EditorGroupManagers.objects.create(name='test_editor_group_manager2',
                                        managed_group=self.test_editor_group2)

        test_utils.create_editor_user('editoruser',
            'editor@example.com', 'secret', (self.test_editor_group,))
        test_utils.create_manager_user(
            'manageruser', 'manager@example.com', 'secret',
            (self.test_editor_group, self.test_editor_group_manager, self.test_editor_group_manager2))

        User.objects.create_superuser('superuser', 'su@example.com', 'secret')

    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        test_utils.set_index_active(True)

    def test_application_page_with_one_editor_group(self):
        """
        Verifies that a user can apply when there is at least one editor group.
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.get('/{0}accounts/editor_group_application/'.format(DJANGO_BASE))
        self.assertContains(response, 'Apply for editor group membership', msg_prefix=
          'expected the system to allow the user to apply to an editor group')

    def test_application_when_not_member_of_any_group(self):
        """
        Verifies that a user can apply to a first group
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        current_requests = EditorGroupApplication.objects.count()
        response = client.post('/{0}accounts/editor_group_application/'.format(DJANGO_BASE), \
          {'editor_group': self.test_editor_group.pk}, follow=True)
        self.assertContains(response, 'You have successfully applied for editor group "{0}"'.format(
          self.test_editor_group.name), msg_prefix='expected the system to accept a new request.')
        self.assertEquals(EditorGroupApplication.objects.count(), current_requests + 1)

    def test_application_when_there_is_a_pending_application(self):
        """
        Verifies that a user can apply for new group when another application is
        still pending.
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        current_requests = EditorGroupApplication.objects.count()
        response = client.post('/{0}accounts/editor_group_application/'.format(DJANGO_BASE), \
          {'editor_group': self.test_editor_group.pk}, follow=True)
        self.assertContains(response, 'You have successfully applied for editor group "{0}"'.format(
          self.test_editor_group.name), msg_prefix='expected the system to accept a new request.')
        response = client.post('/{0}accounts/editor_group_application/'.format(DJANGO_BASE), \
          {'editor_group': self.test_editor_group2.pk}, follow=True)
        self.assertContains(response, 'You have successfully applied for editor group "{0}"'.format(
          self.test_editor_group2.name), msg_prefix='expected the system to accept a new request.')
        self.assertEquals(EditorGroupApplication.objects.count(), current_requests + 2)

    def test_notification_email(self):
        """
        Verifies that an email is sent when the user apply to a group
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        current_requests = EditorGroupApplication.objects.count()
        response = client.post('/{0}accounts/editor_group_application/'.format(DJANGO_BASE), \
          {'editor_group': self.test_editor_group.pk}, follow=True)
        self.assertNotContains(response, 'There was an error sending out the request email', msg_prefix=
          'expected the system to be able to send an email.')
        self.assertEquals(EditorGroupApplication.objects.count(), current_requests + 1)

    def test_cannot_apply_a_group_of_which_the_user_is_member(self):
        """
        Verifies that a user cannot apply to a group he/she is already a member
        """
        client = Client()
        client.login(username='editoruser', password='secret')
        response = client.get('/{0}accounts/editor_group_application/'.format(DJANGO_BASE), follow=True)
        self.assertNotContains(response, '{}</option>'.format(self.test_editor_group),
          msg_prefix='expected the system not to propose the application to a group the user is already a member.')

    def test_cannot_apply_a_group_already_applied(self):
        """
        Verifies that a user cannot apply to a group he/she already applied for
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.post('/{0}accounts/editor_group_application/'.format(DJANGO_BASE), \
          {'editor_group': self.test_editor_group.pk}, follow=True)
        self.assertContains(response, 'You have successfully applied for editor group "{0}"'.format(
          self.test_editor_group.name), msg_prefix='expected the system to accept a new request.')
        response = client.get('/{0}accounts/editor_group_application/'.format(DJANGO_BASE), follow=True)
        self.assertNotContains(response, '{}</option>'.format(self.test_editor_group),
          msg_prefix='expected the system not to propose the application to a group \
          the user already applied for.')

    def test_cannot_access_the_form_when_no_group_available(self):
        """
        Verifies that a user cannot apply when there is no editor group available
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        EditorGroup.objects.all().delete()
        response = client.get('/{0}accounts/editor_group_application/'.format(DJANGO_BASE), follow=True)
        self.assertContains(response, 'There are no editor groups in the database, yet, for which you could apply.',
          msg_prefix='expected the system to prevent access to the form when no editor group is available.')

    def test_superuser_can_change_the_application(self):
        """
        Verifies that a superuser can change an editor group application request
        """
        client = Client()
        client.login(username='superuser', password='secret')
        new_reg = EditorGroupApplication(user=User.objects.get(username='normaluser'),
            editor_group=self.test_editor_group)
        new_reg.save()
        response = client.get('{}accounts/editorgroupapplication/{}/'.format(ADMINROOT, new_reg.pk))
        self.assertContains(response, 'normaluser</option>', msg_prefix=
            'expected a superuser to be able to modify an application.')

    def test_manager_cannot_change_the_application(self):
        """
        Verifies that a manager cannot change an editor group application
        request.
        
        The manager can view the application details anyway.
        """
        client = Client()
        client.login(username='manageruser', password='secret')
        new_reg = EditorGroupApplication(
            user=User.objects.get(username='normaluser'),
            editor_group=self.test_editor_group)
        new_reg.save()
        response = client.get('{}accounts/editorgroupapplication/{}/'
                              .format(ADMINROOT, new_reg.pk))
        self.assertContains(response, 'normaluser', msg_prefix='expected a '
                'manager to be able to see the details of an application.')
        self.assertNotContains(response, '<option value="1" '
                'selected="selected">normaluser</option>', msg_prefix=
            'expected a manager not to be able to modify an application.')

    def test_user_can_add_default_group(self):
        """
        Verifies that a user can set an editor group as default
        """
        client = Client()
        client.login(username='editoruser', password='secret')
        response = client.post('/{0}accounts/update_default_editor_groups/'.format(DJANGO_BASE), \
          {'editor_group': self.test_editor_group.pk}, follow=True)
        self.assertNotContains(response, 'You have successfully added default editor group "{}".'.format(self.test_editor_group),
          msg_prefix='expected the system to set an editor group as default.')
        
    def test_user_can_remove_default_group(self):
        """
        Verifies that a user can remove an editor group from the default list
        """
        client = Client()
        client.login(username='editoruser', password='secret')
        client.post('/{0}accounts/update_default_editor_groups/'.format(DJANGO_BASE), \
          {'editor_group': self.test_editor_group.pk}, follow=True)
        response = client.post('/{0}accounts/update_default_editor_groups/'.format(DJANGO_BASE), \
          {'editor_group': []}, follow=True)
        self.assertNotContains(response, 'You have successfully removed default editor group "{}".'.format(self.test_editor_group),
          msg_prefix='expected the system to remove a default editor group.')
        

class OrganizationApplicationTests(TestCase):
    """
    Test case for the user application to one or several organization of various model instances.
    """

    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))
        
    def setUp(self):
        """
        Sets up test users with and without staff permissions.
        """
        test_utils.set_index_active(False)
        test_utils.setup_test_storage()

        User.objects.create_user('normaluser', 'normal@example.com', 'secret')

        self.test_organization = Organization.objects.create(
                                                    name='test_organization')
        self.test_organization2 = Organization.objects.create(
                                                    name='test_organization2')
        self.test_organization3 = Organization.objects.create(
                                                    name='test_organization3')

        self.test_organization_managers = \
            OrganizationManagers.objects.create(name='test_organization_manager',
                                        managed_organization=self.test_organization)
        self.test_organization_managers2 = \
            OrganizationManagers.objects.create(name='test_organization_managers2',
                                        managed_organization=self.test_organization2)

        test_utils.create_organization_member('organizeruser',
            'organizer@example.com', 'secret', (self.test_organization,))
        test_utils.create_organization_manager_user(
            'organizationmanageruser', 'organizationmanager@example.com', 'secret',
            (self.test_organization, self.test_organization_managers, self.test_organization_managers2))

        User.objects.create_superuser('superuser', 'su@example.com', 'secret')

    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        test_utils.set_index_active(True)

    def test_application_page_with_one_organization_group(self):
        """
        Verifies that a user can apply when there is at least one organization group.
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.get('/{0}accounts/organization_application/'.format(DJANGO_BASE))
        self.assertContains(response, 'Apply for organization membership', msg_prefix=
          'expected the system to allow the user to apply to an organization')

    def test_application_when_not_member_of_any_organization(self):
        """
        Verifies that a user can apply to a first organization
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        current_requests = OrganizationApplication.objects.count()
        response = client.post('/{0}accounts/organization_application/'.format(DJANGO_BASE), \
          {'organization': self.test_organization.pk}, follow=True)
        self.assertContains(response, 'You have successfully applied for organization "{0}"'.format(
          self.test_organization.name), msg_prefix='expected the system to accept a new request.')
        self.assertEquals(OrganizationApplication.objects.count(), current_requests + 1)

    def test_application_when_there_is_a_pending_application(self):
        """
        Verifies that a user can apply for new organization when another application is
        still pending.
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        current_requests = OrganizationApplication.objects.count()
        response = client.post('/{0}accounts/organization_application/'.format(DJANGO_BASE), \
          {'organization': self.test_organization.pk}, follow=True)
        self.assertContains(response, 'You have successfully applied for organization "{0}"'.format(
          self.test_organization.name), msg_prefix='expected the system to accept a new request.')
        response = client.post('/{0}accounts/organization_application/'.format(DJANGO_BASE), \
          {'organization': self.test_organization2.pk}, follow=True)
        self.assertContains(response, 'You have successfully applied for organization "{0}"'.format(
          self.test_organization2.name), msg_prefix='expected the system to accept a new request.')
        self.assertEquals(OrganizationApplication.objects.count(), current_requests + 2)

    def test_notification_email(self):
        """
        Verifies that an email is sent when the user apply to an organization
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        current_requests = OrganizationApplication.objects.count()
        response = client.post('/{0}accounts/organization_application/'.format(DJANGO_BASE), \
          {'organization': self.test_organization.pk}, follow=True)
        self.assertNotContains(response, 'There was an error sending out the request email', msg_prefix=
          'expected the system to be able to send an email.')
        self.assertEquals(OrganizationApplication.objects.count(), current_requests + 1)

    def test_cannot_apply_an_organization_of_which_the_user_is_member(self):
        """
        Verifies that a user cannot apply to an organization he/she is already a member
        """
        client = Client()
        client.login(username='organizeruser', password='secret')
        response = client.get('/{0}accounts/organization_application/'.format(DJANGO_BASE), follow=True)
        self.assertNotContains(response, '{}</option>'.format(self.test_organization),
          msg_prefix='expected the system not to propose the application to an organization the user is already a member.')

    def test_cannot_apply_an_organization_already_applied(self):
        """
        Verifies that a user cannot apply to an organization he/she already applied for
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        response = client.post('/{0}accounts/organization_application/'.format(DJANGO_BASE), \
          {'organization': self.test_organization.pk}, follow=True)
        self.assertContains(response, 'You have successfully applied for organization "{0}"'.format(
          self.test_organization.name), msg_prefix='expected the system to accept a new request.')
        response = client.get('/{0}accounts/organization_application/'.format(DJANGO_BASE), follow=True)
        self.assertNotContains(response, '{}</option>'.format(self.test_organization),
          msg_prefix='expected the system not to propose the application to an organization \
          the user already applied for.')

    def test_cannot_access_the_form_when_no_organization_available(self):
        """
        Verifies that a user cannot apply when there is no organization available
        """
        client = Client()
        client.login(username='normaluser', password='secret')
        Organization.objects.all().delete()
        response = client.get('/{0}accounts/organization_application/'.format(DJANGO_BASE), follow=True)
        self.assertContains(response, 'There are no organizations in the database, yet, for which you could apply.',
          msg_prefix='expected the system to prevent access to the form when no organization is available.')

    def test_superuser_can_change_the_application(self):
        """
        Verifies that a superuser can change an organization application request
        """
        client = Client()
        client.login(username='superuser', password='secret')
        new_reg = OrganizationApplication(user=User.objects.get(username='normaluser'),
            organization=self.test_organization)
        new_reg.save()
        response = client.get('{}accounts/organizationapplication/{}/'.format(ADMINROOT, new_reg.pk))
        self.assertContains(response, 'normaluser</option>', msg_prefix=
            'expected a superuser to be able to modify an application.')

    def test_manager_cannot_change_the_application(self):
        """
        Verifies that a manager cannot change an organization application
        request.
        
        The manager can view the application details anyway.
        """
        client = Client()
        client.login(username='organizationmanageruser', password='secret')
        new_reg = OrganizationApplication(
            user=User.objects.get(username='normaluser'),
            organization=self.test_organization)
        new_reg.save()
        response = client.get('{}accounts/organizationapplication/{}/'
                              .format(ADMINROOT, new_reg.pk))
        self.assertContains(response, 'normaluser', msg_prefix='expected an '
                'organization manager to be able to see the details of an application.')
        self.assertNotContains(response, '<option value="1" '
                'selected="selected">normaluser</option>', msg_prefix=
            'expected an organization manager not to be able to modify an application.')

class BreadcrumbTests(TestCase):
    """
    Test case for the display of some manually added breadcrumbs in the back office.
    """

    @classmethod
    def setUpClass(cls):
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        
    @classmethod
    def tearDownClass(cls):
        LOGGER.info("finished '{}' tests".format(cls.__name__))
        
    def setUp(self):
        """
        Sets up test users.
        """
        test_utils.set_index_active(False)
        test_utils.setup_test_storage()

        self.test_editor_group = EditorGroup.objects.create(
                                                    name='test_editor_group')
        self.test_editor_group_managers = \
            EditorGroupManagers.objects.create(name='test_editor_group_manager',
                                        managed_group=self.test_editor_group)
        self.test_organization = Organization.objects.create(
                                                    name='test_organization')
        self.test_organization_managers = \
            OrganizationManagers.objects.create(name='test_organization_manager',
                                        managed_organization=self.test_organization)

        User.objects.create_superuser('superuser', 'su@example.com', 'secret')

        self.testfixture = _import_test_resource()

    def tearDown(self):
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        test_utils.set_index_active(True)

    def test_breadcrumb_in_add_users_to_editor_group(self):
        """
        Verifies breadcrumb in the add users to editor group page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}accounts/editorgroup/'.format(ADMINROOT),
            {"action": "add_user_to_editor_group",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Accounts</a> &rsaquo;\n    <a href=\"./\">Editor group</a> &rsaquo;\n\
    Add user\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_remove_users_from_editor_group(self):
        """
        Verifies breadcrumb in the remove users from editor group page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}accounts/editorgroup/'.format(ADMINROOT),
            {"action": "remove_user_from_editor_group",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Accounts</a> &rsaquo;\n    <a href=\"./\">Editor group</a> &rsaquo;\n\
    Remove user\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_add_users_to_editor_group_managers(self):
        """
        Verifies breadcrumb in the add users to editor group managers page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}accounts/editorgroupmanagers/'.format(ADMINROOT),
            {"action": "add_user_to_editor_group_managers",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group_managers.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Accounts</a> &rsaquo;\n    <a href=\"./\">Editor group managers group</a> &rsaquo;\n\
    Add user\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_remove_users_from_editor_group_managers(self):
        """
        Verifies breadcrumb in the remove users from editor group managers page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}accounts/editorgroupmanagers/'.format(ADMINROOT),
            {"action": "remove_user_from_editor_group_managers",
             admin.ACTION_CHECKBOX_NAME: self.test_editor_group_managers.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Accounts</a> &rsaquo;\n    <a href=\"./\">Editor group managers group</a> &rsaquo;\n\
    Remove user\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_add_users_to_organization(self):
        """
        Verifies breadcrumb in the add users to organization page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}accounts/organization/'.format(ADMINROOT),
            {"action": "add_user_to_organization",
             admin.ACTION_CHECKBOX_NAME: self.test_organization.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Accounts</a> &rsaquo;\n    <a href=\"./\">Organization</a> &rsaquo;\n\
    Add user\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_remove_users_from_organization(self):
        """
        Verifies breadcrumb in the remove users from organization page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}accounts/organization/'.format(ADMINROOT),
            {"action": "remove_user_from_organization",
             admin.ACTION_CHECKBOX_NAME: self.test_organization.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Accounts</a> &rsaquo;\n    <a href=\"./\">Organization</a> &rsaquo;\n\
    Remove user\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_add_users_to_organization_managers(self):
        """
        Verifies breadcrumb in the add users to organization managers page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}accounts/organizationmanagers/'.format(ADMINROOT),
            {"action": "add_user_to_organization_managers",
             admin.ACTION_CHECKBOX_NAME: self.test_organization_managers.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Accounts</a> &rsaquo;\n    <a href=\"./\">Organization managers group</a> &rsaquo;\n\
    Add user\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_remove_users_from_organization_managers(self):
        """
        Verifies breadcrumb in the remove users from organization managers page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}accounts/organizationmanagers/'.format(ADMINROOT),
            {"action": "remove_user_from_organization_managers",
             admin.ACTION_CHECKBOX_NAME: self.test_organization_managers.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Accounts</a> &rsaquo;\n    <a href=\"./\">Organization managers group</a> &rsaquo;\n\
    Remove user\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_add_editor_groups_to_resource(self):
        """
        Verifies breadcrumb in the add editor groups to resource page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "add_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Repository</a> &rsaquo;\n    <a href=\"./\">Resource</a> &rsaquo;\n\
    Add editor group\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_remove_editor_groups_from_resource(self):
        """
        Verifies breadcrumb in the remove editor groups from resource page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "remove_group",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Repository</a> &rsaquo;\n    <a href=\"./\">Resource</a> &rsaquo;\n\
    Remove editor group\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_add_owners_to_resource(self):
        """
        Verifies breadcrumb in the add owners to resource page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "add_owner",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Repository</a> &rsaquo;\n    <a href=\"./\">Resource</a> &rsaquo;\n\
    Add owner\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_remove_owners_from_resource(self):
        """
        Verifies breadcrumb in the remove owners to resource page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "remove_owner",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Repository</a> &rsaquo;\n    <a href=\"./\">Resource</a> &rsaquo;\n\
    Remove owner\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

    def test_breadcrumb_in_mark_resource_as_deleted(self):
        """
        Verifies breadcrumb in the mark resource as deleted page.
        """
        client = Client()
        client.login(username='superuser', password='secret')

        response = client.post('{}repository/resourceinfotype_model/'.format(ADMINROOT),
            {"action": "delete",
             admin.ACTION_CHECKBOX_NAME: self.testfixture.id})
        self.assertContains(response,
            "<div class=\"breadcrumbs\">\n    <a href=\"../../\">Home</a> &rsaquo;\n\
    <a href=\"../\">Repository</a> &rsaquo;\n    <a href=\"./\">Resource</a> &rsaquo;\n\
    Delete resource\n  </div>", msg_prefix=
                "expected to display a correct breadcrumb.")

