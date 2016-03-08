#!/usr/bin/env python

import os
import re
import sys
import shutil
from StringIO import StringIO
from xml.etree import ElementTree

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
    
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
sys.path.append(PROJECT_HOME)

USERS = "users.xml"
GROUPS = "groups.xml"
PERMISSIONS = "permissions.xml"
CONTENT_TYPES = "content-types.xml"
EDITOR_GROUPS = "editor-groups.xml"
EDITOR_GROUP_MANAGERS = "editor-group-managers.xml"
ORGANIZATIONS = "organizations.xml"
ORGANIZATION_MANAGERS = "organization-managers.xml"
USER_PROFILES = "user-profiles.xml"

LR_STATS = "lr-stats.xml"
QUERY_STATS = "query-stats.xml"

STORAGE_FOLDER = "storage"
STORAGE = "storage.xml"
METADATA = "metadata.xml"
RESOURCE = "resource.xml"
ARCHIVE_TPL = "archive.{}"

XML_DECL = re.compile(r'\s*<\?xml version=".+" encoding=".+"\?>\s*\n?',
  re.I|re.S|re.U)
# same as above, but using using ' quotes for attributes
XML_DECL_2 = re.compile(r"\s*<\?xml version='.+' encoding='.+'\?>\s*\n?",
  re.I|re.S|re.U)

