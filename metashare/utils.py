'''
This file holds globally useful utility functions,
i.e. functions that are generic enough not to be
specific to one app.
'''

def find_first_uppercase(astring):
    '''
    Return the position of the first uppercase character in astring,
    or -1 if there is no such character
    '''
    if astring is None:
        return -1
    for i in range(0, len(astring)):
        if astring[i].isupper():
            return i
    return -1


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
        
