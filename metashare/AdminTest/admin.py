
from django.contrib.admin import ModelAdmin
from django.contrib.admin import StackedInline
from django.contrib.admin.helpers import AdminForm, InlineAdminForm, InlineAdminFormSet, \
            AdminErrorList, InlineFieldset
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.db import models, transaction
from django.core.exceptions import PermissionDenied
from django.forms.formsets import all_valid
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.admin.util import flatten_fieldsets
from django.utils.functional import curry
from django.forms.models import ModelForm, BaseModelFormSet, BaseInlineFormSet, \
            _get_foreign_key, ModelFormMetaclass
from django.forms.formsets import BaseFormSet

csrf_protect_m = method_decorator(csrf_protect)


class TestAdmin(ModelAdmin):
    change_form_template = 'AdminTest/test_change_form.html'

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        "The 'add' admin view for this model."
        model = self.model
        opts = model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request)
        
        formsets = []
        if request.method == 'POST':
            node = FormNode(ModelForm, model_admin=self, request=request)
            form = ModelForm(request.POST, request.FILES)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form_validated = True
            else:
                form_validated = False
                new_object = self.model()
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request), self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(data=request.POST, files=request.FILES,
                                  instance=new_object,
                                  save_as_new="_saveasnew" in request.POST,
                                  prefix=prefix, queryset=inline.queryset(request))
                formsets.append(formset)
            if all_valid(formsets) and form_validated:
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
                    f = opts.get_field(k)
                except models.FieldDoesNotExist:
                    continue
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")
            form = ModelForm(initial=initial)
            node = FormNode(ModelForm, model_admin=self, request=request)
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request),
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=self.model(), prefix=prefix,
                                  queryset=inline.queryset(request))
                formsets.append(formset)

        media = self.media
        
        adminForm = TestAdminForm(form, list(self.get_fieldsets(request)),
            self.prepopulated_fields, self.get_readonly_fields(request),
            model_admin=self, request=request)
        media = media + adminForm.media

        context = {
            'title': _('Add %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': "_popup" in request.REQUEST,
            'show_delete': False,
            'media': mark_safe(media),
            #'inline_admin_formsets': inline_admin_formsets,
            'errors': TestAdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)

class TestInline(StackedInline):
    template = 'AdminTest/test_stacked.html'
    
    def get_formsets(self, request, obj=None):
        for inline in self.inline_instances:
            yield inline.get_formset(request, obj)

    def get_formset(self, request, obj=None, **kwargs):
        Formset = self.get_orig_formset(request, obj, **kwargs)
        if hasattr(self, 'inlines'):
            Formset.nested = self.inlines
        else:
            Formset.nested = None
        return Formset
    
    def get_orig_formset(self, request, obj=None, **kwargs):
        """Returns a BaseInlineFormSet class for use in admin add/change views."""
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
            "formset": self.formset,
            "fk_name": self.fk_name,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
            "extra": self.extra,
            "max_num": self.max_num,
            "can_delete": self.can_delete,
        }
        defaults.update(kwargs)
        return nested_inlineformset_factory(self.parent_model, self.model, **defaults)

class TestAdminForm(AdminForm):
    # inlines contains the list of classes for the formsets of this form
    def __init__(self, form, fieldsets, prepopulated_fields, readonly_fields=None, model_admin=None,
                 request={}):
        super(TestAdminForm, self).__init__(form, fieldsets, prepopulated_fields, readonly_fields, model_admin)
        #self.nested = nested
        self.name = form.__class__.__name__
        self.admin_formsets = []
        media = self.media
        
        # Create the formsets for this form
        inline_instances = []
        for inline in model_admin.inlines:
            inline_obj = inline(model_admin.model, model_admin.admin_site)
            inline_instances.append(inline_obj)
        prefixes = {}
        model_admin.inline_instances = inline_instances
        formsets = []
        for FormSet, inl in zip(model_admin.get_formsets(request),
                                   model_admin.inline_instances):
            prefix = FormSet.get_default_prefix()
            #if parent_prefix is not None:
            #    prefix = "%s-%s" % (parent_prefix, prefix)
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
            if prefixes[prefix] != 1:
                prefix = "%s-%s" % (prefix, prefixes[prefix])
            formset_obj = FormSet(instance=inline.model(), prefix=prefix,
                              queryset=inl.queryset(request))
            formsets.append(formset_obj)
        
        if model_admin.inline_instances is not None and formsets is not None:
            for inline, formset in zip(inline_instances, formsets):
                fieldsets = list(inline.get_fieldsets(request))
                readonly = list(inline.get_readonly_fields(request))
                inline_admin_formset = TestInlineAdminFormSet(inline, formset,
                    fieldsets, readonly, model_admin=inline, request=request)
                media = media + inline_admin_formset.media
                self.admin_formsets.append(inline_admin_formset)
        pass

