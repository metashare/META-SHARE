"""
Checks if user is owner of at least one resource
"""

from django import template
from metashare.repository.models import resourceInfoType_model
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def is_owner(username):
    resources = resourceInfoType_model.objects.filter(owners__username=username)
    return resources.count() != 0
