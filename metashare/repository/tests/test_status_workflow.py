from django.test.testcases import TestCase
from metashare import test_utils
from metashare.settings import ROOT_PATH
from metashare.repository.models import resourceInfoType_model
from metashare.repository.editor.resource_editor import publish_resources, \
    ingest_resources, unpublish_resources
from metashare.storage.models import PUBLISHED, INGESTED, INTERNAL

class StatusWorkflowTest(TestCase):
    def setUp(self):
        """
        Import a resource to test the workflow changes for
        """
        test_utils.setup_test_storage()
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        self.resource_id = _result[0].id

    def test_can_publish_ingested(self):
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = INGESTED
        resource.storage_object.save()
        publish_resources(None, None, (resource,))
        self.assertEquals('published', resource.publication_status())

    def test_cannot_publish_internal(self):
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        publish_resources(None, None, (resource,))
        self.assertEquals('internal', resource.publication_status())

    def test_can_ingest_internal(self):
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        ingest_resources(None, None, (resource,))
        self.assertEquals('ingested', resource.publication_status())

    def test_cannot_ingest_published(self):
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        ingest_resources(None, None, (resource,))
        self.assertEquals('published', resource.publication_status())
        
    def test_can_unpublish_published(self):
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = PUBLISHED
        resource.storage_object.save()
        unpublish_resources(None, None, (resource,))
        self.assertEquals('ingested', resource.publication_status())

    def test_cannot_unpublish_internal(self):
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        resource.storage_object.publication_status = INTERNAL
        resource.storage_object.save()
        unpublish_resources(None, None, (resource,))
        self.assertEquals('internal', resource.publication_status())
