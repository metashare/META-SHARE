import base64
import logging
try:
    import cPickle as pickle
except:
    import pickle

from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.contrib.admin.widgets import AdminTextInputWidget
from django.forms import widgets, TextInput, Textarea, Media, Select
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from selectable.forms.widgets import SelectableMediaMixin, SelectableMultiWidget, \
    LookupMultipleHiddenInput
from django.utils.http import urlencode
from metashare import settings
from selectable.forms.widgets import AutoCompleteWidget, AutoCompleteSelectWidget        
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django import forms

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)

# the maximum length (in characters) where `TextInput` widgets will still be
# used; for larger sizes we use `Textarea` widgets
_MAX_TEXT_INPUT_SIZE = 150


class DictWidget(widgets.Widget):
    """
    A widget for rendering dictionaries as represented by `DictField` form
    fields.
    
    By default key/value input widgets will be `TextInput` widgets. If a
    sufficiently large maximum size is specified for either of them, the input
    widgets may also become `Textarea` widgets.
    """
    class Media:
        css = { 'all': ('{}css/dict_widget.css'.format(
                            settings.ADMIN_MEDIA_PREFIX),) }
        js = ('{}js/dict_widget.js'.format(settings.ADMIN_MEDIA_PREFIX),)

    # templates for the names of key/value "<input/>" fields
    _key_field_name_tpl = 'key_{}_{}'
    _val_field_name_tpl = 'val_{}_{}'
    
    key_widget = None

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
        # path to the Django template which is used to render this widget
        self._template = 'repository/editor/dict_widget.html'
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
                _entries.append(self._get_dict_entry(name, idx, key, val, value))
                idx += 1
        elif isinstance(value, list):
            # (we have gotten a non-valid key/value pair list that was created
            # in value_from_datadict())
            idx = 0
            for entry in value:
                _entries.append(self._get_dict_entry(name, idx, entry[0],
                                                     entry[1], value))
                idx += 1
        elif not self.blank:
            # (we probably have gotten the value None, i.e., the dictionary is
            # only being created; an empty first entry is only shown if the
            # dictionary must not be blank)
            _entries.append(self._get_dict_entry(name, 0, None, None))
        # render final HTML for this widget instance
        return mark_safe(render_to_string(self._template, _context))

    def _get_dict_entry(self, field_name, idx, key, value, values_list=None):
        """
        Returns a tuple (pair) with a rendered key and value input field.
        
        `field_name` and `id` will be used in the names of the input fields.
        """
        _key_field_name = DictWidget._key_field_name_tpl.format(field_name, idx)
        if self.key_widget:
            if isinstance(self.key_widget, type):
                self.key_widget = self.key_widget()
            rendered_key = self.key_widget.render(_key_field_name , key)
        else:
            if self.max_key_length:
                if self.max_key_length > _MAX_TEXT_INPUT_SIZE:
                    rendered_key = Textarea().render(_key_field_name, key)
                else:
                    rendered_key = \
                        TextInput(attrs={ 'maxlength': self.max_key_length }) \
                            .render(_key_field_name, key)
            else:
                rendered_key = TextInput().render(_key_field_name, key)

        _val_field_name = DictWidget._val_field_name_tpl.format(field_name, idx)
        if self.max_val_length:
            if self.max_val_length > _MAX_TEXT_INPUT_SIZE:
                rendered_val = Textarea().render(_val_field_name, value)
            else:
                rendered_val = \
                    TextInput(attrs={ 'maxlength': self.max_val_length }) \
                        .render(_val_field_name, value)
        else:
            rendered_val = TextInput().render(_val_field_name, value)

        return (rendered_key, rendered_val)

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data from the input form and this widget's name,
        returns the value of this widget as a list of key/value pairs (or None
        if the list would be empty).
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
        if len(provided) != 0:
            return provided
        return None


