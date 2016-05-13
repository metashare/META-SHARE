from metashare.repository.model_utils import get_root_resources
from metashare.storage.models import MASTER

def get_master_resources(component):
    """
    Returns the names of the master resources that contain the component
    """
    resources = get_root_resources(component)
    master_resources = [res.identificationInfo.get_default_resourceName() for res in resources \
        if res.storage_object.copy_status==MASTER and not res.storage_object.deleted]
    return master_resources

def write_to_resources_to_be_modified_file(curation_file, component, value, field_name):
    """
    Write to a file the resources and the invalid values. This file will be
    the reference to modify the invalid resources.
    curation_file: the file to which we write the resources to be updated
    component: the instance, which has the not mapped field value
    value: the not mapped field value
    field_name: the name of the field which has non mapped value
    """
    master_resources = get_master_resources(component)
    if len(master_resources) > 0:
        resources_str = u', '.join(master_resources)
        curation_file.write(u'{}: {} in resources: {} \n' \
                    .format(field_name, value, resources_str).encode('utf8'))


def write_warning_to_resources_to_be_modified_file(curation_file, component,
                                        invalid_value, valid_value, field_name):
    """
    Write to a file the resources and the invalid values. This file will be
    the reference to modify the invalid resources.
    curation_file: the file to which we write the resources to be updated
    component: the instance, which has the not mapped field value
    invalid_value: the invalid field value
    valid_value: the valid field value
    field_name: the name of the field which has non mapped value
    """
    master_resources = get_master_resources(component)
    if len(master_resources) > 0:
        resources_str = u', '.join(master_resources)
        curation_file.write(u'{} has invalid value {} in resources: {}. ' \
                    u'The restrictionsOfUse values for licence {} are: {}.\n' \
                    .format(field_name, invalid_value, resources_str,
                            getattr(component, 'licence'), valid_value).encode('utf8'))