class TestInlineAdminForm(InlineAdminForm):
    name = 'NAME'
    def __init__(self, formset, form, fieldsets, prepopulated_fields, original,
      readonly_fields=None, model_admin=None,
      request=None):
        super(TestInlineAdminForm, self).__init__(formset, form, fieldsets, prepopulated_fields,
                                                  original, readonly_fields, model_admin)
        self.name = form.__class__.__name__
        self.admin_formsets = []
        prefix = form.prefix
        # Create the formsets for this form
        inline_instances = []
        if hasattr(model_admin, 'inlines'):
            for inline in model_admin.inlines:
                inline_obj = inline(model_admin.model, model_admin.admin_site)
                inline_instances.append(inline_obj)
            prefixes = {}
            model_admin.inline_instances = inline_instances
            formsets = []
            for FormSet, inl in zip(model_admin.get_formsets(request),
                                       model_admin.inline_instances):
                prefix = form.prefix
                prefix = "%s-%s" % (prefix, FormSet.get_default_prefix())
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset_obj = FormSet(instance=inline.model(), prefix=prefix,
                                  queryset=inl.queryset(request))
                formsets.append(formset_obj)
            
            if model_admin.inline_instances is not None and formsets is not None:
                for inline, formset in zip(inline_instances, formsets):
                    fieldsets = list(inline.get_fieldsets(request))
                    readonly = list(inline.get_readonly_fields(request))
                    inline_admin_formset = TestInlineAdminFormSet(inline, formset,
                        fieldsets, readonly, model_admin=inline, request=request, parent_prefix=prefix)
                    media = self.media + inline_admin_formset.media
                    self.admin_formsets.append(inline_admin_formset)
            pass

class TestInlineAdminFormSet(InlineAdminFormSet):
    def __init__(self, inline, formset, fieldsets, readonly_fields=None, model_admin=None, request={}, parent_prefix=None):
        self.admin_forms = []
        inline_instances = []
        if hasattr(inline, 'inlines'):
            for inline_class in inline.inlines:
                inline_obj = inline_class(inline.model, inline.admin_site)
                inline_instances.append(inline_obj)
        inline.inline_instances = inline_instances
        formsets = []
        prefixes = {}
        for FormSet, inl in zip(inline.get_formsets(request),
                                   inline.inline_instances):
            prefix = FormSet.get_default_prefix()
            if parent_prefix is not None:
                prefix = "%s-%s" % (parent_prefix, prefix)
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
            if prefixes[prefix] != 1:
                prefix = "%s-%s" % (prefix, prefixes[prefix])
            formset_obj = FormSet(instance=inline.model(), prefix=prefix,
                              queryset=inl.queryset(request))
            formsets.append(formset_obj)
        for form in formset.forms:
            original=None
            prefix = form.prefix
            if parent_prefix is not None:
                prefix = "%s-%s" % (parent_prefix, prefix)
            admin_form = TestInlineAdminForm(formset, form, list(inline.get_fieldsets(request)),
            inline.prepopulated_fields, original, request=request,
            model_admin=model_admin)
            self.admin_forms.append(admin_form)
        original=None
        admin_form = TestInlineAdminForm(formset, formset.empty_form, list(inline.get_fieldsets(request)),
        inline.prepopulated_fields, original, request=request)
        self.admin_forms.append(admin_form)
        super(TestInlineAdminFormSet, self).__init__(inline, formset, fieldsets, readonly_fields, model_admin)
        self.descr = 'Formset description'

    def __iter__(self):
        for form in self.admin_forms:
            yield form
            
    def __iter2__(self):
        for form, original in zip(self.formset.initial_forms, self.formset.get_queryset()):
            yield TestInlineAdminForm(self.formset, form, self.fieldsets,
                self.opts.prepopulated_fields, original, self.readonly_fields,
                model_admin=self.opts)
        for form in self.formset.extra_forms:
            yield TestInlineAdminForm(self.formset, form, self.fieldsets,
                self.opts.prepopulated_fields, None, self.readonly_fields,
                model_admin=self.opts)
        yield TestInlineAdminForm(self.formset, self.formset.empty_form,
            self.fieldsets, self.opts.prepopulated_fields, None,
            self.readonly_fields, model_admin=self.opts)

