import shutil
from metashare import settings
import os

def remove_resource(storage_object, keep_stats=False):
    """
    Completely removes the given storage object and its associated language 
    resource from the storage layer.
    Also includes deletion of statistics and recommendations; use keep_stats
    optional parameter to suppress deletion of statistics and recommendations.
    """
    resource = storage_object.resourceinfotype_model_set.all()[0]

    folder = os.path.join(settings.STORAGE_PATH, storage_object.identifier)
    shutil.rmtree(folder)
    resource.delete_deep(keep_stats=keep_stats)
    storage_object.delete()