from django.core.serializers import xml_serializer
class MigrationSerializer(xml_serializer.Serializer):
    """
    Adapted version the extends the fields options with a skip_fields option
    """
    
    def serialize(self, queryset, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.pop("stream", StringIO())
        self.selected_fields = options.pop("fields", None)
        self.skipped_fields = options.pop("skip_fields", None)
        self.use_natural_keys = options.pop("use_natural_keys", False)

        self.start_serialization()
        for obj in queryset:
            print "exporting {}".format(obj)
            self.start_object(obj)
            for field in obj._meta.local_fields:
                if field.serialize:
                    if field.rel is None:
                        if self.skipped_fields and field.attname in self.skipped_fields:
                            print "skipping field {}:{}".format(
                              obj.__class__.__name__, field.attname)
                            continue
                        if self.selected_fields is None or field.attname in self.selected_fields:
                            self.handle_field(obj, field)
                    else:
                        if self.skipped_fields and field.attname in self.skipped_fields:
                            print "skipping field {}:{}".format(
                              obj.__class__.__name__, field.attname)
                            continue
                        if self.selected_fields is None or field.attname in self.selected_fields:
                            self.handle_fk_field(obj, field)
            for field in obj._meta.many_to_many:
                if field.serialize:
                    if self.skipped_fields and field.attname in self.skipped_fields:
                        print "skipping field {}:{}".format(
                          obj.__class__.__name__, field.attname)
                        continue
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_m2m_field(obj, field)
            self.end_object(obj)
        self.end_serialization()
        return self.getvalue()


def export_users(export_folder):
    """
    Exports user related entities as XML into the given folder.
    """

    from django.contrib.auth.models import User
    from django.contrib.auth.models import Group
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from metashare.accounts.models import EditorGroup
    from metashare.accounts.models import EditorGroupManagers
    from metashare.accounts.models import Organization
    from metashare.accounts.models import OrganizationManagers
    from metashare.accounts.models import UserProfile
    
    # create export folder if required
    _check_folder(export_folder)

    mig_serializer = MigrationSerializer()
    # export content types; nothing changes
    _export(
      ContentType.objects.all(), 
      os.path.join(export_folder, "{}".format(CONTENT_TYPES)), 
      mig_serializer)
    # export permissions; nothing changes
    _export(
      Permission.objects.all(), 
      os.path.join(export_folder, "{}".format(PERMISSIONS)), 
      mig_serializer)  
    # export groups; nothing changes
    _export(
      Group.objects.all(), 
      os.path.join(export_folder, "{}".format(GROUPS)), 
      mig_serializer)
    # export editor groups; nothing changes
    _export(
      EditorGroup.objects.all(), 
      os.path.join(export_folder, "{}".format(EDITOR_GROUPS)), 
      mig_serializer)
    # export editor group managers; nothing changes
    _export(
      EditorGroupManagers.objects.all(), 
      os.path.join(export_folder, "{}".format(EDITOR_GROUP_MANAGERS)), 
      mig_serializer)
    # export organizations; nothing changes
    _export(
      Organization.objects.all(), 
      os.path.join(export_folder, "{}".format(ORGANIZATIONS)), 
      mig_serializer)
    # export organization managers; nothing changes
    _export(
      OrganizationManagers.objects.all(), 
      os.path.join(export_folder, "{}".format(ORGANIZATION_MANAGERS)), 
      mig_serializer)
    # export users; nothing changes
    _export(
      User.objects.all(), 
      os.path.join(export_folder, "{}".format(USERS)), 
      mig_serializer)
    # export user profiles; nothing changes
    _export(
      UserProfile.objects.all(), 
      os.path.join(export_folder, "{}".format(USER_PROFILES)), 
      mig_serializer)
    
      
def export_stats(export_folder):
    """
    Exports statistic related entities as XML into the given folder.
    """

    from metashare.stats.models import LRStats, QueryStats
    
    # create export folder if required
    _check_folder(export_folder)
    
    mig_serializer = MigrationSerializer()
    # export lr stats; add 'ignored' field at import
    _export(
      LRStats.objects.all(), 
      os.path.join(export_folder, "{}".format(LR_STATS)), 
      mig_serializer)
    # export query stats; nothing changes
    _export(
      QueryStats.objects.all(), 
      os.path.join(export_folder, "{}".format(QUERY_STATS)), 
      mig_serializer)


def export_resources(export_folder):
    """
    Exports resources into the given folder using a 'storage' subfolder.
    """
    
    from metashare.repository.models import resourceInfoType_model
    from metashare.storage.models import MASTER

    mig_serializer = MigrationSerializer()
    for res in resourceInfoType_model.objects.filter(storage_object__copy_status=MASTER):
        _export_resource(res, export_folder, mig_serializer)
    

def _check_folder(folder):
    """
    Checks if the given folder exists and creates it if not.
    """
    if not folder.strip().endswith('/'):
        folder = '{0}/'.format(folder)
    _fdr = os.path.dirname(folder)
    if not os.path.exists(_fdr):
        os.makedirs(_fdr)


def _export(objects, export_file, serializer, skip_fields=None, fields=None):
    """
    Exports the given objects into the given export file using the given
    serializer; skips the given fields when serializing.
    """
    out = open(export_file, "wb")
    serializer.serialize(objects, stream=out, skip_fields=skip_fields, fields=fields)
    out.close()
    
    
def _export_resource(res, folder, serializer):
    """
    Exports the given resource into the given folder. Uses the given
    serializer to serialize the associated storage object.
    """
    
    storage_obj = res.storage_object
    
    target_storage_path = os.path.join(folder, STORAGE_FOLDER, storage_obj.identifier)
    _check_folder(target_storage_path)
        
    # export resource metadata XML
    print "exporting {}".format(res)
    root_node = res.export_to_elementtree()
    xml_string = _to_xml_string(root_node, encoding="ASCII").encode('ASCII')
    with open(os.path.join(target_storage_path, METADATA), 'wb') as _out:
        _out.write(xml_string)
    
    # export selected fields of resource object
    _export(
      [res,], 
      os.path.join(target_storage_path, RESOURCE), 
      serializer, fields=('owners', 'editor_groups'))
    
    # export associated storage object
    _export(
      [storage_obj,], 
      os.path.join(target_storage_path, STORAGE), 
      serializer)
    
    # copy possible binaries
    source_storage_path = '{0}/{1}/'.format(settings.STORAGE_PATH, storage_obj.identifier)
    from metashare.storage.models import ALLOWED_ARCHIVE_EXTENSIONS
    for archive_name in [ARCHIVE_TPL.format(_ext)
                         for _ext in ALLOWED_ARCHIVE_EXTENSIONS]:
        archive_path = os.path.join(source_storage_path, archive_name)
        if os.path.isfile(archive_path):
            print "copying archive of resource {}".format(res)
            shutil.copy(
              archive_path, os.path.join(target_storage_path, archive_name))
            # there can be at most one binary
            break


def _to_xml_string(node, encoding="ASCII"):
    """
    Serialize the given XML node as Unicode string using the given encoding.
    """
    
    xml_string = ElementTree.tostring(node, encoding=encoding)
    xml_string = xml_string.decode(encoding)
    
    # Delete any XML declaration inside the given XML String.
    xml_string = XML_DECL.sub(u'', xml_string)
    xml_string = XML_DECL_2.sub(u'', xml_string)

    return u'<?xml version="1.0" encoding="{}"?>{}'.format(encoding, xml_string)


if __name__ == "__main__":
    
    # Check command line parameters first.
    if len(sys.argv) < 2:
        print "\n\tusage: {0} <target-folder>\n".format(sys.argv[0])
        sys.exit(-1)
 
    export_users(sys.argv[1])
    export_stats(sys.argv[1])
    export_resources(sys.argv[1])
