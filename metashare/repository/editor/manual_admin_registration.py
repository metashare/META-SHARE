'''
This file contains the manually chosen admin forms, as needed for an easy-to-use
editor.
'''
from django.contrib import admin
from django.conf import settings

from metashare.repository.editor import admin_site as editor_site
from metashare.repository.editor.resource_editor import ResourceModelAdmin, \
    LicenceModelAdmin
from metashare.repository.editor.superadmin import SchemaModelAdmin
from metashare.repository.models import resourceInfoType_model, \
    identificationInfoType_model, metadataInfoType_model, \
    communicationInfoType_model, validationInfoType_model, \
    relationInfoType_model, foreseenUseInfoType_model, \
    corpusMediaTypeType_model, corpusTextInfoType_model, \
    corpusVideoInfoType_model, textNumericalFormatInfoType_model, \
    videoClassificationInfoType_model, imageClassificationInfoType_model, \
    participantInfoType_model, corpusAudioInfoType_model, \
    corpusImageInfoType_model, corpusTextNumericalInfoType_model, \
    corpusTextNgramInfoType_model, languageDescriptionInfoType_model, \
    languageDescriptionTextInfoType_model, actualUseInfoType_model, \
    languageDescriptionVideoInfoType_model, \
    languageDescriptionImageInfoType_model, \
    lexicalConceptualResourceInfoType_model, \
    lexicalConceptualResourceTextInfoType_model, \
    lexicalConceptualResourceAudioInfoType_model, \
    lexicalConceptualResourceVideoInfoType_model, \
    lexicalConceptualResourceImageInfoType_model, toolServiceInfoType_model, \
    licenceInfoType_model, personInfoType_model, projectInfoType_model, \
    documentInfoType_model, organizationInfoType_model, \
    documentUnstructuredString_model
from metashare.repository.editor.related_mixin import RelatedAdminMixin
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.utils.decorators import method_decorator
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.utils.html import escape
from django.utils.encoding import force_unicode
from django.http import Http404
from django.utils.safestring import mark_safe
from django.contrib.admin import helpers
from django.utils.translation import ugettext as _
from metashare.repository.editor.related_objects import AdminRelatedInfo

csrf_protect_m = method_decorator(csrf_protect)

# Custom admin classes

class CorpusTextInfoAdmin(SchemaModelAdmin):
    hidden_fields = ('back_to_corpusmediatypetype_model', )
    show_tabbed_fieldsets = True

class CorpusVideoInfoAdmin(SchemaModelAdmin):
    hidden_fields = ('back_to_corpusmediatypetype_model', )
    show_tabbed_fieldsets = True

class GenericTabbedAdmin(SchemaModelAdmin):
    show_tabbed_fieldsets = True

class LexicalConceptualResourceInfoAdmin(SchemaModelAdmin):
    readonly_fields = ('lexicalConceptualResourceMediaType', )
    show_tabbed_fieldsets = True

class LanguageDescriptionInfoAdmin(SchemaModelAdmin):
    readonly_fields = ('languageDescriptionMediaType', )
    show_tabbed_fieldsets = True

class CorpusAudioModelAdmin(SchemaModelAdmin):
    show_tabbed_fieldsets = True

class PersonModelAdmin(AdminRelatedInfo, SchemaModelAdmin):
    exclude = ('source_url', 'copy_status')
    list_display = ('instance_data', 'num_related_resources', 'related_resources')
    
    def instance_data(self, obj):
        return obj.__unicode__()
    instance_data.short_description = _('Person')

class OrganizationModelAdmin(AdminRelatedInfo, SchemaModelAdmin):
    exclude = ('source_url', 'copy_status')
    list_display = ('instance_data', 'num_related_resources', 'related_resources')
    
    def instance_data(self, obj):
        return obj.__unicode__()
    instance_data.short_description = _('Organization')

class ProjectModelAdmin(AdminRelatedInfo, SchemaModelAdmin):
    exclude = ('source_url', 'copy_status')
    list_display = ('instance_data', 'num_related_resources', 'related_resources')
    
    def instance_data(self, obj):
        return obj.__unicode__()
    instance_data.short_description = _('Project')

class DocumentModelAdmin(AdminRelatedInfo, SchemaModelAdmin):
    exclude = ('source_url', 'copy_status')
    list_display = ('instance_data', 'num_related_resources', 'related_resources')
    
    def instance_data(self, obj):
        return obj.__unicode__()
    instance_data.short_description = _('Document')

