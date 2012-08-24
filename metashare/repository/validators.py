"""
Project: META-SHARE prototype implementation
 Author: Christian Spurk <cspurk@dfki.de>
"""
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
    A validator function which raises a ValidationError if any value of the given
    dictionary should be empty.
    """
    
    for value in dict_value.itervalues():
        if value == '':
            # pylint: disable-msg=E1102
            raise ValidationError('This field is required.')  