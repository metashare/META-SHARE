"""
Project: META-SHARE version v1 release
 Author: Christian Federmann <cfedermann@dfki.de>

Methods for model data conversion between different representations.
"""

import logging
from metashare.settings import LOG_LEVEL, LOG_HANDLER

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
