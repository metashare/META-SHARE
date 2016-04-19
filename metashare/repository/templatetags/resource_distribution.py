from django import template
from metashare.settings import STATIC_URL
from replace import pretty_camel

register = template.Library()

@register.filter("licence_icon")
def licence_icon(licence):
    img_location = "{}metashare/images/licence_icons/licences/{}.png" \
                        .format(STATIC_URL, licence)
    return u"<img style=\"padding:1px\" src=\"{}\" title=\"{}\" alt=\"{}\" height=\"20\"/>" \
            .format(img_location, pretty_camel(licence), pretty_camel(licence))

register.tag('licence_icon', licence_icon)

@register.filter("as_set")
def as_set(licence_list):
    ln = [l.licence for l in licence_list]
    return set(ln)

register.tag('as_set', as_set)

@register.filter("condition_icon")
def condition_icon(condition):
    img_location = "{}metashare/images/licence_icons/conditions" \
        "/{}.png".format(STATIC_URL, condition)
    return u"<img style=\"padding:1px\" src=\"{}\" title=\"{}\" alt=\"{}\" width=\"17\" height=\"17\"/>" \
        .format(img_location, pretty_camel(condition), pretty_camel(condition))

register.tag('condition_icon', condition_icon)
