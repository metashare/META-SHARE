from django import template
from os.path import dirname
from lxml import etree
from metashare.settings import ROOT_PATH

from metashare.settings import STATIC_URL
from replace import pretty_camel


path = '{0}/'.format((dirname(ROOT_PATH)))

xsd = etree.parse('{}misc/schema/v3.1/META-SHARE-SimpleTypes.xsd'.format(path))
register = template.Library()



@register.filter("mimetype_label")
def mimetype_label(input):
    mimetypes = [mimetype for mimetype in input.split(",")]
    output = []
    for m in mimetypes:
        xpath = u"//*[@name='mimeType']/xs:simpleType/xs:restriction/xs:enumeration[@value='{}']//label/text()".format(m.replace(" ","").lower())
        output.append(''.join(xsd.xpath(xpath, namespaces={'xs': 'http://www.w3.org/2001/XMLSchema'})))
        print xpath
    return ', '.join(output)

register.tag('mime_label', mimetype_label)


