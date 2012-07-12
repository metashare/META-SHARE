from django.contrib.auth.models import User
from django.test.client import Client, RequestFactory
from django.test.testcases import TestCase
from metashare import test_utils
from metashare.settings import DJANGO_BASE, ROOT_PATH
from metashare.repository.models import resourceInfoType_model
from metashare.accounts.models import EditorGroup, ManagerGroup
from metashare.repository.editor.resource_editor import publish_resources, \
    ingest_resources, unpublish_resources
from metashare.storage.models import PUBLISHED, INGESTED, INTERNAL

ADMINROOT = '/{0}editor/repository/resourceinfotype_model/'.format(DJANGO_BASE)


class StatusWorkflowTest(TestCase):
    
    test_editor_group = None
    resource_id = None
    factory = RequestFactory()
    
    @classmethod
    def setUpClass(cls):
        """
        Import a resource to test the workflow changes for
        """
        test_utils.set_index_active(False)        
        test_utils.setup_test_storage()
        StatusWorkflowTest.test_editor_group = EditorGroup.objects.create(
                                                    name='test_editor_group')
        StatusWorkflowTest.test_manager_group = \
            ManagerGroup.objects.create(name='test_manager_group',
                                    managed_group=StatusWorkflowTest.test_editor_group)            
        test_utils.create_manager_user(
            'manageruser', 'manager@example.com', 'secret',
            (StatusWorkflowTest.test_editor_group, StatusWorkflowTest.test_manager_group))
        
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        StatusWorkflowTest.resource_id = _result[0].id
    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up the test
        """
        test_utils.set_index_active(True)
        test_utils.clean_db()
        test_utils.clean_storage()
        
        
    def test_can_publish_ingested(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        request = self.factory.get(ADMINROOT)
        if not hasattr(request, 'user'):
            user = User.objects.get(username='manageruser')
            setattr(request, 'user', user)
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.editor_groups.add(StatusWorkflowTest.test_editor_group)
        resource.storage_object.publication_status = INGESTED
        resource.storage_object.save()
        publish_resources(None, request, (resource,))
        self.assertEquals('published', resource.publication_status())
    
    def test_cannot_publish_internal(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        request = self.factory.get(ADMINROOT)
        if not hasattr(request, 'user'):
            user = User.objects.get(username='manageruser')
            setattr(request, 'user', user)
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.editor_groups.add(StatusWorkflowTest.test_editor_group)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        publish_resources(None, request, (resource,))
        self.assertEquals('internal', resource.publication_status())

    def test_can_ingest_internal(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        request = self.factory.get(ADMINROOT)
        if not hasattr(request, 'user'):
            user = User.objects.get(username='manageruser')
            setattr(request, 'user', user)
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.editor_groups.add(StatusWorkflowTest.test_editor_group)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        ingest_resources(None, request, (resource,))
        self.assertEquals('ingested', resource.publication_status())

    def test_cannot_ingest_published(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        request = self.factory.get(ADMINROOT)
        if not hasattr(request, 'user'):
            user = User.objects.get(username='manageruser')
            setattr(request, 'user', user)
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.editor_groups.add(StatusWorkflowTest.test_editor_group)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        ingest_resources(None, request, (resource,))
        self.assertEquals('published', resource.publication_status())

    def test_can_unpublish_published(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        request = self.factory.get(ADMINROOT)
        if not hasattr(request, 'user'):
            user = User.objects.get(username='manageruser')
            setattr(request, 'user', user)
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.editor_groups.add(StatusWorkflowTest.test_editor_group)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        unpublish_resources(None, request, (resource,))
        self.assertEquals('ingested', resource.publication_status())

    def test_cannot_unpublish_internal(self):
        client = Client()
        client.login(username='manageruser', password='secret')        
        request = self.factory.get(ADMINROOT)
        if not hasattr(request, 'user'):
            user = User.objects.get(username='manageruser')
            setattr(request, 'user', user)
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.editor_groups.add(StatusWorkflowTest.test_editor_group)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        unpublish_resources(None, request, (resource,))
        self.assertEquals('internal', resource.publication_status()) 