'''
The Inline classes used in the editor.
'''

from django.forms import ModelForm
from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.functional import curry
from django.contrib.admin.util import flatten_fieldsets
from django.contrib import admin
from django.utils.encoding import force_unicode
from metashare.repository.editor.related_mixin import RelatedAdminMixin
from metashare.repository.editor.schemamodel_mixin import SchemaModelLookup



class SchemaModelInline(admin.StackedInline, RelatedAdminMixin, SchemaModelLookup):
    extra = 1
    collapse = False

    def __init__(self, parent_model, admin_site):
        super(SchemaModelInline, self).__init__(parent_model, admin_site)
        if self.collapse:
            self.verbose_name_plural = '_{}'.format(force_unicode(self.verbose_name_plural))
        # Show m2m fields as horizontal filter widget unless they have a custom widget:
        self.filter_horizontal = self.list_m2m_fields_without_custom_widget(self.model)

    def get_fieldsets(self, request, obj=None):
        return SchemaModelLookup.get_fieldsets(self, request, obj)

    def formfield_for_dbfield(self, db_field, **kwargs):
        if self.is_subclassable(db_field):
            return self.formfield_for_subclassable(db_field, **kwargs)
        self.use_hidden_widget_for_one2one(db_field, kwargs)
        formfield = super(SchemaModelInline, self).formfield_for_dbfield(db_field, **kwargs)
        self.use_related_widget_where_appropriate(db_field, kwargs, formfield)
        return formfield

    def response_change(self, request, obj):
        if '_popup' in request.REQUEST:
            return self.edit_response_close_popup_magic(obj)
        else:
            return super(SchemaModelInline, self).response_change(request, obj)




class ReverseInlineFormSet(BaseModelFormSet):
    '''
    A formset with either a single object or a single empty
    form. Since the formset is used to render a required OneToOne
    relation, the forms must not be empty.
    '''
    model = None
    parent_fk_name = ''
    def __init__(self,
                 data = None,
                 files = None,
                 instance = None,
                 prefix = None,
                 save_as_new = False,
                 queryset=None):
        _qs = None
        if instance.pk:
            obj = getattr(instance, self.parent_fk_name)
            if obj:
                _qs = self.model.objects.filter(pk = obj.id)
        if not _qs:
            _qs = self.model.objects.filter(pk = -1)
            self.extra = 1
        super(ReverseInlineFormSet, self).__init__(data, files,
                                                       prefix = prefix,
                                                       queryset = _qs)
        for form in self.forms:
            # if the form set can be deleted, then it is not required and then
            # its forms may be empty
            form.empty_permitted = getattr(self, 'can_delete', False)


def reverse_inlineformset_factory(parent_model,
                                  model,
                                  parent_fk_name,
                                  formset,
                                  form = ModelForm,
                                  fields = None,
                                  exclude = None,
                                  formfield_callback = lambda f: f.formfield()):
    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': formset,
        'extra': 0,
        'can_delete': parent_fk_name not in \
            parent_model.get_fields()['required'],
        'can_order': False,
        'fields': fields,
        'exclude': exclude,
        'max_num': 1,
    }
    form_set = modelformset_factory(model, **kwargs)
    form_set.parent_fk_name = parent_fk_name
    return form_set

class ReverseInlineModelAdmin(SchemaModelInline):
    '''
    Derived from http://djangosnippets.org/snippets/2032/
    
    reverseadmin
    ============
    
    Module that makes django admin handle OneToOneFields in a better way.
    
    A common use case for one-to-one relationships is to "embed" a model
    inside another one. For example, a Person may have multiple foreign
    keys pointing to an Address entity, one home address, one business
    address and so on. Django admin displays those relations using select
    boxes, letting the user choose which address entity to connect to a
    person. A more natural way to handle the relationship is using
    inlines. However, since the foreign key is placed on the owning
    entity, django admins standard inline classes can't be used. Which is
    why I created this module that implements "reverse inlines" for this
    use case.
    
    Example:
    
        from django.db import models
        class Address(models.Model):
            street = models.CharField(max_length = 255)
            zipcode = models.CharField(max_length = 10)
            city = models.CharField(max_length = 255)
        class Person(models.Model):
            name = models.CharField(max_length = 255)
            business_addr = models.OneToOneField(Address,
                                                 related_name = 'business_addr')
            home_addr = models.OneToOneField(Address, related_name = 'home_addr')
    
    This is how standard django admin renders it:
    
        http://img9.imageshack.us/i/beforetz.png/
    
    Here is how it looks when using the reverseadmin module:
    
        http://img408.imageshack.us/i/afterw.png/
    
    You use reverseadmin in the following way:
    
        from django.contrib import admin
        from models import Person
        from reverseadmin import ReverseModelAdmin
        class PersonAdmin(ReverseModelAdmin):
            inline_type = 'tabular'
        admin.site.register(Person, PersonAdmin)
    
    inline_type can be either "tabular" or "stacked" for tabular and
    stacked inlines respectively.
    
    The module is designed to work with Django 1.1.1. Since it hooks into
    the internals of the admin package, it may not work with later Django
    versions.
    '''
    formset = ReverseInlineFormSet
    
    def __init__(self,
                 parent_model,
                 parent_fk_name,
                 model, admin_site,
                 inline_type):
        self.date_hierarchy = None # Salvatore: to avoid an error in validate
        self.template = 'admin/edit_inline_one2one/%s.html' % inline_type
        self.parent_fk_name = parent_fk_name
        self.model = model
        field_descriptor = getattr(parent_model, self.parent_fk_name)
        field = field_descriptor.field

        # Use the name and the help_text of the owning models field to
        # render the verbose_name and verbose_name_plural texts.
        self.verbose_name_plural = field.verbose_name.title()
        self.verbose_name = field.help_text
        if not self.verbose_name:
            self.verbose_name = self.verbose_name_plural
        super(ReverseInlineModelAdmin, self).__init__(parent_model, admin_site)

    def get_formset(self, request, obj = None, **kwargs):
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        exclude.extend(kwargs.get("exclude", []))
        exclude.extend(self.get_readonly_fields(request, obj))
        # if exclude is an empty list we use None, since that's the actual
        # default
        exclude = exclude or None
        defaults = {
            "form": self.form,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return reverse_inlineformset_factory(self.parent_model,
                                             self.model,
                                             self.parent_fk_name,
                                             self.formset,
                                             **defaults)



