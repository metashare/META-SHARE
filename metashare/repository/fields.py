import base64
from django.contrib.admin import widgets

try:
    import cPickle as pickle
except:
    import pickle

from django import forms
from django.core import exceptions, validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from metashare.repository.editor import form_fields

# NOTE: Custom fields for Django are described in the Django docs:
# - https://docs.djangoproject.com/en/dev/howto/custom-model-fields/
#
# At least basic understanding of the linked docs is required to understand
# the custom field code in this file.  Make sure to consult the docs or the
# related Django code inside django.db.models.fields in case of problems.


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

        if value in ('t', 'True', '1', 'Yes'):
            return True

        if value in ('f', 'False', '0', 'No'):
            return False

        raise exceptions.ValidationError(self.error_messages['invalid'])


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
    default_error_messages = {
        # pylint: disable-msg=E1102
        'too_long': _(u'A single field must be at most {0} characters long '
                      u'(was {1}).'),
    }

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

    def validate(self, value, model_instance):
        """
        Validates value and throws `ValidationError`.
        """
        super(MultiTextField, self).validate(value, model_instance)
        if self.max_length and len(value) > self.max_length:
            raise exceptions.ValidationError(self.error_messages['too_long']
                                    .format(self.max_length, len(value)))

    def clean(self, value, model_instance):
        """
        Convert to the value's type and run validation. Validation errors
        from to_python and validate are propagated. The correct value is
        returned iff no error is raised.
        """
        values = self.to_python(value)
        validation_errors = {}

        if not len(values) and not self.blank:
            raise exceptions.ValidationError(self.error_messages['blank'])

        for value in values:
            try:
                self.validate(value, model_instance)
                self.run_validators(value)

            except exceptions.ValidationError, exc:
                validation_errors[value] = exc.messages[0]

        if len(validation_errors.keys()) > 0:
            self.widget.errors.clear()
            self.widget.errors.update(validation_errors)
            raise exceptions.ValidationError(u'Some fields did not validate.')

        self.widget.errors = {}
        return values

    def get_internal_type(self):
        """
        Returns internal type for this field.
        """
        return "TextField"

    def formfield(self, **kwargs):
        defaults = {'widget': self.widget}

        # If we have a label, update defaults dictionary with it.
        if self.label:
            defaults.update({'label': self.label})

        # Update our defaults dictionary with the given kwargs.
        defaults.update(kwargs)
        return super(MultiTextField, self).formfield(**defaults)

    def get_prep_value(self, value):
        """
        Takes a Python value and converts it into a database String.
        """
        if not value:
            value = []

        # Before converting the value to Base64-encoded, pickle'd format, we
        # have to assert that we are treating a list or tuple type!
        assert(isinstance(value, list) or isinstance(value, tuple))
        
        # We convert the value list into a Base64-encoded String that contains
        # a pickle'd representation of value.
        return base64.b64encode(pickle.dumps(value))

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


