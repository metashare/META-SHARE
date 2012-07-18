'''
This file contains the manually chosen admin forms, as needed for an easy-to-use
editor.
'''
from django.contrib import admin

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
    languageDescriptionTextInfoType_model, \
    languageDescriptionVideoInfoType_model, \
    languageDescriptionImageInfoType_model, \
    lexicalConceptualResourceInfoType_model, \
    lexicalConceptualResourceTextInfoType_model, \
    lexicalConceptualResourceAudioInfoType_model, \
    lexicalConceptualResourceVideoInfoType_model, \
    lexicalConceptualResourceImageInfoType_model, toolServiceInfoType_model, \
    licenceInfoType_model, personInfoType_model, projectInfoType_model, \
    documentInfoType_model, organizationInfoType_model


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

class PersonModelAdmin(SchemaModelAdmin):
    exclude = ('source_url', 'copy_status')

class OrganizationModelAdmin(SchemaModelAdmin):
    exclude = ('source_url', 'copy_status')

class ProjectModelAdmin(SchemaModelAdmin):
    exclude = ('source_url', 'copy_status')

class DocumentModelAdmin(SchemaModelAdmin):
    exclude = ('source_url', 'copy_status')


# Models which are always rendered inline so they don't need their own admin form:
purely_inline_models = (
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

    

