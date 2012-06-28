from django import template
from metashare.settings import MEDIA_URL

def get_media_url():
    return MEDIA_URL

register = template.Library()
register.simple_tag(get_media_url)