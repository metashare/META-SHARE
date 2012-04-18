from metashare.repository.editor.inlines import ReverseInlineFormSet, \
    ReverseInlineModelAdmin
from django.core.exceptions import ValidationError, PermissionDenied
from metashare.repository.models import resourceComponentTypeType_model, \
    corpusInfoType_model, languageDescriptionInfoType_model, \
    lexicalConceptualResourceInfoType_model, toolServiceInfoType_model, \
    corpusMediaTypeType_model, languageDescriptionMediaTypeType_model, \
    lexicalConceptualResourceMediaTypeType_model, resourceInfoType_model, \
    metadataInfoType_model
from metashare.storage.models import PUBLISHED, INGESTED, INTERNAL, \
    ALLOWED_ARCHIVE_EXTENSIONS
from metashare.utils import verify_subclass
from metashare.stats.model_utils import saveLRStats, UPDATE_STAT
from metashare.repository.supermodel import SchemaModel
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from metashare import settings
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from metashare.repository.editor.superadmin import SchemaModelAdmin
from metashare.repository.editor.schemamodel_mixin import encode_as_inline
from django.utils.functional import update_wrapper
from django.views.decorators.csrf import csrf_protect
from metashare.repository.editor.editorutils import FilteredChangeList
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.util import unquote
from django.http import Http404
from metashare.repository.editor.forms import StorageObjectUploadForm
from django.utils.html import escape
from django.utils.translation import ugettext as _

csrf_protect_m = method_decorator(csrf_protect)

    
class ResourceComponentInlineFormSet(ReverseInlineFormSet):
    '''
    A formset with custom save logic for resources.
    '''
    def clean(self):
        actual_instance = self.get_actual_resourceComponentType()

        error_list = ''
        if isinstance(actual_instance, corpusInfoType_model):
            error_list = error_list + self.clean_corpus(actual_instance)
        elif isinstance(actual_instance, languageDescriptionInfoType_model):
            error_list = error_list + self.clean_langdesc(actual_instance)
        elif isinstance(actual_instance, lexicalConceptualResourceInfoType_model):
            error_list = error_list + self.clean_lexicon(actual_instance)
        elif isinstance(actual_instance, toolServiceInfoType_model):
            error_list = error_list + self.clean_toolservice(actual_instance)
        else:
            raise Exception, "unexpected resource component class type: {}".format(actual_instance.__class__.__name__)
        try:
            actual_instance.full_clean()
        except ValidationError:
            #raise ValidationError('The content of the {} general info is not valid.'.format(self.get_actual_resourceComponentType()._meta.verbose_name))
            #raise AssertionError("Meaningful error message for general info")
            error_list = error_list +  'The content of the {} general info is not valid.'.format(self.get_actual_resourceComponentType()._meta.verbose_name)
        
        if error_list != '':
            raise ValidationError(error_list)
        super(ResourceComponentInlineFormSet, self).clean()
        
    def clean_media(self, parent, fieldnames):
        '''
        Clean the list of media data in the XXMediaType parent object. 
        '''
        
        error = ''
        for modelfieldname in fieldnames:
            print modelfieldname
            if modelfieldname not in self.data:
                continue
            value = self.data[modelfieldname]
            if not value:
                # print error
                #raise AssertionError("Meaningful error message")                
                error = error + format(modelfieldname)+' error. '
                
        return error
            
    def clean_corpus(self, corpus):
        return self.clean_media(corpus.corpusMediaType, \
             ('corpusAudioInfo', 'corpusImageInfo', 'corpusTextNumericalInfo', 'corpusTextNgramInfo'))

    def clean_langdesc(self, langdesc):
        return self.clean_media(langdesc.languageDescriptionMediaType, \
            ('languageDescriptionTextInfo', 'languageDescriptionVideoInfo', 'languageDescriptionImageInfo'))

    def clean_lexicon(self, lexicon):
        return self.clean_media(lexicon.lexicalConceptualResourceMediaType, \
             ('lexicalConceptualResourceTextInfo', 'lexicalConceptualResourceAudioInfo', \
              'lexicalConceptualResourceVideoInfo', 'lexicalConceptualResourceImageInfo'))
                
    def clean_toolservice(self, tool):
        return ''
    
    def save_media(self, parent, fieldnames):
        '''
        Save the list of media data in the XXMediaType parent object. 
        '''
        for modelfieldname in fieldnames:
            if modelfieldname not in self.data:
                continue
            value = self.data[modelfieldname]
            if not value:
                continue
            modelfield = parent._meta.get_field(modelfieldname)
            child_id = int(value)
            child = modelfield.rel.to.objects.get(pk=child_id)
            setattr(parent, modelfieldname, child)
            parent.save()

    
    def save_corpus(self, corpus, commit):
        self.save_media(corpus.corpusMediaType, \
             ('corpusAudioInfo', 'corpusImageInfo', 'corpusTextNumericalInfo', 'corpusTextNgramInfo'))

    def save_langdesc(self, langdesc, commit):
        self.save_media(langdesc.languageDescriptionMediaType, \
            ('languageDescriptionTextInfo', 'languageDescriptionVideoInfo', 'languageDescriptionImageInfo'))

    def save_lexicon(self, lexicon, commit):
        self.save_media(lexicon.lexicalConceptualResourceMediaType, \
             ('lexicalConceptualResourceTextInfo', 'lexicalConceptualResourceAudioInfo', \
              'lexicalConceptualResourceVideoInfo', 'lexicalConceptualResourceImageInfo'))
                
    def save_toolservice(self, tool, commit):
        pass
    


    def get_actual_resourceComponentType(self):
        if not (self.forms and self.forms[0].instance):
            raise Exception, "Cannot save for unexisting instance"
        if self.forms[0].instance.pk is not None:
            actual_instance = self.forms[0].instance
        else:
            actual_instance = resourceComponentTypeType_model.objects.get(pk=self.data['resourceComponentId'])
            self.forms[0].instance = actual_instance # we need to use the resourceComponentType we created earlier
        actual_instance = actual_instance.as_subclass()
        return actual_instance

    def save(self, commit=True):
        actual_instance = self.get_actual_resourceComponentType()
        if isinstance(actual_instance, corpusInfoType_model):
            self.save_corpus(actual_instance, commit)
        elif isinstance(actual_instance, languageDescriptionInfoType_model):
            self.save_langdesc(actual_instance, commit)
        elif isinstance(actual_instance, lexicalConceptualResourceInfoType_model):
            self.save_lexicon(actual_instance, commit)
        elif isinstance(actual_instance, toolServiceInfoType_model):
            self.save_toolservice(actual_instance, commit)
        else:
            raise Exception, "unexpected resource component class type: {}".format(actual_instance.__class__.__name__)
        super(ResourceComponentInlineFormSet, self).save(commit)
        return (actual_instance, )
        