class TestInlineFieldset(InlineFieldset):
    pass

class TestAdminErrorList(AdminErrorList):
    pass

class TestBaseInlineFormSet(BaseInlineFormSet):
    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=None, request=None):
        self.admin_forms = []
        super(TestBaseInlineFormSet, self).__init__(data, files, instance, save_as_new, prefix, queryset)
        self.test = 1
        
    def _construct_form(self, i, **kwargs):
        form = super(TestBaseInlineFormSet, self)._construct_form(i)
        return form

def nested_formset_factory(form, formset=BaseFormSet, extra=1, can_order=False,
                    can_delete=False, max_num=None):
    """Return a FormSet for the given form class."""
    attrs = {'form': form, 'extra': extra,
             'can_order': can_order, 'can_delete': can_delete,
             'max_num': max_num}
    return type(form.__name__ + 'FormSet', (formset,), attrs)

def nested_inlineformset_factory(parent_model, model, form=ModelForm,
                          formset=TestBaseInlineFormSet, fk_name=None,
                          fields=None, exclude=None,
                          extra=3, can_order=False, can_delete=True, max_num=None,
                          formfield_callback=None):
    """
    Returns an ``InlineFormSet`` for the given kwargs.

    You must provide ``fk_name`` if ``model`` has more than one ``ForeignKey``
    to ``parent_model``.
    """
    fk = _get_foreign_key(parent_model, model, fk_name=fk_name)
    formset = TestBaseInlineFormSet
    # enforce a max_num=1 when the foreign key to the parent model is unique.
    if fk.unique:
        max_num = 1
    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': formset,
        'extra': extra,
        'can_delete': can_delete,
        'can_order': can_order,
        'fields': fields,
        'exclude': exclude,
        'max_num': max_num,
    }
    FormSet = nested_modelformset_factory(model, **kwargs)
    FormSet.fk = fk
    return FormSet

def nested_modelform_factory(model, form=ModelForm, fields=None, exclude=None,
                       formfield_callback=None):
    # Create the inner Meta class. FIXME: ideally, we should be able to
    # construct a ModelForm without creating and passing in a temporary
    # inner class.

    # Build up a list of attributes that the Meta object will have.
    attrs = {'model': model}
    if fields is not None:
        attrs['fields'] = fields
    if exclude is not None:
        attrs['exclude'] = exclude

    # If parent form class already has an inner Meta, the Meta we're
    # creating needs to inherit from the parent's inner meta.
    parent = (object,)
    if hasattr(form, 'Meta'):
        parent = (form.Meta, object)
    Meta = type('Meta', parent, attrs)

    # Give this new form class a reasonable name.
    class_name = model.__name__ + 'Form'

    # Class attributes for the new form class.
    form_class_attrs = {
        'Meta': Meta,
        'formfield_callback': formfield_callback
    }

    return ModelFormMetaclass(class_name, (form,), form_class_attrs)


def nested_modelformset_factory(model, form=ModelForm, formfield_callback=None,
                         formset=BaseModelFormSet,
                         extra=1, can_delete=False, can_order=False,
                         max_num=None, fields=None, exclude=None):
    """
    Returns a FormSet class for the given Django model class.
    """
    form = nested_modelform_factory(model, form=form, fields=fields, exclude=exclude,
                             formfield_callback=formfield_callback)
    FormSet = nested_formset_factory(form, formset, extra=extra, max_num=max_num,
                              can_order=can_order, can_delete=can_delete)
    FormSet.model = model
    return FormSet

