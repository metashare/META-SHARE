
import pycountry
import sys
from django.utils.encoding import smart_str

USE_EXTENDED_LABELS = False
USE_ALPHA2 = False

def read_lang_alpha2():
    langs = pycountry.languages
    lang_list = []
    for index in range(len(langs.objects)):
        lang = langs.objects[index]
        if hasattr(lang, 'alpha2'):
            lang_item = (lang.alpha2)
            lang_list.append(lang_item)
    return lang_list
    
def read_lang_code():
    langs = pycountry.languages
    lang_list = []
    for index in range(len(langs.objects)):
        lang = langs.objects[index]
        if hasattr(lang, 'alpha2'):
            lang_item = (lang.alpha2)
            lang_list.append(lang_item)
        elif hasattr(lang, 'terminology'):
            lang_item = (lang.terminology)
            # Do not include 'No linguistic content; Not applicable'
            if lang_item == 'zxx':
                continue
            # Do not include 'Reserved ...' entry
            if len(lang_item) == 3:
                lang_list.append(lang_item)
    return lang_list
    
def read_lang_name():
    langs = pycountry.languages
    lang_list = []
    for index in range(len(langs.objects)):
        lang = langs.objects[index]
        if hasattr(lang, 'name'):
            lang_item = (lang.name)
            if hasattr(lang, 'terminology'):
                term = lang.terminology
                # Do not include 'No linguistic content; Not applicable'
                if term == 'zxx':
                    continue
                if len(term) > 3:
                    # Do not include 'Reserved ...' entry
                    continue
            lang_list.append(lang_item)
    return lang_list
    
if __name__ == "__main__":
    sys.stdout.write("/*\n")
    sys.stdout.write("   List of language names and codes obtained from pycountry.\n")
    sys.stdout.write("   To build this file use the following command:\n")
    sys.stdout.write("   python misc/tools/lang/gen_langs.py > metashare/media/admin/js/pycountry.js\n")
    sys.stdout.write("*/\n")
    sys.stdout.write("\n\n")
    
    if USE_ALPHA2:
        sys.stdout.write("var _lang_alpha2_list = [")
        sys.stdout.write("\n")
        lang_list = read_lang_alpha2()
        lang_list_len = len(lang_list)
        line_len = 10
        line = 0
        for index in range(lang_list_len):
            elem = lang_list[index]
            if index > 0:
                sys.stdout.write(', ')
            if line == line_len:
                sys.stdout.write('\n')
                line = 0
            sys.stdout.write('"' + elem + '"')
            line = line + 1
        sys.stdout.write("];")
        sys.stdout.write("\n")
        sys.stdout.write("\n")
    
    sys.stdout.write("var _lang_code_list = [")
    sys.stdout.write("\n")
    lang_list3 = read_lang_code()
    lang_list3_len = len(lang_list3)
    line_len = 10
    line = 0
    for index in range(lang_list3_len):
        elem = lang_list3[index]
        if index > 0:
            sys.stdout.write(', ')
        if line == line_len:
            sys.stdout.write('\n')
            line = 0
        sys.stdout.write('"' + elem + '"')
        line = line + 1
    sys.stdout.write("];")
    sys.stdout.write("\n")
    sys.stdout.write("\n")
    
    if USE_EXTENDED_LABELS:
        sys.stdout.write("\n\n")
        sys.stdout.write("var _lang_alpha2_list_with_labels = [")
        sys.stdout.write("\n")
        lang_list_len = len(lang_list)
        line_len = 10
        line = 0
        for index in range(lang_list_len):
            elem = lang_list[index]
            name = pycountry.languages.get(alpha2=elem).name
            if index > 0:
                sys.stdout.write(', ')
            if line == line_len:
                sys.stdout.write('\n')
                line = 0
            sys.stdout.write('{label: "')
            sys.stdout.write(elem + ' : ')
            sys.stdout.write(smart_str(name))
            sys.stdout.write('", value: "' + elem + u'"}')
            line = line + 1
        sys.stdout.write("];")
        sys.stdout.write("\n")
        sys.stdout.write("\n")
    
    sys.stdout.write("var _lang_name_list = [")
    sys.stdout.write("\n")
    lang_list2 = read_lang_name()
    lang_list2_len = len(lang_list2)
    line_len = 4
    line = 0
    for index in range(lang_list2_len):
        elem = lang_list2[index]
        if index > 0:
            sys.stdout.write(', ')
        if line == line_len:
            sys.stdout.write('\n')
            line = 0
        sys.stdout.write('"' + smart_str(elem) + '"')
        line = line + 1
    sys.stdout.write("];")
    sys.stdout.write("\n")
    sys.stdout.write("\n")

    if USE_ALPHA2:
        sys.stdout.write("var _lang_alpha2_to_name = new Array();\n")
        for index in range(lang_list_len):
            elem = lang_list[index]
            name = pycountry.languages.get(alpha2=elem).name
            sys.stdout.write(u'_lang_alpha2_to_name["%s"] = "' % elem)
            sys.stdout.write(smart_str(name))
            sys.stdout.write(u'";\n')
        sys.stdout.write("\n")
        sys.stdout.write("\n")
    
    sys.stdout.write("var _lang_code_to_name = new Array();\n")
    for index in range(lang_list3_len):
        elem = lang_list3[index]
        if len(elem) == 2:
            name = pycountry.languages.get(alpha2=elem).name
        else:
            name = pycountry.languages.get(terminology=elem).name
        sys.stdout.write(u'_lang_code_to_name["%s"] = "' % elem)
        sys.stdout.write(smart_str(name))
        sys.stdout.write(u'";\n')
    sys.stdout.write("\n")
    sys.stdout.write("\n")
    
    sys.stdout.write("var _lang_name_to_code = new Array();\n")
    for index in range(lang_list3_len):
        elem = lang_list3[index]
        if len(elem) == 2:
            name = pycountry.languages.get(alpha2=elem).name
        else:
            name = pycountry.languages.get(terminology=elem).name
        sys.stdout.write(u'_lang_name_to_code["')
        sys.stdout.write(smart_str(name))
        sys.stdout.write(u'"] = "{0}";\n'.format(elem))
    sys.stdout.write("\n")
    sys.stdout.write("\n")
    