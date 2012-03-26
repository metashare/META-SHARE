
#From: http://djangosnippets.org/snippets/2032/

'''
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
from django.db import transaction
from django.db.models import OneToOneField
from django.forms import ModelForm
from django.forms.formsets import all_valid
from django.forms.models import BaseModelFormSet, modelformset_factory
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from django.contrib.admin.util import flatten_fieldsets
from django.core.exceptions import PermissionDenied
from django.db import models
from django.contrib.admin.util import unquote, escape
from django.http import Http404
from metashare.repo2.editor.superadmin import SchemaModelAdmin, SchemaModelInline
from metashare.repo2.editor.superadmin import is_inline, decode_inline
from django.contrib.admin import helpers

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
                 save_as_new = False):
        if instance.pk:
            obj = getattr(instance, self.parent_fk_name)
            _qs = self.model.objects.filter(pk = obj.id)
        else:
            _qs = self.model.objects.filter(pk = -1)
            self.extra = 1
        super(ReverseInlineFormSet, self).__init__(data, files,
                                                       prefix = prefix,
                                                       queryset = _qs)
        for form in self.forms:
            form.empty_permitted = False


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
        'can_delete': False,
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
    Use the name and the help_text of the owning models field to
    render the verbose_name and verbose_name_plural texts.
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

class ReverseModelAdmin(SchemaModelAdmin):
    '''
    Patched ModelAdmin class. The add_view method is overridden to
    allow the reverse inline formsets to be saved before the parent
    model.
    '''
    # cfedermann: this can be removed as the template now resides in the right
    #   location inside the templates/admin folder...
    #
    # change_form_template = "admin/repo2/change_form.html"
    no_inlines = []
    custom_one2one_inlines = {}
    inline_type = 'stacked'
    
    def __init__(self, model, admin_site):
        
        super(ReverseModelAdmin, self).__init__(model, admin_site)
        self.no_inlines = self.no_inlines or []
        if self.exclude is None:
            self.exclude = []
        for field in model._meta.fields:
            if isinstance(field, OneToOneField):
                name = field.name
                if not self.is_required_field(name):
                    self.no_inlines.append(name)
                if not name in self.no_inlines and not name in self.exclude and not name in self.readonly_fields:
                    parent = field.related.parent_model
                    _inline_class = ReverseInlineModelAdmin
                    if  name in self.custom_one2one_inlines:
                        _inline_class = self.custom_one2one_inlines[name]
                    inline = _inline_class(model,
                                                     name,
                                                     parent,
                                                     admin_site,
                                                     self.inline_type)
                    self.inline_instances.append(inline)
                    self.exclude.append(name)

    def add_view(self, request, form_url='', extra_context=None):
        "The 'add' admin view for this model."
        model = self.model
        opts = model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        model_form = self.get_form(request)
        formsets = []
        if request.method == 'POST':
            form = model_form(request.POST, request.FILES)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=False)
            else:
                form_validated = False
                new_object = self.model()
            prefixes = {}
            for form_set in self.get_formsets(request):
                if getattr(form_set, 'parent_fk_name', None) in self.no_inlines:
                    continue
                prefix = form_set.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = form_set(data=request.POST, files=request.FILES,
                                  instance=new_object,
                                  save_as_new=request.POST.has_key("_saveasnew"),
                                  prefix=prefix)
                formsets.append(formset)
            if all_valid(formsets) and form_validated:
                # Here is the modified code.
                for formset, inline in zip(formsets, self.inline_instances):
                    if not isinstance(inline, ReverseInlineModelAdmin):
                        continue
                    saved = formset.save()
                    if saved:
                        obj = saved[0]
                        setattr(new_object, inline.parent_fk_name, obj)
                self.save_model(request, new_object, form, change=False)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=False)

                self.log_addition(request, new_object)
                return self.response_add(request, new_object)
        else:
            # Prepare the dict of initial data from the request.
            # We have to special-case M2Ms as a list of comma-separated PKs.
            initial = dict(request.GET.items())
            for k in initial:
                try:
                    # pylint: disable-msg=C0103
                    f = opts.get_field(k)
                except models.FieldDoesNotExist:
                    continue
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")

            form = model_form(initial=initial)
            prefixes = {}
            for form_set in self.get_formsets(request):
                if getattr(form_set, 'parent_fk_name', None) in self.no_inlines:
                    continue
                prefix = form_set.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = form_set(instance=self.model(), prefix=prefix)
                formsets.append(formset)

        media = self.media or []
        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request))
            # NOTE: handling of read-only fields is not implemented yet.
            #
            #       See options.py:920
            #         readonly = list(inline.get_readonly_fields(request))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        admin_form = OrderedAdminForm(form, list(self.get_fieldsets_with_inlines(request)),
                self.prepopulated_fields, inlines=inline_admin_formsets)
        media = media + admin_form.media

        context = {
            'title': _('Add %s') % force_unicode(opts.verbose_name),
            'adminform': admin_form,
            'is_popup': request.REQUEST.has_key('_popup'),
            'show_delete': False,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)
    add_view = transaction.commit_on_success(add_view)

    def change_view(self, request, object_id, extra_context=None):
        "The 'change' admin view for this model."
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if request.method == 'POST' and "_saveasnew" in request.POST:
            return self.add_view(request, form_url='../add/')

        model_form = self.get_form(request, obj)
        formsets = []
        if request.method == 'POST':
            form = model_form(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj
            prefixes = {}
            for form_set in self.get_formsets(request, new_object):
                if getattr(form_set, 'parent_fk_name', None) in self.no_inlines:
                    continue
                prefix = form_set.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = form_set(request.POST, request.FILES,
                                  instance=new_object, prefix=prefix)

                formsets.append(formset)

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=True)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=True)

                change_message = self.construct_change_message(request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = model_form(instance=obj)
            prefixes = {}
            for form_set in self.get_formsets(request, obj):
                if getattr(form_set, 'parent_fk_name', None) in self.no_inlines:
                    continue
                prefix = form_set.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = form_set(instance=obj, prefix=prefix)
                formsets.append(formset)

        media = self.media or []
        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        admin_form = OrderedAdminForm(form, self.get_fieldsets_with_inlines(request, obj),
            self.prepopulated_fields, self.get_readonly_fields(request, obj),
            model_admin=self, inlines=inline_admin_formsets)
        media = media + admin_form.media

        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': admin_form,
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)

class OrderedAdminForm(helpers.AdminForm):
    def __init__(self, form, fieldsets, prepopulated_fields, readonly_fields=None, model_admin=None, inlines=None):
        self.inlines = inlines
        super(OrderedAdminForm, self).__init__(form, fieldsets, prepopulated_fields, readonly_fields, model_admin)
        
    def __iter__(self):
        for name, options in self.fieldsets:
            yield OrderedFieldset(self.form, name,
                readonly_fields=self.readonly_fields,
                model_admin=self.model_admin, inlines=self.inlines,
                **options
            )

class OrderedFieldset(helpers.Fieldset):
    def __init__(self, form, name=None, readonly_fields=(), fields=(), classes=(),
      description=None, model_admin=None, inlines=None):
        self.inlines = inlines
        if not inlines:
            for field in fields:
                if is_inline(field):
                    # an inline is in the field list, but the list of inlines is empty
                    pass
        super(OrderedFieldset, self).__init__(form, name, readonly_fields, fields, classes, description, model_admin)
        
    def __iter__(self):
        for field in self.fields:
            if not is_inline(field):
                fieldline = helpers.Fieldline(self.form, field, self.readonly_fields, model_admin=self.model_admin)
                elem = OrderedElement(fieldline=fieldline)
                yield elem
            else:
                field = decode_inline(field)
                for inline in self.inlines:
                    if hasattr(inline.opts, 'parent_fk_name'):
                        if inline.opts.parent_fk_name == field:
                            elem = OrderedElement(inline=inline)
                            yield elem
                    elif hasattr(inline.formset, 'prefix'):
                        if inline.formset.prefix == field:
                            elem = OrderedElement(inline=inline)
                            yield elem
                    else:
                        raise InlineError('Incorrect inline: no opts.parent_fk_name or formset.prefix found')

class OrderedElement():
    def __init__(self, fieldline=None, inline=None):
        if fieldline:
            self.is_field = True
            self.fieldline = fieldline
        else:
            self.is_field = False
            self.inline = inline
    
            
class InlineError(Exception):
    def __init__(self, msg=None):
        super(InlineError, self).__init__()
        self.msg = msg
