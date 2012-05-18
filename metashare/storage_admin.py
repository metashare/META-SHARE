"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import os
import sys
from traceback import format_exc

def _import_xml_from_string(x, y):
    """
    Reminder that actual import XML code has to be integrated here.
    """
    _msg = "XML upload code needs to be integrated!"
    raise NotImplementedError, _msg

USAGE_INFORMATION = {
  'help': {
    'required': ('MODE',),
    'optional': (),
    'description': 'Prints usage instructions for the given MODE.'
  },
  'create': {
    'required': ('xml-file',),
    'optional': (),
    'description': 'Allows to create a new storage object from the given ' \
      'XML file.\n\tThis will also create all corresponding object instances.'
  },
  'update': {
    'required': ('object-id', 'xml-file'),
    'optional': (),
    'description': 'Updates the storage object instance with the given ' \
      'identifier using the contents of the given XML file.'
  },
  'checksum': {
    'required': ('object-id',),
    'optional': (),
    'description': 'Updates the checksum for the storage object instance ' \
      'with the given identifier.'
  },
  'folder': {
    'required': ('object-id',),
    'optional': (),
    'description': 'Prints the storage folder path for the given object id.'
  },
  'delete': {
    'required': ('object-id',),
    'optional': (),
    'description': 'NOT IMPLEMENTED YET'
  },
  'purge': {
    'required': (),
    'optional': (),
    'description': 'Removes outdated and invalid objects/folders from the ' \
      'storage base.\n\tEmpty folders are removed directly, non-empty ' \
      'folders will be prefixed\n\twith DELETED-<folder-name> to flag them.'
  }
}


def create(xml_file):
    """
    Creates a new storage object instance for the given XML file.
    
    This also creates all corresponding object instances.
    """
    # Check if the given input file exists.
    if not os.path.exists(xml_file):
        print "Error: input file '{0}' does not exist!".format(xml_file)
        sys.exit(-1)
    
    with open(xml_file, 'r') as _handle:
        _metadata = _handle.read()
        storage_object = StorageObject.objects.create(metadata=_metadata)
        
        try:
            _import_xml_from_string(_metadata, storage_object)
            storage_object.published = True
            storage_object.save()
        
        except:
            print format_exc()
            storage_object.delete()
            print "Error: could not create object model instances, aborting!"
            return
    
    #statistics call
    #saveLRStats("", storage_object.identifier, "", UPDATE_STAT)
    
    print "Success: created new storage object {0} with id '{1}'.".format(
      storage_object, storage_object.identifier)

def update(object_id, xml_file):
    """
    Updates the storage object instance with the given object_id using the
    contents of the given XML file.
    """
    # Check if the given input file exists.
    if not os.path.exists(xml_file):
        print "Error: input file '{0}' does not exist!".format(xml_file)
        sys.exit(-1)
    
    # Check that the storage object instance exists.
    storage_object = StorageObject.objects.filter(identifier=object_id)
    if not storage_object:
        print "Error: no storage object with the given identifier exists!"
        return
    
    else:
        storage_object = storage_object[0]
    
    with open(xml_file, 'r') as _handle:
        _metadata = _handle.read()
        
        try:
            _import_xml_from_string(_metadata, storage_object)
        
        except:
            print format_exc()
            print "Error: could not update object model instances, aborting!"
            return
        
        storage_object.metadata = _metadata
        storage_object.save()

    #statistics call
    #saveLRStats("", storage_object.identifier, "", UPDATE_STAT)
    
    print "Success: updated storage object {0} with id '{1}'.".format(
      storage_object, storage_object.identifier)

def checksum(object_id):
    """
    Updates the checksum for the storage object with the given object_id.
    """
    # Check that the storage object instance exists.
    storage_object = StorageObject.objects.filter(identifier=object_id)
    if not storage_object:
        print "Error: no storage object with the given identifier exists!"
        return
    
    else:
        storage_object = storage_object[0]
    
    storage_object.save()
    print "Checksum: {0}".format(storage_object.checksum)

