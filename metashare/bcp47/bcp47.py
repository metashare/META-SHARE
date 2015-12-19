# -*- coding: utf-8 -*-
from lxml import etree

registry = etree.parse("xml_files/language-subtag-registry.xml")

"""
Tags for Identifying Languages
https://tools.ietf.org/html/bcp47
"""

xpath1 = u"//language[count(deprecated)=0]/description/text()"
xpath2 = u"//language[count(deprecated)=0]/description/text()"

class Language:
    """
    CONTAINS:
    subtag,
    description+,
    added,
    deprecated,
    suppress-script,
    macrolanguage,
    scope,
    preferred-value,
    """
    subtag = None
    description = None
    suppress_script = None
    macrolanguage = None
    added = None
    scope = None
    preferred_value = None

    def __init__(self, description):
        try:
            xpath = u"(//language[./description = \"{}\" and count(deprecated)=0])[1]/description/text()".format(description)
            self.description = registry.xpath(xpath)

            # keep the user selection so that it can be shown back to the form when the subtag is
            # pulled from the database
            self.user_selection = description

            xpath = u"(//language[./description = \"{}\"])[1]/subtag/text()".format(self.description[0])
            self.subtag = u''.join(registry.xpath(xpath))

            xpath = u"(//language[./description = \"{}\"])[1]/suppress-script[.!='']/text()".format(description)
            has_suppress = registry.xpath(xpath)
            if has_suppress:
                self.suppress_script = u''.join(has_suppress)

            xpath = u"(//language[./description = \"{}\"])[1]/macrolanguage[.!='']/text()".format(description)
            has_macro = registry.xpath(xpath)
            if has_macro:
                self.macrolanguage = u''.join(has_macro)

            xpath = u"(//language[./description = \"{}\"])[1]/preferred-value[.!='']/text()".format(description)
            has_pref = registry.xpath(xpath)
            if has_pref:
                self.preferred_value = u''.join(has_pref)

            xpath = u"(//language[./description = \"{}\"])[1]/scope[.!='']/text()".format(description)
            has_scope = registry.xpath(xpath)
            if has_scope:
                self.scope = u''.join(has_scope)

            xpath = u"(//language[./description = \"{}\"])[1]/added/text()".format(description)
            self.added = u''.join(registry.xpath(xpath))

        except IndexError:
            print u"The language you specified does not exist"

    def get_info(self,added=False):
        description_to_string = u""
        for d in self.description:
            description_to_string += d
            if not self.description.index(d) == len(self.description) - 1:
                description_to_string += u", "
        output = u"Language\n\tDescriptions: {}\n\tCode: {}".format(description_to_string, self.subtag)
        if not self.suppress_script is None:
            output += u"\n\tSuppress Script: {}".format(self.suppress_script)
        if not self.macrolanguage is None:
            output += u"\n\tMacrolanguage: {}".format(self.macrolanguage)
        if not self.preferred_value is None:
            output += u"\n\tPreferred Value: {}".format(self.preferred_value)
        if not self.scope is None:
            output += u"\n\tScope: {}".format(self.scope)
        if added:
            output += u"\n\tAdded: {}".format(self.added)
        return output

class Script:
    """
    CONTAINS:
    description+
    subtag
    added
    """

    description = None
    subtag = None
    added = None

    def __init__(self, description):
        try:
            xpath = u"(//script[./description = \"{}\" and count(deprecated)=0])[1]/description/text()".format(
                description)
            self.description = registry.xpath(xpath)

            # keep the user selection so that it can be shown back to the form when the subtag is
            # pulled from the database
            self.user_selection = description

            xpath = u"(//script[./description = \"{}\"])[1]/subtag/text()".format(self.description[0])
            self.subtag = u''.join(registry.xpath(xpath))

            xpath = u"(//script[./description = \"{}\"])[1]/added/text()".format(description)
            self.added = u''.join(registry.xpath(xpath))

        except IndexError:
            print u"The script you specified does not exist"

    def get_info(self):
        description_to_string = u""
        for d in self.description:
            description_to_string += d
            if not self.description.index(d) == len(self.description) - 1:
                description_to_string += u", "
        return u"Script\n\tDescriptions: {}\n\t" \
               u"Code: {}\n\t" \
               u"Added: {}".format(description_to_string, self.subtag, self.added)

