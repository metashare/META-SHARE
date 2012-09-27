"""
Replaces underscores by spaces
"""

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def rep(value):
    return value.replace("_", " ")
