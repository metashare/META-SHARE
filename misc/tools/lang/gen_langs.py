
import pycountry
import sys
from django.utils.encoding import smart_str

def read_lang_alpha2():
    langs = pycountry.languages
    lang_list = []
    for index in range(len(langs.objects)):
        lang = langs.objects[index]
        if hasattr(lang, 'alpha2'):
            lang_item = (lang.alpha2)
            lang_list.append(lang_item)
    return lang_list
    
def read_lang_name():
    langs = pycountry.languages
    lang_list = []
    for index in range(len(langs.objects)):
        lang = langs.objects[index]
        if hasattr(lang, 'name'):
            lang_item = (lang.name)
            lang_list.append(lang_item)
    return lang_list
    
if __name__ == "__main__":
    lang_list = read_lang_alpha2()
    sys.stdout.write("/* Obtained from pycountry. */")
    sys.stdout.write("\n\n")
    sys.stdout.write("var _lang_alpha2_list = [")
    sys.stdout.write("\n")
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
    #sys.stdout.write(lang_list)
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
    #sys.stdout.write(lang_list)
    sys.stdout.write("];")
    sys.stdout.write("\n")
    sys.stdout.write("\n")
    sys.stdout.write("var _lang_alpha2_to_name = new Array();")
    for index in range(lang_list_len):
        elem = lang_list[index]
        name = pycountry.languages.get(alpha2=elem).name
        sys.stdout.write(u'_lang_alpha2_to_name["%s"] = "' % elem)
        sys.stdout.write(smart_str(name))
        sys.stdout.write(u'";\n')
    sys.stdout.write("\n")
    sys.stdout.write("\n")
    