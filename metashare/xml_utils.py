#! /usr/bin/env python
"""
Call the external program xdiff to compare two XML files

"""

from subprocess import call, STDOUT
import sys
import os
import logging
from metashare.settings import LOG_LEVEL, LOG_HANDLER, XDIFF_LOCATION
from metashare.stats.model_utils import saveLRStats, UPDATE_STAT
from zipfile import is_zipfile, ZipFile
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.xml_utils')
LOGGER.addHandler(LOG_HANDLER)

CONSOLE = "/dev/null"

def xml_compare(file1, file2, outfile=None):
    """
    Compare two XML files with the external program xdiff.

    Return True, if they are equal, False otherwise.

    """
    if not os.access(XDIFF_LOCATION, os.X_OK):
        LOGGER.error("no executable xdiff binary: {0}".format(XDIFF_LOCATION))
        return False

    if not outfile:
        outfile = "{0}.diff".format(file1)
    
    # If diff-file exists, remove it so that there is no diff after a clean run:
    if os.access(outfile, os.F_OK):
        os.remove(outfile)
        
    for __f in [file1, file2]:
        if not os.path.isfile(__f):
            LOGGER.warning("file {0} does not exist".format(__f))
    
    with open(CONSOLE, "w+") as out:
        retval = call([XDIFF_LOCATION, file1, file2, outfile],
                      stdout=out, stderr=STDOUT)

    return (retval == 0)

if __name__ == "__main__":
    if xml_compare(sys.argv[1], sys.argv[2]):
        print "equal"
    else :
        print "not equal"


def import_from_string(xml_string, targetstatus, owner_id=None):
    """
    Import a single resource from a string representation of its XML tree, 
    and save it with the given target status.
    
    Returns the imported resource object on success, raises and Exception on failure.
    """
    from metashare.repo2.models import resourceInfoType_model
    result = resourceInfoType_model.import_from_string(xml_string)
    
    if not result[0]:
        msg = u''
        if len(result) > 2:
            msg = u'{}'.format(result[2])
        raise Exception(msg)
    
    resource = result[0]
    
    # Set publication_status for new object.
    resource.storage_object.publication_status = targetstatus
    if owner_id:
        resource.owners.add(owner_id)
        
    resource.storage_object.save()

    # Create log ADDITION message for the new object, but only if we have a user:
    if owner_id:
        LogEntry.objects.log_action(
            user_id         = owner_id,
            content_type_id = ContentType.objects.get_for_model(resource).pk,
            object_id       = resource.pk,
            object_repr     = force_unicode(resource),
            action_flag     = ADDITION
        )

    # Update statistics
    saveLRStats("", resource.storage_object.identifier, "", UPDATE_STAT)

    return resource
    
    
def import_from_file(filehandle, descriptor, targetstatus, owner_id=None):
    """
    Import the xml metadata record(s) contained in the opened file identified by filehandle.
    filehandle: an opened file handle to either a single XML file or a zip archive containing
        only XML files.
    descriptor: a descriptor for the file handle, e.g. the file name.
    targetstatus: one of PUBLISHED, INGESTED or INTERNAL. 
        All imported records will be assigned this status.
    owner_id (optional): if present, the given user ID will be added to the list of owners of the
        resource.

    Returns a pair of lists, the first list containing the successfully imported resource objects,
         the second containing pairs of descriptors of the erroneous XML file(s) and error messages.
    """
    imported_resources = []
    erroneous_descriptors = []

    handling_zip_file = is_zipfile(filehandle)
    # Reset file handle for proper reading of the file contents.
    filehandle.seek(0)

    if not handling_zip_file:
        try:
            print 'Importing XML file: "{0}"'.format(descriptor)
            xml_string = filehandle.read()
            resource = import_from_string(xml_string, targetstatus, owner_id)
            imported_resources.append(resource)
        except Exception as problem:
            erroneous_descriptors.append((descriptor, problem))
    
    else:
        temp_zip = ZipFile(filehandle)
        
        print 'Importing ZIP file: "{0}"'.format(descriptor)
        for xml_name in temp_zip.namelist():
            try:
                if xml_name.endswith('/') or xml_name.endswith('\\'):
                    continue
                
                print 'Importing extracted XML file: "{0}"'.format(xml_name)
                xml_string = temp_zip.read(xml_name)
                resource = import_from_string(xml_string, targetstatus, owner_id)
                imported_resources.append(resource)
            except Exception as problem:
                erroneous_descriptors.append((xml_name, problem))
    return imported_resources, erroneous_descriptors

