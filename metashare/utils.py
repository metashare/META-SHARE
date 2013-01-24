'''
This file holds globally useful utility classes and functions, i.e., classes and
functions that are generic enough not to be specific to one app.
'''
import logging
import os
import re
import sys
from datetime import tzinfo, timedelta

from django.conf import settings


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)

# try to import the `fcntl` module for locking support through the `Lock` class
# below
try:
    import fcntl
except ImportError:
    LOGGER.warn("Locking support is not available for your (non-Unix?) system. "
            "Using multiple processes might not be safe.")


def get_class_by_name(module_name, class_name):
    '''
    Given the name of a module (e.g., 'metashare.resedit.admin')
    and the name of a class (e.g., 'ContactSMI'),
    return the class type object (in the example, the class ContactSMI).
    If no such class exists, throws an AttributeError
    '''
    try:
        class_type = getattr(sys.modules[module_name], class_name)
        return class_type
    except AttributeError:
        raise AttributeError("Module '{0}' has no class '{1}'".format(module_name, class_name))


def verify_subclass(subclass, superclass):
    '''
    Verify that subclass is indeed a subclass of superclass.
    If that is not the case, a TypeError is raised.
    '''
    if not issubclass(subclass, superclass):
        raise TypeError('class {0} is not a subclass of class {1}'.format(subclass, superclass))


def prettify_camel_case_string(cc_str):
    '''
    Prettifies the given camelCase string so that it is better readable.
    
    For example, "speechAnnotation-soundToTextAlignment" is converted to "Speech
    Annotation - Sound To Text Alignment". N.B.: The conversion currently only
    recognizes boundaries with ASCII letters.
    '''
    result = cc_str
    if len(result) > 1:
        result = result.replace('-', ' - ')
        result = re.sub(r'(.)(?=[A-Z][a-z])', r'\1 ', result)
        result = ' '.join([(len(token) > 1 and (token[0].upper() + token[1:]))
                           or token[0].upper() for token in result.split()])
    return result


def create_breadcrumb_template_params(model, action):
    '''
    Create a dictionary for breadcrumb templates.
    '''
    opts = model._meta

    dictionary = {
                  'app_label': opts.app_label,
                  'verbose_name': opts.verbose_name,
                  'action': action,
                 }
    
    return dictionary


class Lock():
    """
    Each instance of this class can be used to acquire an exclusive, system-wide
    (multi-process) lock on a particular name.
    
    This class will only work on Unix systems viz. systems that provide the
    `fcntl` module. On other systems the class will silently do nothing.
    """
    def __init__(self, lock_name):
        """
        Create a `Lock` object which can create an exclusive lock on the given
        name.
        """
        if 'fcntl' in sys.modules:
            self.handle = open(os.path.join(settings.LOCK_DIR, lock_name), 'w')
        else:
            self.handle = None

    def acquire(self):
        """
        Acquire a lock on the name for which this `Lock` was created.
        """
        if self.handle:
            fcntl.flock(self.handle, fcntl.LOCK_EX)

    def release(self):
        """
        Release any lock on the name for which this `Lock` was created.
        """
        if self.handle:
            fcntl.flock(self.handle, fcntl.LOCK_UN)

    def __del__(self):
        if self.handle:
            self.handle.close()


class SimpleTimezone(tzinfo):
    """
    A fixed offset timezone with an unknown name and an unknown DST adjustment.
    """
    def __init__(self, offset):
        self.__offset = timedelta(minutes=offset)

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return None

    def dst(self, dt):
        return None