# pylint: disable-msg=W0201
class MultiSelectField(models.Field):
    """
    Model field which allows to select one or several choices.
    """
    __metaclass__ = models.SubfieldBase

    # Maps 1-digit hexadecimal numbers to their corresponding bit quadruples.
    __HEX_TO_BITS__ = {
      'f': (1,1,1,1), 'e': (1,1,1,0), 'd': (1,1,0,1), 'c': (1,1,0,0),
      'b': (1,0,1,1), 'a': (1,0,1,0), '9': (1,0,0,1), '8': (1,0,0,0),
      '7': (0,1,1,1), '6': (0,1,1,0), '5': (0,1,0,1), '4': (0,1,0,0),
      '3': (0,0,1,1), '2': (0,0,1,0), '1': (0,0,0,1), '0': (0,0,0,0)
    }
    
    # Maps bit quadruples to their hexadecimal correspondents.
    __BITS_TO_HEX__ = {
      (1,1,1,1): 'f', (1,1,1,0): 'e', (1,1,0,1): 'd', (1,1,0,0): 'c',
      (1,0,1,1): 'b', (1,0,1,0): 'a', (1,0,0,1): '9', (1,0,0,0): '8',
      (0,1,1,1): '7', (0,1,1,0): '6', (0,1,0,1): '5', (0,1,0,0): '4',
      (0,0,1,1): '3', (0,0,1,0): '2', (0,0,0,1): '1', (0,0,0,0): '0'
    }

    @classmethod
    def _get_FIELD_display(cls, self, field):
        """
        Returns a String containing the "human-readable" values of the field.
        """
        values = getattr(self, field.attname)
        choices_dict = dict(field.choices)
        return u', '.join([force_unicode(choices_dict.get(value, value),
          strings_only=True) for value in values])

    @classmethod
    def _get_FIELD_display_list(cls, self, field):
        """
        Returns a list containing the "human-readable" values of the field.
        """
        values = getattr(self, field.attname)
        choices_dict = dict(field.choices)
        return [force_unicode(choices_dict.get(value, value),
          strings_only=True) for value in values]

    def contribute_to_class(self, cls, name):
        """
        Adds get_FOO_display(), get_FOO_display_list() methods to this class.
        """
        self.set_attributes_from_name(name)
        self.model = cls
        cls._meta.add_field(self)
        setattr(cls, 'get_%s_display' % self.name,
          curry(self._get_FIELD_display, field=self))
        setattr(cls, 'get_%s_display_list' % self.name,
          curry(self._get_FIELD_display_list, field=self))

    def formfield(self, form_class=forms.MultipleChoiceField, **kwargs):
        """
        Returns a django.forms.Field instance for this database Field.
        
        Using super() won't work because this would replace the form_class!
        
        """
        defaults = {
          'choices': sorted(self.get_choices(include_blank=False),
                            key=lambda choice: choice[1].lower()),
          'help_text': self.help_text,
          'label': capfirst(self.verbose_name),
          'required': not self.blank,
        }

        if self.has_default():
            if callable(self.default):
                defaults['initial'] = self.default
                defaults['show_hidden_initial'] = True

            else:
                defaults['initial'] = self.get_default()
        # replace default widget
        kwargs['widget'] = widgets.FilteredSelectMultiple(self.verbose_name, False)
        defaults.update(kwargs)
        return form_class(**defaults)

    def get_choices_default(self):
        """
        Returns choices without the default blank choice.
        """
        return self.get_choices(include_blank=False)

    def get_internal_type(self):
        """
        Returns internal type for this field.
        """
        return "CharField"

    def get_prep_value(self, value):
        """
        Takes a Python value and converts it into a database String.
        """
        # If the value is empty or None, we return an empty String for it.
        if not value:
            return ''

        # If the value is already a String, we simply return the value.
        if isinstance(value, basestring):
            return value

        # Otherwise, we assert that we are working on a list.  This will raise
        # an exception for ill-typed values.
        assert(isinstance(value, list))

        # We now want to convert the list of values into a bit vector matching
        # the values' index positions inside list(enumerate(self.choices))...
        #
        # For this, we first create a list of "bits", defaulting to 0.  The
        # length of this list is (1 + len(self.choices) / 4) * 4 as we will
        # convert quadruples of (a,b,c,d) to their hexadecimal counterparts.
        # 
        # The resulting list already has the right amount of zero padding.
        bits = [0] * (1 + len(self.choices) / 4) * 4

        # We iterate over the enumerated choices and compare each choice value
        # with the current list of selected values.  If there is a match, we
        # store a 1 in the right index position of the bits list.
        #
        # Example: if we have 3 possible choices A, B, C and our value list
        # contains [A, C], we would create the following bits list [1,0,1].
        for index, choice in enumerate(self.choices):
            if choice[0] in value:
                bits[index] = 1

        # The bits list has to be converted into a hexadecimal String.  To do
        # so, we take all (1 + len(self.choicese) / 4) quadruples inside the
        # bits list and map them to their hexadecimal correspondent.
        values = ''
        for index in range(len(bits)/4):
            offset = index * 4
            values += self.__BITS_TO_HEX__[tuple(bits[offset:offset+4])]

        # Finally, we return the resulting hexadecimal String.
        return values

    def to_python(self, value):
        """
        Takes a hexadecimal String value and converts it into a Python list.
        """
        # If the value is empty or None, we return an empty list.
        if not value:
            return []

        # If the value is already a list, we simply return the value.
        if isinstance(value, list):
            return value

        # Otherwise, we assert that we are working on a String.  This will
        # raise an exception for ill-typed values.
        assert(isinstance(value, basestring))

        # We iterate over all characters of the hexadecimal String and convert
        # it to the corresponding bits quadruple.  Using these data, we can
        # then compute the index positions of selected choices for this field.
        indices = []
        for index in range(len(value.lower())):
            offset = index * 4
            _value = self.__HEX_TO_BITS__[value[index]]
            for _pos in range(4):
                if _value[_pos]:
                    indices.append(offset + _pos)

        # Now that we know the index positions of all selected choices, we
        # simply have to convert these to the corresponding choice values.
        values = []
        for index, choice in enumerate(self.choices):
            if index in indices:
                values.append(choice[0])

        # Finally, we return the list of selected choice values.
        return values

    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError.
        """
        if isinstance(value, list):
            valid_choices = [k for k, _unused_value in self.choices]
            for choice in value:
                if choice not in valid_choices:
                    _msg = self.error_messages['invalid_choice'] % choice
                    raise exceptions.ValidationError(_msg)

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages['null'])

        if not self.blank and value in validators.EMPTY_VALUES:
            raise exceptions.ValidationError(self.error_messages['blank'])

    def value_to_string(self, obj):
        """
        Used by the serialisers to convert the field into a string for output.
        """
        return self.get_prep_value(self._get_val_from_obj(obj))


class DictField(models.Field):
    """
    A model field which represents a Python dictionary.
    
    A `DictField` with `blank=False` must not be empty/None. The `null` argument
    does not have any effect for `DictField`s, it is always set to `True`.
    
    Every model with a `DictField` can be instructed to return the default value
    of the dictionary using the `get_default_FOO()` method (where `FOO` is the
    name of the field on the model). By default, the default value will be the
    unicode representation of a random value from the dictionary or the empty
    string if the dictionary is empty. You may override the mechanism which
    determines the default value; see the constructor documentation for more
    information.
    """
    __metaclass__ = models.SubfieldBase
    default_error_messages = {
        # pylint: disable-msg=E1102
        'key_too_long': _(u'A key must be at most {1} characters long, "{0}" '
                          u'has {2} characters.'),
        'val_too_long': _(u'The corresponding value for "{0}" must be at most '
                          u'{1} characters long (was {2}).'),
        'blank_key': _(u'Keys must not be empty.'),
        'blank_value': _(u'Values must not be empty.'),
    }

    def __init__(self, *args, **kwargs):
        """
        Initializes a new `DictField`.
        
        You might want to specify a `label` argument which is used in the
        rendering of form fields of this custom field. Any `default_retriever`
        argument may be a function taking a single Python dictionary argument
        which overrides the default value retrieval.
        
        Any `max_key_length`/`max_val_length` arguments specify the maximum
        length of a dictionary entry key/value (there isno maximum length by
        default). Any `blank_keys`/`blank_values` arguments denote whether
        keys/values may be empty/None (both must not be empty by default).
        """
        kwargs['null'] = True
        self.label = kwargs.pop('label', None)
        self.max_key_length = kwargs.pop('max_key_length', None)
        self.max_val_length = kwargs.pop('max_val_length', None)
        self.blank_keys = kwargs.pop('blank_keys', False)
        self.blank_values = kwargs.pop('blank_values', False)
        if 'default_retriever' in kwargs:
            self.default_retriever = kwargs.pop('default_retriever')
        else:
            def _default_retriever(_dict):
                if _dict:
                    _result = _dict.itervalues().next()
                else:
                    _result = ''
                return force_unicode(_result, strings_only=True)
            self.default_retriever = _default_retriever
        super(DictField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        """
        Specifies which *preexisting* Django Field class this class is most
        similar to.
        
        This helps Django to decide which kind of DB column type to use for
        storing this field.
        """
        return "TextField"

    def formfield(self, **kwargs):
        """
        Returns the default form field to use when this custom field is used in
        a form.
        """
        defaults = { 'form_class': form_fields.DictField,
                     'max_key_length': self.max_key_length,
                     'max_val_length': self.max_val_length }
        if self.label:
            defaults['label'] = self.label
        defaults.update(kwargs)
        return super(DictField, self).formfield(**defaults)

    def validate(self, value, model_instance):
        """
        Validates the given dictionary value and throws `ValidationError`s.
        """
        super(DictField, self).validate(value, model_instance)
        for key, val in value.iteritems():
            # ensure that there are no blank keys
            if not self.blank_keys and not key:
                raise ValidationError(self.error_messages['blank_key'])
            # ensure that there are no blank values
            if not self.blank_values and not value:
                raise ValidationError(self.error_messages['blank_value'])
            # ensure that the provided entry's key is not too long
            if self.max_key_length and len(key) > self.max_key_length:
                raise ValidationError(self.error_messages['key_too_long']
                                .format(key, self.max_key_length, len(key)))
            # ensure that the provided entry's value is not too long
            if self.max_val_length and len(val) > self.max_val_length:
                raise ValidationError(self.error_messages['val_too_long']
                                .format(key, self.max_val_length, len(val)))

    def get_prep_value(self, value):
        """
        Converts the given Python dictionary to its DB representation.
        """
        # before converting the value to Base64-encoded, pickle'd format, we
        # assert that we are treating a dictionary
        assert(isinstance(value, dict))
        # we convert the value list into a Base64-encoded String that contains
        # a pickle'd representation of value
        return base64.b64encode(pickle.dumps(value))

    def to_python(self, value):
        """
        Converts the given value to a Python dictionary.
        
        The value can be in the internal DB representation, an empty value or a
        Python dictionary.  
        """
        # if for some reason value is already of type dict, then just return it
        if isinstance(value, dict):
            return value
        # create an empty dictionary for empty values
        if not value:
            return {}
        # otherwise, we expect value to be a Base64-encoded String which in turn
        # contains a pickle'd Python list. We try to decode and load this into a
        # Python dict which is returned as this field's value.
        return pickle.loads(base64.b64decode(value))

    @classmethod
    def _get_default_FIELD(cls, self, field):
        """
        Returns the default value of the given field instance.
        """
        return field.default_retriever(getattr(self, field.attname))

    def contribute_to_class(self, cls, name):
        """
        Adds the get_default_FOO() method to this class.
        """
        self.set_attributes_from_name(name)
        self.model = cls
        cls._meta.add_field(self)
        setattr(cls, 'get_default_%s' % self.name,
                curry(self._get_default_FIELD, field=self))


class XmlCharField(models.CharField):
    """
    A `CharField` which only allows the characters that match the Char
    production from XML 1.0 (Second Edition) (cf.
    http://www.w3.org/TR/2000/WD-xml-2e-20000814#NT-Char).
    """
    def formfield(self, **kwargs):
        defaults = {'form_class': form_fields.XmlCharField}
        defaults.update(kwargs)
        return super(XmlCharField, self).formfield(**defaults)


def best_lang_value_retriever(_dict):
    """
    A `default_retriever` function which can be passed into a `DicField`.
    
    This default value retriever prefers values of entries which have some
    common English language code as the key. If there is no such key, an 'und'
    language code key is tried. Otherwise a random value is returned. If the
    dictionary is empty, then the empty string is returned.
    """
    if _dict:
        if 'en' in _dict:
            _result = _dict['en']
        elif 'eng' in _dict:
            _result = _dict['eng']
        elif 'en-GB' in _dict:
            _result = _dict['en-GB']
        elif 'en-US' in _dict:
            _result = _dict['en-US']
        elif 'und' in _dict:
            _result = _dict['und']
        else:
            _result = _dict.itervalues().next()
    else:
        _result = ''
    return force_unicode(_result, strings_only=True)