class Region:
    """
    CONTAINS:
    description+
    subtag
    added
    """

    description = None
    subtag = None
    added = None

    def __init__(self, description):
        try:
            xpath = u"(//region[./description = \"{}\" and count(deprecated)=0])[1]/description/text()".format(description)
            self.description = registry.xpath(xpath)

            # keep the user selection so that it can be shown back to the form when the subtag is
            # pulled from the database
            self.user_selection = description

            xpath = u"(//region[./description = \"{}\"])[1]/subtag/text()".format(self.description[0])
            self.subtag = u''.join(registry.xpath(xpath))

            xpath = u"(//region[./description = \"{}\"])[1]/added/text()".format(description)
            self.added = u''.join(registry.xpath(xpath))

        except IndexError:
            print u"The region you specified does not exist"

    def get_info(self):
        description_to_string = u""
        for d in self.description:
            description_to_string += d
            if not self.description.index(d) == len(self.description) - 1:
                description_to_string += u", "

        return u"Region\n\tDescriptions: {}\n\t" \
               u"Code: {}\n\t" \
               u"Added: {}".format(description_to_string, self.subtag, self.added)

class Variant:
    """
    CONTAINS:
    subtag
    added
    description+
    prefix+
    """

    description = None
    subtag = None
    added = None
    prefix = None

    def __init__(self, description):
        try:
            xpath = u"(//variant[./description = \"{}\" and count(deprecated)=0])[1]/description/text()".format(description)
            self.description = registry.xpath(xpath)

            # keep the user selection so that it can be shown back to the form when the subtag is
            # pulled from the database
            self.user_selection = description

            xpath = u"(//variant[./description = \"{}\"])[1]/subtag/text()".format(self.description[0])
            self.subtag = u''.join(registry.xpath(xpath))

            xpath = u"(//variant[./description = \"{}\"])[1]/added/text()".format(description)
            self.added = u''.join(registry.xpath(xpath))

            xpath = u"(//variant[./description = \"{}\"])[1]/prefix/text()".format(description)
            self.prefix = registry.xpath(xpath)

        except IndexError:
            print u"The variant you specified does not exist"

    def get_info(self):
        description_to_string = u""
        prefix_to_string = u""
        for d in self.description:
            description_to_string += d
            if not self.description.index(d) == len(self.description) - 1:
                description_to_string += u", "

        for p in self.prefix:
            prefix_to_string += p
            if not self.prefix.index(p) == len(self.prefix) - 1:
                prefix_to_string += u", "
        output = u"Variant\n\tDescriptions: {}\n\tCode: {}\n\tAdded: {}".format(description_to_string, self.subtag, self.added)
        if not self.prefix is None:
            output += u"\n\tPrefixes: {}".format(prefix_to_string)
        return output

class LanguageTag:
    def __init__(self, subtags):
        self.language = Language(subtags[0])
        if len(subtags) >= 2:
            self.script = Script(subtags[1])
        if len(subtags) >= 3:
            self.region = Region(subtags[2])
        if len(subtags) == 4:
            self.variant = Variant(subtags[3])
        if len(subtags) > 4:
            print u"Invalid number of arguments"

    def get_info(self):
        return u"{}\n{}\n{}\n{}".format(self.language.get_info(), self.script.get_info(), self.region.get_info(),
            self.variant.get_info())

    def get_tag(self):
        l = list()
        l.append(self.language.subtag)
        if not self.script.subtag == None and \
                not self.script.subtag == self.language.suppress_script:
            l.append(self.script.subtag)
        if not self.region.subtag == None:
            l.append(self.region.subtag)
        if not self.variant.subtag == None:
            l.append(self.variant.subtag)
        return '-'.join(l)

# test
# lang1 = Language(u"E'ñapa Woromaipu")
# script1= Script(u"Alibata")
# region1 = Region(u"Singapore")
# variant1 = Variant(u"Wade-Giles romanization")
