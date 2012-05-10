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


def _is_valid_lang_code(code):
    """
    Returns whether the given string is a (lexically) valid RFC 3066 language
    code.
    """
    # TODO get valid language codes from somewhere else (e.g., from pycountry)
    return bool(_RFC_3066_LANG_CODE_REGEX.match(code))


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
