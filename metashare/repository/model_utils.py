"""
Methods for model data conversion between different representations.
"""

import logging

from django.db.models import OneToOneField, Sum

from metashare.repository.models import resourceInfoType_model, \
    corpusInfoType_model, lexicalConceptualResourceInfoType_model, \
    languageDescriptionInfoType_model, toolServiceInfoType_model
from metashare.settings import LOG_HANDLER
from metashare.stats.models import LRStats


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)


def get_related_models(instance, parent):
    """
    Returns a list containing model names of classes that reference instance.
    
    Related models for a given class X are all classes Y that have a relation
    set to X via a ForeignKey field.
    """
    LOGGER.info('get_related_models({0}) called.'.format(
      instance.__class__.__name__))
    
    # If a parent is given, compute the corresponding parent_set String.
    parent_set = None
    if parent:
        parent_set = '{0}_set'.format(parent).lower()
    
    # Related model class names should have this suffix.
    related_suffix = '_{0}'.format(instance.__class__.__name__)
    
    result = []
    for name in dir(instance):
        if name.endswith('_set'):
            if name != parent_set:
                model_instance = getattr(instance, name)
                model_name = model_instance.model.__name__
                
                LOGGER.info('{0} ({1})'.format(name, model_name))
                
                if model_name.endswith(related_suffix):
                    result.append(model_name)
    
    return result


def get_root_resources(*instances):
    """
    Returns the set of `resourceInfoType_model` instances which somewhere
    contain the given model instances.
    
    If any of the given instances is a `resourceInfoType_model` itself, then
    this instance will be in the returned set, too. The returned set can be
    empty.
    """
    return _get_root_resources(set(), *instances)


def _get_root_resources(ignore, *instances):
    """
    Returns the set of `resourceInfoType_model` instances which somewhere
    contain the given model instances.
    
    If any of the given instances is a `resourceInfoType_model` itself, then
    this instance will be in the returned set, too. The returned set can be
    empty. All instances which are found in the given ignore set will not be
    looked at. The ignore set will be extended with the given instances.
    """
    result = set()
    for instance in instances:
        if instance in ignore:
            continue
        ignore.add(instance)

        # `resourceInfoType_model` instances are our actual results
        if isinstance(instance, resourceInfoType_model):
            result.add(instance)
        # an instance may be None, in which case we ignore it
        elif instance:
            # There are 3 possibilities for going backward in our model graph:

            # case (1): we have to follow a `ForeignKey` with a name starting
            #   with "back_to_":
            for rel in [r for r in instance._meta.get_all_field_names()
                        if r.startswith('back_to_')]:
                result.update(_get_root_resources(ignore,
                                                  getattr(instance, rel)))

            # case (2): we have to follow "reverse" `ForeignKey`s and
            #   `OneToOneField`s which are pointing at the current instance from
            #   a model which is closer to the searched root model:
            for rel in instance._meta.get_all_related_objects():
                accessor_name = rel.get_accessor_name()
                # the accessor name may point to a field which is None, so test
                # first, if a field instance is actually available (?)
                if hasattr(instance, accessor_name):
                    accessor = getattr(instance, accessor_name)
                    if isinstance(rel.field, OneToOneField):
                        # in the case of `OneToOneField`s the accessor is the
                        # new instance itself
                        result.update(_get_root_resources(ignore, accessor))
                    else:
                        result.update(_get_root_resources(ignore,
                                                          *accessor.all()))

            # case (2): we have to follow the "reverse" part of a `ManyToMany`
            #   field which is pointing at the current instance from a model
            #   which is closer to the searched root model:
            for rel in instance._meta.get_all_related_many_to_many_objects():
                result.update(_get_root_resources(ignore,
                        *getattr(instance, rel.get_accessor_name()).all()))

    return result


def get_resource_linguality_infos(res_obj):
    """
    Returns a list of all linguality types of the given language resource
    instance.
    """
    result = []
    corpus_media = res_obj.resourceComponentType.as_subclass()

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


