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


@register.filter("licence_set")
def licence_set(dist_list):
    dl_info = []
    for d in dist_list:
        dl_info.extend(d.licenceInfo.all())

    l_info =[]
    l_info.extend([li.licence for li in dl_info])
    return sorted(set(l_info))

register.tag('licence_set', licence_set)

@register.filter("condition_icon")
def condition_icon(condition):
    img_location = "{}metashare/images/licence_icons/conditions" \
        "/{}.png".format(STATIC_URL, condition)
    return u"<img style=\"padding:1px\" src=\"{}\" title=\"{}\" alt=\"{}\" width=\"17\" height=\"17\"/>" \
        .format(img_location, pretty_camel(condition), pretty_camel(condition))

register.tag('condition_icon', condition_icon)