class DocumentUnstructuredStringModelAdmin(admin.ModelAdmin, RelatedAdminMixin):
    def response_change(self, request, obj):
        '''
        Response sent after a successful submission of a change form.
        We customize this to allow closing edit popups in the same way
        as response_add deals with add popups.
        '''
        if '_popup_o2m' in request.REQUEST:
            caller = None
            if '_caller' in request.REQUEST:
                caller = request.REQUEST['_caller']
            return self.edit_response_close_popup_magic_o2m(obj, caller)
        if '_popup' in request.REQUEST:
            if request.POST.has_key("_continue"):
                return self.save_and_continue_in_popup(obj, request)
            return self.edit_response_close_popup_magic(obj)
        else:
            return super(DocumentUnstructuredStringModelAdmin, self).response_change(request, obj)

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        The 'change' admin view for this model.
        This follows closely the base implementation from Django 1.4's
        django.contrib.admin.options.ModelAdmin,
        with the explicitly marked modifications.
        """
        # pylint: disable-msg=C0103
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        #### begin modification ####
        # make sure that the user has a full session length time for the current
        # edit activity
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        #### end modification ####

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if request.method == 'POST' and "_saveasnew" in request.POST:
            return self.add_view(request, form_url=reverse('admin:%s_%s_add' %
                                    (opts.app_label, opts.module_name),
                                    current_app=self.admin_site.name))

        ModelForm = self.get_form(request, obj)
        formsets = []
        inline_instances = self.get_inline_instances(request)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj

            if form_validated:
                #### begin modification ####
                self.save_model(request, new_object, form, True)
                #### end modification ####

                change_message = self.construct_change_message(request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = ModelForm(instance=obj)

        #### begin modification ####
        media = self.media or []
        #### end modification ####
        inline_admin_formsets = []

        #### begin modification ####
        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self)
        media = media + adminForm.media
        #### end modification ####

        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST or \
                        "_popup_o2m" in request.REQUEST,
            'media': media,
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'app_label': opts.app_label,
            'kb_link': settings.KNOWLEDGE_BASE_URL,
            'comp_name': _('%s') % force_unicode(opts.verbose_name),
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj, form_url=form_url)

# Models which are always rendered inline so they don't need their own admin form:
purely_inline_models = (
    actualUseInfoType_model,
    identificationInfoType_model,
    metadataInfoType_model,
    communicationInfoType_model,
    validationInfoType_model,
    relationInfoType_model,
    foreseenUseInfoType_model,
    corpusMediaTypeType_model,
    textNumericalFormatInfoType_model,
    videoClassificationInfoType_model,
    imageClassificationInfoType_model,
    participantInfoType_model,
)

custom_admin_classes = {
    resourceInfoType_model: ResourceModelAdmin,
    corpusAudioInfoType_model: CorpusAudioModelAdmin,
    corpusTextInfoType_model: CorpusTextInfoAdmin,
    corpusVideoInfoType_model: CorpusVideoInfoAdmin,
    corpusImageInfoType_model: GenericTabbedAdmin,
    corpusTextNumericalInfoType_model: GenericTabbedAdmin,
    corpusTextNgramInfoType_model: GenericTabbedAdmin,
    languageDescriptionInfoType_model: LanguageDescriptionInfoAdmin,
    languageDescriptionTextInfoType_model: GenericTabbedAdmin,
    languageDescriptionVideoInfoType_model: GenericTabbedAdmin,
    languageDescriptionImageInfoType_model: GenericTabbedAdmin,
    lexicalConceptualResourceInfoType_model: LexicalConceptualResourceInfoAdmin,
    lexicalConceptualResourceTextInfoType_model: GenericTabbedAdmin,
    lexicalConceptualResourceAudioInfoType_model: GenericTabbedAdmin,
    lexicalConceptualResourceVideoInfoType_model: GenericTabbedAdmin,
    lexicalConceptualResourceImageInfoType_model: GenericTabbedAdmin,
    toolServiceInfoType_model: GenericTabbedAdmin,
    licenceInfoType_model: LicenceModelAdmin,
    personInfoType_model: PersonModelAdmin, 
    organizationInfoType_model: OrganizationModelAdmin, 
    projectInfoType_model: ProjectModelAdmin, 
    documentInfoType_model: DocumentModelAdmin,
    documentUnstructuredString_model: DocumentUnstructuredStringModelAdmin, 
}

def register():
    '''
    Manual improvements over the automatically generated admin registration.
    This presupposes the automatic parts have already been run.
    '''
    for model in purely_inline_models:
        admin.site.unregister(model)
    
    
    for modelclass, adminclass in custom_admin_classes.items():
        admin.site.unregister(modelclass)
        admin.site.register(modelclass, adminclass)
        
    # And finally, make sure that our editor has the exact same model/admin pairs registered:
    for modelclass, adminobject in admin.site._registry.items():
        editor_site.register(modelclass, adminobject.__class__)

    