# pylint: disable-msg=R0901
class ResourceComponentInline(ReverseInlineModelAdmin):
    formset = ResourceComponentInlineFormSet
    def __init__(self,
                 parent_model,
                 parent_fk_name,
                 model, admin_site,
                 inline_type):
        super(ResourceComponentInline, self). \
            __init__(parent_model, parent_fk_name, model, admin_site, inline_type)
        self.template = 'repository/editor/resourceComponentInline.html'

# pylint: disable-msg=R0901
class IdentificationInline(ReverseInlineModelAdmin):
    readonly_fields = ('metaShareId', )


def change_resource_status(resource, status, precondition_status=None):
    '''
    Change the status of the given resource to the new status given.
    If precondition_status is not None, then apply the change ONLY IF
    the current status of the resource is precondition_status;
    otherwise do nothing.
    '''
    if not hasattr(resource, 'storage_object'):
        raise NotImplementedError, "{0} has no storage object".format(resource)
    if precondition_status is None \
            or precondition_status == resource.storage_object.publication_status:
        resource.storage_object.publication_status = status
        resource.storage_object.save()
    
def publish_resources(modeladmin, request, queryset):
    for obj in queryset:
        change_resource_status(obj, status=PUBLISHED, precondition_status=INGESTED)
publish_resources.short_description = "Publish selected ingested resources"

def unpublish_resources(modeladmin, request, queryset):
    for obj in queryset:
        change_resource_status(obj, status=INGESTED, precondition_status=PUBLISHED)
unpublish_resources.short_description = "Unpublish selected published resources"

def ingest_resources(modeladmin, request, queryset):
    for obj in queryset:
        change_resource_status(obj, status=INGESTED, precondition_status=INTERNAL)
ingest_resources.short_description = "Ingest selected internal resources"


from selectable.base import LookupBase, ModelLookup
from selectable.registry import registry
from selectable.forms.widgets import AutoCompleteSelectMultipleWidget
from metashare.repository.models import personInfoType_model

