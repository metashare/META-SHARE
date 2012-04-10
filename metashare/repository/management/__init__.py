from metashare.repository import models as repository_models
from django.db.models import get_models, signals
from django.contrib.auth.models import Group, Permission
import inspect
from metashare.repository.supermodel import SchemaModel
from django.core.exceptions import ObjectDoesNotExist

GROUP_GLOBAL_EDITORS = 'globaleditors'

def is_schema_model(obj):
    return inspect.isclass(obj) and issubclass(obj, SchemaModel) and \
        not obj.__name__ in ('SchemaModel', 'InvisibleStringModel', 'SubclassableModel')




def setup_group_global_editors(app, created_models, verbosity, **kwargs):
    '''
    Set up a group for the staff users and give it add / change permissions
    for all repository models.
    '''
    
    # Local functions
    def has_group_globaleditors():
        return Group.objects.filter(name=GROUP_GLOBAL_EDITORS).count() > 0
    
    def create_group_globaleditors():
        return Group.objects.create(name=GROUP_GLOBAL_EDITORS)

    def list_applabels_and_modelnames():
        result = []
        for name, classobj in inspect.getmembers(repository_models, is_schema_model):
            app_label = classobj._meta.app_label
            result.append((app_label, name))
        return result

    def get_permission_object(applabel, modelname, permission_name):
        codename = '{}_{}'.format(permission_name, modelname.lower())
        return Permission.objects.get(codename=codename, content_type__app_label=applabel)

    # Begin setup_group_global_editors():

    if has_group_globaleditors():
        return # already have the group
    
    staffusers = create_group_globaleditors()
    
    for applabel, modelname in list_applabels_and_modelnames():
        add_permission = get_permission_object(applabel, modelname, 'add')
        change_permission = get_permission_object(applabel, modelname, 'change')
        staffusers.permissions.add(add_permission, change_permission)



# Register the setup_group_global_editors method such that it is called after syncdb is done.
# We must make sure that the post_syncdb hooks from auth.management are executed first,
# or else our code cannot find the permissions we want to use:\

from django.contrib.auth import management

signals.post_syncdb.connect(setup_group_global_editors,
    sender=repository_models, dispatch_uid = "metashare.repository.management.setup_group_global_editors")
