
from xml.etree.ElementTree import XML
import os
import logging
from metashare.settings import LOG_HANDLER
import pycountry

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

def read_langs(filename):
    if not os.path.isfile(filename):
        LOGGER.error('read_langs: {0} not found'.format(filename))
        return None
    
    file_hnd = os.open(filename, os.O_RDONLY)
    xml_langs = XML(os.read(file_hnd, 10000))
    return xml_langs

def read_languages():
    langs = pycountry.languages
    lang_list = []
    for index in range(len(langs.objects)):
        lang = langs.objects[index]
        if hasattr(lang, 'alpha2'):
            lang_item = (index, lang.alpha2, lang.name)
            lang_list.append(lang_item)
        else:
            #lang_item = (index, '', lang.name)
            pass
    return lang_list
    
def read_lang_alpha2():
    langs = pycountry.languages
    lang_list = []
    for index in range(len(langs.objects)):
        lang = langs.objects[index]
        if hasattr(lang, 'alpha2'):
            lang_item = (lang.alpha2)
            lang_list.append(lang_item)
    return lang_list
    
def get_lang_list(xml_tree):
    lang_el_list = xml_tree.findall('lang')
    lang_list = []
    for lel in lang_el_list:
        lang_id = lel.find('id').text
        lang_name = lel.find('name').text
        lang_list.append((lang_id, lang_name))
    return lang_list

