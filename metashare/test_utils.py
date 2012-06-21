"""
Project: META-SHARE
Utility functions for unit tests useful across apps.
"""
import os

from django.contrib.auth.models import Group, User, Permission
from django.core.management import call_command
from django.test.testcases import TestCase

from metashare import settings
from metashare.repository.management import GROUP_GLOBAL_EDITORS
from metashare.repository.models import resourceInfoType_model, \
    personInfoType_model, actorInfoType_model, documentationInfoType_model, \
    documentInfoType_model, targetResourceInfoType_model, \
    organizationInfoType_model, projectInfoType_model
from metashare.storage.models import PUBLISHED, MASTER, StorageObject
from metashare.xml_utils import import_from_file


def setup_test_storage():
    settings.STORAGE_PATH = '{0}/test-tmp'.format(settings.ROOT_PATH)
    try:
        os.mkdir(settings.STORAGE_PATH)
    except:
        pass

def clean_db():
    """
    Deletes all entities from db.
    """
    for res in resourceInfoType_model.objects.all():
        res.delete_deep()
    # delete storage objects
    StorageObject.objects.all().delete()
    # delete all reusable entities
    actorInfoType_model.objects.all().delete()
    documentationInfoType_model.objects.all().delete()
    documentInfoType_model.objects.all().delete()
    personInfoType_model.objects.all().delete()
    targetResourceInfoType_model.objects.all().delete()
    organizationInfoType_model.objects.all().delete()
    projectInfoType_model.objects.all().delete()

def clean_storage():
    """
    Deletes content of storage folder.
    """
    for _folder in os.listdir(settings.STORAGE_PATH):
        for _file in os.listdir(os.path.join(settings.STORAGE_PATH, _folder)):
            os.remove(os.path.join(settings.STORAGE_PATH, _folder, _file))
        os.rmdir(os.path.join(settings.STORAGE_PATH, _folder))

def create_user(username, email, password):
    User.objects.all().filter(username=username).delete()
    return User.objects.create_user(username, email, password)

def import_xml(filename, copy_status=MASTER):
    _xml = open(filename)
    _xml_string = _xml.read()
    _xml.close()
    result = resourceInfoType_model.import_from_string(_xml_string, copy_status=copy_status)
    return result

def import_xml_or_zip(filename, copy_status=MASTER):
    _xml = open(filename, 'rb')
    return import_from_file(_xml, filename, PUBLISHED, copy_status)

def set_index_active(is_active):
    """
    A helper allowing tests to disable the index if it is not needed,
    e.g. for tests that have no front-facing UI component.
    """
    os.environ['DISABLE_INDEXING_DURING_IMPORT'] = str(bool(not is_active))

def create_manager_user(user_name, email, password, groups=None):
    """
    Creates a new managing editor user account with the given credentials and
    group memberships.
    """
    result = create_editor_user(user_name, email, password, groups)
    # add resource delete permission
    opts = resourceInfoType_model._meta
    result.user_permissions.add(Permission.objects.filter(
        content_type__app_label=opts.app_label,
        codename=opts.get_delete_permission())[0])
    return result


def create_editor_user(user_name, email, password, groups=None):
    """
    Creates a new editor user account with the given credentials and group
    memberships.
    """
    result = User.objects.create_user(user_name, email, password)
    result.is_staff = True
    if groups:
        for group in groups:
            result.groups.add(group)
    # always add basic editing permissions
    result.groups.add(Group.objects.get(name=GROUP_GLOBAL_EDITORS))
    result.save()
    return result


class IndexAwareTestCase(TestCase):
    """
    A Django `TestCase` which makes sure to always rebuild the search index
    before and after every test so that it always matches the current database
    state.
    """
    def _fixture_setup(self):
        result = super(IndexAwareTestCase, self)._fixture_setup()
        call_command('rebuild_index', interactive=False,
                     using=settings.TEST_MODE_NAME)
        return result

    def _fixture_teardown(self):
        result = super(IndexAwareTestCase, self)._fixture_teardown()
        call_command('rebuild_index', interactive=False,
                     using=settings.TEST_MODE_NAME)
        return result
