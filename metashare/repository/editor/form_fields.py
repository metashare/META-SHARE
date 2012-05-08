"""
Project: META-SHARE prototype implementation
 Author: Christian Spurk <cspurk@dfki.de>
"""
from django.core.exceptions import ValidationError
from django.forms.fields import Field
from django.utils.translation import ugettext_lazy as _

from metashare.repository.editor.widgets import DictWidget


class DictField(Field):
    """
    A form field which represents a Python dictionary.
    
    A `required` `DictField` will be validated to not be empty.
    """
    # custom validation error messages
    custom_error_messages = {
        # pylint: disable-msg=E1102
        'duplicate_key': _(u'There may be only one entry with key "{}".'),
        'key_too_long': _(u'A key must be at most {1} characters long, "{0}" '
                          u'has {2} characters.'),
        'val_too_long': _(u'The corresponding value for "{0}" must be at most '
                          u'{1} characters long (was {2}).'),
        'blank_key': _(u'Keys must not be empty.'),
        'blank_value': _(u'Values must not be empty.'),
    }

    def __init__(self, blank_keys=False, blank_values=False,
                 max_key_length=None, max_val_length=None, **kwargs):
        """
        Initializes a new `DictField`.
        
        The `max_key_length`/`max_val_length` arguments specify the maximum
        length of a dictionary entry key/value. The `blank_keys`/`blank_values`
        arguments denote whether keys/values may be empty.
        """
        self.blank_keys = blank_keys
        self.blank_values = blank_values
        self.max_key_length = max_key_length
        self.max_val_length = max_val_length
        # we only work with `DictWidget`s
        kwargs['widget'] = DictWidget(blank=not kwargs.get('required', True),
                                      max_key_length=self.max_key_length,
                                      max_val_length=self.max_val_length)
        # add our custom error messages
        updated_error_messages = {}
        updated_error_messages.update(DictField.custom_error_messages)
        if 'error_messages' in kwargs:
            updated_error_messages.update(kwargs['error_messages'])
        kwargs['error_messages'] = updated_error_messages
        # let our parent do the rest
        super(DictField, self).__init__(**kwargs)

    def to_python(self, value):
        """
        Converts the list of key/value pairs from `DictWidget` to a Python
        dictionary, making sure that there is no duplicate key.
        """
        result = {}
        for key, val in value:
            # ensure that there are no blank keys
            if not self.blank_keys and not key:
                raise ValidationError(self.error_messages['blank_key'])
            # ensure that there are no blank values
            if not self.blank_values and not value:
                raise ValidationError(self.error_messages['blank_value'])
            # ensure that there is no duplicate key in the provided pairs
            if key in result:
                raise ValidationError(self.error_messages['duplicate_key']
                                      .format(key))
            # ensure that the provided entry's key is not too long
            if self.max_key_length and len(key) > self.max_key_length:
                raise ValidationError(self.error_messages['key_too_long']
                                .format(key, self.max_key_length, len(key)))
            # ensure that the provided entry's value is not too long
            if self.max_val_length and len(val) > self.max_val_length:
                raise ValidationError(self.error_messages['val_too_long']
                                .format(key, self.max_val_length, len(val)))
            result[key] = val
        return result
