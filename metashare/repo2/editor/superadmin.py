'''
Custom base classes for admin interface, for both the top-level admin page
and for inline forms.
'''
import logging
from django import template
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
from metashare.utils import get_class_by_name, verify_subclass
from metashare.repo2.supermodel import SchemaModel, REQUIRED, RECOMMENDED, \
  OPTIONAL
from metashare import settings
from metashare.repo2.editor.forms import StorageObjectUploadForm
from metashare.repo2.editor.related_admin import RelatedWidgetWrapperAdmin, \
  RelatedWidgetWrapperInline
from metashare.storage.models import ALLOWED_ARCHIVE_EXTENSIONS
from django.db.models.fields.related import ManyToManyField
from django.core.urlresolvers import reverse

# Setup logging support.
logging.basicConfig(level=settings.LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repo2.superadmin')
LOGGER.addHandler(settings.LOG_HANDLER)

csrf_protect_m = method_decorator(csrf_protect)

# inline names included in fieldsets are prepended with an '_'
def encode_as_inline(name):
    return '_' + name

def decode_inline(fieldname):
    if fieldname.startswith('_'):
        name = fieldname[1:]
        return name
    else:
        return fieldname

def is_inline(fieldname):
    if fieldname.startswith('_'):
        return True
    else:
        return False

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
        return get_class_by_name('metashare.repo2.admin', inline_class_name)


class SchemaModelInline(RelatedWidgetWrapperInline, SchemaModelLookup):
    extra = 1
    collapse = False

    def __init__(self, parent_model, admin_site):
        super(SchemaModelInline, self).__init__(parent_model, admin_site)
        if self.collapse:
            self.verbose_name_plural = '_{}'.format(force_unicode(self.verbose_name_plural))
        self.filter_horizontal = self.model.get_many_to_many_fields()

    def get_fieldsets(self, request, obj=None):
        return SchemaModelLookup.get_fieldsets(self, request, obj)


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

class SchemaModelAdmin(RelatedWidgetWrapperAdmin, SchemaModelLookup):
    inlines = ()
    class Media:
        js = (settings.MEDIA_URL + 'js/jquery-1.7.1.min.js',
              settings.MEDIA_URL + 'js/addCollapseToAllStackedInlines.js',
              settings.MEDIA_URL + 'js/jquery-ui.min.js',
              settings.ADMIN_MEDIA_PREFIX + 'js/collapse.min.js',
              settings.ADMIN_MEDIA_PREFIX + 'js/metashare-editor.js',)
    
    def __init__(self, model, admin_site):
        self.inlines += tuple(self._inlines(model))
        #self.filter_horizontal = [] + self._m2m(model)
        self.filter_horizontal = []
        for fld in self._m2m(model):
            has_widget = False
            if hasattr(self.form, 'Meta'):
                if hasattr(self.form.Meta, 'widgets'):
                    if fld in self.form.Meta.widgets:
                        has_widget = True
            if not has_widget:
                self.filter_horizontal.append(fld)
        super(SchemaModelAdmin, self).__init__(model, admin_site)    

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
