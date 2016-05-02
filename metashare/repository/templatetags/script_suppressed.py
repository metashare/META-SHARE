from django import template
from metashare.bcp47.iana import get_suppressed_script_description

register = template.Library()


@register.filter("script_suppressed")
def script_suppressed(input):
    return get_suppressed_script_description(input)

register.tag('script_suppressed', script_suppressed)