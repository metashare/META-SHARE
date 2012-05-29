'''
A number of utility functions and classes which do not easily fit into a single place.
To avoid circular imports, this file must not import anything from metashare.repository.editor. 
'''

# inline names included in fieldsets are prepended with an '_'
def encode_as_inline(name):
    return '_' + name

def decode_inline(fieldname):
    if fieldname.startswith('_'):
        name = fieldname[1:]
        return name
    else:
        return fieldname

def is_inline(fieldname):
    if fieldname.startswith('_'):
        return True
    else:
        return False
