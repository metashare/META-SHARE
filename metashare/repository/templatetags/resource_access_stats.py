from django import template

from metashare.repository import model_utils
from metashare.stats.model_utils import DOWNLOAD_STAT, VIEW_STAT


# module level "register" variable as required by Django
register = template.Library()


def get_download_count(identifier):
    """
    Template filter which returns the download count for the resource with the
    given (storage object) identifier string.
    
    If the given identifier should be unknown, then 0 is returned.
    """
    return model_utils.get_lr_stat_action_count(identifier, DOWNLOAD_STAT)

register.filter('get_download_count', get_download_count)


def get_view_count(identifier):
    """
    Template filter which returns the view count for the resource with the given
    (storage object) identifier string.
    
    If the given identifier should be unknown, then 0 is returned.
    """
    return model_utils.get_lr_stat_action_count(identifier, VIEW_STAT)

register.filter('get_view_count', get_view_count)
