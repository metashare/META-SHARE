'''
This file contains the manually chosen admin forms, as needed for an easy-to-use
editor.
'''
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.formsets import all_valid
from django.http import Http404, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.utils.encoding import force_unicode, force_text
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect

from metashare.repository.editor import admin_site as editor_site
from metashare.repository.editor.related_mixin import RelatedAdminMixin
from metashare.repository.editor.related_objects import AdminRelatedInfo
from metashare.repository.editor.resource_editor import ResourceModelAdmin, \
    LicenceModelAdmin
from metashare.repository.editor.superadmin import SchemaModelAdmin, \
    IS_POPUP_O2M_VAR
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
        if IS_POPUP_O2M_VAR in request.REQUEST:
            caller = None
            if '_caller' in request.REQUEST:
                caller = request.REQUEST['_caller']
            return self.edit_response_close_popup_magic_o2m(obj, caller)
        if IS_POPUP_VAR in request.REQUEST:
            if request.POST.has_key("_continue"):
                return self.save_and_continue_in_popup(obj, request)
            return self.edit_response_close_popup_magic(obj)
        else:
            return super(DocumentUnstructuredStringModelAdmin, self).response_change(request, obj)

    @csrf_protect_m
    @transaction.atomic
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        This follows closely the base implementation from Django 1.7's
        django.contrib.admin.options.ModelAdmin with the explicitly marked
        modifications.
        """
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)

        model = self.model
        opts = model._meta
        add = object_id is None

        if add:
            if not self.has_add_permission(request):
                raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id))

            if not self.has_change_permission(request, obj):
                raise PermissionDenied

            if obj is None:
                raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
                    'name': force_text(opts.verbose_name), 'key': escape(object_id)})

            if request.method == 'POST' and "_saveasnew" in request.POST:
                return self.add_view(request, form_url=reverse('admin:%s_%s_add' % (
                    opts.app_label, opts.model_name),
                    current_app=self.admin_site.name))

        #### begin modification ####
        # make sure that the user has a full session length time for the current
        # edit activity
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        #### end modification ####

        ModelForm = self.get_form(request, obj)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=not add)
            else:
                form_validated = False
                new_object = form.instance
            formsets, inline_instances = self._create_formsets(request, new_object, change=not add)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, not add)
                self.save_related(request, form, formsets, not add)
                if add:
                    self.log_addition(request, new_object)
                    return self.response_add(request, new_object)
                else:
                    change_message = self.construct_change_message(request, form, formsets)
                    self.log_change(request, new_object, change_message)
                    return self.response_change(request, new_object)
        else:
            if add:
                initial = self.get_changeform_initial_data(request)
                form = ModelForm(initial=initial)
                formsets, inline_instances = self._create_formsets(request, self.model(), change=False)
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(request, obj, change=True)

        adminForm = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request, obj)),
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + adminForm.media

        inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
        for inline_formset in inline_formsets:
            media = media + inline_formset.media

        context = dict(self.admin_site.each_context(),
            title=(_('Add %s') if add else _('Change %s')) % force_text(opts.verbose_name),
            adminform=adminForm,
            object_id=object_id,
            original=obj,
            is_popup=(IS_POPUP_VAR in request.REQUEST or \
                      IS_POPUP_O2M_VAR in request.REQUEST),
            to_field=to_field,
            media=media,
            inline_admin_formsets=inline_formsets,
            errors=helpers.AdminErrorList(form, formsets),
            preserved_filters=self.get_preserved_filters(request),
            kb_link=settings.KNOWLEDGE_BASE_URL,
            app_label=opts.app_label,
            show_delete=False,
        )

        context.update(extra_context or {})
        return self.render_change_form(request, context, add=add, change=not add, obj=obj, form_url=form_url)

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

    