class LangDictWidget(DictWidget):
    """
    A `DictWidget` which has RFC 3066 language codes as keys.
    """
    def __init__(self, *args, **kwargs):
        self.key_widget = LangAutoCompleteWidget
        super(LangDictWidget, self).__init__(*args, **kwargs)
        # path to the Django template which is used to render this widget
        self._template = 'repository/editor/lang_dict_widget.html'

    def _get_dict_entry(self, field_name, idx, key, value, values_list=None):
        # Set the default value only if the values_list is empty.
        # This should occur if the key,value does not come from
        # the database nor from user input.
        if not values_list and not key and not value:
            # by default we (blindly) propose the ISO 639-1 language code for
            # English (as per WP7 request in issue #206)
            key = 'en'
        return super(LangDictWidget, self)._get_dict_entry(field_name, idx, key,
                                                           value)

    def _media(self):
        """
        Returns a `Media` object for this widget which is dynamically created
        from the JavaScript of `DictWidget` and CSS specific to this widget.
        """
        # pylint: disable-msg=E1101
        return Media(js = ('js/jquery-ui.min.js',
                           '{}js/pycountry.js'\
                           .format(settings.ADMIN_MEDIA_PREFIX),
                           '{}js/autocomp.js'\
                           .format(settings.ADMIN_MEDIA_PREFIX),
                           '{}js/lang_dict_widget.js'\
                           .format(settings.ADMIN_MEDIA_PREFIX),)) \
            + Media(css={'all': ('{}css/lang_dict_widget.css'.format(
                                        settings.ADMIN_MEDIA_PREFIX),)})
    media = property(_media)


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
            # on Windows browsers onclick is triggered as soon as the
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
    
    def __init__(self, widget_id, max_length=None, **kwargs):
        """
        Initialises a new MultiFieldWidget instance.
        
        This saves the given, required widget_id, clears the errors dictionary
        and then calls the super class constructor with any remaining args.
        Any max_length argument is used to determine the appropriate size for
        the input fields.
        """
        self.widget_id = widget_id
        self.max_length = max_length
        self.errors = {}
        super(MultiFieldWidget, self).__init__(**kwargs)

    def _render_input_widget(self, name, value, attrs):
        """
        Renders and returns the most suitable widget for inputting a single
        field in this `MultiFieldWidget`.
        """
        if self.max_length:
            if self.max_length > _MAX_TEXT_INPUT_SIZE:
                result = Textarea().render(name, value, attrs)
            else:
                result = TextInput(attrs={ 'maxlength': self.max_length }) \
                            .render(name, value, attrs)
        else:
            result = TextInput().render(name, value, attrs)
        return result

    def _render_container(self, _context):
        return render_to_string('repository/container.html', _context)
    
    def _render_multifield(self, _context):
        return render_to_string('repository/multi_field_widget.html', _context)
    
    
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

        # We collect all rendered widgets inside _field_widgets.
        _field_widgets = []
        _field_attrs = {'id': 'id_{0}'.format(name), 'class': 'input',
          'style': self.attrs.get('style', 'width:250px;')}
        
        # Iterate over all sub values for this MultiFieldWidget instance,
        # adding an index number 0..n-1 to support container id generation.
        for _id, _value in enumerate(value):
            # Render input_widget instance as HTML.
            _field_widget = self._render_input_widget(name, _value,
                                                      _field_attrs)
            
            # Define context for container template rendering.
            _context = {'id': _id, 'field_widget': _field_widget,
              'widget_id': self.widget_id,
              'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
              'field_name': name}
            
            # If there have been any validation errors, add the message.
            if _value in self.errors.keys():
                _context.update({'error_msg': self.errors[_value]})
            
            # Render container for this sub value's widget and append to list.
            _container = self._render_container(_context)
            _field_widgets.append(_container)
        
        # If list of values is empty, render an empty container instead.
        _id = len(value)
        if not _id:
            # Note that value='' as values is empty.
            _field_widget = self._render_input_widget(name, '', _field_attrs)
            _context = {'id': _id, 'field_widget': _field_widget,
              'widget_id': self.widget_id,
              'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
              'field_name': name}
            
            _container = self._render_container(_context)
            _field_widgets.append(_container)
        
            _field_widget = self._render_input_widget(name, '', _field_attrs)
            _context = {'id': _id, 'field_widget': _field_widget,
              'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX}
        
        # The JavaScript code needs an empty "template" to create new input
        # widgets dynamically; this is pre-rendered and added to the template
        # for the MultiFieldWidget instance here.
        _empty_widget = self._render_input_widget(name, '', _field_attrs)
        _context = {'empty_widget': _empty_widget,
          'field_widgets': mark_safe(u'\n'.join(_field_widgets)),
          'widget_id': self.widget_id,
          'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
          'field_name': name}
        
        # Render final HTML for this MultiFieldWidget instance.
        _html = self._render_multifield(_context)
        return mark_safe(_html)
    
    def value_from_datadict(self, data, files, name):
        """
        Encodes the data for this MultiFieldWidget instance as base64 String.
        """
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

class MultiChoiceWidget(widgets.Widget):
    """
    A MultiChoiceWidget allows to enter lists of data using a certain widget.

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

    def __init__(self, widget_id, max_length=None, choices = (), **kwargs):
        """
        Initialises a new MultiFieldWidget instance.

        This saves the given, required widget_id, clears the errors dictionary
        and then calls the super class constructor with any remaining args.
        Any max_length argument is used to determine the appropriate size for
        the input fields.
        """
        self.choices = [('','--------')]
        self.choices.extend(choices)
        self.widget_id = widget_id
        self.max_length = max_length
        self.errors = {}
        super(MultiChoiceWidget, self).__init__(**kwargs)

    def _render_input_widget(self, name, value, attrs):
        """
        Renders and returns the most suitable widget for inputting a single
        field in this `MultiFieldWidget`.
        """
        # if self.max_length:
        #     if self.max_length > _MAX_TEXT_INPUT_SIZE:
        #         result = Select(choices=self.choices).render(name, value, attrs)
        #     else:
        #         result = Select(choices=self.choices) \
        #             .render(name, value, attrs)
        # else:
        #     result = Select(choices=self.choices) \
        #             .render(name, value, attrs)
        return Select(choices=self.choices).render(name, value, attrs)

    def _render_container(self, _context):
        return render_to_string('repository/container.html', _context)

    def _render_multifield(self, _context):
        return render_to_string('repository/multi_field_widget.html', _context)


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

        # We collect all rendered widgets inside _field_widgets.
        _field_widgets = []
        _field_attrs = {'id': 'id_{0}'.format(name), 'class': 'input',
                        'style': self.attrs.get('style', 'width:480px')
                        }

        # Iterate over all sub values for this MultiFieldWidget instance,
        # adding an index number 0..n-1 to support container id generation.
        for _id, _value in enumerate(value):
            # Render input_widget instance as HTML.
            _field_widget = self._render_input_widget(name, _value,
                                                      _field_attrs)

            # Define context for container template rendering.
            _context = {'id': _id, 'field_widget': _field_widget,
                        'widget_id': self.widget_id,
                        'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
                        'field_name': name}

            # If there have been any validation errors, add the message.
            if _value in self.errors.keys():
                _context.update({'error_msg': self.errors[_value]})

            # Render container for this sub value's widget and append to list.
            _container = self._render_container(_context)
            _field_widgets.append(_container)

        # If list of values is empty, render an empty container instead.
        _id = len(value)
        if not _id:
            # Note that value='' as values is empty.
            _field_widget = self._render_input_widget(name, '', _field_attrs)
            _context = {'id': _id, 'field_widget': _field_widget,
                        'widget_id': self.widget_id,
                        'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
                        'field_name': name}

            _container = self._render_container(_context)
            _field_widgets.append(_container)

            _field_widget = self._render_input_widget(name, '', _field_attrs)
            _context = {'id': _id, 'field_widget': _field_widget,
                        'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX}

        # The JavaScript code needs an empty "template" to create new input
        # widgets dynamically; this is pre-rendered and added to the template
        # for the MultiFieldWidget instance here.
        _empty_widget = self._render_input_widget(name, '', _field_attrs)
        _context = {'empty_widget': _empty_widget,
                    'field_widgets': mark_safe(u'\n'.join(_field_widgets)),
                    'widget_id': self.widget_id,
                    'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
                    'field_name': name}

        # Render final HTML for this MultiFieldWidget instance.
        _html = self._render_multifield(_context)
        return mark_safe(_html)

    def value_from_datadict(self, data, files, name):
        """
        Encodes the data for this MultiFieldWidget instance as base64 String.
        """
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

            # _data = []
            pass

        return initial != _data

class TestHiddenWidget(TextInput, SelectableMediaMixin):
    def __init__(self, lookup_class, *args, **kwargs):
        self.lookup_class = lookup_class
        self.allow_new = kwargs.pop('allow_new', False)
        self.qset = kwargs.pop('query_params', {})
        self.limit = kwargs.pop('limit', None)
        super(TestHiddenWidget, self).__init__(*args, **kwargs)

    def update_query_parameters(self, qs_dict):
        self.qset.update(qs_dict)

    def build_attrs(self, extra_attrs=None, **kwargs):
        attrs = super(TestHiddenWidget, self).build_attrs(extra_attrs, **kwargs)
        url = self.lookup_class.url()
        if self.limit and 'limit' not in self.qset:
            self.qset['limit'] = self.limit
        if self.qset:
            url = '%s?%s' % (url, urlencode(self.qset))
        attrs[u'data-selectable-url'] = url
        attrs[u'data-selectable-type'] = 'text'
        attrs[u'data-selectable-allow-new'] = str(self.allow_new).lower()
        attrs[u'type'] = 'hidden'
        return attrs

    def render(self, name, value, attrs=None):
        return mark_safe(super(TestHiddenWidget, self).render(name, value, attrs))

class OneToManyWidget(SelectableMultiWidget, SelectableMediaMixin):

    def __init__(self, lookup_class, *args, **kwargs):
        self.lookup_class = lookup_class
        self.limit = kwargs.pop('limit', None)
        position = kwargs.pop('position', 'bottom')
        attrs = {
            u'data-selectable-multiple': 'true',
            u'data-selectable-position': position,
            u'data-selectable-allow-editing': 'true'
        }
        query_params = kwargs.pop('query_params', {})
        widget_list = [
            TestHiddenWidget(
                lookup_class, allow_new=False,
                limit=self.limit, query_params=query_params, attrs=attrs
            ),
            LookupMultipleHiddenInput(lookup_class)
        ]
        super(OneToManyWidget, self).__init__(widget_list, *args, **kwargs)

    def value_from_datadict(self, data, files, name):
        return self.widgets[1].value_from_datadict(data, files, name + '_1')

    def render(self, name, value, attrs=None):
        if value and not hasattr(value, '__iter__'):
            value = [value]
        value = [u'', value]
        return super(OneToManyWidget, self).render(name, value, attrs)
    
    def decompress(self, value):
        pass

class ComboWidget(AdminTextInputWidget):
    class Media:
        """
        Media sub class to inject custom CSS and JavaScript code.
        """
        css = {
          'all': ('{}css/themes/smoothness/jquery-ui.css'
                    .format(settings.ADMIN_MEDIA_PREFIX),
                  '{}css/combo.css'.format(settings.ADMIN_MEDIA_PREFIX))
        }
        js = ('js/jquery-ui.min.js',
              '{}js/pycountry.js'.format(settings.ADMIN_MEDIA_PREFIX),
              '{}js/autocomp.js'.format(settings.ADMIN_MEDIA_PREFIX),)

    def __init__(self, field_type=None, attrs=None):
        self.field_type = field_type
        self.id_field = attrs.pop('id_field')
        self.name_field = attrs.pop('name_field')
        if not attrs:
            attrs = {}
        super(ComboWidget, self).__init__(attrs)
        
    def render(self, name, value, attrs=None):
        val = super(ComboWidget, self).render(name, value, attrs)
        if 'id' in attrs:
            id1 = attrs['id']
            if self.field_type == 'id':
                linked_to = attrs['id'].replace(self.id_field, self.name_field)
                js_script = u'<script>autocomp_single("id", "{0}", "{1}");</script>'.format(id1, linked_to)
            elif self.field_type == 'name':
                linked_to = attrs['id'].replace(self.name_field, self.id_field)
                js_script = u'<script>autocomp_single("name", "{0}", "{1}");</script>'.format(id1, linked_to)
            val = val + js_script

        return mark_safe(val)

class MultiComboWidget(MultiFieldWidget):
    class Media:
        """
        Media sub class to inject custom CSS and JavaScript code.
        """
        css = {
          'all': ('{}css/themes/smoothness/jquery-ui.css'
                    .format(settings.ADMIN_MEDIA_PREFIX),
                  '{}css/combo.css'.format(settings.ADMIN_MEDIA_PREFIX))
        }
        js = ('js/jquery-ui.min.js',
              '{}js/pycountry.js'.format(settings.ADMIN_MEDIA_PREFIX),
              '{}js/autocomp.js'.format(settings.ADMIN_MEDIA_PREFIX),)

    def __init__(self, field_type=None, attrs=None, widget_id=None, max_length=None, **kwargs):
        self.field_type = field_type
        self.id_field = attrs.pop('id_field')
        self.name_field = attrs.pop('name_field')
        super(MultiComboWidget, self).__init__(widget_id, max_length, **kwargs)
        
    def _render_container(self, _context):
        if self.field_type == 'name':
            _context.update({'autocomp_name': True})
            linked_field_name = _context['field_name']
            linked_field_name = linked_field_name.replace(self.name_field, self.id_field)
            _context.update({'linked_field_name': linked_field_name})
        elif self.field_type == 'id':
            _context.update({'autocomp_id': True})
            linked_field_name = _context['field_name']
            linked_field_name = linked_field_name.replace(self.id_field, self.name_field)
            _context.update({'linked_field_name': linked_field_name})
        val = super(MultiComboWidget, self)._render_container(_context)
        return val
    
    def _render_multifield(self, _context):
        if self.field_type == 'name':
            _context.update({'autocomp_name': True})
            linked_field_name = _context['field_name']
            linked_field_name = linked_field_name.replace(self.name_field, self.id_field)
            _context.update({'linked_field_name': linked_field_name})
        elif self.field_type == 'id':
            _context.update({'autocomp_id': True})
            linked_field_name = _context['field_name']
            linked_field_name = linked_field_name.replace(self.id_field, self.name_field)
            _context.update({'linked_field_name': linked_field_name})
        val = super(MultiComboWidget, self)._render_multifield(_context)
        return val

class LangAutoCompleteWidget(widgets.Widget):
    class Media:
        js = ('js/jquery-ui.min.js',
              '{}js/pycountry.js'.format(settings.ADMIN_MEDIA_PREFIX),
              '{}js/autocomp.js'.format(settings.ADMIN_MEDIA_PREFIX),)
        css = {}
        
    def __init__(self, attrs=None):
        super(LangAutoCompleteWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if not value:
            value = u''
        res1 = u'<input type="text" class="lang_autocomplete" name="{0}" value="{1}"/>'.format(name, value)
        res2 = u'</br><span class="lang_name" for="{0}"/>'.format(name)
        res = res1 + res2
        res = mark_safe(res)
        return res

class AutoCompleteSelectMultipleEditWidget(SelectableMultiWidget, SelectableMediaMixin):

    def __init__(self, lookup_class, *args, **kwargs):
        self.lookup_class = lookup_class
        default_lookup_widget = LookupMultipleHiddenInput
        self.lookup_widget = kwargs.pop('lookup_widget', None)
        if not self.lookup_widget:
            self.lookup_widget = default_lookup_widget
        self.limit = kwargs.pop('limit', None)
        position = kwargs.pop('position', 'bottom')
        more_attrs = kwargs.pop('attrs', None)
        
        proto_url = '/{}editor/repository/'.format(settings.DJANGO_BASE)
        attrs = {
            u'data-selectable-multiple': 'true',
            u'data-selectable-position': position,
            u'data-selectable-allow-editing': 'true',
            u'data-selectable-base-url': proto_url,
            u'data-selectable-throbber-img': '{0}img/admin/throbber_16.gif'.format(settings.ADMIN_MEDIA_PREFIX),
            u'data-selectable-use-state-error': 'false',
        }
        if more_attrs:
            attrs.update(more_attrs)
        query_params = kwargs.pop('query_params', {})
        widget_list = [
            AutoCompleteWidget(
                lookup_class, allow_new=False,
                limit=self.limit, query_params=query_params, attrs=attrs
            ),
            self.lookup_widget(lookup_class)
        ]
        super(AutoCompleteSelectMultipleEditWidget, self).__init__(widget_list, *args, **kwargs)

    def value_from_datadict(self, data, files, name):
        return self.widgets[1].value_from_datadict(data, files, name + '_1')

    def render(self, name, value, attrs=None):
        if value and not hasattr(value, '__iter__'):
            value = [value]
        value = [u'', value]
        html_code = super(AutoCompleteSelectMultipleEditWidget, self).render(name, value, attrs)
        return html_code

    def decompress(self, value):
        pass
    
    # Copied from django.contrib.admin.widgets.ManyToManyRawIdWidget class
    def _has_changed(self, initial, data):
        if initial is None:
            initial = []
        if data is None:
            data = []
        if len(initial) != len(data):
            return True
        for pk1, pk2 in zip(initial, data):
            if force_unicode(pk1) != force_unicode(pk2):
                return True
        return False

class AutoCompleteSelectMultipleSubClsWidget(AutoCompleteSelectMultipleEditWidget):

    def __init__(self, lookup_class, *args, **kwargs):
        new_attrs = {u'data-selectable-is-subclassable': 'true',}
        kwargs.update({'attrs': new_attrs})
        kwargs.update({'lookup_widget': LookupMultipleHiddenInputMS})
        super(AutoCompleteSelectMultipleSubClsWidget, self).__init__(lookup_class, *args, **kwargs)


class LookupMultipleHiddenInputMS(LookupMultipleHiddenInput):
    def render(self, name, value, attrs=None, choices=()):
        lookup = self.lookup_class()
        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        id_ = final_attrs.get('id', None)
        inputs = []
        model = getattr(self.lookup_class, 'model', None)
        for index, val in enumerate(value):
            item = None
            if model and isinstance(val, model):
                item = val
                val = lookup.get_item_id(item)
            input_attrs = dict(value=force_unicode(val), **final_attrs)
            if id_:
                # An ID attribute was given. Add a numeric index as a suffix
                # so that the inputs don't all have the same ID attribute.
                input_attrs['id'] = '%s_%s' % (id_, index)
            if val:
                item = item or lookup.get_item(val)
                item_cls = item.as_subclass().__class__.__name__.lower()
                input_attrs['title'] = lookup.get_item_value(item)
                input_attrs['model-class'] = item_cls
            inputs.append(u'<input%s />' % flatatt(input_attrs))
        return mark_safe(u'\n'.join(inputs))

class AutoCompleteSelectSingleWidget(AutoCompleteSelectWidget):

    def __init__(self, lookup_class, *args, **kwargs):
        self.lookup_class = lookup_class
        self.allow_new = kwargs.pop('allow_new', False)
        self.limit = kwargs.pop('limit', None)
        query_params = kwargs.pop('query_params', {})
        attrs = {
            u'data-selectable-throbber-img': '{0}img/admin/throbber_16.gif'.format(settings.ADMIN_MEDIA_PREFIX),
            u'data-selectable-use-state-error': 'false',
        }
        widget_list = [
            AutoCompleteWidget(
                lookup_class, allow_new=self.allow_new,
                limit=self.limit, query_params=query_params, attrs=attrs
            ),
            forms.HiddenInput(attrs={u'data-selectable-type': 'hidden'})
        ]
        # Directly call the super-super-class __init__ method.
        # The super-class __init__ method does not allow custom attributes
        # to be passed to the AutoCompleteWidget. For this reason this
        # __init__ method is a modified version of the super-class one
        # and replaces it.
        # pylint: disable-msg=E1003
        super(AutoCompleteSelectWidget, self).__init__(widget_list, *args, **kwargs)
    