class PersonLookup(ModelLookup):
    model = personInfoType_model
    search_fields = ('surname__contains', )
    filters = {}
    
    def get_query(self, request, term):
        #results = super(PersonLookup, self).get_query(request, term)
        # Since MultiTextFields cannot be searched using query sets (they are base64-encoded and pickled),
        # we must do the searching by hand.
        # TODO: this is excessively slow, replace with more appropriate search mechanism, e.g. a SOLR index
        lcterm = term.lower()
        def matches(person):
            'Helper function to group the search code for a person'
            for multifield in (person.surname, person.givenName):
                for field in multifield:
                    if lcterm in field.lower():
                        return True
            return False
        persons = self.get_queryset()
        if term == '*':
            results = persons
        else:
            results = [p for p in persons if matches(p)]
        if results is not None:
            print u'{} results'.format(results.__len__())
        else:
            print u'No results'
        return results
    
    def get_item_label(self, item):
        return unicode(item)
#        name_flat = ' '.join(item.givenName)
#        surname_flat = ' '.join(item.surname)
#        return u'%s %s' % (name_flat, surname_flat)
    
    def get_item_id(self, item):
        return item.id

class ValidationReportLookup(LookupBase):
    pass

registry.register(PersonLookup)
registry.register(ValidationReportLookup)

from django import forms

class MetadataForm(forms.ModelForm):
    class Meta:
        model = metadataInfoType_model
        widgets = {'metadataCreator' : AutoCompleteSelectMultipleWidget(lookup_class=PersonLookup)}

class MetadataInline(ReverseInlineModelAdmin):
    form = MetadataForm
            
class ResourceForm(forms.ModelForm):
    class Meta:
        model = resourceInfoType_model
        widgets = {'contactPerson' : AutoCompleteSelectMultipleWidget(lookup_class=PersonLookup)}

