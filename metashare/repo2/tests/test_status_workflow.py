from django.test.testcases import TestCase
from metashare import test_utils
from metashare.settings import ROOT_PATH
from metashare.repo2.models import resourceInfoType_model
from metashare.repo2.editor.resource_editor import change_resource_status
from metashare.storage.models import PUBLISHED, INGESTED

class StatusWorkflowTest(TestCase):
    def setUp(self):
        """
        Import a resource to test the workflow changes for
        """
        test_utils.setup_test_storage()
        _fixture = '{0}/repo2/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        self.resource_id = _result[0].id

    def test_can_publish(self):
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        change_resource_status(resource, status=PUBLISHED)
        self.assertEquals('published', resource.publication_status())

    def test_can_unpublish(self):
        resource = resourceInfoType_model.objects.get(pk=self.resource_id)
        change_resource_status(resource, status=INGESTED)
        self.assertEquals('ingested', resource.publication_status())
