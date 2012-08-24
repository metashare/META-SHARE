'''
This file holds globally useful utility classes and functions, i.e., classes and
functions that are generic enough not to be specific to one app.
'''
from datetime import tzinfo, timedelta


def get_class_by_name(module_name, class_name):
    '''
    Given the name of a module (e.g., 'metashare.resedit.admin')
    and the name of a class (e.g., 'ContactSMI'),
    return the class type object (in the example, the class ContactSMI).
    If no such class exists, throws an AttributeError
    '''
    import sys
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
