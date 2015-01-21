#!/usr/bin/env python

import os
import sys

#from django import db
from zipfile import is_zipfile, ZipFile

# Magic python path, based on http://djangosnippets.org/snippets/281/
from os.path import abspath, dirname, join
parentdir = dirname(dirname(abspath(__file__)))
# Insert our dependencies:
sys.path.insert(0, join(parentdir, 'lib', 'python2.7', 'site-packages'))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, parentdir)

try:
    import settings # Assumed to be in the same directory.

except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the " \
      "directory containing %r. It appears you've customized things.\n" \
      "You'll have to run django-admin.py, passing it your settings " \
      "module.\n(If the file settings.py does indeed exist, it's causing" \
      " an ImportError somehow.)\n" % __file__)
    sys.exit(1)
   
def replace_price(res, url, licenceInfo, imported_resources, erroneous_descriptors):
    ### update previous resource there
    if 1:
        print "replace price - {} - {}".format(res.pk, url)
        for licence in licenceInfo:
            licences = res.distributionInfo.licenceinfotype_model_set.filter(licence=[licenceInfo[licence]["licence"]]) \
              .filter(restrictionsOfUse=[licenceInfo[licence]["restrictionsOfUse"]]) \
              .filter(userNature=[licenceInfo[licence]["userNature"]]) \
              .filter(membershipInfo__member=licenceInfo[licence]["member"]) \
              .filter(membershipInfo__membershipInstitution=[licenceInfo[licence]["membershipInstitution"]])

            if licences.count() > 1:
                print "More than too licence results!"
                print "Licences (licence, restrictionsOfUse, userNature, membershipInfo.member, membershipInfo.membershipInstitution):"
                for lic in licences:
                    print "{}, {}, {}, {}".format(lic.licence, lic.restrictionsOfUse, lic.userNature, \
                      lic.membershipInfo.all())
            elif licences.count() != 1:
                print "Licence not found! - adding licence..."
                from metashare.repository.models import licenceInfoType_model, membershipInfoType_model
                new_licence = licenceInfoType_model()
                new_licence = licenceInfoType_model.objects.create()
                new_licence.fee=licenceInfo[licence]["fee"]
                new_licence.licence=[licenceInfo[licence]["licence"]]
                new_licence.restrictionsOfUse=[licenceInfo[licence]["restrictionsOfUse"]]
                new_licence.userNature=[licenceInfo[licence]["userNature"]]
                new_licence.membershipInfo=membershipInfoType_model.objects.filter( \
                  membershipInstitution=[licenceInfo[licence]["membershipInstitution"]], \
                  member=licenceInfo[licence]["member"])
                new_licence.save()
                res.distributionInfo.licenceinfotype_model_set.add(new_licence)
                print "Licence added..."
                print new_licence.licence
                print new_licence.restrictionsOfUse
                print new_licence.userNature
                print new_licence.membershipInfo.all()
            else:
                for lic in licences:
                    lic.fee = licenceInfo[licence]["fee"]
                    lic.save()

                    ### change modified / digest for storage object (of the previous resource) there
                    res.storage_object.update_storage(force_digest=True)
        
    try:
        imported_resources.append(url)
    # pylint: disable-msg=W0703
    except Exception as problem:
        print 'Caught an exception while updating {} from {}:'.format(
            res, url)
        erroneous_descriptors.append((res, problem))

    return imported_resources, erroneous_descriptors
    

def import_from_batch(filehandle, descriptor):
    imported_resources = []
    erroneous_descriptors = []

    # Reset file handle for proper reading of the file contents.
    filehandle.seek(0)
    xml_string = filehandle.read()

    print 'Importing XML file: "{0}"'.format(descriptor)

    from xml.etree import ElementTree
    from metashare.repository.models import resourceInfoType_model

   
    resources = ElementTree.fromstring(xml_string)
    lst = resources.findall("resource")
    print "{} resource(s) to update.".format(len(lst))
    for item in lst:
        #url = []
        #url.append(item.find("url").text)
        url = item.find("url").text
        licenceInfo = {}
        num = 0
        for lic in item.getiterator('licenceInfo'):
            licenceInfo[num] = {}
            licenceInfo[num]["licence"] = lic.find("licence").text
            licenceInfo[num]["restrictionsOfUse"] = lic.find("restrictionsOfUse").text
            licenceInfo[num]["fee"] = lic.find("fee").text
            licenceInfo[num]["userNature"] = lic.find("userNature").text
            for mem in lic.getiterator('membershipInfo'):
                licenceInfo[num]["member"] = True if mem.find("member").text in ['true', 'True'] else False
                licenceInfo[num]["membershipInstitution"] = mem.find("membershipInstitution").text
            num += 1

        print "Start checking"
        if resourceInfoType_model.objects.filter(identificationInfo__url=[url]).count() ==0:
            multiple_urls_case = False
            print "Check for multiple urls case..."
            for res in resourceInfoType_model.objects.all():
                if url in res.identificationInfo.url:
                    multiple_urls_case = True
                    print "Multiple urls case found."
                    replace_price(res, url, licenceInfo, imported_resources, erroneous_descriptors)
            if not multiple_urls_case:
                print "No correspondance with url {}".format(url) 
                erroneous_descriptors.append((url, "No correspondance."))
        else:
            for res in resourceInfoType_model.objects.filter(identificationInfo__url=[url]):
                replace_price(res, url, licenceInfo, imported_resources, erroneous_descriptors)
        print "done."

    return imported_resources, erroneous_descriptors


def print_usage():
    print "\n\tusage: {0} [--id-file=idfile] <file.xml|archive.zip> [<file.xml|archive." \
      "zip> ...]\n".format(sys.argv[0])
    print "  --id-file=idfile : print identifier of imported resources in idfile"
    return

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
    sys.path.append(PROJECT_HOME)
    
    # Check command line parameters first.
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(-1)
    
    # Check command line options for --id-file
    id_filename = None
    arg_num=1
    if sys.argv[arg_num].startswith("--id-file="):
        opt_len = len("--id-file=")
        id_filename = sys.argv[arg_num][opt_len:]
        arg_num = arg_num + 1
        if len(id_filename) == 0:
            print "Incorrect option"
            print_usage()
            sys.exit(-1)
        if len(sys.argv) < 3:
            print_usage()
            sys.exit(-1)
        

    # Check that SOLR is running, or else all resources will stay at status INTERNAL:
    from metashare.repository import verify_at_startup
    verify_at_startup() # may raise Exception, which we don't want to catch.

    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = 'True'
    
    successful_imports = []
    erroneous_imports = []
    from metashare.storage.models import PUBLISHED, MASTER
    from metashare.repository.supermodel import OBJECT_XML_CACHE
    
    # Clean cache before starting the import process.
    OBJECT_XML_CACHE.clear()
    
    for filename in sys.argv[arg_num:]:
        temp_file = open(filename, 'rb')
        success, failure = import_from_batch(temp_file, filename)
        successful_imports += success
        erroneous_imports += failure
        temp_file.close()
    
    print "Done.  Successfully updated {0} files into the database, errors " \
      "occurred in {1} cases.".format(len(successful_imports), len(erroneous_imports))
    if len(erroneous_imports) > 0:
        print "The following files could not be imported:"
        for descriptor, exception in erroneous_imports:
            if isinstance(exception, basestring):
                print "\t{}: {}".format(descriptor, exception)
            else:
                if isinstance(exception.args, basestring):
                    print "\t{}: {}".format(descriptor, ' '.join(exception.args))
                else:
                    print "\t{}: {}".format(descriptor, exception.args)
    
    # Salvatore:
    # This is useful for tracking where the resource is stored.
    # It is used by some scripts for testing purposes
    if not id_filename is None:
        id_file = open(id_filename, 'w')
        for resource in successful_imports:
            id_file.write('--->RESOURCE_ID:{0};STORAGE_IDENTIFIER:{1}\n'\
                .format(resource.id, resource.storage_object.identifier))
        id_file.close()

    # Be nice and cleanup cache...
    _cache_size = sum([len(x) for x in OBJECT_XML_CACHE.values()])
    OBJECT_XML_CACHE.clear()
    print "Cleared OBJECT_XML_CACHE ({} bytes)".format(_cache_size)

