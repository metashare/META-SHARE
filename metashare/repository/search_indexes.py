import logging
import os
import re

from haystack.indexes import CharField, IntegerField, RealTimeSearchIndex
from haystack import indexes, connections as haystack_connections, \
    connection_router as haystack_connection_router

from django.db.models import signals
from django.utils.translation import ugettext as _
from unidecode import unidecode

from metashare.repository import model_utils
from metashare.repository.models import resourceInfoType_model, \
    corpusInfoType_model, \
    toolServiceInfoType_model, lexicalConceptualResourceInfoType_model, \
    languageDescriptionInfoType_model
from metashare.repository.search_fields import LabeledCharField, \
    LabeledMultiValueField
from metashare.storage.models import StorageObject, INGESTED, PUBLISHED
from metashare.settings import LOG_HANDLER
from metashare.stats.model_utils import DOWNLOAD_STAT, VIEW_STAT


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)


def update_lr_index_entry(res_obj):
    """
    Updates/creates the search index entry for the given language resource
    object.
    
    The appropriate search index is automatically chosen.
    """
    haystack_connections[haystack_connection_router.for_write()] \
        .get_unified_index().get_index(resourceInfoType_model) \
        .update_object(res_obj)


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
    # search fields are defined in templates/search/indexes/repository/resourceinfotype_model_text.txt 
    text = CharField(document=True, use_template=True, stored=False)

    # view and download counts of the resource
    dl_count = IntegerField(stored=False)
    view_count = IntegerField(stored=False)

    # list of sorting results
    # the access to the sorting results is made in the MetashareFacetedSearchView function of views.py
    resourceNameSort = CharField(indexed=True, faceted=True)
    resourceTypeSort = CharField(indexed=True, faceted=True)
    mediaTypeSort = CharField(indexed=True, faceted=True)
    languageNameSort = CharField(indexed=True, faceted=True)

    # list of filters
    #
    # filter fields are described using:
    #   - label: the display of the filter in the interface,
    #   - facet_id: a unique id per filter,
    #   - parent_id: used for sub filters, indicates which filter is the parent of a sub filter
    #       (parent_id=0 is mandatory for top filters)
    #   - faceted=True: mandatory to indicate the field is a filter
    #
    # notice: variable names must end by "Filter"
    #
    # important notice: the definition of the variable name is important for sub filters:
    #   The item name of the sub filter must be lower cased for (e.g. textngram),
    #     then followed by the sub filter name with the first character upper cased (e.g. textngramOrder),
    #     and finalised with "Filter" (e.g. textngramOrderFilter). Otherwise, another item of the same top filter
    #     could be considered as parent (here, for instance, "text" instead of "textngram")
    #
    # for each filter, a facet function must be added to "SearchQuerySet()" in urls.py
    #   (e.g. .facet("textngramOrderFilter"), the function parameter corresponding to the variable name of the filter
    #
    # the creation of the filter structure is made in the _create_filters_structure function of views.py
    languageNameFilter = LabeledMultiValueField(
                                label=_('Language'), facet_id=1, parent_id=0,
                                faceted=True)
    resourceTypeFilter = LabeledMultiValueField(
                                label=_('Resource Type'), facet_id=2, parent_id=0,
                                faceted=True)
    mediaTypeFilter = LabeledMultiValueField(
                                label=_('Media Type'), facet_id=3, parent_id=0,
                                faceted=True)
    availabilityFilter = LabeledCharField(
                                label=_('Availability'), facet_id=4, parent_id=0,
                                faceted=True)
    licenceFilter = LabeledMultiValueField(
                                label=_('Licence'), facet_id=5, parent_id=0,
                                faceted=True)
    restrictionsOfUseFilter = LabeledMultiValueField(
                                label=_('Restrictions of Use'), facet_id=6, parent_id=0,
                                faceted=True)
    validatedFilter = LabeledMultiValueField(
                                label=_('Validated'), facet_id=7, parent_id=0,
                                faceted=True)
    foreseenUseFilter = LabeledMultiValueField(
                                label=_('Foreseen Use'), facet_id=8, parent_id=0,
                                faceted=True)
    useNlpSpecificFilter = LabeledMultiValueField(
                                label=_('Use Is NLP Specific'), facet_id=9, parent_id=0,
                                faceted=True)
    lingualityTypeFilter = LabeledMultiValueField(
                                label=_('Linguality Type'), facet_id=10, parent_id=0,
                                faceted=True)
    multilingualityTypeFilter = LabeledMultiValueField(
                                label=_('Multilinguality Type'), facet_id=11, parent_id=0,
                                faceted=True)
    modalityTypeFilter = LabeledMultiValueField(
                                label=_('Modality Type'), facet_id=12, parent_id=0,
                                faceted=True)
    mimeTypeFilter = LabeledMultiValueField(
                                label=_('MIME Type'), facet_id=13, parent_id=0,
                                faceted=True)
    bestPracticesFilter = LabeledMultiValueField(
                                label=_('Conformance to Standards/Best Practices'), facet_id=14, parent_id=0,
                                faceted=True)
    domainFilter = LabeledMultiValueField(
                                label=_('Domain'), facet_id=15, parent_id=0,
                                faceted=True)
    geographicCoverageFilter = LabeledMultiValueField(
                                label=_('Geographic Coverage'), facet_id=16, parent_id=0,
                                faceted=True)
    timeCoverageFilter = LabeledMultiValueField(
                                label=_('Time Coverage'), facet_id=17, parent_id=0,
                                faceted=True)
    subjectFilter = LabeledMultiValueField(
                                label=_('Subject'), facet_id=18, parent_id=0,
                                faceted=True)

    corpusAnnotationTypeFilter = LabeledMultiValueField(
                                label=_('Annotation Type'), facet_id=19, parent_id=2,
                                faceted=True)
    corpusAnnotationFormatFilter = LabeledMultiValueField(
                                label=_('Annotation Format'), facet_id=20, parent_id=2,
                                faceted=True)
    languageDescriptionLDTypeFilter = LabeledMultiValueField(
                                label=_('Language Description Type'), facet_id=21, parent_id=2,
                                faceted=True)
    languageDescriptionEncodingLevelFilter = LabeledMultiValueField(
                                label=_('Encoding Level'), facet_id=22, parent_id=2,
                                faceted=True)
    languageDescriptionGrammaticalPhenomenaCoverageFilter = LabeledMultiValueField(
                                label=_('Grammatical Phenomena Coverage'), facet_id=23, parent_id=2,
                                faceted=True)
    lexicalConceptualResourceLRTypeFilter = LabeledMultiValueField(
                                label=_('Lexical/Conceptual Resource Type'), facet_id=24, parent_id=2,
                                faceted=True)
    lexicalConceptualResourceEncodingLevelFilter = LabeledMultiValueField(
                                label=_('Encoding Level'), facet_id=25, parent_id=2,
                                faceted=True)
    lexicalConceptualResourceLinguisticInformationFilter = LabeledMultiValueField(
                                label=_('Linguistic Information'), facet_id=26, parent_id=2,
                                faceted=True)

    toolServiceToolServiceTypeFilter = LabeledMultiValueField(
                                label=_('Tool/Service Type'), facet_id=27, parent_id=2,
                                faceted=True)
    toolServiceToolServiceSubTypeFilter = LabeledMultiValueField(
                                label=_('Tool/Service Subtype'), facet_id=28, parent_id=2,
                                faceted=True)
    toolServiceLanguageDependentTypeFilter = LabeledMultiValueField(
                                label=_('Language Dependent'), facet_id=29, parent_id=2,
                                faceted=True)
    toolServiceInputOutputResourceTypeFilter = LabeledMultiValueField(
                                label=_('InputInfo/OutputInfo Resource Type'), facet_id=30, parent_id=2,
                                faceted=True)
    toolServiceInputOutputMediaTypeFilter = LabeledMultiValueField(
                                label=_('InputInfo/OutputInfo Media Type'), facet_id=31, parent_id=2,
                                faceted=True)
    toolServiceAnnotationTypeFilter = LabeledMultiValueField(
                                label=_('Annotation Type'), facet_id=32, parent_id=2,
                                faceted=True)
    toolServiceAnnotationFormatFilter = LabeledMultiValueField(
                                label=_('Annotation Format'), facet_id=33, parent_id=2,
                                faceted=True)
    toolServiceEvaluatedFilter = LabeledMultiValueField(
                                label=_('Evaluated'), facet_id=34, parent_id=2,
                                faceted=True)
    #Start sub filters
    textTextGenreFilter = LabeledMultiValueField(
                                label=_('Text Genre'), facet_id=35, parent_id=3,
                                faceted=True)
    textTextTypeFilter = LabeledMultiValueField(
                                label=_('Text Type'), facet_id=36, parent_id=3,
                                faceted=True)
    textRegisterFilter = LabeledMultiValueField(
                                label=_('Register'), facet_id=37, parent_id=3,
                                faceted=True)
    audioAudioGenreFilter = LabeledMultiValueField(
                                label=_('Audio Genre'), facet_id=38, parent_id=3,
                                faceted=True)
    audioSpeechGenreFilter = LabeledMultiValueField(
                                label=_('Speech Genre'), facet_id=39, parent_id=3,
                                faceted=True)
    audioRegisterFilter = LabeledMultiValueField(
                                label=_('Register'), facet_id=40, parent_id=3,
                                faceted=True)
    audioSpeechItemsFilter = LabeledMultiValueField(
                                label=_('Speech Items'), facet_id=41, parent_id=3,
                                faceted=True)
    audioNaturalityFilter = LabeledMultiValueField(
                                label=_('Naturality'), facet_id=42, parent_id=3,
                                faceted=True)
    audioConversationalTypeFilter = LabeledMultiValueField(
                                label=_('Conversational Type'), facet_id=43, parent_id=3,
                                faceted=True)
    audioScenarioTypeFilter = LabeledMultiValueField(
                                label=_('Scenario Type'), facet_id=44, parent_id=3,
                                faceted=True)
    videoVideoGenreFilter = LabeledMultiValueField(
                                label=_('Video Genre'), facet_id=45, parent_id=3,
                                faceted=True)
    videoTypeOfVideoContentFilter = LabeledMultiValueField(
                                label=_('Type of Video Content'), facet_id=46, parent_id=3,
                                faceted=True)
    videoNaturalityFilter = LabeledMultiValueField(
                                label=_('Naturality'), facet_id=47, parent_id=3,
                                faceted=True)
    videoConversationalTypeFilter = LabeledMultiValueField(
                                label=_('Conversational Type'), facet_id=48, parent_id=3,
                                faceted=True)
    videoScenarioTypeFilter = LabeledMultiValueField(
                                label=_('Scenario Type'), facet_id=49, parent_id=3,
                                faceted=True)
    imageImageGenreFilter = LabeledMultiValueField(
                                label=_('Image Genre'), facet_id=50, parent_id=3,
                                faceted=True)
    imageTypeOfImageContentFilter = LabeledMultiValueField(
                                label=_('Type of Image Content'), facet_id=51, parent_id=3,
                                faceted=True)
    textnumericalTypeOfTnContentFilter = LabeledMultiValueField(
                                label=_('Type of Text Numerical Content'), facet_id=52, parent_id=3,
                                faceted=True)
    textngramBaseItemFilter = LabeledMultiValueField(
                                label=_('Base Item'), facet_id=53, parent_id=3,
                                faceted=True)
    textngramOrderFilter = LabeledMultiValueField(
                                label=_('Order'), facet_id=54, parent_id=3,
                                faceted=True)
    languageVarietyFilter = LabeledMultiValueField(
                                label=_('Language Variety'), facet_id=55, parent_id=0,
                                faceted=True)

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

        In our case this is a QuerySet containing only published resources that
        have not been deleted, yet.
        """
        return self.read_queryset()

    def read_queryset(self):
        """
        Returns the default QuerySet for read actions.

        In our case this is a QuerySet containing only published resources that
        have not been deleted, yet.
        """
        return self.get_model().objects.filter(storage_object__deleted=False,
            storage_object__publication_status=PUBLISHED)

    def should_update(self, instance, **kwargs):
        '''
        Only index resources that are at least ingested.
        In other words, do not index internal resources.
        '''
        return instance.storage_object.publication_status in (INGESTED, PUBLISHED)

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
            if kwargs["sender"] == StorageObject:
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
        # we better recreate our resource instance from the DB as otherwise it
        # has happened for some reason that the instance was not up-to-date
        instance = self.get_model().objects.get(pk=instance.id)
        # only create/update index entries of published resources
        if instance.storage_object.publication_status == PUBLISHED:
            LOGGER.info("Published resource #{0} scheduled for reindexing." \
                        .format(instance.id))
            super(resourceInfoType_modelIndex, self) \
                .update_object(instance, using=using, **kwargs)
        # make sure that there are no index entries for ingested/unpublished
        # resources
        elif instance.storage_object.publication_status == INGESTED:
            LOGGER.info("Will now remove the ingested resource #{0} from the "
                        "index if it is currently indexed.".format(instance.id))
            super(resourceInfoType_modelIndex, self) \
                .remove_object(instance, using=using, **kwargs)

    def _setup_save(self):
        """
        A hook for controlling what happens when the registered model is saved.

        In this implementation we additionally connect to frequently changed
        parts of the model which is returned by get_model().
        """
        if PatchedRealTimeSearchIndex._signal_setup_done[0]:
            return
        PatchedRealTimeSearchIndex._signal_setup_done[0] = True

        # For efficiency, we watch the storage object for save events only.
        # This relies on resourceInfoType_model.save() to call storage_object.save()
        # every time!
        signals.post_save.connect(self.update_object, sender=StorageObject)
        # This also relies on the fact that all changes relevant to the index
        # are concluded with the resource being saved.
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

    def prepare_dl_count(self, obj):
        """
        Returns the download count for the given resource object.
        """
        return model_utils.get_lr_stat_action_count(
            obj.storage_object.identifier, DOWNLOAD_STAT)

    def prepare_view_count(self, obj):
        """
        Returns the view count for the given resource object.
        """
        return model_utils.get_lr_stat_action_count(
            obj.storage_object.identifier, VIEW_STAT)

    def prepare_resourceNameSort(self, obj):
        """
        Collect the data to sort the Resource Names
        """
        # get the Resource Name
        resourceNameSort = obj.identificationInfo.get_default_resourceName()
        resourceNameSort = unidecode(resourceNameSort)
        # keep alphanumeric characters only
        resourceNameSort = re.sub('[\W_]', '', resourceNameSort)
        # set Resource Name to lower case
        resourceNameSort = resourceNameSort.lower()

        return resourceNameSort

    def prepare_resourceTypeSort(self, obj):
        """
        Collect the data to sort the Resource Types
        """
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
                               corpus_info.languageinfotype_model_set.all()])
            if media_type.corpusAudioInfo:
                result.extend([lang.languageName for lang in
                               media_type.corpusAudioInfo.languageinfotype_model_set.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([lang.languageName for lang in
                               corpus_info.languageinfotype_model_set.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([lang.languageName for lang in
                            media_type.corpusTextNgramInfo.languageinfotype_model_set.all()])
            if media_type.corpusImageInfo:
                result.extend([lang.languageName for lang in
                               media_type.corpusImageInfo.languageinfotype_model_set.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceAudioInfo.languageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceTextInfo.languageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceVideoInfo.languageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([lang.languageName for lang in lcr_media_type \
                        .lexicalConceptualResourceImageInfo.languageinfotype_model_set.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionTextInfo.languageinfotype_model_set.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionVideoInfo.languageinfotype_model_set.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([lang.languageName for lang in ld_media_type \
                            .languageDescriptionImageInfo.languageinfotype_model_set.all()])

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
        resType = obj.resourceComponentType.as_subclass().resourceType
        if resType:
            return [resType]
        return []

    def prepare_mediaTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type
        """
        return model_utils.get_resource_media_types(obj)

    def prepare_availabilityFilter(self, obj):
        """
        Collect the data to filter the resources on Availability
        """
        return obj.distributionInfo.get_availability_display()

    def prepare_licenceFilter(self, obj):
        """
        Collect the data to filter the resources on Licence
        """
        return model_utils.get_resource_license_types(obj)

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
        return model_utils.get_resource_linguality_infos(obj)

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
                        corpus_info.modalityinfotype_model_set.all() for mt in
                        modalityInfo.get_modalityType_display_list()])
            if media_type.corpusAudioInfo:
                result.extend([mt for modalityInfo in
                        media_type.corpusAudioInfo.modalityinfotype_model_set.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([mt for modalityInfo in
                        corpus_info.modalityinfotype_model_set.all() for mt in
                        modalityInfo.get_modalityType_display_list()])
            if media_type.corpusTextNgramInfo and \
                    media_type.corpusTextNgramInfo.modalityInfo:
                result.extend(media_type.corpusTextNgramInfo.modalityInfo \
                              .get_modalityType_display_list())
            if media_type.corpusImageInfo:
                result.extend([mt for modalityInfo in
                               media_type.corpusImageInfo.modalityinfotype_model_set.all()
                               for mt in
                               modalityInfo.get_modalityType_display_list()])
            if media_type.corpusTextNumericalInfo:
                result.extend([mt for modalityInfo in
                        media_type.corpusTextNumericalInfo.modalityinfotype_model_set.all()
                        for mt in modalityInfo.get_modalityType_display_list()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([mt for modalityInfo in lcr_media_type \
                        .lexicalConceptualResourceTextInfo.modalityinfotype_model_set.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([mt for modalityInfo in lcr_media_type \
                        .lexicalConceptualResourceAudioInfo.modalityinfotype_model_set.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([mt for modalityInfo in lcr_media_type \
                        .lexicalConceptualResourceVideoInfo.modalityinfotype_model_set.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([mt for modalityInfo in lcr_media_type \
                        .lexicalConceptualResourceImageInfo.modalityinfotype_model_set.all()
                        for mt in modalityInfo.get_modalityType_display_list()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo and \
                    ld_media_type.languageDescriptionTextInfo.modalityInfo:
                result.extend(ld_media_type.languageDescriptionTextInfo \
                              .modalityInfo.get_modalityType_display_list())
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([mt for modalityInfo in ld_media_type \
                        .languageDescriptionVideoInfo.modalityinfotype_model_set.all()
                        for mt in modalityInfo.get_modalityType_display_list()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([mt for modalityInfo in ld_media_type \
                        .languageDescriptionImageInfo.modalityinfotype_model_set.all()
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
                                      corpus_info.textformatinfotype_model_set.all()])
            if media_type.corpusAudioInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        media_type.corpusAudioInfo.audioformatinfotype_model_set.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                mimeType_list.extend([mimeType.mimeType for mimeType in
                                      corpus_info.videoformatinfotype_model_set.all()])
            if media_type.corpusTextNgramInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        media_type.corpusTextNgramInfo.textformatinfotype_model_set.all()])
            if media_type.corpusImageInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        media_type.corpusImageInfo.imageformatinfotype_model_set.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        lcr_media_type.lexicalConceptualResourceTextInfo \
                            .textformatinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        lcr_media_type.lexicalConceptualResourceAudioInfo \
                            .audioformatinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        lcr_media_type.lexicalConceptualResourceVideoInfo \
                            .videoformatinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        lcr_media_type.lexicalConceptualResourceImageInfo \
                            .imageformatinfotype_model_set.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        ld_media_type.languageDescriptionTextInfo \
                            .textformatinfotype_model_set.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        ld_media_type.languageDescriptionVideoInfo \
                            .videoformatinfotype_model_set.all()])
            if ld_media_type.languageDescriptionImageInfo:
                mimeType_list.extend([mimeType.mimeType for mimeType in
                        ld_media_type.languageDescriptionImageInfo \
                            .imageformatinfotype_model_set.all()])

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
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                for annotation_info in corpus_info.annotationinfotype_model_set.all():
                    result.extend(annotation_info.get_conformanceToStandardsBestPractices_display_list())
            if media_type.corpusAudioInfo:
                for annotation_info in media_type.corpusAudioInfo.annotationinfotype_model_set.all():
                    result.extend(annotation_info.get_conformanceToStandardsBestPractices_display_list())
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                for annotation_info in corpus_info.annotationinfotype_model_set.all():
                    result.extend(annotation_info.get_conformanceToStandardsBestPractices_display_list())
            if media_type.corpusTextNgramInfo:
                for annotation_info in media_type.corpusTextNgramInfo.annotationinfotype_model_set.all():
                    result.extend(annotation_info.get_conformanceToStandardsBestPractices_display_list())
            if media_type.corpusImageInfo:
                for annotation_info in media_type.corpusImageInfo.annotationinfotype_model_set.all():
                    result.extend(annotation_info.get_conformanceToStandardsBestPractices_display_list())
            if media_type.corpusTextNumericalInfo:
                for annotation_info in media_type.corpusTextNumericalInfo.annotationinfotype_model_set.all():
                    result.extend(annotation_info.get_conformanceToStandardsBestPractices_display_list())

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            if corpus_media.lexicalConceptualResourceEncodingInfo:
                result.extend(corpus_media.lexicalConceptualResourceEncodingInfo \
                  .get_conformanceToStandardsBestPractices_display_list())

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            if corpus_media.languageDescriptionEncodingInfo:
                result.extend(corpus_media.languageDescriptionEncodingInfo \
                  .get_conformanceToStandardsBestPractices_display_list())

        elif isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(corpus_media.inputInfo \
                  .get_conformanceToStandardsBestPractices_display_list())
            if corpus_media.outputInfo:
                result.extend(corpus_media.outputInfo \
                  .get_conformanceToStandardsBestPractices_display_list())

        return result

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
                               corpus_info.domaininfotype_model_set.all()])
            if media_type.corpusAudioInfo:
                result.extend([domain_info.domain for domain_info in
                               media_type.corpusAudioInfo.domaininfotype_model_set.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([domain_info.domain for domain_info in
                               corpus_info.domaininfotype_model_set.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([domain_info.domain for domain_info in
                               media_type.corpusTextNgramInfo.domaininfotype_model_set.all()])
            if media_type.corpusImageInfo:
                result.extend([domain_info.domain for domain_info in
                               media_type.corpusImageInfo.domaininfotype_model_set.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([domain_info.domain for domain_info in
                        lcr_media_type.lexicalConceptualResourceTextInfo \
                                .domaininfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([domain_info.domain for domain_info in
                        lcr_media_type.lexicalConceptualResourceAudioInfo \
                                .domaininfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([domain_info.domain for domain_info in
                        lcr_media_type.lexicalConceptualResourceVideoInfo \
                                .domaininfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([domain_info.domain for domain_info in
                        lcr_media_type.lexicalConceptualResourceImageInfo \
                                .domaininfotype_model_set.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([domain_info.domain for domain_info in
                               ld_media_type.languageDescriptionTextInfo \
                                    .domaininfotype_model_set.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([domain_info.domain for domain_info in
                               ld_media_type.languageDescriptionVideoInfo \
                                    .domaininfotype_model_set.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([domain_info.domain for domain_info in
                               ld_media_type.languageDescriptionImageInfo \
                                    .domaininfotype_model_set.all()])

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
                               corpus_info.geographiccoverageinfotype_model_set.all()])
            if media_type.corpusAudioInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               media_type.corpusAudioInfo \
                                    .geographiccoverageinfotype_model_set.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([gc_info.geographicCoverage for gc_info in
                               corpus_info.geographiccoverageinfotype_model_set.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               media_type.corpusTextNgramInfo \
                                    .geographiccoverageinfotype_model_set.all()])
            if media_type.corpusImageInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               media_type.corpusImageInfo \
                                    .geographiccoverageinfotype_model_set.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                        lcr_media_type.lexicalConceptualResourceTextInfo \
                            .geographiccoverageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                        lcr_media_type.lexicalConceptualResourceAudioInfo \
                            .geographiccoverageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                        lcr_media_type.lexicalConceptualResourceVideoInfo \
                            .geographiccoverageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                        lcr_media_type.lexicalConceptualResourceImageInfo \
                            .geographiccoverageinfotype_model_set.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               ld_media_type.languageDescriptionTextInfo \
                                    .geographiccoverageinfotype_model_set.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               ld_media_type.languageDescriptionVideoInfo \
                                    .geographiccoverageinfotype_model_set.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([gc_info.geographicCoverage for gc_info in
                               ld_media_type.languageDescriptionImageInfo \
                                    .geographiccoverageinfotype_model_set.all()])

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
                               corpus_info.timecoverageinfotype_model_set.all()])
            if media_type.corpusAudioInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        media_type.corpusAudioInfo.timecoverageinfotype_model_set.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                               corpus_info.timecoverageinfotype_model_set.all()])
            if media_type.corpusTextNgramInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        media_type.corpusTextNgramInfo.timecoverageinfotype_model_set.all()])
            if media_type.corpusImageInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        media_type.corpusImageInfo.timecoverageinfotype_model_set.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                            lcr_media_type.lexicalConceptualResourceTextInfo \
                                .timecoverageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                            lcr_media_type.lexicalConceptualResourceAudioInfo \
                                .timecoverageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                            lcr_media_type.lexicalConceptualResourceVideoInfo \
                                .timecoverageinfotype_model_set.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                            lcr_media_type.lexicalConceptualResourceImageInfo \
                                .timecoverageinfotype_model_set.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        ld_media_type.languageDescriptionTextInfo \
                            .timecoverageinfotype_model_set.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        ld_media_type.languageDescriptionVideoInfo \
                            .timecoverageinfotype_model_set.all()])
            if ld_media_type.languageDescriptionImageInfo:
                result.extend([timeCoverage.timeCoverage for timeCoverage in
                        ld_media_type.languageDescriptionImageInfo \
                            .timecoverageinfotype_model_set.all()])

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
                    corpus_info.textclassificationinfotype_model_set.all()]
                if sf != ['']:
                    result.extend(sf)
            if media_type.corpusAudioInfo:
                sf = [class_info.subject_topic for class_info in
                    media_type.corpusAudioInfo.audioclassificationinfotype_model_set.all()]
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
                            .textclassificationinfotype_model_set.all()]
                if sf != ['']:
                    result.extend(sf)
            if media_type.corpusImageInfo:
                sf = [class_info.subject_topic for class_info in
                        media_type.corpusImageInfo \
                            .imageclassificationinfotype_model_set.all()]
                if sf != ['']:
                    result.extend(sf)

        return result

    def prepare_corpusAnnotationTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                for annotation_info in corpus_info.annotationinfotype_model_set.all():
                    result.append(annotation_info.get_annotationType_display())
            if media_type.corpusAudioInfo:
                for annotation_info in media_type.corpusAudioInfo.annotationinfotype_model_set.all():
                    result.append(annotation_info.get_annotationType_display())
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                for annotation_info in corpus_info.annotationinfotype_model_set.all():
                    result.append(annotation_info.get_annotationType_display())
            if media_type.corpusTextNgramInfo:
                for annotation_info in media_type.corpusTextNgramInfo.annotationinfotype_model_set.all():
                    result.append(annotation_info.get_annotationType_display())
            if media_type.corpusImageInfo:
                for annotation_info in media_type.corpusImageInfo.annotationinfotype_model_set.all():
                    result.append(annotation_info.get_annotationType_display())
            if media_type.corpusTextNumericalInfo:
                for annotation_info in media_type.corpusTextNumericalInfo.annotationinfotype_model_set.all():
                    result.append(annotation_info.get_annotationType_display())

        return result
    
    def prepare_corpusAnnotationFormatFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                for annotation_info in corpus_info.annotationinfotype_model_set.all():
                    result.append(annotation_info.annotationFormat)
            if media_type.corpusAudioInfo:
                for annotation_info in media_type.corpusAudioInfo.annotationinfotype_model_set.all():
                    result.append(annotation_info.annotationFormat)
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                for annotation_info in corpus_info.annotationinfotype_model_set.all():
                    result.append(annotation_info.annotationFormat)
            if media_type.corpusTextNgramInfo:
                for annotation_info in media_type.corpusTextNgramInfo.annotationinfotype_model_set.all():
                    result.append(annotation_info.annotationFormat)
            if media_type.corpusImageInfo:
                for annotation_info in media_type.corpusImageInfo.annotationinfotype_model_set.all():
                    result.append(annotation_info.annotationFormat)
            if media_type.corpusTextNumericalInfo:
                for annotation_info in media_type.corpusTextNumericalInfo.annotationinfotype_model_set.all():
                    result.append(annotation_info.annotationFormat)

        return result
    
    def prepare_languageDescriptionLDTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        corpus_media = obj.resourceComponentType.as_subclass()
        if isinstance(corpus_media, languageDescriptionInfoType_model):
            return [corpus_media.get_languageDescriptionType_display()]
        return []

    def prepare_languageDescriptionEncodingLevelFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        corpus_media = obj.resourceComponentType.as_subclass()
        if isinstance(corpus_media, languageDescriptionInfoType_model) \
                and corpus_media.languageDescriptionEncodingInfo:
            return corpus_media.languageDescriptionEncodingInfo \
                .get_encodingLevel_display_list()
        return []

    def prepare_languageDescriptionGrammaticalPhenomenaCoverageFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        corpus_media = obj.resourceComponentType.as_subclass()
        if isinstance(corpus_media, languageDescriptionInfoType_model) \
                and corpus_media.languageDescriptionEncodingInfo:
            return corpus_media.languageDescriptionEncodingInfo \
                .get_grammaticalPhenomenaCoverage_display_list()
        return []

    def prepare_lexicalConceptualResourceLRTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for lexicalConceptual
        if isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            result.append(corpus_media.get_lexicalConceptualResourceType_display())

        return result
    
    def prepare_lexicalConceptualResourceEncodingLevelFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for lexicalConceptual
        if isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            if corpus_media.lexicalConceptualResourceEncodingInfo:
                result.extend(corpus_media.lexicalConceptualResourceEncodingInfo. \
                  get_encodingLevel_display_list())

        return result
    
    def prepare_lexicalConceptualResourceLinguisticInformationFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for lexicalConceptual
        if isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            if corpus_media.lexicalConceptualResourceEncodingInfo:
                result.extend(corpus_media.lexicalConceptualResourceEncodingInfo. \
                  get_linguisticInformation_display_list())

        return result
    

    def prepare_toolServiceToolServiceTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for toolService
        if isinstance(corpus_media, toolServiceInfoType_model):
            result.append(corpus_media.get_toolServiceType_display())

        return result
    
    def prepare_toolServiceToolServiceSubTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for toolService
        if isinstance(corpus_media, toolServiceInfoType_model):
            result.extend(corpus_media.toolServiceSubtype)

        return result

    def prepare_toolServiceLanguageDependentTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for toolService
        if isinstance(corpus_media, toolServiceInfoType_model):
            result.append(corpus_media.get_languageDependent_display())

        return result
    
    def prepare_toolServiceInputOutputResourceTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for toolService
        if isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(
                    corpus_media.inputInfo.get_resourceType_display_list())
            if corpus_media.outputInfo:
                result.extend(
                    corpus_media.outputInfo.get_resourceType_display_list())

        return result
    
    def prepare_toolServiceInputOutputMediaTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for toolService
        if isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.append(corpus_media.inputInfo.get_mediaType_display())
            if corpus_media.outputInfo:
                result.append(corpus_media.outputInfo.get_mediaType_display())

        return result
    
    def prepare_toolServiceAnnotationTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(corpus_media.inputInfo.get_annotationType_display_list())
            if corpus_media.outputInfo:
                result.extend(corpus_media.outputInfo.get_annotationType_display_list())

        return result
    
    def prepare_toolServiceAnnotationFormatFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for toolService
        if isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                if corpus_media.inputInfo.annotationFormat:
                    result.extend(corpus_media.inputInfo.annotationFormat)
            if corpus_media.outputInfo:
                if corpus_media.outputInfo.annotationFormat:
                    result.extend(corpus_media.outputInfo.annotationFormat)

        return result
    
    def prepare_toolServiceEvaluatedFilter(self, obj):
        """
        Collect the data to filter the resources on Resource Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for toolService
        if isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.toolServiceEvaluationInfo:
                result.append(corpus_media.toolServiceEvaluationInfo.get_evaluated_display())

        return result

    def prepare_textTextGenreFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([text_classification_info.textGenre \
                  for text_classification_info in corpus_info.textclassificationinfotype_model_set.all()])

        return result

    def prepare_textTextTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([text_classification_info.textType \
                  for text_classification_info in corpus_info.textclassificationinfotype_model_set.all()])

        return result
    
    def prepare_textRegisterFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                result.extend([text_classification_info.register \
                  for text_classification_info in corpus_info.textclassificationinfotype_model_set.all()])

        return result
    
    def prepare_audioAudioGenreFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusAudioInfo:
                result.extend([audio_classification_info.get_audioGenre_display() \
                  for audio_classification_info in media_type.corpusAudioInfo.audioclassificationinfotype_model_set.all()])

        return result
    
    def prepare_audioSpeechGenreFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusAudioInfo:
                result.extend([audio_classification_info.get_speechGenre_display() 
                  for audio_classification_info in media_type.corpusAudioInfo.audioclassificationinfotype_model_set.all()])

        return result
    
    def prepare_audioRegisterFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusAudioInfo:
                result.extend([audio_classification_info.register \
                  for audio_classification_info in media_type.corpusAudioInfo.audioclassificationinfotype_model_set.all()])

        return result
    
    def prepare_audioSpeechItemsFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusAudioInfo:
                if media_type.corpusAudioInfo.audioContentInfo:
                    result.extend([media_type.corpusAudioInfo.audioContentInfo.get_speechItems_display()])

        # Filter for lexical conceptual
        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                if lcr_media_type.lexicalConceptualResourceAudioInfo.audioContentInfo:
                    result.extend([lcr_media_type.lexicalConceptualResourceAudioInfo.audioContentInfo.get_speechItems_display()])

        return result
    
    def prepare_audioNaturalityFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusAudioInfo \
                    and media_type.corpusAudioInfo.settingInfo:
                result.append(media_type.corpusAudioInfo.settingInfo.get_naturality_display())

        return result
    
    def prepare_audioConversationalTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusAudioInfo \
                    and media_type.corpusAudioInfo.settingInfo:
                result.append(media_type.corpusAudioInfo.settingInfo.get_conversationalType_display())

        return result
    
    def prepare_audioScenarioTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusAudioInfo \
                    and media_type.corpusAudioInfo.settingInfo:
                result.append(media_type.corpusAudioInfo.settingInfo.get_scenarioType_display())

        return result
    
    def prepare_videoVideoGenreFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                if corpus_info.videoclassificationinfotype_model_set:
                    result.extend([video_classification_info.videoGenre
                        for video_classification_info
                        in corpus_info.videoclassificationinfotype_model_set.all()
                        if video_classification_info.videoGenre])

        return result
    
    def prepare_videoTypeOfVideoContentFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                if corpus_info.videoContentInfo:
                    result.extend(corpus_info.videoContentInfo \
                                  .typeOfVideoContent)

        # Filter for lexical conceptual
        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceVideoInfo \
                    and lcr_media_type.lexicalConceptualResourceVideoInfo.videoContentInfo:
                result.extend(lcr_media_type.lexicalConceptualResourceVideoInfo \
                              .videoContentInfo.typeOfVideoContent)

        # Filter for language description
        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionVideoInfo \
                    and ld_media_type.languageDescriptionVideoInfo.videoContentInfo:
                result.extend(ld_media_type.languageDescriptionVideoInfo \
                              .videoContentInfo.typeOfVideoContent)

        return result
    
    def prepare_videoNaturalityFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                if corpus_info.settingInfo:
                    result.append(corpus_info.settingInfo.get_naturality_display())

        return result
    
    def prepare_videoConversationalTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                if corpus_info.settingInfo:
                    result.append(corpus_info.settingInfo.get_conversationalType_display())

        return result
    
    def prepare_videoScenarioTypeFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                if corpus_info.settingInfo:
                    result.append(corpus_info.settingInfo.get_scenarioType_display())

        return result
    
    def prepare_imageImageGenreFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusImageInfo:
                for image_classification_info in media_type.corpusImageInfo \
                        .imageclassificationinfotype_model_set.all():
                    if image_classification_info.imageGenre:
                        result.append(image_classification_info.imageGenre)

        return result
    
    def prepare_imageTypeOfImageContentFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        result = []

        corpus_media = obj.resourceComponentType.as_subclass()

        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusImageInfo \
                    and media_type.corpusImageInfo.imageContentInfo:
                result.extend(media_type.corpusImageInfo \
                              .imageContentInfo.typeOfImageContent)

        # Filter for lexical conceptual
        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceImageInfo \
                    and lcr_media_type.lexicalConceptualResourceImageInfo \
                        .imageContentInfo:
                result.extend(lcr_media_type.lexicalConceptualResourceImageInfo \
                              .imageContentInfo.typeOfImageContent)

        # Filter for language description
        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionImageInfo \
                    and ld_media_type.languageDescriptionImageInfo.imageContentInfo:
                result.extend(ld_media_type.languageDescriptionImageInfo \
                              .imageContentInfo.typeOfImageContent)

        return result
    
    def prepare_textnumericalTypeOfTnContentFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        corpus_media = obj.resourceComponentType.as_subclass()
        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusTextNumericalInfo \
                    and media_type.corpusTextNumericalInfo.textNumericalContentInfo:
                return media_type.corpusTextNumericalInfo \
                    .textNumericalContentInfo.typeOfTextNumericalContent
        return []
    
    def prepare_textngramBaseItemFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        corpus_media = obj.resourceComponentType.as_subclass()
        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusTextNgramInfo:
                return [media_type.corpusTextNgramInfo.ngramInfo \
                        .get_baseItem_display()]
        return []

    def prepare_textngramOrderFilter(self, obj):
        """
        Collect the data to filter the resources on Media Type children
        """
        corpus_media = obj.resourceComponentType.as_subclass()
        # Filter for corpus
        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            if media_type.corpusTextNgramInfo:
                return [str(media_type.corpusTextNgramInfo.ngramInfo.order)]
        return []

    def prepare_languageVarietyFilter(self, obj):
        """
        Collect the data to filter the resources on Language Variety
        """
        result = []
        corpus_media = obj.resourceComponentType.as_subclass()

        if isinstance(corpus_media, corpusInfoType_model):
            media_type = corpus_media.corpusMediaType
            for corpus_info in media_type.corpustextinfotype_model_set.all():
                for lang in corpus_info.languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            if media_type.corpusAudioInfo:
                for lang in media_type.corpusAudioInfo.languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            for corpus_info in media_type.corpusvideoinfotype_model_set.all():
                for lang in corpus_info.languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            if media_type.corpusTextNgramInfo:
                for lang in media_type.corpusTextNgramInfo.languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            if media_type.corpusImageInfo:
                for lang in media_type.corpusImageInfo.languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])

        elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
            lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
            if lcr_media_type.lexicalConceptualResourceAudioInfo:
                for lang in lcr_media_type.lexicalConceptualResourceAudioInfo. \
                  languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            if lcr_media_type.lexicalConceptualResourceTextInfo:
                for lang in lcr_media_type.lexicalConceptualResourceTextInfo. \
                  languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            if lcr_media_type.lexicalConceptualResourceVideoInfo:
                for lang in lcr_media_type.lexicalConceptualResourceVideoInfo. \
                  languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            if lcr_media_type.lexicalConceptualResourceImageInfo:
                for lang in lcr_media_type.lexicalConceptualResourceImageInfo. \
                  languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])

        elif isinstance(corpus_media, languageDescriptionInfoType_model):
            ld_media_type = corpus_media.languageDescriptionMediaType
            if ld_media_type.languageDescriptionTextInfo:
                for lang in ld_media_type.languageDescriptionTextInfo. \
                  languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            if ld_media_type.languageDescriptionVideoInfo:
                for lang in ld_media_type.languageDescriptionVideoInfo. \
                  languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])
            if ld_media_type.languageDescriptionImageInfo:
                for lang in ld_media_type.languageDescriptionImageInfo. \
                  languageinfotype_model_set.all():
                    result.extend([variety.languageVarietyName for variety in
                               lang.languageVarietyInfo.all()])

        elif isinstance(corpus_media, toolServiceInfoType_model):
            if corpus_media.inputInfo:
                result.extend(corpus_media.inputInfo.languageVarietyName)
            if corpus_media.outputInfo:
                result.extend(corpus_media.outputInfo.languageVarietyName)

        return result

