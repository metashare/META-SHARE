"""
Replaces underscores by spaces
"""
import re

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def rep(value):
    return value.replace("_", " ")

@register.filter
@stringfilter
def pretty_camel(cc_str):
    '''
    Prettifies the given camelCase string so that it is better readable.

    For example, "speechAnnotation-soundToTextAlignment" is converted to "Speech
    Annotation - Sound To Text Alignment". N.B.: The conversion currently only
    recognizes boundaries with ASCII letters.
    '''
    result = cc_str
    if len(result) > 1:
        # result = result.replace('-', ' - ')  AtA
        result = result.replace('_', ' ')
        result = result.replace('AtA', 'At a')
        result = re.sub(r'(..)(?=[A-Z][a-z])', r'\1 ', result)
        result = ' '.join([(len(token) > 1 and (token[0].upper() + token[1:]))
                           or token[0].upper() for token in result.split()])
    return result