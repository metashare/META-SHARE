'''
The mixin code for ModelAdmin to link to the SchemaModel objects in models.py.
'''
from metashare.utils import verify_subclass, get_class_by_name
from metashare.repository.supermodel import SchemaModel
from metashare.repository.editor.editorutils import encode_as_inline



class SchemaModelLookup(object):
    show_tabbed_fieldsets = False
    
    def is_field(self, name):
        return not name.endswith('_set')
    
    def is_inline(self, name):
        return not self.is_field(name)


    def is_required_field(self, name):
        """
        Checks whether the field with the given name is a required field.
        """
        # pylint: disable-msg=E1101
        _fields = self.model.get_fields()
        return name in _fields['required']


    def build_fieldsets_from_schema_plain(self, include_inlines=False):
        """
        Builds fieldsets using SchemaModel.get_fields().
        """
        # pylint: disable-msg=E1101
        verify_subclass(self.model, SchemaModel)

        exclusion_list = ()
        if hasattr(self, 'exclude') and self.exclude is not None:
            exclusion_list += tuple(self.exclude)

        _hidden_fields = getattr(self, 'hidden_fields', None)
        _hidden_fields = _hidden_fields or []
        # hidden fields are also excluded
        for _hidden_field in _hidden_fields:
            if _hidden_field not in exclusion_list:
                exclusion_list += _hidden_field

        _readonly_fields = getattr(self, 'readonly_fields', None)
        # readonly fields are also excluded
        if _readonly_fields:
            for _readonly_field in _readonly_fields:
                if _readonly_field not in exclusion_list:
                    exclusion_list += (_readonly_field, )

        # pylint: disable-msg=E1101
        _fields = self.model.get_fields_flat()
        _visible_fields = []
        
        for _field_name in _fields:
            # Two possible reasons why a field might be encoded as an inline:
            # - either it's a OneToOneField and we have put 
            #   it into tht eexclusion list;
            # - or it's a reverse foreigh key, so it is not a field.
            # In both cases, we only include it in visible fields if
            # include_inlines is requested.
            _is_visible = False
            if self.is_field(_field_name) and _field_name not in exclusion_list:
                _is_visible = True
                _fieldname_to_append = _field_name
            elif include_inlines:
                _is_visible = True
                _fieldname_to_append = encode_as_inline(_field_name)
            if _is_visible:
                _visible_fields.append(_fieldname_to_append)

        _fieldsets = ((None,
            {'fields': _visible_fields + list(_hidden_fields)}
        ),)
        return _fieldsets

    def build_fieldsets_from_schema_tabbed(self, include_inlines):
        """
        Builds fieldsets using SchemaModel.get_fields(),
        for tabbed viewing (required/recommended/optional).
        """
        # pylint: disable-msg=E1101
        verify_subclass(self.model, SchemaModel)

        exclusion_list = ()
        if hasattr(self, 'exclude') and self.exclude is not None:
            exclusion_list += tuple(self.exclude)

        _hidden_fields = getattr(self, 'hidden_fields', None)
        # hidden fields are also excluded
        if _hidden_fields:
            for _hidden_field in _hidden_fields:
                if _hidden_field not in exclusion_list:
                    exclusion_list += (_hidden_field, )

        _readonly_fields = getattr(self, 'readonly_fields', None)
        # readonly fields are also excluded
        if _readonly_fields:
            for _readonly_field in _readonly_fields:
                if _readonly_field not in exclusion_list:
                    exclusion_list += (_readonly_field, )


        
        _fieldsets = []
        # pylint: disable-msg=E1101
        _fields = self.model.get_fields()

        for _field_status in ('required', 'recommended', 'optional'):
            _visible_fields = []
            _visible_fields_verbose_names = []

            for _field_name in _fields[_field_status]:
                # Two possible reasons why a field might be encoded as an inline:
                # - either it's a OneToOneField and we have put 
                #   it into tht eexclusion list;
                # - or it's a reverse foreigh key, so it is not a field.
                # In both cases, we only include it in visible fields if
                # include_inlines is requested.
                _is_visible = False
                if self.is_field(_field_name) and _field_name not in exclusion_list:
                    _is_visible = True
                    _fieldname_to_append = _field_name
                elif include_inlines:
                    _is_visible = True
                    _fieldname_to_append = encode_as_inline(_field_name)

                _relevant_fields = _visible_fields
                _verbose_names = _visible_fields_verbose_names

                # And now put the field where it belongs:
                if _is_visible:
                    _relevant_fields.append(_fieldname_to_append)
                    _verbose_names.append(self.model.get_verbose_name(_field_name))
            
            
            if len(_visible_fields) > 0:
                _detail = ', '.join(_visible_fields_verbose_names)
                _caption = '{0} information: {1}'.format(_field_status.capitalize(), _detail)
                _fieldset = {'fields': _visible_fields}
                _fieldsets.append((_caption, _fieldset))

        if _hidden_fields:
            _fieldsets.append((None, {'fields': _hidden_fields, 'classes':('display_none', )}))

        return _fieldsets

    def build_fieldsets_from_schema(self, include_inlines=False):
        if self.show_tabbed_fieldsets:
            return self.build_fieldsets_from_schema_tabbed(include_inlines)
        return self.build_fieldsets_from_schema_plain(include_inlines)

    def get_fieldsets(self, request, obj=None):
        return self.build_fieldsets_from_schema(include_inlines=False)


    def get_fieldsets_with_inlines(self, request, obj=None):
        return self.build_fieldsets_from_schema(include_inlines=True)


    def get_inline_classes(self, model, status):
        '''
        For the inlines listed in the given SchemaModel's __schema_fields__,
        provide the list of matching inline classes.
        '''
        result = []
        for rec_path, rec_accessor, rec_status in model.__schema_fields__:
            if status == rec_status and self.is_inline(rec_accessor):
                if '/' in rec_path:
                    slashpos = rec_path.rfind('/')
                    rec_name = rec_path[(slashpos+1):]
                else:
                    rec_name = rec_path
                one_model_class_name = model.__schema_classes__[rec_name]
                result.append(self.get_inline_class_from_model_class_name(one_model_class_name))
        return result


    def get_inline_class_from_model_class_name(self, model_class_name):
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
        modelname_without_suffix = model_class_name[:-suffix_length]
        inline_class_name = modelname_without_suffix + "_model_inline"
        return get_class_by_name('metashare.repository.admin', inline_class_name)