def get_resource_license_types(res_obj):
    """
    Returns a list of license under which the given language resource is
    available.
    """
    return [licence for licence_info in
            res_obj.distributionInfo.licenceinfotype_model_set.all()
            for licence in licence_info.get_licence_display_list()]

def get_resource_attribution_texts(res_obj):
    """
    Returns a list of attribution texts for the given resource. The attribution
    texts that are collected, are only in the default language
    """
    return [licence_info.get_default_attributionText() for licence_info in
            res_obj.distributionInfo.licenceinfotype_model_set.iterator() \
            if licence_info.get_default_attributionText()]

def get_resource_media_types(res_obj):
    """
    Returns a list of all media types of the given language resource instance.
    """
    result = []
    corpus_media = res_obj.resourceComponentType.as_subclass()

    if isinstance(corpus_media, corpusInfoType_model):
        media_type = corpus_media.corpusMediaType
        for corpus_info in media_type.corpustextinfotype_model_set.all():
            result.append(corpus_info.mediaType)
        if media_type.corpusAudioInfo:
            result.append(media_type.corpusAudioInfo.mediaType)
        for corpus_info in media_type.corpusvideoinfotype_model_set.all():
            result.append(corpus_info.mediaType)
        if media_type.corpusTextNgramInfo:
            result.append(media_type.corpusTextNgramInfo.mediaType)
        if media_type.corpusImageInfo:
            result.append(media_type.corpusImageInfo.mediaType)
        if media_type.corpusTextNumericalInfo:
            result.append(media_type.corpusTextNumericalInfo.mediaType)

    elif isinstance(corpus_media, lexicalConceptualResourceInfoType_model):
        lcr_media_type = corpus_media.lexicalConceptualResourceMediaType
        if lcr_media_type.lexicalConceptualResourceTextInfo:
            result.append(
                lcr_media_type.lexicalConceptualResourceTextInfo.mediaType)
        if lcr_media_type.lexicalConceptualResourceAudioInfo:
            result.append(
                lcr_media_type.lexicalConceptualResourceAudioInfo.mediaType)
        if lcr_media_type.lexicalConceptualResourceVideoInfo:
            result.append(
                lcr_media_type.lexicalConceptualResourceVideoInfo.mediaType)
        if lcr_media_type.lexicalConceptualResourceImageInfo:
            result.append(
                lcr_media_type.lexicalConceptualResourceImageInfo.mediaType)

    elif isinstance(corpus_media, languageDescriptionInfoType_model):
        ld_media_type = corpus_media.languageDescriptionMediaType
        if ld_media_type.languageDescriptionTextInfo:
            result.append(ld_media_type.languageDescriptionTextInfo.mediaType)
        if ld_media_type.languageDescriptionVideoInfo:
            result.append(ld_media_type.languageDescriptionVideoInfo.mediaType)
        if ld_media_type.languageDescriptionImageInfo:
            result.append(ld_media_type.languageDescriptionImageInfo.mediaType)

    elif isinstance(corpus_media, toolServiceInfoType_model):
        if corpus_media.inputInfo:
            result.extend(corpus_media.inputInfo \
                          .get_mediaType_display_list())
        if corpus_media.outputInfo:
            result.extend(corpus_media.outputInfo \
                          .get_mediaType_display_list())

    result_lower = []
    for res in result:
        result_lower.append(res.lower())

    return result_lower

def get_lr_stat_action_count(obj_identifier, stats_action):
    """
    Returns the count of the given stats action for the given resource instance.
    
    The obj_identifier is the identifier from the storage object.
    """
    result = LRStats.objects.filter(lrid=obj_identifier, action=stats_action) \
        .aggregate(Sum('count'))['count__sum']
    # `result` may be None in case the filter doesn't match any LRStats for the
    # specified resource and action
    if result is not None:
        return result
    else:
        return 0

def get_lr_master_url(resource):
    """
    Returns the full URL of the master copy of the given resource object.
    
    This URL points to the single resource view of the resource on the resource'
    master node.
    """
    return "{0}/{1}".format(resource.storage_object.source_url,
                            resource.get_relative_url())
