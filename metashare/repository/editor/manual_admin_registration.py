'''
This file contains the manually chosen admin forms, as needed for an easy-to-use editor.
'''

from django.contrib import admin
# pylint: disable-msg=W0611
from metashare.repository.models import resourceInfoType_model, \
    identificationInfoType_model, \
    metadataInfoType_model, communicationInfoType_model, \
    validationInfoType_model, relationInfoType_model, licenceInfoType_model, \
    foreseenUseInfoType_model, corpusMediaTypeType_model, \
    corpusTextInfoType_model, corpusVideoInfoType_model, audioSizeInfoType_model, \
    durationOfAudioInfoType_model, durationOfEffectiveSpeechInfoType_model, \
    textNumericalFormatInfoType_model, videoClassificationInfoType_model, \
    imageClassificationInfoType_model, \
    participantInfoType_model, corpusAudioInfoType_model,\
    corpusImageInfoType_model, corpusTextNumericalInfoType_model,\
    corpusTextNgramInfoType_model, languageDescriptionInfoType_model,\
    languageDescriptionTextInfoType_model,\
    languageDescriptionVideoInfoType_model,\
    languageDescriptionImageInfoType_model,\
    lexicalConceptualResourceInfoType_model,\
    lexicalConceptualResourceTextInfoType_model,\
    lexicalConceptualResourceAudioInfoType_model,\
    lexicalConceptualResourceVideoInfoType_model,\
    lexicalConceptualResourceImageInfoType_model, toolServiceInfoType_model
from metashare.repository.editor.superadmin import SchemaModelAdmin
from metashare.repository.editor import admin_site as editor_site
from metashare.repository.editor.corpus_editor import CorpusAudioForm
from metashare.repository.editor.resource_editor import ResourceModelAdmin




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
    form = CorpusAudioForm
    show_tabbed_fieldsets = True
    
    def __init__(self, model, admin_site):
        super(CorpusAudioModelAdmin, self).__init__(model, admin_site)
        try:
            for instance in self.inline_instances:
                if instance.model().__class__.__name__ == 'audioSizeInfoType_model':
                    self.inline_instances.remove(instance)
                    break
        except:
            pass
        
    def build_fieldsets_from_schema(self, include_inlines=False, inlines=()):
        fieldsets = super(CorpusAudioModelAdmin, self).build_fieldsets_from_schema(include_inlines, inlines)
        for fieldset in fieldsets:
            # name = fieldset[0]
            values = fieldset[1]
            try:
                field_list = values['fields']
                if u'_audiosizeinfotype_model_set' in field_list:
                    index = field_list.index(u'_audiosizeinfotype_model_set')
                    field_list.remove(u'_audiosizeinfotype_model_set')
                    # pylint: disable-msg=E1101
                    for new_field in self.form.declared_fields:
                        field_list.insert(index, new_field)
                        index = index + 1
            except:
                continue
                
        return fieldsets
    
    def save_model(self, request, obj, form, change):
        super(CorpusAudioModelAdmin, self).save_model(request, obj, form, change)
        form.save_audio_sizes()

            
# Models which are always rendered inline so they don't need their own admin form:
purely_inline_models = (
    identificationInfoType_model,
#    distributionInfoType_model,
    metadataInfoType_model,
    communicationInfoType_model,
    validationInfoType_model,
    relationInfoType_model,
    licenceInfoType_model,
    foreseenUseInfoType_model,
    corpusMediaTypeType_model,
 #   corpusTextInfoType_model,
 #   corpusVideoInfoType_model,
    audioSizeInfoType_model,
    durationOfAudioInfoType_model,
    durationOfEffectiveSpeechInfoType_model,
    textNumericalFormatInfoType_model,
    videoClassificationInfoType_model,
    imageClassificationInfoType_model,
#    languageVarietyInfoType_model,
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

    