class FormNode(object):
    def __init__(self, model_form_cls, model_admin=None, request=None,
                 form=None, formset=None, initial={}, instance=None):
        self.form = None
        self.model_admin = model_admin
        self.formsetNodes = []
        self.form_validated = None
        self.request = request
        self.formset = formset
        self.saved_form = None
        self.instance = instance
        if request.method == 'POST':
            if form is None:
                if instance is None:
                    self.form = model_form_cls(request.POST, request.FILES)
                else:
                    self.form = model_form_cls(request.POST, request.FILES, instance=instance)
            else:
                self.form = form
            if self.form.is_valid():
                if hasattr(model_admin, 'save_form'):
                    new_object = model_admin.save_form(request, self.form, change=False)
                    self.saved_form = new_object
                else:
                    new_object = self.form.save(commit=False)
                self.form_validated = True
            else:
                self.form_validated = False
                new_object = model_admin.model()
                print 'Error in form ' + (self.form.prefix or 'Main')
            prefixes = {}
            if hasattr(model_admin, 'inline_instances'):
                if instance is not None:
                    for FormSet, inline in zip(model_admin.get_formsets(request, instance), model_admin.inline_instances):
                        prefix = FormSet.get_default_prefix()
                        if self.form.prefix is not None:
                            prefix = "%s-%s" % (self.form.prefix, prefix)
                        prefixes[prefix] = prefixes.get(prefix, 0) + 1
                        if prefixes[prefix] != 1:
                            prefix = "%s-%s" % (prefix, prefixes[prefix])
                        formsetNode = FormsetNode(FormSet, inline=inline, instance=instance, prefix=prefix,
                                                  request=request, queryset=inline.queryset(request))
                        self.formsetNodes.append(formsetNode)
                else:
                    for FormSet, inline in zip(model_admin.get_formsets(request), model_admin.inline_instances):
                        prefix = FormSet.get_default_prefix()
                        if self.form.prefix is not None:
                            prefix = "%s-%s" % (self.form.prefix, prefix)
                        prefixes[prefix] = prefixes.get(prefix, 0) + 1
                        if prefixes[prefix] != 1:
                            prefix = "%s-%s" % (prefix, prefixes[prefix])
                        formsetNode = FormsetNode(FormSet, inline=inline, instance=new_object, prefix=prefix, request=request)
                        self.formsetNodes.append(formsetNode)
        else:
            if form is None:
                if instance is None:
                    self.form = model_form_cls(initial=initial)
                else:
                    self.form = model_form_cls(initial=initial, instance=instance)
            else:
                self.form = form
            prefixes = {}
            inline_instances = []
            if(hasattr(model_admin, 'inlines')):
                for inline_cls in model_admin.inlines:
                    inline_obj = inline_cls(model_admin.model, model_admin.admin_site)
                    inline_instances.append(inline_obj)
                model_admin.inline_instances = inline_instances
                for FormSet, inline in zip(model_admin.get_formsets(request, obj=instance),
                                           model_admin.inline_instances):
                    prefix = FormSet.get_default_prefix()
                    if self.form.prefix is not None:
                        prefix = "%s-%s" % (self.form.prefix, prefix)
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
                    if prefixes[prefix] != 1:
                        prefix = "%s-%s" % (prefix, prefixes[prefix])
                    if instance is None:
                        instance = model_admin.model()
                    formsetNode = FormsetNode(FormSet, inline=inline, instance=instance,
                                              prefix=prefix, queryset=inline.queryset(request),
                                              request=request)
                    self.formsetNodes.append(formsetNode)
        
    def is_valid(self):
        result = self.form.is_valid()
        for formsetNode in self.formsetNodes:
            if not formsetNode.is_valid():
                result = False
        return result
    
    def save(self):
        self.saved_form.save()
        self.form.save_m2m()
        self.save_formsets()
            
    def save_formsets(self):
        for formsetNode in self.formsetNodes:
            formsetNode.save()

class FormsetNode(object):
    def __init__(self, FormSet, inline=None, instance=None, prefix=None, request={}, queryset=None):
        self.formNodes = []
        self.inline = inline
        self.request = request
        if request.method == 'POST':
            self.formset = FormSet(data=request.POST, files=request.FILES,
                              instance=instance,
                              save_as_new="_saveasnew" in request.POST,
                              prefix=prefix, queryset=inline.queryset(request))
            for form in self.formset.forms:
                formNode = FormNode(inline.model, inline, request=request, form=form, formset=self.formset)
                self.formNodes.append(formNode)
        else:
            if instance is None:
                instance = inline.model()
            self.formset = FormSet(instance=instance, prefix=prefix,
                              queryset=inline.queryset(request))
            for form in self.formset.forms:
                formNode = FormNode(inline.model, inline, request=request, form=form, formset=self.formset, instance=form.instance)
                self.formNodes.append(formNode)
        
    def is_valid(self):
        result = True
        for formNode in self.formNodes:
            if not formNode.is_valid():
                result = False
        return result
    
    def save(self):
        saved_instances = self.formset.save()
        for formNode in self.formNodes:
            formNode.save_formsets()
        return saved_instances
