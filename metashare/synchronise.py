"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import os
import sys
from datetime import datetime
from xml.etree import ElementTree as etree
from traceback import format_exc
from urllib import urlopen

def _import_xml_from_string(x, y):
    """
    Reminder that actual import XML code has to be integrated here.
    """
    _msg = "XML upload code needs to be integrated!"
    raise NotImplementedError, _msg

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
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
    sys.path.append(PROJECT_HOME)
    from metashare.storage.models import StorageServer, StorageObject
    from metashare.settings import DEBUG
    
    for storage_server in StorageServer.objects.all():
        if storage_server.is_local_server():
            continue
        
        try:
            _sync_url = storage_server.synchronise()
            
            # Retrieve exported XML data from the URL.
            _handle = urlopen(_sync_url)
            _xml_data = _handle.read()
            _handle.close()

            # Parse exported XML data into tree object.
            _xml_tree = etree.fromstring(_xml_data)
            if DEBUG:
                print _xml_tree.findall('storage-object')

            # Iterate over all <storage-oject> nodes and handle them.
            for _xml in _xml_tree.findall('storage-object'):
                _storage_object_xml = etree.tostring(_xml)
                _identifier = _xml.findtext('identifier')
                _metadata = etree.tostring(_xml.find('metadata/*'))

                # Check if the storage object instance already exists.
                _storage_object = StorageObject.objects.filter(
                  identifier=_identifier)

                # If already existing, update storage object attributes.
                if _storage_object:
                    _storage_object = _storage_object[0]
                    _storage_object.source = storage_server
                    _storage_object.checksum = _xml.findtext('checksum')
                    _storage_object.revision = _xml.findtext('revision')
                    _storage_object.deleted = _xml.findtext('deleted') == True
                    _storage_object.metadata = _metadata
                    _storage_object.published = True
                    
                    # In order to allow the corresponding objects to be saved,
                    #   we have to turn the storage object into a temporary
                    #   master copy;  otherwise, ResourceInfo.save() fails.
                    _storage_object.master_copy = True
                    _storage_object.save()

                # Otherwise, create a new storage object.
                else:
                    _storage_object = StorageObject.objects.create(
                      identifier=_identifier, source=storage_server,
                      metadata=_metadata)
                    _storage_object.checksum = _xml.findtext('checksum')
                    _storage_object.revision = _xml.findtext('revision')
                    _storage_object.deleted = _xml.findtext('deleted') == True
                    _storage_object.published = True
                    _storage_object.save()

                # Create corresponding objects and disable master copy flag.
                _import_xml_from_string(_metadata, _storage_object)
                _storage_object.master_copy = False
                _storage_object.save()
                
                print "Imported '{0}'.".format(_identifier)

            storage_server.updated = datetime.now()
            storage_server.save()
        
        except:
            print "Error: could not synchronise storage server '{0}'!".format(
              storage_server.shortname)
            
            if DEBUG:
                print format_exc()
            continue
