"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import base64
import logging

try:
    import cPickle as pickle
except:
    import pickle

from django.forms.util import flatatt

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.forms import widgets, TextInput
from django.template.loader import render_to_string
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

from metashare import settings

# Setup logging support.
logging.basicConfig(level=settings.LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repository.widgets')
LOGGER.addHandler(settings.LOG_HANDLER)


class TextInputWithLanguageAttribute(widgets.Input):
    input_type = 'text'
    attribute_length = 5
    
    def __init__(self, *args, **kwargs):
        """
        Initialises a new TextInputWithLanguageAttribute instance.
        
        This calls the super class constructor with any remaining args.
        """
        super(TextInputWithLanguageAttribute, self).__init__(*args, **kwargs)
    
    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, returns the value
        of this widget. Returns None if it's not provided.
        """
        lang = '{0}_lang'.format(name)
        _value = '{0:5}{1}'.format(data.get(lang, '')[:self.attribute_length],
          data.get(name, '')).strip()
        
        if _value == '':
            return None
        
        return _value
    
    def render(self, name, value, attrs=None):
        if value is None or value == '':
            attribute = ''
            value = ''
        
        else:
            attribute = value[:self.attribute_length].strip()
            value = value[self.attribute_length:]
        
        lang = '{0}_lang'.format(name)
        attribute_attrs = self.build_attrs({'maxlength': self.attribute_length},
          type='text', name=lang)
        if attribute != '':
            # Only add the 'value' attribute if a value is non-empty.
            attribute_attrs['value'] = force_unicode(self._format_value(attribute))
        
        final_attrs = self.build_attrs({'style': 'width:400px;'},
          type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))
        
        return mark_safe(u'<input{0} /> <strong>Language:</strong> <input{1} />'.format(
          flatatt(final_attrs), flatatt(attribute_attrs)))


class SingleChoiceTypeWidget(RelatedFieldWidgetWrapper):
    """
    A widget for a single element of a xs:choice type.
    """
    class Media:
        js = (
          settings.MEDIA_URL + "js/jquery-1.7.1.min.js",
          settings.MEDIA_URL + "js/choice-type-widget.js",
        )

    def __init__(self, rel, admin_site, *args, **kwargs):
        """
        Initialises this widget instance.
        """
        super(SingleChoiceTypeWidget, self).__init__(widgets.Select(), rel,
          admin_site, *args, **kwargs)

        self.subclass_select = None        
        self.subclasses = self._compute_sub_classes()

    def _compute_sub_classes(self):
        """
        Computes the choice tuple of available sub classes for this widget.
        """
        _subclasses = []

        _instance = self.rel.to()
        for _cls in _instance.__class__.__subclasses__():
            _subclass = _cls()
            data_type = _subclass.__class__.__name__.lower()
            type_name = _subclass.__schema_name__

            if type_name == "STRINGMODEL":
                type_name = _subclass.__class__.__name__
                type_name = type_name[0:type_name.find('String_model')]

            _subclasses.append((data_type, type_name))

        _choices = [('', 'Create new ...')]
        _choices.extend(_subclasses)
        if len(_choices) == 1:
            raise AssertionError('No sub classes found for {}?'.format(
              _instance.__class__.__name__))

        self.subclass_select = widgets.Select(choices=_choices)
        return _subclasses

    def render(self, name, value, *args, **kwargs):
        # We are not using self.admin_site.root_path as this seems broken...
        proto_url = '/{}admin/{}'.format(settings.DJANGO_BASE,
          self.rel.to._meta.app_label)
        self.widget.choices = self.choices
        output = [self.widget.render(name, value, *args, **kwargs)]

        if self.can_add_related:
            output.append(' ')
            # Salvatore: changed from 'onclick' to 'onchange' because
            # on Windwos browsers onclick is triggered as soon as the
            # user click on the down arrow and before he/she actually
            # selects the item from the list.
            output.append(self.subclass_select.render('subclass_select', '',
              attrs={'onchange': 'javascript:createNewSubInstance($(this), ' \
                '"add_id_{}", "{}");'.format(name, proto_url)}))

        return mark_safe(u''.join(output))


class MultiChoiceTypeWidget(SingleChoiceTypeWidget):
    """
    A widget for several elements of a xs:choice type.
    """
    def __init__(self, rel, admin_site, *args, **kwargs):
        """
        Initialises this widget instance.
        """
        # pylint: disable-msg=E1003
        super(SingleChoiceTypeWidget, self).__init__(widgets.SelectMultiple(),
          rel, admin_site, *args, **kwargs)
        
        self._compute_sub_classes()



class MultiFieldWidget(widgets.Widget):
    """
    A MultiFieldWidget allows to enter lists of data using a certain widget.
    
    Attributes:
    - widget: input widget, defaults to TextInput.
    - style: CSS style settings for the input widget.
    """
    class Media:
        """
        Media sub class to inject custom CSS and JavaScript code.
        """
        css = {
          'all': ('css/repository.css',)
        }
        js = ('js/multi-field-widget.js',)
    
    def __init__(self, widget_id, *args, **kwargs):
        """
        Initialises a new MultiFieldWidget instance.
        
        This saves the given, required widget_id, clears the errors dictionary
        and then calls the super class constructor with any remaining args.
        """
        self.widget_id = widget_id
        self.errors = {}
        super(MultiFieldWidget, self).__init__(*args, **kwargs)
    
    def render(self, name, value, attrs=None):
        """
        Renders the MultiFieldWidget with the given name and value.
        """
        LOGGER.info('render({0}, {1} [{2}])'.format(name, value, type(value)))
        LOGGER.debug('attrs: {0} errors: {1}'.format(self.attrs, self.errors))
        
        # If no value is given, we set it to an empty list.
        if not value:
            value = []
        
        # If we get a String object instead of the expected list-typed value,
        # there has been a validation problem.  This means that the value is
        # not yet converted from its serialised form into a list of values.
        if isinstance(value, basestring):
            # Try converting the String to list type.
            try:
                value = pickle.loads(base64.b64decode(value))
            
            # 
            except:
                LOGGER.error('Error converting value to list!')
                value = []
        
        # The widget used for this MultiFieldWidget is defined in self.attrs.
        input_widget = self.attrs.get('widget', TextInput)
        
        # We collect all rendered widgets inside _field_widgets.
        _field_widgets = []
        _field_attrs = {'id': 'id_{0}'.format(name), 'class': 'input',
          'style': self.attrs.get('style', 'width:250px;')}
        
        # Iterate over all sub values for this MultiFieldWidget instance,
        # adding an index number 0..n-1 to support container id generation.
        for _id, _value in enumerate(value):
            # Render input_widget instance as HTML.
            _field_widget = input_widget().render(name, _value, _field_attrs)
            
            # Define context for container template rendering.
            _context = {'id': _id, 'field_widget': _field_widget,
              'widget_id': self.widget_id,
              'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX}
            
            # If there have been any validation errors, add the message.
            if _value in self.errors.keys():
                _context.update({'error_msg': self.errors[_value]})
            
            # Render container for this sub value's widget and append to list.
            _container = render_to_string('repository/container.html', _context)
            _field_widgets.append(_container)
        
        # If list of values is empty, render an empty container instead.
        _id = len(value)
        if not _id:
            # Note that value='' as values is empty.
            _field_widget = input_widget().render(name, '', _field_attrs)
            _context = {'id': _id, 'field_widget': _field_widget,
              'widget_id': self.widget_id,
              'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX}
            
            _container = render_to_string('repository/container.html', _context)
            _field_widgets.append(_container)
        
            _field_widget = input_widget().render(name, '', _field_attrs)
            _context = {'id': _id, 'field_widget': _field_widget,
              'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX}
        
        # The JavaScript code needs an empty "template" to create new input
        # widgets dynamically; this is pre-rendered and added to the template
        # for the MultiFieldWidget instance here.
        _empty_widget = input_widget().render(name, '', _field_attrs)
        _context = {'empty_widget': _empty_widget,
          'field_widgets': mark_safe(u'\n'.join(_field_widgets)),
          'widget_id': self.widget_id,
          'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX}
        
        # Render final HTML for this MultiFieldWidget instance.
        _html = render_to_string('repository/multi_field_widget.html', _context)
        return mark_safe(_html)
    
    def value_from_datadict(self, data, files, name):
        """
        Encodes the data for this MultiFieldWidget instance as base64 String.
        """
        widget = self.attrs.get('widget', TextInput)()
        if isinstance(widget, TextInputWithLanguageAttribute):
            _attributes = [v[:widget.attribute_length]
              for v in data.getlist('{0}_lang'.format(name))]
            _values = [v for v in data.getlist(name)]
            
            _value = ['{0:5}{1}'.format(_a, _v).strip()
              for _a, _v in zip(_attributes, _values)]
            _value = [v for v in _value if v]
        
        else:
            _value = [v for v in data.getlist(name) if v]
        
        if not len(_value):
            return None
        
        return base64.b64encode(pickle.dumps(_value))

    def _has_changed(self, initial, data):
        """
        Checks whether the field values have changed.  As data is already an
        pickled, base64 encoded String, we have to de-serialise it first!
        """
        _data = data
        
        if isinstance(data, basestring):
            # Try converting the String to list type.
            try:
                _data = pickle.loads(base64.b64decode(data))
            
            # 
            except:
                LOGGER.error('Error converting value to list!')
                _data = []
        
        elif data is None:
            # Salvatore: If the user leaves the field empty assigning
            # an empty list will result in a comparison between
            # None (the value of initial) and [] (the value of _data),
            # yielding a True value as if the user changed the value
            # of the field. Check if in other cases this should really
            # be the empty list.
            
            #_data = []
            pass
        
        return initial != _data
