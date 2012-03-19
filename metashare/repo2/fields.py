"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import base64

try:
    import cPickle as pickle
except:
    import pickle

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from metashare.repo2.editor.widgets import TextInputWithLanguageAttribute

# NOTE: Custom fields for Django are described in the Django docs:
# - https://docs.djangoproject.com/en/dev/howto/custom-model-fields/
#
# At least basic understanding of the linked docs is required to understand
# the custom field code in this file.  Make sure to consult the docs or the
# related Django code inside django.db.models.fields in case of problems.

# TODO: create MultiTextFieldWithLanguageAttribute...

# pylint: disable-msg=E1102
class MetaBooleanField(models.NullBooleanField):
    """
    BooleanField that can be set to False even if it is requried.
    """
    YES_NO_CHOICES = (
      (True, "Yes"),
      (False, "No")
    )

    default_error_messages = {
        'invalid': _(u'This value must be either True or False.'),
    }
    description = _("Boolean (Either True or False)")
    empty_strings_allowed = False

    # pylint: disable-msg=W0231,W0233
    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['choices'] = self.YES_NO_CHOICES
        models.Field.__init__(self, *args, **kwargs)

    def to_python(self, value):
        if value in (True, False):
            # If value is 1 or 0 than it's equal to True or False, but we want
            # to return a true bool for semantic reasons.
            return bool(value)

        if value in ('t', 'True', '1'):
            return True

        if value in ('f', 'False', '0'):
            return False

        raise ValidationError(self.error_messages['invalid'])


class TextFieldWithLanguageAttribute(models.TextField):
    """
    Customised TextField which also renders a language attribute selection.
    """
    def formfield(self, **kwargs):
        defaults = {'widget': TextInputWithLanguageAttribute}
        
        # If the given kwargs contain widget as key, remove it!
        if 'widget' in kwargs:
            kwargs.pop('widget')

        # Update our defaults dictionary with the given kwargs.
        defaults.update(kwargs)
        return super(TextFieldWithLanguageAttribute, self).formfield(**defaults)


class MultiTextField(models.Field):
    """
    TextField which allows storage of several Strings in one field.
    
    NOTE: due to the Base64-encoded String that is used to store the value(s)
    of a MultiTextField, it is NOT POSSIBLE to access value(s) from instances
    of this field type in QuerySet operations!
    
    If you need to work on MultiTextField instances for filtering, etc. you
    have to retrieve the "real" object instances and check the respective
    fields of type MultiTextField using "obj.attr" field access.
    
    Django will auto-magically convert the raw database representation of the
    MultiTextField value(s) to a Python list of Strings during runtime.
    
    """
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        """
        Initialises this MultiTextField instance.
        """
        # If the given kwargs contain widget as key, remove it!
        if 'widget' in kwargs:
            self.widget = kwargs.pop('widget')

        # Check if label is specified in kwargs.  If so, bind it.
        self.label = None
        if 'label' in kwargs:
            self.label = kwargs.pop('label')

        super(MultiTextField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "TextField"

    def formfield(self, **kwargs):
        defaults = {'widget': self.widget}

        # If we have a label, update defaults dictionary with it.
        if self.label:
            defaults.update({'label': self.label})

        # Update our defaults dictionary with the given kwargs.
        defaults.update(kwargs)
        return super(MultiTextField, self).formfield(**defaults)

    def clean(self, value, model_instance):
        """
        Convert to the value's type and run validation. Validation errors
        from to_python and validate are propagated. The correct value is
        returned iff no error is raised.
        """
        values = self.to_python(value)
        validation_errors = {}

        if not len(values) and not self.blank:
            raise ValidationError(u'This field cannot be blank.')

        for value in values:
            try:
                self.validate(value, model_instance)
                self.run_validators(value)

            except ValidationError, exc:
                validation_errors[value] = exc.messages[0]

        if len(validation_errors.keys()) > 0:
            self.widget.errors.clear()
            self.widget.errors.update(validation_errors)
            raise ValidationError(u'Some fields did not validate.')

        self.widget.errors = {}
        return values

    def to_python(self, value):
        # If we don't have a value, we return an empty list.
        if not value:
            return []

        # If, for some reason, value is already of type list, just return it.
        if isinstance(value, list):
            return value

        # Otherwise, we expect value to be a Base64-encoded String which in
        # turn contains a pickle'd Python list.  We try to decode and loads
        # this into a Python list which is returned as this field's value.
        try:
            return pickle.loads(base64.b64decode(value))

        # In case of problems, we create a list containing information about
        # the exception we have encountered. This is useful for debugging.
        except  :
            return [u'Exception for value {} ({})'.format(value, type(value))]

    def get_prep_value(self, value):
        if not value:
            value = []

        # Before converting the value to Base64-encoded, pickle'd format, we
        # have to assert that we are treating a list or tuple type!
        assert(isinstance(value, list) or isinstance(value, tuple))
        
        # We convert the value list into a Base64-encoded String that contains
        # a pickle'd representation of value.
        return base64.b64encode(pickle.dumps(value))

