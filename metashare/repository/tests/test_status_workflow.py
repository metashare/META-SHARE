import logging

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.test.client import Client
from django.test.testcases import TestCase

from metashare import test_utils
from metashare.accounts.models import EditorGroup, EditorGroupManagers
from metashare.repository.models import resourceInfoType_model
from metashare.settings import DJANGO_BASE, ROOT_PATH, LOG_HANDLER
from metashare.storage.models import PUBLISHED, INGESTED, INTERNAL, REMOTE


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

ADMINROOT = '/{0}editor/repository/resourceinfotype_model/'.format(DJANGO_BASE)

class StatusWorkflowTest(TestCase):

    resource_id = None
    
    @classmethod
    def setUpClass(cls):
        """
        Import a resource to test the workflow changes for
        """
        LOGGER.info("running '{}' tests...".format(cls.__name__))
        test_utils.set_index_active(False)        
        test_utils.setup_test_storage()
        _test_editor_group = \
            EditorGroup.objects.create(name='test_editor_group')
        _test_manager_group = \
            EditorGroupManagers.objects.create(name='test_manager_group',
                                               managed_group=_test_editor_group)            
        test_utils.create_manager_user(
            'manageruser', 'manager@example.com', 'secret',
            (_test_editor_group, _test_manager_group))
        
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        _result.editor_groups.add(_test_editor_group)
        StatusWorkflowTest.resource_id = _result.id
    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up the test
        """
        test_utils.clean_resources_db()
        test_utils.clean_storage()
        test_utils.clean_user_db()
        test_utils.set_index_active(True)
        LOGGER.info("finished '{}' tests".format(cls.__name__))

    def test_can_publish_ingested(self):
        client = Client()
        client.login(username='manageruser', password='secret')
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = INGESTED
        resource.storage_object.save()
        client.post(ADMINROOT,
            {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        # fetch the resource from DB as our object is not up-to-date anymore
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.assertEquals('published', resource.publication_status())

    def test_cannot_publish_internal(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        client.post(ADMINROOT,
            {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        # fetch the resource from DB as our object is not up-to-date anymore
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.assertEquals('internal', resource.publication_status())

    def test_can_ingest_internal(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        client.post(ADMINROOT,
            {"action": "ingest_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        # fetch the resource from DB as our object is not up-to-date anymore
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.assertEquals('ingested', resource.publication_status())

    def test_cannot_ingest_published(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        client.post(ADMINROOT,
            {"action": "ingest_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        # fetch the resource from DB as our object is not up-to-date anymore
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.assertEquals('published', resource.publication_status())

    def test_can_unpublish_published(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        client.post(ADMINROOT,
            {"action": "unpublish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        # fetch the resource from DB as our object is not up-to-date anymore
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.assertEquals('ingested', resource.publication_status())

    def test_cannot_unpublish_internal(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        client.post(ADMINROOT,
            {"action": "unpublish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        # fetch the resource from DB as our object is not up-to-date anymore
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        self.assertEquals('internal', resource.publication_status())

    def test_cannot_change_publication_status_of_remote_copies(self):
        # not even a superuser must change the publication status of a remote
        # resource copy
        superuser = User.objects.create_superuser(
            "superuser", "su@example.com", "secret")
        client = Client()
        client.login(username=superuser.username, password='secret')
        # import a temporary resource to not mess with the other tests and set
        # the copy status to remote
        resource = test_utils.import_xml(
            '{0}/repository/fixtures/ILSP10.xml'.format(ROOT_PATH))
        resource.storage_object.copy_status = REMOTE
        # (1) verify that a status change from published is not possible:
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        client.post(ADMINROOT,
            {"action": "unpublish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        # fetch the resource from DB as our object is not up-to-date anymore
        resource = resourceInfoType_model.objects.get(pk=resource.id)
        self.assertEquals('published', resource.publication_status())
        # (2) verify that a status change from ingested is not possible:
        resource.storage_object.publication_status = INGESTED
        resource.storage_object.save()
        client.post(ADMINROOT,
            {"action": "publish_action", ACTION_CHECKBOX_NAME: resource.id},
            follow=True)
        # fetch the resource from DB as our object is not up-to-date anymore
        resource = resourceInfoType_model.objects.get(pk=resource.id)
        self.assertEquals('ingested', resource.publication_status())
