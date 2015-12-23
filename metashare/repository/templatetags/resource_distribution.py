from django import template
from metashare.settings import MEDIA_URL
from metashare.repository.model_utils import get_resource_license_types
from replace import pretty_camel

register = template.Library()

@register.filter("licence_icon")
def licence_icon(licence):
    if licence == "nonStandardLicenceTerms":
        img_location = "{}images/licence_icons/licences/other.png".format(MEDIA_URL)
    elif licence.startswith("CC"):
        img_location = "{}images/licence_icons/licences/cc.png".format(MEDIA_URL)
    elif licence == ("underNegotiation"):
        img_location = "{}images/licence_icons/licences/negotiate.png".format(MEDIA_URL)
    else:
        img_location = "{}images/licence_icons/licences/open_licence.png".format(MEDIA_URL)
    return u"".join(u"<img style=\"padding:1px\" src=\"{}\" title=\"{}\" alt=\"{}\" width=\"17\" height=\"17\"/>" \
                    .format(img_location, pretty_camel(licence), pretty_camel(licence)))


register.tag('licence_icon', licence_icon)

@register.filter("condition_icon")
def condition_icon(condition):
    img_location = "{}images/licence_icons/conditions/{}.png".format(MEDIA_URL,condition)
    return u"".join(u"<img style=\"padding:1px\" src=\"{}\" title=\"{}\" alt=\"{}\" width=\"17\" height=\"17\"/>" \
                    .format(img_location, pretty_camel(condition), pretty_camel(condition)))


register.tag('condition_icon', condition_icon)
