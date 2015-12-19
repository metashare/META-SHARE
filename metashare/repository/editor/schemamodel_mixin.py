'''
The mixin code for ModelAdmin to link to the SchemaModel objects in models.py.
'''
from metashare.utils import verify_subclass, get_class_by_name
from metashare.repository.supermodel import SchemaModel
from metashare.repository.editor.editorutils import encode_as_inline
from django.db.models.fields import FieldDoesNotExist
from metashare.repository.editor.widgets import ComboWidget, MultiComboWidget
from metashare.repository.models import inputInfoType_model, \
    outputInfoType_model, languageInfoType_model, metadataInfoType_model, \
    documentInfoType_model, annotationInfoType_model

# Fields that need the ComboWidget/MultiComboWidget with autocomplete functionality
# to use with languageId,languageName pairs.
LANGUAGE_ID_NAME_FIELDS = {
   # inputInfoType_model:
   #     {'type': 'multiple', 'id': "languageId", 'name': "languageName"},
   # outputInfoType_model:
   #     {'type': 'multiple', 'id': "languageId", 'name': "languageName"},
   # languageInfoType_model:
   #     {'type': 'single', 'id': "languageId", 'name': "languageName"},
   # metadataInfoType_model:
   #     {'type': 'multiple', 'id': "metadataLanguageId", 'name': "metadataLanguageName"},
   # documentInfoType_model:
   #     {'type': 'single', 'id': "documentLanguageId", 'name': "documentLanguageName"},
   # annotationInfoType_model:
   #     {'type': 'single', 'id': "tagsetLanguageId", 'name': "tagsetLanguageName"},
}


