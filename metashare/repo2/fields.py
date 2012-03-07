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
    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _(u'This value must be either True or False.'),
    }
    description = _("Boolean (Either True or False)")
    # pylint: disable-msg=W0231,W0233
    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['choices'] = self.YES_NO_CHOICES
        models.Field.__init__(self, *args, **kwargs)

    def to_python(self, value):
        if value in (True, False):
            # if value is 1 or 0 than it's equal to True or False, but we want
            # to return a true bool for semantic reasons.
            return bool(value)
        if value in ('t', 'True', '1'):
            return True
        if value in ('f', 'False', '0'):
            return False
        raise ValidationError(self.error_messages['invalid'])


class TextFieldWithLanguageAttribute(models.TextField):
    def formfield(self, **kwargs):
        defaults = {'widget': TextInputWithLanguageAttribute}
        
        if 'widget' in kwargs:
            kwargs.pop('widget')
        
        defaults.update(kwargs)
        return super(TextFieldWithLanguageAttribute, self).formfield(**defaults)


class MultiTextField(models.Field):
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        if 'widget' in kwargs:
            self.widget = kwargs.pop('widget')
        
        self.label = None
        if 'label' in kwargs:
            self.label = kwargs.pop('label')
        
        super(MultiTextField, self).__init__(*args, **kwargs)
    
    def get_internal_type(self):
        return "TextField"
    
    def formfield(self, **kwargs):
        defaults = {'widget': self.widget}
        
        if self.label:
            defaults.update({'label': self.label})
        
        defaults.update(kwargs)
        return super(MultiTextField, self).formfield(**defaults)
    
    def clean(self, value, model_instance):
        """
        Convert the value's type and run validation. Validation errors from to_python
        and validate are propagated. The correct value is returned if no error is
        raised.
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
        if not value:
            return []
        
        if isinstance(value, list):
            return value
        
        try:
            return pickle.loads(base64.b64decode(value))
        
        except:
            # In case of problems, we create a list containing 'exception'.
            # This is useful for debugging, we could use format_exc() to
            # get more detailed information on the exception raised...
            return [u'Exception for value {0} ({1})'.format(value,
              type(value))]
    
    def get_prep_value(self, value):
        if not value:
            value = []
        
        assert(isinstance(value, list) or isinstance(value, tuple))
        return base64.b64encode(pickle.dumps(value))

