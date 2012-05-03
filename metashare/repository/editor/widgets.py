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

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.forms import widgets, TextInput, Textarea
from django.forms.util import flatatt
from django.template.loader import render_to_string
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

from metashare import settings

# Setup logging support.
logging.basicConfig(level=settings.LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repository.widgets')
LOGGER.addHandler(settings.LOG_HANDLER)

# the maximum length (in characters) where `TextInput` widgets will still be
# used; for larger sizes we use `Textarea` widgets
_MAX_TEXT_INPUT_SIZE = 80


class DictWidget(widgets.Widget):
    """
    A widget for rendering dictionaries as represented by `DictField` form
    fields.
    
    By default key/value input widgets will be `TextInput` widgets. If a
    sufficiently large maximum size is specified for either of them, the input
    wisgets may also become `Textarea` widgets.
    """
    class Media:
        css = { 'all': ('admin/css/dict_widget.css',) }
        js = ('admin/js/dict_widget.js',)

    # templates for the names of key/value "<input/>" fields
    _key_field_name_tpl = 'key_{}_{}'
    _val_field_name_tpl = 'val_{}_{}'

    def __init__(self, blank=False, max_key_length=None, max_val_length=None):
        """
        Initializes a new `DictWidget` with the given maximum dictionary
        key/value sizes (in characters).
        
        The `blank` argument denotes whether empty dictionarys should be allowed
        or not. This is only enforced via JavaScript, though!
        """
        self.blank = blank
        self.max_key_length = max_key_length
        self.max_val_length = max_val_length
        super(DictWidget, self).__init__()

    def render(self, name, value, attrs=None):
        """
        Returns this Widget rendered as HTML, as a Unicode string.

        The 'value' given is not guaranteed to be valid input, so subclass
        implementations should program defensively.
        """
        _entries = []
        _context = { 'blank': self.blank, 'entries': _entries,
            'new_entry_tpl': self._get_dict_entry(name, '', None, None) }
        if isinstance(value, dict):
            # (we have gotten an existing Python dict)
            idx = 0
            for key, val in value.iteritems():
                _entries.append(self._get_dict_entry(name, idx, key, val))
                idx += 1
        elif isinstance(value, list):
            # (we have gotten a non-valid key/value pair list that was created
            # in value_from_datadict())
            idx = 0
            for entry in value:
                _entries.append(self._get_dict_entry(name, idx, entry[0],
                                                     entry[1]))
                idx += 1
        else:
            _entries.append(self._get_dict_entry(name, 0, None, None))
        # render final HTML for this widget instance
        return mark_safe(render_to_string('repository/editor/dict_widget.html',
                                          _context))

    def _get_dict_entry(self, field_name, idx, key, value):
        """
        Returns a tuple (pair) with a rendered key and value input field.
        
        `field_name` and `id` will be used in the names of the input fields.
        """
        _key_field_name = DictWidget._key_field_name_tpl.format(field_name, idx)
        if self.max_key_length and self.max_key_length > _MAX_TEXT_INPUT_SIZE:
            rendered_key = Textarea().render(_key_field_name, key)
        else:
            rendered_key = \
                TextInput(attrs={ 'maxlength': self.max_key_length }) \
                    .render(_key_field_name, key)

        _val_field_name = DictWidget._val_field_name_tpl.format(field_name, idx)
        if self.max_val_length and self.max_val_length > _MAX_TEXT_INPUT_SIZE:
            rendered_val = Textarea().render(_val_field_name, value)
        else:
            rendered_val = \
                TextInput(attrs={ 'maxlength': self.max_val_length }) \
                    .render(_val_field_name, value)

        return (rendered_key, rendered_val)

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data from the input form and this widget's name,
        returns the value of this widget as a list of key/value pairs.
        """
        # collect the key/value data that was provided by the user (not as a
        # dictionary, so that we can later cleanly validate the data):
        provided = []
        idx = 0
        while True:
            key_name = DictWidget._key_field_name_tpl.format(name, idx)
            val_name = DictWidget._val_field_name_tpl.format(name, idx)
            if not key_name in data or not val_name in data:
                break
            provided.append((data[key_name], data[val_name]))
            idx += 1
        return provided


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


class SubclassableRelatedFieldWidgetWrapper(RelatedFieldWidgetWrapper):
    """
    A replacement for RelatedWidgetWrapper suitable for related fields which are subclassable.
    
    Instead of the default 'plus' button to add a new related item in a popup window,
    this implementation shows a dropdown menu letting the user choose which subtype to create.
    """
    class Media:
        js = (
          settings.MEDIA_URL + "js/choice-type-widget.js",
        )

    def __init__(self, widget, rel, admin_site, *args, **kwargs):
        """
        Initialises this widget instance.
        """
        super(SubclassableRelatedFieldWidgetWrapper, self).__init__(widget, rel,
          admin_site, *args, **kwargs)

        self.subclass_select, self.subclasses = self._compute_sub_classes()

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

        _subclass_select = widgets.Select(choices=_choices)
        return _subclass_select, _subclasses

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
        LOGGER.debug('render({0}, {1} [{2}])'.format(name, value, type(value)))
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