class SchemaModelLookup(object):
    show_tabbed_fieldsets = False
    
    def is_field(self, name):
        return not self.is_inline(name)
    
    def is_inline(self, name):
        return name.endswith('_set')


    def is_required_field(self, name):
        """
        Checks whether the field with the given name is a required field.
        """
        # pylint: disable-msg=E1101
        _fields = self.model.get_fields()
        return name in _fields['required']


    def is_visible_as_normal_field(self, field_name, exclusion_list):
        return self.is_field(field_name) and field_name not in exclusion_list
    
    def is_visible_as_inline(self, field_name, include_inlines, inlines):
        return include_inlines and (field_name in inlines or self.is_inline(field_name))

    def get_excluded_fields(self):
        # pylint: disable-msg=E1101
        if hasattr(self, 'exclude') and self.exclude is not None:
            return tuple(self.exclude)
        return ()
    
    def get_hidden_fields(self):
        # pylint: disable-msg=E1101
        if hasattr(self, 'hidden_fields') and self.hidden_fields is not None:
            return tuple(self.hidden_fields)
        return ()
    
    def get_non_editable_fields(self):
        # pylint: disable-msg=E1101
        _readonly = ()
        if hasattr(self, 'readonly_fields') and self.readonly_fields is not None:
            _readonly += tuple(self.readonly_fields)
        _fields = self.model.get_fields_flat()
        for _field_name in _fields:
            try:
                if not self.model._meta.get_field(_field_name).editable:
                    _readonly += (_field_name, )
            except FieldDoesNotExist:
                pass
        return _readonly

    def build_fieldsets_from_schema_plain(self, include_inlines=False, inlines=()):
        """
        Builds fieldsets using SchemaModel.get_fields().
        """
        # pylint: disable-msg=E1101
        verify_subclass(self.model, SchemaModel)

        exclusion_list = set(self.get_excluded_fields() + self.get_hidden_fields() + self.get_non_editable_fields())

        # pylint: disable-msg=E1101
        _fields = self.model.get_fields_flat()
        _visible_fields = []
        
        for _field_name in _fields:
            if self.is_visible_as_normal_field(_field_name, exclusion_list):
                _visible_fields.append(_field_name)
            elif self.is_visible_as_inline(_field_name, include_inlines, inlines):
                _visible_fields.append(encode_as_inline(_field_name))

        _fieldsets = ((None,
            {'fields': _visible_fields + list(self.get_hidden_fields())}
        ),)
        return _fieldsets



    def build_fieldsets_from_schema_tabbed(self, include_inlines=False, inlines=()):
        """
        Builds fieldsets using SchemaModel.get_fields(),
        for tabbed viewing (required/recommended/optional).
        """
        # pylint: disable-msg=E1101
        verify_subclass(self.model, SchemaModel)

        exclusion_list = set(self.get_excluded_fields() + self.get_hidden_fields() + self.get_non_editable_fields())
        
        _fieldsets = []
        # pylint: disable-msg=E1101
        _fields = self.model.get_fields()

        for _field_status in ('required', 'recommended', 'optional'):
            _visible_fields = []
            _visible_fields_verbose_names = []

            for _field_name in _fields[_field_status]:
                if self.is_visible_as_normal_field(_field_name, exclusion_list):
                    _visible_fields.append(_field_name)
                    is_visible = True
                elif self.is_visible_as_inline(_field_name, include_inlines, inlines):
                    _visible_fields.append(encode_as_inline(_field_name))
                    is_visible = True
                else:
                    is_visible = False
                
                if is_visible:
                    _visible_fields_verbose_names.append(self.model.get_verbose_name(_field_name))
            
            if len(_visible_fields) > 0:
                _detail = ', '.join(_visible_fields_verbose_names)
                _caption = '{0} information: {1}'.format(_field_status.capitalize(), _detail)
                _fieldset = {'fields': _visible_fields}
                _fieldsets.append((_caption, _fieldset))

        _hidden_fields = self.get_hidden_fields()
        if _hidden_fields:
            _fieldsets.append((None, {'fields': _hidden_fields, 'classes':('display_none', )}))

        return _fieldsets

    def build_fieldsets_from_schema(self, include_inlines=False, inlines=()):
        if self.show_tabbed_fieldsets:
            return self.build_fieldsets_from_schema_tabbed(include_inlines, inlines)
        return self.build_fieldsets_from_schema_plain(include_inlines, inlines)

    def get_fieldsets(self, request, obj=None):
        return self.build_fieldsets_from_schema()


    def get_fieldsets_with_inlines(self, request, obj=None):
        # pylint: disable-msg=E1101
        inline_names = [inline.parent_fk_name for inline in self.inline_instances if hasattr(inline, 'parent_fk_name')]
        return self.build_fieldsets_from_schema(include_inlines=True, inlines=inline_names)


    def get_inline_classes(self, model, status):
        '''
        For the inlines listed in the given SchemaModel's __schema_fields__,
        provide the list of matching inline classes.
        '''
        result = []
        parent_model_class_name = model._meta.object_name
        for rec_path, rec_accessor, rec_status in model.__schema_fields__:
            if status == rec_status and self.is_inline(rec_accessor):
                if '/' in rec_path:
                    slashpos = rec_path.rfind('/')
                    rec_name = rec_path[(slashpos+1):]
                else:
                    rec_name = rec_path
                # pylint: disable-msg=E1101
                if hasattr(self, 'custom_one2many_inlines') and rec_name in self.custom_one2many_inlines:
                    inline_class = self.custom_one2many_inlines[rec_name]
                else:
                    one_model_class_name = model.__schema_classes__[rec_name]
                    inline_class = self.get_inline_class_from_model_class_name(one_model_class_name, parent_model_class_name)
                result.append(inline_class)
        return result


    def get_inline_class_from_model_class_name(self, model_class_name, parent_model_class_name=None):
        '''
        For a model class object such as identificationInfoType_model,
        return the class object extending SchemaModelInline which
        can be used to render this model inline in the admin interface.
        Raises an AttributeError if no suitable class can be found.
        
        This expects the following naming convention:
        - Take the model class name and remove the suffix 'Type_model';
        - append '_model_inline'.
        '''
        suffix_length = len("Type_model")
        if model_class_name == 'documentUnstructuredString_model':
            modelname_without_suffix = model_class_name[:-len("_model")]
        else:
            modelname_without_suffix = model_class_name[:-suffix_length]
        inline_class_name = modelname_without_suffix + "_model_inline"
        if parent_model_class_name:
            context_specific_name = inline_class_name + "_" + parent_model_class_name
            try:
                return get_class_by_name('metashare.repository.admin', context_specific_name)
            except AttributeError:
                pass
        return get_class_by_name('metashare.repository.admin', inline_class_name)
    
    def add_lang_widget(self, db_field):
        # pylint: disable-msg=E1101
        model_cls = self.model().__class__
        widget_dict = {}
        if model_cls in LANGUAGE_ID_NAME_FIELDS:
            item = LANGUAGE_ID_NAME_FIELDS[model_cls]
            if item['type'] == 'single':
                attrs = {}
                attrs['id_field'] = item['id']
                attrs['name_field'] = item['name']
                if db_field.name == item['id']:
                    widget_dict.update({'widget': ComboWidget(field_type='id', attrs=attrs)})
                elif db_field.name == item['name']:
                    widget_dict.update({'widget': ComboWidget(field_type='name', attrs=attrs)})
            elif item['type'] == 'multiple':
                attrs = {}
                attrs['id_field'] = item['id']
                attrs['name_field'] = item['name']
                if db_field.name == item['name']:
                    prev_widget = db_field.widget
                    widget_id = prev_widget.widget_id
                    max_length = prev_widget.max_length
                    widget_dict.update({'widget': MultiComboWidget(field_type='name', attrs=attrs, widget_id=widget_id, max_length=max_length)})
                elif db_field.name == item['id']:
                    prev_widget = db_field.widget
                    widget_id = prev_widget.widget_id
                    max_length = prev_widget.max_length
                    widget_dict.update({'widget': MultiComboWidget(field_type='id', attrs=attrs, widget_id=widget_id, max_length=max_length)})

        return widget_dict
    
    def add_lang_templ_params(self, inline_admin_formset):
        model_cls = inline_admin_formset.formset.form.Meta.model().__class__
        if model_cls in LANGUAGE_ID_NAME_FIELDS:
            item = LANGUAGE_ID_NAME_FIELDS[model_cls]
            inline_admin_formset.has_lang = True
            inline_admin_formset.lang_id = item['id']
            inline_admin_formset.lang_name = item['name']
