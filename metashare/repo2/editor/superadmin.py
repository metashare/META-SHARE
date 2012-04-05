'''
Custom base classes for admin interface, for both the top-level admin page
and for inline forms.
'''
import logging
from django import template
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.utils.encoding import force_unicode
from django.utils.functional import update_wrapper
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect
from django.db.models.fields.related import ManyToManyField
from django.core.urlresolvers import reverse
from django.contrib.admin import helpers
from django.forms.formsets import all_valid
from django.utils.safestring import mark_safe
from django.db import transaction, models
from metashare.repo2.supermodel import REQUIRED, RECOMMENDED, \
  OPTIONAL
from metashare import settings
from metashare.repo2.editor.forms import StorageObjectUploadForm
from metashare.repo2.editor.related_mixin import RelatedAdminMixin
from metashare.storage.models import ALLOWED_ARCHIVE_EXTENSIONS
from metashare.repo2.editor.schemamodel_mixin import SchemaModelLookup,\
    is_inline, decode_inline
from metashare.repo2.editor.inlines import ReverseInlineModelAdmin

# Setup logging support.
logging.basicConfig(level=settings.LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repo2.superadmin')
LOGGER.addHandler(settings.LOG_HANDLER)

csrf_protect_m = method_decorator(csrf_protect)



class FilteredChangeList(ChangeList):
    """
    A FilteredChangeList filters the result_list for request.user objects.
    This implementation always filters; use the superclass ChangeList for
    unfiltered views.
    """
    def __init__(self, request, model, list_display, list_display_links,
      list_filter, date_hierarchy, search_fields, list_select_related,
      list_per_page, list_editable, model_admin):
        # Call super constructor to initialise object instance.
        super(FilteredChangeList, self).__init__(request, model, list_display,
          list_display_links, list_filter, date_hierarchy, search_fields,
          list_select_related, list_per_page, list_editable, model_admin)
        # Check if the current model has an "owners" ManyToManyField.
        _has_owners_field = False
        if 'owners' in self.opts.get_all_field_names():
            _field = self.opts.get_field_by_name('owners')[0]
            _has_owners_field = isinstance(_field, ManyToManyField)

        # If "owners" are available, we
        # have to constrain the QuerySet using an additional filter...
        if _has_owners_field:
            _user = request.user
            self.root_query_set = self.root_query_set.filter(owners=_user)

        self.query_set = self.get_query_set()
        self.get_results(request)

    def url_for_result(self, result):
        return reverse("editor:{}_{}_change".format(self.opts.app_label, self.opts.module_name), args=(getattr(result, self.pk_attname),))

class SchemaModelAdmin(admin.ModelAdmin, RelatedAdminMixin, SchemaModelLookup):
    '''
    Patched ModelAdmin class. The add_view method is overridden to
    allow the reverse inline formsets to be saved before the parent
    model.
    '''
    no_inlines = []
    custom_one2one_inlines = {}
    inline_type = 'stacked'
    inlines = ()

    class Media:
        js = (settings.MEDIA_URL + 'js/jquery-1.7.1.min.js',
              settings.MEDIA_URL + 'js/addCollapseToAllStackedInlines.js',
              settings.ADMIN_MEDIA_PREFIX + 'js/collapse.min.js',
              settings.ADMIN_MEDIA_PREFIX + 'js/metashare-editor.js',)
    
    def __init__(self, model, admin_site):
        self.inlines += tuple(self._inlines(model))
        self.filter_horizontal = self._m2m(model)
        super(SchemaModelAdmin, self).__init__(model, admin_site)    
        # Revers inline code:
        self.no_inlines = self.no_inlines or []
        if self.exclude is None:
            self.exclude = []
        for field in model._meta.fields:
            if isinstance(field, models.OneToOneField):
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

    def _inlines(self, model):
        return self.get_inline_classes(model, status=REQUIRED) + \
          self.get_inline_classes(model, status=RECOMMENDED) + \
          self.get_inline_classes(model, status=OPTIONAL)

    def _m2m(self, model):
        return model.get_many_to_many_fields()

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urlpatterns = super(SchemaModelAdmin, self).get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name
        
        # cfedermann: add "/upload-data/" and "/my/" URLs for resourceInfoType_model only.
        _schema_name = getattr(self.model, '__schema_name__', None)
        if _schema_name == 'resourceInfo':
            urlpatterns = patterns('',
                url(r'^(.+)/upload-data/$',
                    wrap(self.uploaddata_view),
                    name='%s_%s_uploaddata' % info),
                url(r'^my/$',
                    wrap(self.changelist_view_filtered),
                    name='%s_%s_myresources' % info),
            ) + urlpatterns
        return urlpatterns

    
    def get_fieldsets(self, request, obj=None):
        return SchemaModelLookup.get_fieldsets(self, request, obj)

    @csrf_protect_m
    def changelist_view_filtered(self, request, extra_context=None):
        '''
        The filtered changelist view for My Resources.
        We reuse the generic django changelist_view and squeeze in our wish to
        show the filtered view in two places:
        1. we patch request.POST to insert a parameter 'myresources'='true',
           which will be interpreted in get_changelist to show the filtered
           version;
        2. we pass a extra_context variable 'myresources' which will be
           interpreted in the template change_list.html. 
        '''
        _post = request.POST.copy()
        _post['myresources'] = 'true'
        request.POST = _post
        _extra_context = extra_context or {}
        _extra_context.update({'myresources':True})
        return self.changelist_view(request, _extra_context)

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        if 'myresources' in request.POST:
            return FilteredChangeList
        else:
            return ChangeList

    def log_addition(self, request, obj):
        """
        Log that an object has been successfully added and update owners.
        
        We currently update owners information here as save_model() for some
        reason does not properly store the request.user's id in the M2M field.
        """
        if hasattr(obj, 'owners'):
            _field = obj._meta.get_field_by_name('owners')[0]
            if isinstance(_field, ManyToManyField):
                obj.owners.add(request.user.pk)
                obj.save()

        super(SchemaModelAdmin, self).log_addition(request, obj)

    def log_change(self, request, obj, message):
        """
        Log that an object has been successfully changed and update owners.
        """
        if hasattr(obj, 'owners'):
            _field = obj._meta.get_field_by_name('owners')[0]
            if isinstance(_field, ManyToManyField):
                obj.owners.add(request.user.pk)
                obj.save()

        super(SchemaModelAdmin, self).log_change(request, obj, message)


    @csrf_protect_m
    def uploaddata_view(self, request, object_id, extra_context=None):
        """
        The 'upload data' admin view for resourceInfoType_model instances.
        """
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        _schema_name = getattr(model, '__schema_name__', None)
        if not _schema_name == "resourceInfo":
            return HttpResponseRedirect(request.get_full_path())

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') \
             % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        storage_object = obj.storage_object
        if storage_object is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not have a StorageObject attached.') \
              % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if not storage_object.master_copy:
            raise Http404(_('%(name)s object with primary key %(key)r is not a master-copy.') \
              % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        existing_download = storage_object.get_download()
        storage_folder = storage_object._storage_folder()

        if request.method == 'POST':
            form = StorageObjectUploadForm(request.POST, request.FILES)
            form_validated = form.is_valid()

            if form_validated:
                # Check if a new file has been uploaded to resource.
                resource = request.FILES['resource']                
                _extension = None
                for _allowed_extension in ALLOWED_ARCHIVE_EXTENSIONS:
                    if resource.name.endswith(_allowed_extension):
                        _extension = _allowed_extension
                        break
                
                # We can assert that an extension has been found as the form
                # validation would have raise a ValidationError otherwise;
                # still, we raise an AssertionError if anything goes wrong!
                assert(_extension in ALLOWED_ARCHIVE_EXTENSIONS)

                if _extension:
                    _storage_folder = storage_object._storage_folder()
                    _out_filename = '{}/archive.{}'.format(_storage_folder,
                      _extension)

                    # Copy uploaded file to storage folder for this object.                    
                    with open(_out_filename, 'wb') as _out_file:
                        # pylint: disable-msg=E1101
                        for _chunk in resource.chunks():
                            _out_file.write(_chunk)

                    # Save corresponding StorageObject to update its checksum.
                    obj.storage_object.save()

                    change_message = 'Uploaded "{}" to "{}" in {}.'.format(
                      resource.name, storage_object._storage_folder(),
                      storage_object)

                    self.log_change(request, obj, change_message)

                return self.response_change(request, obj)

        else:
            form = StorageObjectUploadForm()

        context = {
            'title': _('Upload resource: "%s"') % force_unicode(obj),
            'form': form,
            'storage_folder': storage_folder,
            'existing_download': existing_download,
            'object_id': object_id,
            'original': obj,
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request,
          current_app=self.admin_site.name)
        return render_to_response(
          ['admin/repo2/resourceinfotype_model/upload_resource.html'], context,
          context_instance)
        
    def formfield_for_dbfield(self, db_field, **kwargs):
        self.hide_hidden_fields(db_field, kwargs)
        if self.is_subclassable(db_field):
            return self.formfield_for_subclassable(db_field, **kwargs)
        self.use_hidden_widget_for_one2one(db_field, kwargs)
        formfield = super(SchemaModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        self.use_related_widget_where_appropriate(db_field, kwargs, formfield)
        return formfield

    def response_change(self, request, obj):
        if '_popup' in request.REQUEST:
            return self.edit_response_close_popup_magic(obj)
        else:
            return super(SchemaModelAdmin, self).response_change(request, obj)

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