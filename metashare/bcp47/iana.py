from os.path import dirname
from lxml import etree
from metashare.settings import ROOT_PATH

path = '{0}/'.format((dirname(ROOT_PATH)))

registry = etree.parse('{}metashare/bcp47/language-subtag-registry-min4.xml'.format(path))

# LISTS

def get_all_languages():
    xpath = u"//language/description/text()"
    return registry.xpath(xpath)

def get_most_used_languages():
    xpath = u"//language[position()<25]/description/text()"
    return registry.xpath(xpath)

def get_rest_of_languages():
    xpath = u"//language[position()>25]/description/text()"
    return registry.xpath(xpath)

def get_languages_by_substring():
    xpath = u"//language[matches(lower-case(description),\"\\b{}\")]/description/text()"
    return registry.xpath(xpath)

def get_language_by_subtag(subtag):
    xpath = u"//language[@subtag='{}']/description/text()".format(subtag)
    return ''.join(registry.xpath(xpath))

def get_all_scripts():
    xpath = u"//script/description/text()"
    return registry.xpath(xpath)

def get_all_regions():
    xpath = u"//region/description/text()"
    return registry.xpath(xpath)

def get_bcp47_description(iso_description):
    pass

def get_all_variants():
    xpath = u"//registry/variants/variant/description/text()"
    return registry.xpath(xpath)

# Get subtags
def get_language_subtag(language):
    xpath = u"//language[description=\"{}\"]/@subtag".format(language)
    return ''.join(registry.xpath(xpath))

def get_script_subtag(script):
    xpath = u"//script[description=\"{}\"]/@subtag".format(script)
    return ''.join(registry.xpath(xpath))

def get_region_subtag(region):
    xpath = u"//region[description=\"{}\"]/@subtag".format(region)
    return '/'.join(registry.xpath(xpath))

def get_variant_subtag(variant):
    xpath = u"//registry/variants//variant[description=\"{}\"]/@subtag".format(variant)
    return ''.join(registry.xpath(xpath))

# Get Variants
def get_variants_by_language(lang):
    xpath = u"//language[description=\"{}\"]//variant/text()".format(lang)
    return registry.xpath(xpath)

def get_variants_by_script(script,lang):
    lang_id = get_language_subtag(lang)
    xpath = u"//script[description=\"{}\"]//variant[@lang=\"{}\"]/text()".format(script,lang_id)
    return sorted(list(set.union(set(get_variants_by_language(lang)), registry.xpath(xpath))))

def get_variants_by_variant(variant):
    xpath = u"//variants/variant[description=\"{}\"]//variant/text()".format(variant)
    return registry.xpath(xpath)

def make_id(lang, script = None, region= None, variants= None):
    id = get_language_subtag(lang)

    if script and not registry.xpath(u"//language[description =\"{}\" and suppress-script =\"{}\"]"\
            .format(lang, get_script_subtag(script))):
        id += u"-{}".format(get_script_subtag(script))

    if region:
        id += u"-{}".format(get_region_subtag(region))
    if variants:
        for v in variants:
            id += u"-{}".format(get_variant_subtag(v))
    return id

def get_suppressed_script_description(lang):
    xpath = u"//language[description=\"{}\"]//suppress-script/text()".format(lang)
    sctipt_subtag = ''.join(registry.xpath(xpath))
    xpath = u"//script[@subtag=\"{}\"]/description/text()".format(sctipt_subtag)
    return ''.join(registry.xpath(xpath))

# print get_variants_by_language(u"Japanese")
#
# print get_variants_by_script(u"Latin", u"Japanese", )
