"""
Project: META-SHARE prototype implementation
 Author: Christian Spurk <cspurk@dfki.de>
"""
import logging
import os

from haystack.indexes import CharField, RealTimeSearchIndex, BooleanField
from haystack import indexes

from django.db.models import signals
from django.utils.translation import ugettext as _

from metashare.repository.models import resourceInfoType_model, \
    identificationInfoType_model, corpusInfoType_model, \
    toolServiceInfoType_model, lexicalConceptualResourceInfoType_model, \
    languageDescriptionInfoType_model
from metashare.repository.search_fields import LabeledCharField, \
    LabeledMultiValueField
from metashare.storage.models import StorageObject
from metashare.settings import LOG_LEVEL, LOG_HANDLER

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repository.search_indexes')
LOGGER.addHandler(LOG_HANDLER)


class PatchedRealTimeSearchIndex(RealTimeSearchIndex):
    """
    A patched version of the `RealTimeSearchIndex` which works around Haystack
    issue #548.
    """
    # whether the setup in _setup_save(), _setup_delete(), _teardown_save(),
    # _teardown_delete() has been done already or not
    _signal_setup_done = [False, False, False, False]

    def _setup_save(self):
        if PatchedRealTimeSearchIndex._signal_setup_done[0]:
            return True
        PatchedRealTimeSearchIndex._signal_setup_done[0] = True
        super(PatchedRealTimeSearchIndex, self)._setup_save()
        return False

    def _setup_delete(self):
        if PatchedRealTimeSearchIndex._signal_setup_done[1]:
            return True
        PatchedRealTimeSearchIndex._signal_setup_done[1] = True
        super(PatchedRealTimeSearchIndex, self)._setup_delete()
        return False

    def _teardown_save(self):
        if PatchedRealTimeSearchIndex._signal_setup_done[2]:
            return True
        PatchedRealTimeSearchIndex._signal_setup_done[2] = True
        super(PatchedRealTimeSearchIndex, self)._teardown_save()
        return False

    def _teardown_delete(self):
        if PatchedRealTimeSearchIndex._signal_setup_done[3]:
            return True
        PatchedRealTimeSearchIndex._signal_setup_done[3] = True
        super(PatchedRealTimeSearchIndex, self)._teardown_delete()
        return False


