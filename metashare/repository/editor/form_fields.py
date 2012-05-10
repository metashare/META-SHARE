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
    }

    def __init__(self, max_key_length=None, max_val_length=None, **kwargs):
        """
        Initializes a new `DictField`.
        
        The `max_key_length`/`max_val_length` arguments specify the maximum
        length of a dictionary entry key/value.
        """
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
        if value is None:
            return None
        result = {}
        for key, val in value:
            # ensure that there is no duplicate key in the provided pairs
            if key in result:
                raise ValidationError(self.error_messages['duplicate_key']
                                      .format(key))
            result[key] = val
        return result
