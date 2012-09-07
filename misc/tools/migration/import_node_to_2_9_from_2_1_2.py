#!/usr/bin/env python

import os
import sys
import shutil

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
USER_PROFILES = "user-profiles.xml"
LR_STATS = "lr-stats.xml"
QUERY_STATS = "query-stats.xml"
USAGE_STATS = "usage-stats.xml"
STORAGE_FOLDER = "storage"
STORAGE = "storage.xml"
METADATA = "metadata.xml"
RESOURCE = "resource.xml"
ARCHIVE = "archive.zip"

def import_users(import_folder):
    """
    Imports user related entities from XML in the given folder.
    """
    # delete existing users
    from django.contrib.auth.models import User
    User.objects.all().delete()
    # import users
    _import(os.path.join(import_folder, "{}".format(USERS)))
    _update_pk("auth")
    
    # delete existing user profiles
    from metashare.accounts.models import UserProfile
    UserProfile.objects.all().delete()
    # import user profiles
    _import(os.path.join(import_folder, "{}".format(USER_PROFILES)))
    _update_pk("accounts")


def import_stats(import_folder):
    """
    Imports statistic related entities from XML in the given folder.
    """
    # import lr stats
    _import(os.path.join(import_folder, "{}".format(LR_STATS)))
    # import query stats
    _import(os.path.join(import_folder, "{}".format(QUERY_STATS)))
    # import usage stats
    _import(os.path.join(import_folder, "{}".format(USAGE_STATS)))

    _update_pk("stats")


def import_resources(import_folder):
    """
    Imports resources from the given folder.
    """
    # Check that SOLR is running, or else all resources will stay at status INTERNAL:
    from metashare.repository import verify_at_startup
    verify_at_startup() # may raise Exception, which we don't want to catch.

    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = 'True'
    
    from metashare.repository.supermodel import OBJECT_XML_CACHE

    # Clean cache before starting the import process.
    OBJECT_XML_CACHE.clear()
    
    # iterate over storage folder content
    from django.core import serializers
    from metashare.storage.models import MASTER
    from metashare.repository.models import resourceInfoType_model

    imported_resources = []
    erroneous_descriptors = []

    storage_path = os.path.join(import_folder, STORAGE_FOLDER)
    for folder_name in os.listdir(storage_path):
        folder_path = "{}/{}/".format(storage_path, folder_name)
        if os.path.isdir(folder_path):
            try:
                print "importing from folder: '{0}'".format(folder_name)
                # import storage object
                so_filename = os.path.join(folder_path, STORAGE)
                so_in = open(so_filename, "rb")
                for obj in serializers.deserialize("xml", so_in):
                    print "importing storage object"
                    # storage.xml only contains a single storage object
                    storage_obj = obj.object
                    # this storage object is NOT saved!
                    # we only copy the relevant attributes from this storage
                    # object to the one at the resource!
                so_in.close()
                # import resource object
                ro_filename = os.path.join(folder_path, RESOURCE)
                ro_in = open(ro_filename, "rb")
                for obj in serializers.deserialize("xml", ro_in):
                    print "importing resource object"
                    # resource.xml only contains a single resource object
                    res_obj = obj
                    # the deserialized object contains the ManyToMany attributes
                    # in m2m_data
                ro_in.close()
                # import resource from metadata.xml
                res_filename = os.path.join(folder_path, METADATA)
                temp_file = open(res_filename, 'rb')
                xml_string = temp_file.read()
                result = resourceInfoType_model.import_from_string(
                  xml_string, copy_status=MASTER)
                if not result[0]:
                    msg = u''
                    if len(result) > 2:
                        msg = u'{}'.format(result[2])
                    raise Exception(msg)
                res = result[0]
                # update imported resource with imported resource object 
                # and storage object
                _update_resource(res, res_obj, storage_obj)
                # copy possible binaries archives
                archive_filename = os.path.join(folder_path, ARCHIVE)
                res_storage_path = '{0}/{1}/'.format(
                  settings.STORAGE_PATH, res.storage_object.identifier)
                if os.path.isfile(archive_filename):
                    print "copying archive"
                    shutil.copy(
                      archive_filename, os.path.join(res_storage_path, ARCHIVE))
                imported_resources.append(res)
            except Exception as problem:
                erroneous_descriptors.append((folder_name, problem))

    print "Done.  Successfully imported {0} resources into the database, " \
      "errors occurred in {1} cases.".format(
      len(imported_resources), len(erroneous_descriptors))
    if len(erroneous_descriptors) > 0:
        print "The following resources could not be imported:"
        for descriptor, exception in erroneous_descriptors:
            print "\t{}: {}".format(descriptor, exception)

    # Be nice and cleanup cache...
    _cache_size = sum([len(x) for x in OBJECT_XML_CACHE.values()])
    OBJECT_XML_CACHE.clear()
    print "Cleared OBJECT_XML_CACHE ({} bytes)".format(_cache_size)
    
    from django.core.management import call_command
    call_command('rebuild_index', interactive=False)


def _update_resource(res, res_obj, storage_obj):
    """
    Adds information to given resource from the given resource object 
    and storage object.
    """
    
    # transfer owner from old resource object
    for owner in res_obj.m2m_data['owners']:
        res.owners.add(owner)
    
    # transfer attributes from old storage object; skip attributes that were not
    # available in 2.1.2
    skip_fields = (
      'id', 'copy_status', 'digest_checksum', 'digest_last_checked', 'digest_modified', 
      'global_storage', 'local_storage', 'metashare_version', 'source_url',)
    for field in storage_obj._meta.local_fields:
        if field.attname in skip_fields:
            continue
        setattr(res.storage_object, field.attname, getattr(storage_obj, field.attname))
    # manually set the revision to 0, so that it is 1 
    # when creating the storage folder
    res.storage_object.revision = 0
        
    # saving the resource also saves the associated storage object
    res.save()
    # recreate storage folder
    res.storage_object.update_storage()
    

def _import(import_file):
    """
    Imports the objects from the given import file and saves them in the database.
    """
    from django.core import serializers    
    
    _in = open(import_file, "rb")
    for obj in serializers.deserialize("xml", _in):
        _obj = obj.object
        print "importing {}".format(_obj)
        _obj.save()
    _in.close()


def _update_pk(app_name):
    """
    Updates the primary keys for the tables of the given app; 
    required for PostgreSQL to avoid the next db element created using a pk that
    already exists.
    """
    from StringIO import StringIO
    from django.db import connection
    from django.db.models.loading import get_app
    from django.core.management import call_command
    
    commands = StringIO()
    cursorll = connection.cursor()

    if get_app(app_name, emptyOK=True):
        call_command('sqlsequencereset', app_name, stdout=commands)
        cursorll.execute(commands.getvalue())


def recreate_sync_users():
    """
    Recreates sync users as the might have been overwritten.
    """
    
    from django.contrib.auth.models import User
    from django.core.management import call_command

    syncusers = getattr(settings, "SYNC_USERS", {})
    for username, password in syncusers.iteritems():
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            call_command(
              "createsyncuser", username=username, password=password, verbosity=1)


if __name__ == "__main__":

    # Check command line parameters first.
    if len(sys.argv) < 2:
        print "\n\tusage: {0} <source-folder>\n".format(sys.argv[0])
        sys.exit(-1)

    import_users(sys.argv[1])
    import_stats(sys.argv[1])
    import_resources(sys.argv[1])
    recreate_sync_users()
