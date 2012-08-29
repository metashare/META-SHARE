"""
Methods for model data conversion between different representations.
"""

import logging

from django.db.models import OneToOneField, Sum

from metashare.repository.models import resourceInfoType_model
from metashare.settings import LOG_LEVEL, LOG_HANDLER
from metashare.stats.models import LRStats


# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repository.model_utils')
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