def folder(object_id):
    """
    Prints the storage folder path for the given object_id.
    """
    # Check that the storage object instance exists.
    storage_object = StorageObject.objects.filter(identifier=object_id)
    if not storage_object:
        print "Error: no storage object with the given identifier exists!"
        return
    
    else:
        storage_object = storage_object[0]
    
    print "Storage folder: {0}".format(storage_object._storage_folder())

def purge():
    """
    Removes outdated and invalid objects/folders from the storage base.
    
    Empty folders are removed directly, non-empty folders will be prefixed
    with DELETED-<folder-name> to flag them.
    """
    _total = 0
    _deleted = 0
    _renamed = 0
    for identifier in os.listdir(STORAGE_PATH):
        if not len(identifier) == 64:
            continue
        
        _total += 1
        if not StorageObject.objects.filter(identifier=identifier).exists():
            _old_name = '{0}/{1}'.format(STORAGE_PATH, identifier)
            _new_name = '{0}/DELETED-{1}'.format(STORAGE_PATH, identifier)
            try:
                os.rmdir(_old_name)
                _deleted += 1
            
            except OSError:
                os.rename(_old_name, _new_name)
                _renamed += 1
    
    print "Done.  Total: {0}, Deleted: {1}, Renamed: {2}".format(_total,
      _deleted, _renamed)

def print_usage(tool):
    """
    Prints basic usage information for this script.
    """
    print "\n\tusage: {0} MODE ARGS...\n".format(tool)
    print "\tMODE = [{0}]".format(', '.join(USAGE_INFORMATION.keys()))
    print "\tUse {0} help MODE for detailed usage instructions.\n".format(tool)

def print_description(tool, mode):
    """
    Prints detailed usage information for the given mode of operation.
    """
    _required = '> <'.join(USAGE_INFORMATION[mode]['required'])
    if _required:
        _required = '<{0}>'.format(_required)
    _optional = '] ['.join(USAGE_INFORMATION[mode]['optional'])
    if _optional:
        _optional = '[{0}]'.format(_optional)
    print "\n\tusage: {0} {1} {2} {3}\n".format(tool, mode, _required,
      _optional)
    print "\t{0}\n".format(USAGE_INFORMATION[mode]['description'])

try:
    import settings # Assumed to be in the same directory.

except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the " \
      "directory containing %r. It appears you've customized things.\n" \
      "You'll have to run django-admin.py, passing it your settings " \
      "module.\n(If the file settings.py does indeed exist, it's causing" \
      " an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/../")
    sys.path.append(PROJECT_HOME)
    from metashare.storage.models import StorageObject
    from metashare.settings import STORAGE_PATH
    #from metashare.stats.model_utils import saveLRStats, UPDATE_STAT
    
    # Check command line parameters first.
    if len(sys.argv) < 2 or sys.argv[1] not in USAGE_INFORMATION.keys():
        print_usage(sys.argv[0])
        sys.exit(-1)
    
    # Process help requests.
    if sys.argv[1] == 'help':
        if len(sys.argv) < 3 or sys.argv[2] not in USAGE_INFORMATION.keys():
            print_usage(sys.argv[0])
        
        else:
            print_description(sys.argv[0], sys.argv[2])
        
        sys.exit(-1)
    
    # Check that we have enough command line parameters for the chosen MODE.
    if not len(sys.argv) == 2 + len(USAGE_INFORMATION[sys.argv[1]]['required']):
        print_description(sys.argv[0], sys.argv[1])
        sys.exit(-1)
    
    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    
    MODE = sys.argv[1]
    if MODE == 'create':
        create(sys.argv[2])
    
    elif MODE == 'update':
        update(sys.argv[2], sys.argv[3])
    
    elif MODE == 'checksum':
        checksum(sys.argv[2])
    
    elif MODE == 'folder':
        folder(sys.argv[2])
    
    elif MODE == 'purge':
        purge()
    