# pylint: disable-msg=C0103
class resourceInfoType_modelIndex(PatchedRealTimeSearchIndex,
                                  indexes.Indexable):
    """
    The `SearchIndex` which indexes `resourceInfoType_model`s.
    """
    # in the text field we list all resource model field that shall be searched
    text = CharField(document=True, use_template=True, stored=False)

    # List of sorting results
    resourceNameSort = CharField(indexed=True, faceted=True)
    resourceTypeSort = CharField(indexed=True, faceted=True)
    mediaTypeSort = CharField(indexed=True, faceted=True)
    languageNameSort = CharField(indexed=True, faceted=True)

    # whether the resource has been published or not; used only to filter what
    # a searching user may see
    published = BooleanField(stored=False)

    # List of filters
    languageNameFilter = LabeledMultiValueField(
                                label=_('Language'), faceted=True)
    resourceTypeFilter = LabeledMultiValueField(
                                label=_('Resource Type'), faceted=True)
    mediaTypeFilter = LabeledMultiValueField(
                                label=_('Media Type'), faceted=True)
    availabilityFilter = LabeledCharField(
                                label=_('Availability'), faceted=True)
    licenceFilter = LabeledMultiValueField(
                                label=_('Licence'), faceted=True)
    restrictionsOfUseFilter = LabeledMultiValueField(
                                label=_('Restrictions of Use'), faceted=True)
    validatedFilter = LabeledMultiValueField(
                                label=_('Validated'), faceted=True)
    foreseenUseFilter = LabeledMultiValueField(
                                label=_('Foreseen Use'), faceted=True)
    useNlpSpecificFilter = LabeledMultiValueField(
                                label=_('Use Is NLP Specific'), faceted=True)
    lingualityTypeFilter = LabeledMultiValueField(
                                label=_('Linguality Type'), faceted=True)
    multilingualityTypeFilter = LabeledMultiValueField(
                                label=_('Multilinguality Type'), faceted=True)
    modalityTypeFilter = LabeledMultiValueField(
                                label=_('Modality Type'), faceted=True)
    mimeTypeFilter = LabeledMultiValueField(
                                label=_('MIME Type'), faceted=True)
    bestPracticesFilter = LabeledMultiValueField(
                                label=_('Best Practices'), faceted=True)
    domainFilter = LabeledMultiValueField(
                                label=_('Domain'), faceted=True)
    geographicCoverageFilter = LabeledMultiValueField(
                                label=_('Geographic Coverage'), faceted=True)
    timeCoverageFilter = LabeledMultiValueField(
                                label=_('Time Coverage'), faceted=True)
    subjectFilter = LabeledMultiValueField(
                                label=_('Subject'), faceted=True)

    # we create all items that may appear in the search results list already at
    # index time
    rendered_result = CharField(use_template=True, indexed=False)

    def get_model(self):
        """
        Returns the model class of which instances are indexed here.
        """
        return resourceInfoType_model

    def index_queryset(self):
        """
        Returns the default QuerySet to index when doing a full index update.

        In our case this is a QuerySet containing only resources that have not
        been deleted, yet.
        """
        return self.read_queryset()

    def read_queryset(self):
        """
        Returns the default QuerySet for read actions.

        In our case this is a QuerySet containing only resources that have not
        been deleted, yet.
        """
        return self.get_model().objects.filter(storage_object__deleted=False)

    def update_object(self, instance, using=None, **kwargs):
        """
        Updates the index for a single object instance.

        In this implementation we do not only handle instances of the model as
        returned by get_model(), but we also support the models that are
        registered in our own _setup_save() method.
        """
        if os.environ.get('DISABLE_INDEXING_DURING_IMPORT', False) == 'True':
            return

        # have we been called from a post_save signal dispatcher?
        if "sender" in kwargs:
            # explicitly set `using` to None in order to let our Haystack router
            # decide which search index to use; the `using` argument which is
            # set by Django's post_save signal dispatcher has a different
            # meaning that we need to overwrite
            using = None
            if kwargs["sender"] == identificationInfoType_model:
                try:
                    instance = instance.resourceinfotype_model
                except resourceInfoType_model.DoesNotExist:
                    # may happen when an identificationInfoType_model is created
                    # in isolation; for example, in case of resource imports
                    # from XML where the identificationInfoType_model is created
                    # before the corresponding resourceInfoType_model is created
                    return
                assert instance, "At this stage there must be a related " \
                    "resource for the saved identification info."
                LOGGER.debug("identificationInfo changed for resource #{0}." \
                             .format(instance.id))
            elif kwargs["sender"] == StorageObject:
                LOGGER.debug("StorageObject changed for resource #{0}." \
                             .format(instance.id))
                related_resource_qs = instance.resourceinfotype_model_set
                if (not related_resource_qs.count()):
                    # no idea why this happens, but it does; there are storage
                    # objects which are not attached to any
                    # resourceInfoType_model
                    return
                related_resource = related_resource_qs.iterator().next()
                if instance.deleted:
                    # if the resource has been flagged for deletion, then we
                    # don't want to keep/have it in the index
                    LOGGER.info("Resource #{0} scheduled for deletion from " \
                                "the index.".format(related_resource.id))
                    self.remove_object(related_resource, using=using)
                    return
                instance = related_resource
            elif not kwargs["sender"] == self.get_model():
                assert False, "Unexpected sender: {0}".format(kwargs["sender"])
                LOGGER.error("Unexpected sender: {0}".format(kwargs["sender"]))
                return
        LOGGER.info("Resource #{0} scheduled for reindexing." \
                    .format(instance.id))
        # we better recreate our resource instance from the DB as otherwise it
        # has happened for some reason that the instance was not up-to-date
        instance = self.get_model().objects.get(pk=instance.id)
        super(resourceInfoType_modelIndex, self).update_object(instance,
                                                               using=using,
                                                               **kwargs)

    def _setup_save(self):
        """
        A hook for controlling what happens when the registered model is saved.

        In this implementation we additionally connect to frequently changed
        parts of the model which is returned by get_model().
        """
        if super(resourceInfoType_modelIndex, self)._setup_save():
            return
        # in addition to the default setup of our super class, we connect to
        # frequently changed parts of resourceInfoType_model so that they
        # trigger an automatic reindexing, too:
        signals.post_save.connect(self.update_object,
                                  sender=identificationInfoType_model)
        signals.post_save.connect(self.update_object, sender=StorageObject)
        # all other changes somewhere in a resource (such as language info
        # changes) must be handled elsewhere, e.g., in a periodic reindexing
        # cron job

    def remove_object(self, instance, using=None, **kwargs):
        """
        Removes a single object instance from the index.
        """
        if os.environ.get('DISABLE_INDEXING_DURING_IMPORT', False) == 'True':
            return

        # have we been called from a post_delete signal dispatcher?
        if "sender" in kwargs:
            # explicitly set `using` to None in order to let our Haystack router
            # decide which search index to use; the `using` argument which is
            # set by Django's post_delete signal dispatcher has a different
            # meaning that we need to overwrite
            using = None
        super(resourceInfoType_modelIndex, self).remove_object(instance,
                                                               using=using,
                                                               **kwargs)

    def prepare_resourceNameSort(self, obj):
        """
        Collect the data to sort the Resource Names
        """
        import re

        # get the Resource Name
        resourceNameSort = obj.identificationInfo.resourceName[0]
        # keep alphanumeric characters only
        resourceNameSort = re.sub('[\W_]', '', resourceNameSort)
        # set Resource Name to lower case
        resourceNameSort = resourceNameSort.lower()

        return resourceNameSort

    def prepare_resourceTypeSort(self, obj):
        """
        Collect the data to sort the Resource Types
        """
        import re

        # get the list of Resource Types
        resourceTypeSort = self.prepare_resourceTypeFilter(obj)
        # render unique list of Resource Types
        resourceTypeSort = list(set(resourceTypeSort))
        # sort Resource Types
        resourceTypeSort.sort()
        # join Resource Types into a string
        resourceTypeSort = ",".join(resourceTypeSort)
        # keep alphanumeric characters only
        resourceTypeSort = re.sub('[\W_]', '', resourceTypeSort)
        # set list of Resource Types to lower case
        resourceTypeSort = resourceTypeSort.lower()

        return resourceTypeSort

    def prepare_mediaTypeSort(self, obj):
        """
        Collect the data to sort the Media Types
        """
        import re

        # get the list of Media Types
        mediaTypeSort = self.prepare_mediaTypeFilter(obj)
        # render unique list of Media Types
        mediaTypeSort = list(set(mediaTypeSort))
        # sort Media Types
        mediaTypeSort.sort()
        # join Media Types into a string
        mediaTypeSort = ",".join(mediaTypeSort)
        # keep alphanumeric characters only
        mediaTypeSort = re.sub('[\W_]', '', mediaTypeSort)
        # set list of Media Types to lower case
        mediaTypeSort = mediaTypeSort.lower()

        return mediaTypeSort

    def prepare_languageNameSort(self, obj):
        """
        Collect the data to sort the Language Names
        """
        import re

        # get the list of languages
        languageNameSort = self.prepare_languageNameFilter(obj)
        # render unique list of languages
        languageNameSort = list(set(languageNameSort))
        # sort languages
        languageNameSort.sort()
        # join languages into a string
        languageNameSort = ",".join(languageNameSort)
        # keep alphanumeric characters only
        languageNameSort = re.sub('[\W_]', '', languageNameSort)
        # set list of languages to lower case
        languageNameSort = languageNameSort.lower()

        return languageNameSort

    def prepare_published(self, obj):
        """
        Collect the data to filter the Published resources
        """
        return obj.storage_object and obj.storage_object.published

    def prepare_languageNameFilter(self, obj):
        """
        Collect the data to filter the resources on Language Name
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([lang.languageName for lang in
                               corpus_info.languageInfo.all()])
            if media_type.corpusAudioInfo:
                result.extend([lang.languageName for lang in
                               media_type.corpusAudioInfo.languageInfo.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([lang.languageName for lang in
                               corpus_info.languageInfo.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([lang.languageName for lang in
                            media_type.corpusTextNgramInfo.languageInfo.all()])
            if media_type.corpusImageInfo:
                result.extend([lang.languageName for lang in
                               media_type.corpusImageInfo.languageInfo.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceAudioInfo.languageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceTextInfo.languageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceVideoInfo.languageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceImageInfo.languageInfo.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionTextInfo.languageInfo.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionVideoInfo.languageInfo.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionImageInfo.languageInfo.all()])

        elif isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(corpus_media.inputInfo.languageName)
            if corpus_media.outputInfo:
                result.extend(corpus_media.outputInfo.languageName)

        return result

    def prepare_resourceTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type
        """
        result = []

        if obj.resourceComponentType.as_subclass().get_resourceType_display() \
                != '':
            result.append(obj.resourceComponentType.as_subclass() \
                          .get_resourceType_display())

        return result

    def prepare_mediaTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.append(corpus_info.get_mediaType_display())
            if media_type.corpusAudioInfo:
                result.append(media_type.corpusAudioInfo \
                              .get_mediaType_display())
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.append(corpus_info.get_mediaType_display())
            if media_type.corpusTextNgramInfo:
                result.append(media_type.corpusTextNgramInfo \
                              .get_mediaType_display())
            if media_type.corpusImageInfo:
                result.append(media_type.corpusImageInfo \
                              .get_mediaType_display())
            if media_type.corpusTextNumericalInfo:
                result.append(media_type.corpusTextNumericalInfo \
                              .get_mediaType_display())

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.append(lcr_media_type.lexicalConceptualResourceTextInfo \
                              .get_mediaType_display())
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.append(lcr_media_type \
                    .lexicalConceptualResourceAudioInfo.get_mediaType_display())
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.append(lcr_media_type \
                    .lexicalConceptualResourceVideoInfo.get_mediaType_display())
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.append(lcr_media_type \
                    .lexicalConceptualResourceImageInfo.get_mediaType_display())

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.append(ld_media_type.languageDescriptionTextInfo \
                              .get_mediaType_display())
            if ld_media_type.languageDescriptionVideoInfo:
                result.append(ld_media_type.languageDescriptionVideoInfo \
                              .get_mediaType_display())
            if ld_media_type.languageDescriptionImageInfo:
                result.append(ld_media_type.languageDescriptionImageInfo \
                              .get_mediaType_display())

        elif isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(corpus_media.inputInfo \
                              .get_mediaType_display_list())
            if corpus_media.outputInfo:
                result.extend(corpus_media.outputInfo \
                              .get_mediaType_display_list())

        return result

    def prepare_availabilityFilter(self, obj):
        """
        Collect the data to filter the resources on Availability
        """
        return obj.distributionInfo.get_availability_display()

    def prepare_licenceFilter(self, obj):
        """
        Collect the data to filter the resources on Licence
        """
        return [licence for licence_info in
                obj.distributionInfo.licenceinfotype_model_set.all()
                for licence in licence_info.get_licence_display_list()]

    def prepare_restrictionsOfUseFilter(self, obj):
        """
        Collect the data to filter the resources on Restrictions Of USe
        """
        return [restr for licence_info in
                obj.distributionInfo.licenceinfotype_model_set.all()
                for restr in licence_info.get_restrictionsOfUse_display_list()]

    def prepare_validatedFilter(self, obj):
        """
        Collect the data to filter the resources on Validated
        """
        return [validation_info.validated for validation_info in
                obj.validationinfotype_model_set.all()]

    def prepare_foreseenUseFilter(self, obj):
        """
        Collect the data to filter the resources on Foreseen Use
        """
        if obj.usageInfo:
            return [use_info.get_foreseenUse_display() for use_info in
                    obj.usageInfo.foreseenuseinfotype_model_set.all()]
        return []

    def prepare_useNlpSpecificFilter(self, obj):
        """
        Collect the data to filter the resources on NLP Specific
        """
        if obj.usageInfo:
            return [use for use_info in
                    obj.usageInfo.foreseenuseinfotype_model_set.all()
                    for use in use_info.get_useNLPSpecific_display_list()]
        return []

    def prepare_lingualityTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Linguality Type
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.append(corpus_info.lingualityInfo
                              .get_lingualityType_display())
            if media_type.corpusAudioInfo:
                result.append(media_type.corpusAudioInfo.lingualityInfo \
                              .get_lingualityType_display())
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                if corpus_info.lingualityInfo:
                    result.append(corpus_info.lingualityInfo \
                                  .get_lingualityType_display())
            if media_type.corpusTextNgramInfo:
                result.append(media_type.corpusTextNgramInfo.lingualityInfo \
                              .get_lingualityType_display())
            if media_type.corpusImageInfo and \
                    media_type.corpusImageInfo.lingualityInfo:
                result.append(media_type.corpusImageInfo.lingualityInfo \
                              .get_lingualityType_display())

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.append(lcr_media_type.lexicalConceptualResourceTextInfo \
                              .lingualityInfo.get_lingualityType_display())
            if lcr_media_type.lexicalConceptualResourceAudioInfo and \
                    lcr_media_type.lexicalConceptualResourceAudioInfo \
                        .lingualityInfo:
                result.append(lcr_media_type \
                        .lexicalConceptualResourceAudioInfo.lingualityInfo \
                        .get_lingualityType_display())
            if lcr_media_type.lexicalConceptualResourceVideoInfo and \
                    lcr_media_type.lexicalConceptualResourceVideoInfo \
                        .lingualityInfo:
                result.append(lcr_media_type \
                        .lexicalConceptualResourceVideoInfo.lingualityInfo \
                        .get_lingualityType_display())
            if lcr_media_type.lexicalConceptualResourceImageInfo and \
                    lcr_media_type.lexicalConceptualResourceImageInfo \
                        .lingualityInfo:
                result.append(lcr_media_type \
                        .lexicalConceptualResourceImageInfo.lingualityInfo \
                        .get_lingualityType_display())

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.append(ld_media_type.languageDescriptionTextInfo \
                              .lingualityInfo.get_lingualityType_display())
            if ld_media_type.languageDescriptionVideoInfo and \
                    ld_media_type.languageDescriptionVideoInfo.lingualityInfo:
                result.append(ld_media_type.languageDescriptionVideoInfo \
                              .lingualityInfo.get_lingualityType_display())
            if ld_media_type.languageDescriptionImageInfo and \
                    ld_media_type.languageDescriptionImageInfo.lingualityInfo:
                result.append(ld_media_type.languageDescriptionImageInfo \
                              .lingualityInfo.get_lingualityType_display())

        return result

    def prepare_multilingualityTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Multilinguality Type
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                mtf = corpus_info.lingualityInfo \
                  .get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)
            if media_type.corpusAudioInfo:
                mtf = media_type.corpusAudioInfo.lingualityInfo \
                  .get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                if corpus_info.lingualityInfo:
                    mtf = corpus_info.lingualityInfo \
                  .get_multilingualityType_display()
                    if mtf != '':
                        result.append(mtf)
            if media_type.corpusTextNgramInfo:
                mtf = media_type.corpusTextNgramInfo.lingualityInfo \
                  .get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)
            if media_type.corpusImageInfo and \
                    media_type.corpusImageInfo.lingualityInfo:
                mtf = media_type.corpusImageInfo.lingualityInfo \
                  .get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                mtf = lcr_media_type.lexicalConceptualResourceTextInfo \
                  .lingualityInfo.get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)
            if lcr_media_type.lexicalConceptualResourceAudioInfo and \
                    lcr_media_type.lexicalConceptualResourceAudioInfo \
                        .lingualityInfo:
                mtf = lcr_media_type.lexicalConceptualResourceAudioInfo \
                  .lingualityInfo.get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)
            if lcr_media_type.lexicalConceptualResourceVideoInfo and \
                    lcr_media_type.lexicalConceptualResourceVideoInfo \
                        .lingualityInfo:
                mtf = lcr_media_type.lexicalConceptualResourceVideoInfo \
                  .lingualityInfo.get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)
            if lcr_media_type.lexicalConceptualResourceImageInfo and \
                    lcr_media_type.lexicalConceptualResourceImageInfo \
                        .lingualityInfo:
                mtf = lcr_media_type.lexicalConceptualResourceImageInfo \
                  .lingualityInfo.get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                mtf = ld_media_type.languageDescriptionTextInfo \
                  .lingualityInfo.get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)
            if ld_media_type.languageDescriptionVideoInfo and \
                    ld_media_type.languageDescriptionVideoInfo.lingualityInfo:
                mtf = ld_media_type.languageDescriptionVideoInfo \
                  .lingualityInfo.get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)
            if ld_media_type.languageDescriptionImageInfo and \
                    ld_media_type.languageDescriptionImageInfo.lingualityInfo:
                mtf = ld_media_type.languageDescriptionImageInfo \
                  .lingualityInfo.get_multilingualityType_display()
                if mtf != '':
                    result.append(mtf)

        return result

    def prepare_modalityTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Modality Type
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([mt for modalityInfo in
                        corpus_info.modalityInfo.all() for mt in
                        modalityInfo.get_modalityType_display_list()])
            if media_type.corpusAudioInfo:
                result.extend([mt for modalityInfo in
                        media_type.corpusAudioInfo.modalityInfo.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                if corpus_info.modalityInfo:
                    result.extend(corpus_info.modalityInfo \
                                  .get_modalityType_display_list())
            if media_type.corpusTextNgramInfo and \
                    media_type.corpusTextNgramInfo.modalityInfo:
                result.extend(media_type.corpusTextNgramInfo.modalityInfo \
                              .get_modalityType_display_list())
            if media_type.corpusImageInfo:
                result.extend([mt for modalityInfo in
                               media_type.corpusImageInfo.modalityInfo.all()
                               for mt in
                               modalityInfo.get_modalityType_display_list()])
            if media_type.corpusTextNumericalInfo:
                result.extend([mt for modalityInfo in
                        media_type.corpusTextNumericalInfo.modalityInfo.all()
                        for mt in modalityInfo.get_modalityType_display_list()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([mt for modalityInfo in lcr_media_type \
                        .lexicalConceptualResourceTextInfo.modalityInfo.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([mt for modalityInfo in lcr_media_type \
                        .lexicalConceptualResourceAudioInfo.modalityInfo.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([mt for modalityInfo in lcr_media_type \
                        .lexicalConceptualResourceVideoInfo.modalityInfo.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([mt for modalityInfo in lcr_media_type \
                        .lexicalConceptualResourceImageInfo.modalityInfo.all()
                        for mt in modalityInfo.get_modalityType_display_list()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo and \
                    ld_media_type.languageDescriptionTextInfo.modalityInfo:
                result.extend(ld_media_type.languageDescriptionTextInfo \
                              .modalityInfo.get_modalityType_display_list())
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([mt for modalityInfo in ld_media_type \
                        .languageDescriptionVideoInfo.modalityInfo.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([mt for modalityInfo in ld_media_type \
                        .languageDescriptionImageInfo.modalityInfo.all()
                        for mt in modalityInfo.get_modalityType_display_list()])

        elif isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(corpus_media.inputInfo \
                              .get_modalityType_display_list())
            if corpus_media.outputInfo:
                result.extend(corpus_media.outputInfo \
                              .get_modalityType_display_list())

        return result

    def prepare_mimeTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Mime Type
        """
        mimeType_list = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                mimeType_list.extend([mimeType.mimeType for mimeType in
                                      corpus_info.textFormatInfo.all()])
            if media_type.corpusAudioInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        media_type.corpusAudioInfo.audioFormatInfo.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                mimeType_list.extend([mimeType.mimeType for mimeType in
                                      corpus_info.videoFormatInfo.all()])
            if media_type.corpusTextNgramInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        media_type.corpusTextNgramInfo.textFormatInfo.all()])
            if media_type.corpusImageInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        media_type.corpusImageInfo.imageFormatInfo.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        lcr_media_type.lexicalConceptualResourceTextInfo \
                            .textFormatInfo.all()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        lcr_media_type.lexicalConceptualResourceAudioInfo \
                            .audioFormatInfo.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        lcr_media_type.lexicalConceptualResourceVideoInfo \
                            .videoFormatInfo.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        lcr_media_type.lexicalConceptualResourceImageInfo \
                            .imageFormatInfo.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        ld_media_type.languageDescriptionTextInfo \
                            .textFormatInfo.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        ld_media_type.languageDescriptionVideoInfo \
                            .videoFormatInfo.all()])
            if ld_media_type.languageDescriptionImageInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        ld_media_type.languageDescriptionImageInfo \
                            .imageFormatInfo.all()])

        elif isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                mimeType_list.extend(corpus_media.inputInfo.mimeType)
            if corpus_media.outputInfo:
                mimeType_list.extend(corpus_media.outputInfo.mimeType)

        return mimeType_list

    def prepare_bestPracticesFilter(self, obj):
        """
        Collect the data to filter the resources on Best Practices
        """
        tool_service = obj.resourceComponentType.as_subclass()
        if isinstance(tool_service, toolServiceInfoType_model) \
                and tool_service.inputInfo:
            return tool_service.inputInfo \
                    .get_conformanceToStandardsBestPractices_display_list()

    def prepare_domainFilter(self, obj):
        """
        Collect the data to filter the resources on Domain
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([domain_info.domain for domain_info in
                               corpus_info.domainInfo.all()])
            if media_type.corpusAudioInfo:
                result.extend([domain_info.domain for domain_info in
                               media_type.corpusAudioInfo.domainInfo.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([domain_info.domain for domain_info in
                               corpus_info.domainInfo.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([domain_info.domain for domain_info in
                               media_type.corpusTextNgramInfo.domainInfo.all()])
            if media_type.corpusImageInfo:
                result.extend([domain_info.domain for domain_info in
                               media_type.corpusImageInfo.domainInfo.all()])
            if media_type.corpusTextNumericalInfo:
                result.extend([domain_info.domain for domain_info in
                        media_type.corpusTextNumericalInfo.domainInfo.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([domain_info.domain for domain_info in
                        lcr_media_type.lexicalConceptualResourceTextInfo \
                                .domainInfo.all()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([domain_info.domain for domain_info in
                        lcr_media_type.lexicalConceptualResourceAudioInfo \
                                .domainInfo.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([domain_info.domain for domain_info in
                        lcr_media_type.lexicalConceptualResourceVideoInfo \
                                .domainInfo.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([domain_info.domain for domain_info in
                        lcr_media_type.lexicalConceptualResourceImageInfo \
                                .domainInfo.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([domain_info.domain for domain_info in
                               ld_media_type.languageDescriptionTextInfo \
                                    .domainInfo.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([domain_info.domain for domain_info in
                               ld_media_type.languageDescriptionVideoInfo \
                                    .domainInfo.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([domain_info.domain for domain_info in
                               ld_media_type.languageDescriptionImageInfo \
                                    .domainInfo.all()])

        return result

    def prepare_geographicCoverageFilter(self, obj):
        """
        Collect the data to filter the resources on Geographic Coverage
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([gc_info.geographicCoverage for gc_info in
                               corpus_info.geographicCoverageInfo.all()])
            if media_type.corpusAudioInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               media_type.corpusAudioInfo \
                                    .geographicCoverageInfo.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([gc_info.geographicCoverage for gc_info in
                               corpus_info.geographicCoverageInfo.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               media_type.corpusTextNgramInfo \
                                    .geographicCoverageInfo.all()])
            if media_type.corpusImageInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               media_type.corpusImageInfo \
                                    .geographicCoverageInfo.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                        lcr_media_type.lexicalConceptualResourceTextInfo \
                            .geographicCoverageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                        lcr_media_type.lexicalConceptualResourceAudioInfo \
                            .geographicCoverageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                        lcr_media_type.lexicalConceptualResourceVideoInfo \
                            .geographicCoverageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                        lcr_media_type.lexicalConceptualResourceImageInfo \
                            .geographicCoverageInfo.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               ld_media_type.languageDescriptionTextInfo \
                                    .geographicCoverageInfo.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               ld_media_type.languageDescriptionVideoInfo \
                                    .geographicCoverageInfo.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               ld_media_type.languageDescriptionImageInfo \
                                    .geographicCoverageInfo.all()])

        return result

    def prepare_timeCoverageFilter(self, obj):
        """
        Collect the data to filter the resources on Time Coverage
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                               corpus_info.timeCoverageInfo.all()])
            if media_type.corpusAudioInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        media_type.corpusAudioInfo.timeCoverageInfo.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                               corpus_info.timeCoverageInfo.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        media_type.corpusTextNgramInfo.timeCoverageInfo.all()])
            if media_type.corpusImageInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        media_type.corpusImageInfo.timeCoverageInfo.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                            lcr_media_type.lexicalConceptualResourceTextInfo \
                                .timeCoverageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                            lcr_media_type.lexicalConceptualResourceAudioInfo \
                                .timeCoverageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                            lcr_media_type.lexicalConceptualResourceVideoInfo \
                                .timeCoverageInfo.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                            lcr_media_type.lexicalConceptualResourceImageInfo \
                                .timeCoverageInfo.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        ld_media_type.languageDescriptionTextInfo \
                            .timeCoverageInfo.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        ld_media_type.languageDescriptionVideoInfo \
                            .timeCoverageInfo.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        ld_media_type.languageDescriptionImageInfo \
                            .timeCoverageInfo.all()])

        return result

    def prepare_subjectFilter(self, obj):
        """
        Collect the data to filter the resources on Subject
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                sf = [class_info.subject_topic for class_info in
                    corpus_info.textClassificationInfo.all()]
                if sf != ['']:
                    result.extend(sf)
            if media_type.corpusAudioInfo:
                sf = [class_info.subject_topic for class_info in
                    media_type.corpusAudioInfo.audioClassificationInfo.all()]
                if sf != ['']:
                    result.extend(sf)
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                sf = [class_info.subject_topic for class_info in
                        corpus_info.videoclassificationinfotype_model_set.all()]
                if sf != ['']:
                    result.extend(sf)
            if media_type.corpusTextNgramInfo:
                sf = [class_info.subject_topic for class_info in
                        media_type.corpusTextNgramInfo \
                            .textClassificationInfo.all()]
                if sf != ['']:
                    result.extend(sf)
            if media_type.corpusImageInfo:
                sf = [class_info.subject_topic for class_info in
                        media_type.corpusImageInfo \
                            .imageclassificationinfotype_model_set.all()]
                if sf != ['']:
                    result.extend(sf)

        return result
