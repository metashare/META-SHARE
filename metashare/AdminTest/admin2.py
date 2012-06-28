'''
Created on Feb 14, 2012

@author: Administrator
'''
from django.conf import settings
from django.contrib.admin import ModelAdmin
from django.contrib.admin.helpers import AdminForm, InlineAdminForm, InlineAdminFormSet, \
            AdminErrorList, InlineFieldset
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db import models, transaction
from django.core.exceptions import PermissionDenied
from django.forms.formsets import all_valid
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.forms.util import ErrorList
from django.contrib.admin import helpers
from django.contrib.admin.util import unquote, escape
from django.http import Http404
from django.forms.widgets import Media
from metashare.AdminTest.admin import FormNode, TestInlineAdminForm

csrf_protect_m = method_decorator(csrf_protect)

class TestAdmin2(ModelAdmin):
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
        
        if request.method == 'POST':
            node = FormNode(ModelForm, model_admin=self, request=request)
            if node.is_valid():
                node.save()
                self.log_addition(request, node.saved_form)
                return self.response_add(request, node.saved_form)
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
            node = FormNode(ModelForm, model_admin=self, request=request, initial=initial)

        media = self.media
        
        adminForm = TestAdminForm2(node)
        media = media + adminForm.media
        media = media + Media(js=[settings.ADMIN_MEDIA_PREFIX + 'js/inlines.min.js',])

        context = {
            'title': _('Add %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': "_popup" in request.REQUEST,
            'show_delete': False,
            'media': mark_safe(media),
            #'inline_admin_formsets': inline_admin_formsets,
            'errors': TestAdminErrorList2(node),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, extra_context=None):
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if request.method == 'POST' and "_saveasnew" in request.POST:
            return self.add_view(request, form_url='../add/')

        ModelForm = self.get_form(request, obj)
        formsets = []
        if request.method == 'POST':
            node = FormNode(ModelForm, model_admin=self, request=request, instance=obj)
            if node.is_valid():
                node.save()
                new_object = node.saved_form
                change_message = self.construct_change_message(request, node.form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)
        else:
            node = FormNode(ModelForm, model_admin=self, request=request, instance=obj)

        adminForm = TestAdminForm2(node)
        media = self.media + adminForm.media
        media = media + Media(js=[settings.ADMIN_MEDIA_PREFIX + 'js/inlines.min.js',])

        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': mark_safe(media),
            #'inline_admin_formsets': inline_admin_formsets,
            'errors': TestAdminErrorList2(node),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)

class TestAdminForm2(AdminForm):
    def __init__(self, node):
        super(TestAdminForm2, self).__init__(node.form, node.model_admin.get_fieldsets(node.request),
                                             node.model_admin.prepopulated_fields,
                                             node.model_admin.readonly_fields, node.model_admin)
        self.name = node.form.__class__.__name__
        self.admin_formsets = []
        media = self.media
        
        for formsetNode in node.formsetNodes:
            inline_admin_formset = TestInlineAdminFormSet2(formsetNode)
            self.admin_formsets.append(inline_admin_formset)

class TestAdminErrorList2(ErrorList):
    def __init__(self, formNode):
        super(TestAdminErrorList2, self).__init__()

class TestInlineAdminFormSet2(InlineAdminFormSet):
    def __init__(self, formsetNode):
        self.formset = formsetNode.formset
        self.admin_forms = []
        super(TestInlineAdminFormSet2, self).__init__(formsetNode.inline, formsetNode.formset,
                                                      list(formsetNode.inline.get_fieldsets(formsetNode.request)),
                                                      formsetNode.inline.get_readonly_fields(formsetNode.request), formsetNode.inline)
        
        formset = formsetNode.formset
        inline = formsetNode.inline
        request = formsetNode.request
        for formNode in formsetNode.formNodes:
            admin_form = TestInlineAdminForm2(formNode)
            self.admin_forms.append(admin_form)
            
        original=None
        admin_form = TestInlineAdminForm(formset, formset.empty_form, list(inline.get_fieldsets(request)),
        inline.prepopulated_fields, original, request=request)
        self.admin_forms.append(admin_form)
        self.descr = 'Formset description'

    def __iter__(self):
        for form in self.admin_forms:
            yield form
            
class TestInlineAdminForm2(InlineAdminForm):
    name = 'NAME'
    def __init__(self, formNode):
        formset = formNode.formset
        form = formNode.form
        fieldsets = formNode.model_admin.get_fieldsets(formNode.request)
        prepopulated_fields = formNode.model_admin.prepopulated_fields
        original = None
        readonly_fields = formNode.model_admin.readonly_fields
        model_admin = formNode.model_admin
        super(TestInlineAdminForm2, self).__init__(formset, form, fieldsets, prepopulated_fields,
                                                  original, readonly_fields, model_admin)
        self.name = form.__class__.__name__
        self.admin_formsets = []

        for formsetNode in formNode.formsetNodes:
            inline_admin_formset = TestInlineAdminFormSet2(formsetNode)
            self.admin_formsets.append(inline_admin_formset)

