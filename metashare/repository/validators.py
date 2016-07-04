import re

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


# a compiled regular expression which matches a lexically valid RFC 3066
# language code
_RFC_3066_LANG_CODE_REGEX = re.compile(r'^[a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})*$')

# a compiled regular expression which matches a lexically valid XML Schema
# `gYear` value
_XML_SCHEMA_GYEAR_REGEX = re.compile(
    r'^\-?\d{4,}(?:Z|14:00|(?:[\-\+](?:0\d|1[0123])):(?:[0-5]\d))?$')

# a tuple of characters that do not match the Char production from XML 1.0
# (Second Edition), cf. http://www.w3.org/TR/2000/WD-xml-2e-20000814#NT-Char
_INVALID_XML_CHARS = tuple([unichr(i) for i in range(0x0, 0x9) + [0xB, 0xC]
        + range(0xE, 0x20) + range(0xD800, 0xE000) + range(0xFFFE, 0x10000)])


def _is_valid_lang_code(code):
    """
    Returns whether the given string is a (lexically) valid RFC 3066 language
    code.
    """
    # TODO get valid language codes from somewhere else (e.g., from pycountry)
    return bool(_RFC_3066_LANG_CODE_REGEX.match(code))


def validate_xml_schema_year(year_value):
    """
    A validator function which raises a ValidationError if the given string
    should not be a valid XML Schema `gYear` value.
    """
    if not bool(_XML_SCHEMA_GYEAR_REGEX.match(year_value)):
        # pylint: disable-msg=E1102
        raise ValidationError(_(u'Enter a valid year value which conforms to '
                u'the XML Schema "gYear" type (see '
                u'http://www.w3.org/TR/xmlschema-2/#gYear). "{}" is not valid.')
            .format(year_value), code='invalid')


def validate_matches_xml_char_production(value):
    """
    A validator function which raises a ValidationError if the given string
    should contain any characters that do not match the Char production from XML
    1.0 (Second Edition), cf.
    http://www.w3.org/TR/2000/WD-xml-2e-20000814#NT-Char.
    """
    for invalid_char in _INVALID_XML_CHARS:
        _pos = value.find(invalid_char)
        if _pos != -1:
            _msg_params = {'char_pos': _pos + 1, 'char_code': ord(invalid_char)}
            # pylint: disable-msg=E1102
            raise ValidationError(_(u'The character at position {char_pos} '
                    u'(&#x{char_code:0>4x};) must not be used. Enter a string '
                    u'consisting of only characters that match the Char '
                    u'production from XML 1.0 (Second Edition), cf. '
                    u'http://www.w3.org/TR/2000/WD-xml-2e-20000814#NT-Char.')
                .format(**_msg_params), code='invalid', params=_msg_params)


def validate_lang_code_keys(dict_value):
    """
    A validator function which raises a ValidationError if any key of the given
    dictionary should not be an RFC 3066 language code.
    """
    for code in dict_value.iterkeys():
        if not _is_valid_lang_code(code):
            # pylint: disable-msg=E1102
            raise ValidationError(_(u'Enter a valid language code as the key '
                                    u'for each pair. "{}" is not valid.')
                                  .format(code), code='invalid')            


def validate_dict_values(dict_value):
    """
    A validator function which raises a ValidationError if any value of the
    given dictionary should be empty or contain any characters that do not match
    the Char production from XML 1.0 (Second Edition).
    """
    for value in dict_value.itervalues():
        if value == '':
            # pylint: disable-msg=E1102
            raise ValidationError(_(u'This field is required.'))
        validate_matches_xml_char_production(value)
