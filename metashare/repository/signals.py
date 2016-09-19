from django.db import models

from haystack.exceptions import NotHandled
from haystack.signals import BaseSignalProcessor

from metashare.storage.models import StorageObject, INGESTED, PUBLISHED
from metashare.repository.models import resourceInfoType_model

class PatchedSignalProcessor(BaseSignalProcessor):
    """
    A patched haystack signal processor. Send signal to update
    haystack resourceInfoType_modelIndex when the StorageObject instance
    gets saved and the resourceInfoType_model gets deleted.
    """
    def setup(self):
        """
        Register the ``StorageOject`` model post_save signal
        and the ``resourceInfoType_model`` model post_delete signal.
        """
        models.signals.post_save.connect(self.handle_save,
                                         sender=StorageObject)

        models.signals.post_delete.connect(self.handle_delete,
                                               sender=resourceInfoType_model)

    def teardown(self):
        """
        Unregister the ``StorageOject`` model post_save signal
        and the ``resourceInfoType_model`` model post_delete signal.
        """
        models.signals.post_save.disconnect(self.handle_save,
                                            sender=StorageObject)

        models.signals.post_delete.disconnect(self.handle_delete,
                                              sender=resourceInfoType_model)

    def handle_save(self, sender, instance, **kwargs):
        """
        Given a StorageObject model instance, determine which backends the
        update should be sent to & update the object on those backends.
        """
        # only create/update index entries of ingested and published resources
        if instance.publication_status in (INGESTED, PUBLISHED):
            using_backends = self.connection_router.for_write(instance=instance)

            for using in using_backends:
                try:
                    index = self.connections[using].get_unified_index()\
                        .get_index(resourceInfoType_model)
                    index.update_object(instance, using=using)
                except NotHandled:
                    # TODO: Maybe log it or let the exception bubble?
                    pass