class ResourceModelAdmin(SchemaModelAdmin):
    form = ResourceForm
    inline_type = 'stacked'
    custom_one2one_inlines = {'identificationInfo':IdentificationInline,
                              'resourceComponentType':ResourceComponentInline,
                              'metadataInfo':MetadataInline}
    content_fields = ('resourceComponentType',)
    list_display = ('__unicode__', 'resource_type', 'publication_status')
    actions = (publish_resources, unpublish_resources, ingest_resources, )
    hidden_fields = ('storage_object',)


    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urlpatterns = super(ResourceModelAdmin, self).get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name
        
        urlpatterns = patterns('',
            url(r'^(.+)/upload-data/$',
                wrap(self.uploaddata_view),
                name='%s_%s_uploaddata' % info),
            url(r'^my/$',
                wrap(self.changelist_view_filtered),
                name='%s_%s_myresources' % info),
        ) + urlpatterns
        return urlpatterns

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


    @csrf_protect_m
    def uploaddata_view(self, request, object_id, extra_context=None):
        """
        The 'upload data' admin view for resourceInfoType_model instances.
        """
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

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
        context_instance = RequestContext(request,
          current_app=self.admin_site.name)
        return render_to_response(
          ['admin/repository/resourceinfotype_model/upload_resource.html'], context,
          context_instance)


    def build_fieldsets_from_schema(self, include_inlines=False, inlines=()):
        """
        Builds fieldsets using SchemaModel.get_fields().
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
        _content_fieldsets = []
        # pylint: disable-msg=E1101
        _fields = self.model.get_fields()
        _has_content_fields = hasattr(self, 'content_fields')

        for _field_status in ('required', 'recommended', 'optional'):
            _visible_fields = []
            _visible_fields_verbose_names = []
            _visible_content_fields = []
            # pylint: disable-msg=C0103
            _visible_content_fields_verbose_names = []

            for _field_name in _fields[_field_status]:
                _is_visible = False
                if self.is_visible_as_normal_field(_field_name, exclusion_list):
                    _is_visible = True
                    _fieldname_to_append = _field_name
                elif self.is_visible_as_inline(_field_name, include_inlines, inlines):
                    _is_visible = True
                    _fieldname_to_append = encode_as_inline(_field_name)

                # Now, where to show the field: in administrative or in content fieldset:
                if _has_content_fields and _field_name in self.content_fields:
                    _relevant_fields = _visible_content_fields
                    _verbose_names = _visible_content_fields_verbose_names
                else:
                    _relevant_fields = _visible_fields
                    _verbose_names = _visible_fields_verbose_names

                # And now put the field where it belongs:
                if _is_visible:
                    _relevant_fields.append(_fieldname_to_append)
                    _verbose_names.append(self.model.get_verbose_name(_field_name))
            
            
            if len(_visible_fields) > 0:
                _detail = ', '.join(_visible_fields_verbose_names)
                _caption = '{0} administration information: {1}'.format(_field_status.capitalize(), _detail)
                _fieldset = {'fields': _visible_fields}
                _fieldsets.append((_caption, _fieldset))
            if len(_visible_content_fields) > 0:
                _caption = '{0} content information: {1}'.format(_field_status.capitalize(), '')
                _fieldset = {'fields': _visible_content_fields}
                _content_fieldsets.append((_caption, _fieldset))
        
        _fieldsets += _content_fieldsets

        if _hidden_fields:
            _fieldsets.append((None, {'fields': _hidden_fields, 'classes':('display_none', )}))

        return _fieldsets


    def resource_type_selection_view(self, request, form_url, extra_context):
        opts = self.model._meta
        media = self.media or []
        context = {
            'title': 'Add %s' % force_unicode(opts.verbose_name),
            'show_delete': False,
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
            'media': mark_safe(media),
            'add': True,
            'has_add_permission': self.has_add_permission(request),
            'opts': opts,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
        }
        if extra_context:
            context.update(extra_context)
        return render_to_response("repository/editor/select_resource_type.html", context, RequestContext(request))

    def copy_show_media(self, post):
        showtags = ('showCorpusTextInfo', 'showCorpusAudioInfo', 'showCorpusVideoInfo', 'showCorpusImageInfo', 'showCorpusTextNumericalInfo',
                 'showCorpusTextNgramInfo',
                 'showLangdescTextInfo', 'showLangdescVideoInfo', 'showLangdescImageInfo',
                 'showLexiconTextInfo', 'showLexiconAudioInfo', 'showLexiconVideoInfo', 'showLexiconImageInfo',
                 )
        out = {}
        for item in showtags:
            if item in post:
                out[item] = True
        return out
        
        

    def create_hidden_structures(self, request):
        '''
        For a new resource of the given resource type, create the
        hidden structures needed and return them as a dict.
        '''
        resource_type = request.POST['resourceType']
        structures = {}
        if resource_type == 'corpus':
            corpus_media_type = corpusMediaTypeType_model.objects.create()
            corpus_info = corpusInfoType_model.objects.create(corpusMediaType=corpus_media_type, resourceType='0')
            structures['resourceComponentType'] = corpus_info
            structures['corpusMediaType'] = corpus_media_type
        elif resource_type == 'langdesc':
            language_description_media_type = languageDescriptionMediaTypeType_model.objects.create()
            langdesc_info = languageDescriptionInfoType_model.objects.create(languageDescriptionMediaType=language_description_media_type, resourceType='0')
            structures['resourceComponentType'] = langdesc_info
            structures['languageDescriptionMediaType'] = language_description_media_type
        elif resource_type == 'lexicon':
            lexicon_media_type = lexicalConceptualResourceMediaTypeType_model.objects.create()
            lexicon_info = lexicalConceptualResourceInfoType_model.objects.create(lexicalConceptualResourceMediaType=lexicon_media_type, resourceType='0')
            structures['resourceComponentType'] = lexicon_info
            structures['lexicalConceptualResourceMediaType'] = lexicon_media_type
        elif resource_type == 'toolservice':
            tool_info = toolServiceInfoType_model.objects.create(resourceType='0')
            structures['resourceComponentType'] = tool_info
            structures['toolServiceInfoId'] = tool_info.pk
        else:
            raise NotImplementedError, "Cannot deal with '{}' resource types just yet".format(resource_type)
        return structures

    def get_hidden_structures(self, request, resource_id=None):
        '''
        For a resource with existing hidden structures,
        fill a dict with the hidden objects.
        '''
        def get_mediatype_id(media_type_name, media_type_field):
            if media_type_name in request.POST:
                return request.POST[media_type_name]
            if media_type_field:
                return media_type_field.pk
            return ''
        resource_component_id = self.get_resource_component_id(request, resource_id)
        structures = {}
        resource_component = resourceComponentTypeType_model.objects.get(pk=resource_component_id)
        content_info = resource_component.as_subclass()
        structures['resourceComponentType'] = content_info
        if isinstance(content_info, corpusInfoType_model):
            structures['corpusMediaType'] = content_info.corpusMediaType
            structures['corpusAudioInfoId'] = get_mediatype_id('corpusAudioInfo', \
                content_info.corpusMediaType.corpusAudioInfo)
            structures['corpusImageInfoId'] = get_mediatype_id('corpusImageInfo', \
                content_info.corpusMediaType.corpusImageInfo)
            structures['corpusTextNumericalInfoId'] = get_mediatype_id('corpusTextNumericalInfo', \
                content_info.corpusMediaType.corpusTextNumericalInfo)
            structures['corpusTextNgramInfoId'] = get_mediatype_id('corpusTextNgramInfo', \
                content_info.corpusMediaType.corpusTextNgramInfo)
        elif isinstance(content_info, languageDescriptionInfoType_model):
            structures['langdescTextInfoId'] = get_mediatype_id('languageDescriptionTextInfo', \
                content_info.languageDescriptionMediaType.languageDescriptionTextInfo)
            structures['langdescVideoInfoId'] = get_mediatype_id('languageDescriptionVideoInfo', \
                content_info.languageDescriptionMediaType.languageDescriptionVideoInfo)
            structures['langdescImageInfoId'] = get_mediatype_id('languageDescriptionImageInfo', \
                content_info.languageDescriptionMediaType.languageDescriptionImageInfo)
        elif isinstance(content_info, lexicalConceptualResourceInfoType_model):
            structures['lexiconTextInfoId'] = get_mediatype_id('lexicalConceptualResourceTextInfo', \
                content_info.lexicalConceptualResourceMediaType.lexicalConceptualResourceTextInfo)
            structures['lexiconAudioInfoId'] = get_mediatype_id('lexicalConceptualResourceAudioInfo', \
                content_info.lexicalConceptualResourceMediaType.lexicalConceptualResourceAudioInfo)
            structures['lexiconVideoInfoId'] = get_mediatype_id('lexicalConceptualResourceVideoInfo', \
                content_info.lexicalConceptualResourceMediaType.lexicalConceptualResourceVideoInfo)
            structures['lexiconImageInfoId'] = get_mediatype_id('lexicalConceptualResourceImageInfo', \
                content_info.lexicalConceptualResourceMediaType.lexicalConceptualResourceImageInfo)
        elif isinstance(content_info, toolServiceInfoType_model):
            structures['toolServiceInfoId'] = content_info.pk
            
        else:
            raise NotImplementedError, "Cannot deal with '{}' resource types just yet".format(content_info.__class__.__name__)
        return structures

    def get_resource_component_id(self, request, resource_id=None):
        '''
        For the given resource (if any) and request, try to get a resource component ID.
        '''
        if resource_id is not None:
            resource = resourceInfoType_model.objects.get(pk=resource_id)
            return resource.resourceComponentType.pk
        if request.method == 'POST':
            return request.POST['resourceComponentId']
        return None

    @method_decorator(permission_required('repository.add_resourceinfotype_model'))
    def add_view(self, request, form_url='', extra_context=None):
        _extra_context = extra_context or {}
        _extra_context.update({'DJANGO_BASE':settings.DJANGO_BASE})
        
        # First, we show the resource type selection view:
        if not request.POST:
            return self.resource_type_selection_view(request, form_url, extra_context)
        # When we get that one back, we create any hidden structures:
        _extra_context.update(self.copy_show_media(request.POST))
        if 'resourceType' in request.POST:
            _structures = self.create_hidden_structures(request)
            _extra_context.update(_structures)
            request.method = 'GET' # simulate a first call to add/
        else:
            _structures = self.get_hidden_structures(request)
            _extra_context.update(_structures)
        # And in any case, we serve the usual change form if we have a post request
        return super(ResourceModelAdmin, self).add_view(request, form_url, _extra_context)


    def save_model(self, request, obj, form, change):
        super(ResourceModelAdmin, self).save_model(request, obj, form, change)
        #update statistics
        if hasattr(obj, 'storage_object') and obj.storage_object is not None:
            saveLRStats("", obj.storage_object.identifier, "", UPDATE_STAT)            
        
    def change_view(self, request, object_id, extra_context=None):
        _extra_context = extra_context or {}
        _extra_context.update({'DJANGO_BASE':settings.DJANGO_BASE})
        _structures = self.get_hidden_structures(request, object_id)
        _extra_context.update(_structures)
        return super(ResourceModelAdmin, self).change_view(request, object_id, _extra_context)
