import sys
from lxml import etree
from django.utils.encoding import smart_str


registry = etree.parse('metashare/bcp47/language-subtag-registry-min4.xml')

def get_all_languages():
    xpath = u"//language/description/text()"
    return registry.xpath(xpath)

def get_language_codes():
    xpath = u"//language/@subtag"
    return registry.xpath(xpath)

def get_language_by_subtag(subtag):
    xpath = u"//language[@subtag='{}']/description/text()".format(subtag)
    return ''.join(registry.xpath(xpath))

def get_language_subtag(language):
    xpath = u"//language[description=\"{}\"]/@subtag".format(language)
    return ''.join(registry.xpath(xpath))

codes = get_language_codes()
languages = get_all_languages()


if __name__ == "__main__":
    sys.stdout.write("/*\n")
    sys.stdout.write("   List of language names and codes obtained from bcp47 registry.\n")
    sys.stdout.write("   To build this file use the following command:\n")
    sys.stdout.write("   python misc/tools/lang/gen_bcp47_langs.py > metashare/media/admin/js/pybcp47.js\n")
    sys.stdout.write("*/\n")
    sys.stdout.write("\n\n")

line_break = 0

sys.stdout.write("var _lang_code_list = [")
sys.stdout.write("\n")

for subtag in sorted(codes):
    sys.stdout.write('"{}", '.format(subtag))
    line_break +=1
    if line_break == 10:
        sys.stdout.write("\n")
        line_break = 0

sys.stdout.write("];")
sys.stdout.write("\n")
sys.stdout.write("\n")

sys.stdout.write("var _lang_name_list = [")
sys.stdout.write("\n")

for lang in sorted(languages):
    sys.stdout.write('"{}", '.format(smart_str(lang)))
    line_break +=1
    if line_break == 10:
        sys.stdout.write("\n")
        line_break = 0

sys.stdout.write("];")
sys.stdout.write("\n")
sys.stdout.write("\n")

sys.stdout.write("var _lang_code_to_name = new Array();\n")
for code in sorted(codes):
    sys.stdout.write("_lang_code_to_name[\"{}\"] = \"{}\";\n"\
                     .format(code,smart_str(get_language_by_subtag(code))))

sys.stdout.write("\n")
sys.stdout.write("\n")

sys.stdout.write("var _lang_name_to_code = new Array();\n")
for lang in languages:
    sys.stdout.write("_lang_name_to_code[\"{}\"] = \"{}\";\n"\
                     .format(smart_str(lang),get_language_subtag(lang)))