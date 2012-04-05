from django.contrib import admin
from metashare.repo2.editor.superadmin import SchemaModelAdmin
from metashare.repo2.editor.inlines import SchemaModelInline

from metashare.repo2.models import documentUnstructuredString_model
admin.site.register(documentUnstructuredString_model)


from metashare.repo2.models import \
    actorInfoType_model, \
    actualUseInfoType_model, \
    annotationInfoType_model, \
    audioClassificationInfoType_model, \
    audioContentInfoType_model, \
    audioFormatInfoType_model, \
    audioSizeInfoType_model, \
    captureInfoType_model, \
    characterEncodingInfoType_model, \
    communicationInfoType_model, \
    compressionInfoType_model, \
    corpusAudioInfoType_model, \
    corpusImageInfoType_model, \
    corpusInfoType_model, \
    corpusMediaTypeType_model, \
    corpusTextInfoType_model, \
    corpusTextNgramInfoType_model, \
    corpusTextNumericalInfoType_model, \
    corpusVideoInfoType_model, \
    creationInfoType_model, \
    distributionInfoType_model, \
    documentInfoType_model, \
    documentListType_model, \
    documentationInfoType_model, \
    domainInfoType_model, \
    durationOfAudioInfoType_model, \
    durationOfEffectiveSpeechInfoType_model, \
    dynamicElementInfoType_model, \
    foreseenUseInfoType_model, \
    geographicCoverageInfoType_model, \
    identificationInfoType_model, \
    imageClassificationInfoType_model, \
    imageContentInfoType_model, \
    imageFormatInfoType_model, \
    inputInfoType_model, \
    languageDescriptionEncodingInfoType_model, \
    languageDescriptionImageInfoType_model, \
    languageDescriptionInfoType_model, \
    languageDescriptionMediaTypeType_model, \
    languageDescriptionOperationInfoType_model, \
    languageDescriptionPerformanceInfoType_model, \
    languageDescriptionTextInfoType_model, \
    languageDescriptionVideoInfoType_model, \
    languageInfoType_model, \
    languageVarietyInfoType_model, \
    lexicalConceptualResourceAudioInfoType_model, \
    lexicalConceptualResourceEncodingInfoType_model, \
    lexicalConceptualResourceImageInfoType_model, \
    lexicalConceptualResourceInfoType_model, \
    lexicalConceptualResourceMediaTypeType_model, \
    lexicalConceptualResourceTextInfoType_model, \
    lexicalConceptualResourceVideoInfoType_model, \
    licenceInfoType_model, \
    lingualityInfoType_model, \
    linkToOtherMediaInfoType_model, \
    membershipInfoType_model, \
    metadataInfoType_model, \
    modalityInfoType_model, \
    ngramInfoType_model, \
    organizationInfoType_model, \
    organizationListType_model, \
    outputInfoType_model, \
    participantInfoType_model, \
    personInfoType_model, \
    personListType_model, \
    personSourceSetInfoType_model, \
    projectInfoType_model, \
    projectListType_model, \
    recordingInfoType_model, \
    relatedLexiconInfoType_model, \
    relationInfoType_model, \
    resolutionInfoType_model, \
    resourceComponentTypeType_model, \
    resourceCreationInfoType_model, \
    resourceDocumentationInfoType_model, \
    resourceInfoType_model, \
    runningEnvironmentInfoType_model, \
    settingInfoType_model, \
    sizeInfoType_model, \
    staticElementInfoType_model, \
    targetResourceInfoType_model, \
    textClassificationInfoType_model, \
    textFormatInfoType_model, \
    textNumericalContentInfoType_model, \
    textNumericalFormatInfoType_model, \
    timeCoverageInfoType_model, \
    toolServiceCreationInfoType_model, \
    toolServiceEvaluationInfoType_model, \
    toolServiceInfoType_model, \
    toolServiceOperationInfoType_model, \
    usageInfoType_model, \
    validationInfoType_model, \
    versionInfoType_model, \
    videoClassificationInfoType_model, \
    videoContentInfoType_model, \
    videoFormatInfoType_model


# pylint: disable-msg=C0103
class audioSizeInfo_model_inline(SchemaModelInline):
    model = audioSizeInfoType_model
    collapse = False

# pylint: disable-msg=C0103
class corpusInfo_model_inline(SchemaModelInline):
    model = corpusInfoType_model
    collapse = False

# pylint: disable-msg=C0103
class corpusTextInfo_model_inline(SchemaModelInline):
    model = corpusTextInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class corpusVideoInfo_model_inline(SchemaModelInline):
    model = corpusVideoInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class documentInfo_model_inline(SchemaModelInline):
    model = documentInfoType_model
    collapse = False

# pylint: disable-msg=C0103
class durationOfAudioInfo_model_inline(SchemaModelInline):
    model = durationOfAudioInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class durationOfEffectiveSpeechInfo_model_inline(SchemaModelInline):
    model = durationOfEffectiveSpeechInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class foreseenUseInfo_model_inline(SchemaModelInline):
    model = foreseenUseInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class imageClassificationInfo_model_inline(SchemaModelInline):
    model = imageClassificationInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class languageDescriptionInfo_model_inline(SchemaModelInline):
    model = languageDescriptionInfoType_model
    collapse = False

# pylint: disable-msg=C0103
class lexicalConceptualResourceInfo_model_inline(SchemaModelInline):
    model = lexicalConceptualResourceInfoType_model
    collapse = False

# pylint: disable-msg=C0103
class licenceInfo_model_inline(SchemaModelInline):
    model = licenceInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class organizationInfo_model_inline(SchemaModelInline):
    model = organizationInfoType_model
    collapse = False

# pylint: disable-msg=C0103
class participantInfo_model_inline(SchemaModelInline):
    model = participantInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class personInfo_model_inline(SchemaModelInline):
    model = personInfoType_model
    collapse = False

# pylint: disable-msg=C0103
class relationInfo_model_inline(SchemaModelInline):
    model = relationInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class textNumericalFormatInfo_model_inline(SchemaModelInline):
    model = textNumericalFormatInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class toolServiceInfo_model_inline(SchemaModelInline):
    model = toolServiceInfoType_model
    collapse = False

# pylint: disable-msg=C0103
class validationInfo_model_inline(SchemaModelInline):
    model = validationInfoType_model
    collapse = True

# pylint: disable-msg=C0103
class videoClassificationInfo_model_inline(SchemaModelInline):
    model = videoClassificationInfoType_model
    collapse = True

admin.site.register(actorInfoType_model, SchemaModelAdmin)
admin.site.register(actualUseInfoType_model, SchemaModelAdmin)
admin.site.register(annotationInfoType_model, SchemaModelAdmin)
admin.site.register(audioClassificationInfoType_model, SchemaModelAdmin)
admin.site.register(audioContentInfoType_model, SchemaModelAdmin)
admin.site.register(audioFormatInfoType_model, SchemaModelAdmin)
admin.site.register(audioSizeInfoType_model, SchemaModelAdmin)
admin.site.register(captureInfoType_model, SchemaModelAdmin)
admin.site.register(characterEncodingInfoType_model, SchemaModelAdmin)
admin.site.register(communicationInfoType_model, SchemaModelAdmin)
admin.site.register(compressionInfoType_model, SchemaModelAdmin)
admin.site.register(corpusAudioInfoType_model, SchemaModelAdmin)
admin.site.register(corpusImageInfoType_model, SchemaModelAdmin)
admin.site.register(corpusInfoType_model, SchemaModelAdmin)
admin.site.register(corpusMediaTypeType_model, SchemaModelAdmin)
admin.site.register(corpusTextInfoType_model, SchemaModelAdmin)
admin.site.register(corpusTextNgramInfoType_model, SchemaModelAdmin)
admin.site.register(corpusTextNumericalInfoType_model, SchemaModelAdmin)
admin.site.register(corpusVideoInfoType_model, SchemaModelAdmin)
admin.site.register(creationInfoType_model, SchemaModelAdmin)
admin.site.register(distributionInfoType_model, SchemaModelAdmin)
admin.site.register(documentInfoType_model, SchemaModelAdmin)
admin.site.register(documentListType_model, SchemaModelAdmin)
admin.site.register(documentationInfoType_model, SchemaModelAdmin)
admin.site.register(domainInfoType_model, SchemaModelAdmin)
admin.site.register(durationOfAudioInfoType_model, SchemaModelAdmin)
admin.site.register(durationOfEffectiveSpeechInfoType_model, SchemaModelAdmin)
admin.site.register(dynamicElementInfoType_model, SchemaModelAdmin)
admin.site.register(foreseenUseInfoType_model, SchemaModelAdmin)
admin.site.register(geographicCoverageInfoType_model, SchemaModelAdmin)
admin.site.register(identificationInfoType_model, SchemaModelAdmin)
admin.site.register(imageClassificationInfoType_model, SchemaModelAdmin)
admin.site.register(imageContentInfoType_model, SchemaModelAdmin)
admin.site.register(imageFormatInfoType_model, SchemaModelAdmin)
admin.site.register(inputInfoType_model, SchemaModelAdmin)
admin.site.register(languageDescriptionEncodingInfoType_model, SchemaModelAdmin)
admin.site.register(languageDescriptionImageInfoType_model, SchemaModelAdmin)
admin.site.register(languageDescriptionInfoType_model, SchemaModelAdmin)
admin.site.register(languageDescriptionMediaTypeType_model, SchemaModelAdmin)
admin.site.register(languageDescriptionOperationInfoType_model, SchemaModelAdmin)
admin.site.register(languageDescriptionPerformanceInfoType_model, SchemaModelAdmin)
admin.site.register(languageDescriptionTextInfoType_model, SchemaModelAdmin)
admin.site.register(languageDescriptionVideoInfoType_model, SchemaModelAdmin)
admin.site.register(languageInfoType_model, SchemaModelAdmin)
admin.site.register(languageVarietyInfoType_model, SchemaModelAdmin)
admin.site.register(lexicalConceptualResourceAudioInfoType_model, SchemaModelAdmin)
admin.site.register(lexicalConceptualResourceEncodingInfoType_model, SchemaModelAdmin)
admin.site.register(lexicalConceptualResourceImageInfoType_model, SchemaModelAdmin)
admin.site.register(lexicalConceptualResourceInfoType_model, SchemaModelAdmin)
admin.site.register(lexicalConceptualResourceMediaTypeType_model, SchemaModelAdmin)
admin.site.register(lexicalConceptualResourceTextInfoType_model, SchemaModelAdmin)
admin.site.register(lexicalConceptualResourceVideoInfoType_model, SchemaModelAdmin)
admin.site.register(licenceInfoType_model, SchemaModelAdmin)
admin.site.register(lingualityInfoType_model, SchemaModelAdmin)
admin.site.register(linkToOtherMediaInfoType_model, SchemaModelAdmin)
admin.site.register(membershipInfoType_model, SchemaModelAdmin)
admin.site.register(metadataInfoType_model, SchemaModelAdmin)
admin.site.register(modalityInfoType_model, SchemaModelAdmin)
admin.site.register(ngramInfoType_model, SchemaModelAdmin)
admin.site.register(organizationInfoType_model, SchemaModelAdmin)
admin.site.register(organizationListType_model, SchemaModelAdmin)
admin.site.register(outputInfoType_model, SchemaModelAdmin)
admin.site.register(participantInfoType_model, SchemaModelAdmin)
admin.site.register(personInfoType_model, SchemaModelAdmin)
admin.site.register(personListType_model, SchemaModelAdmin)
admin.site.register(personSourceSetInfoType_model, SchemaModelAdmin)
admin.site.register(projectInfoType_model, SchemaModelAdmin)
admin.site.register(projectListType_model, SchemaModelAdmin)
admin.site.register(recordingInfoType_model, SchemaModelAdmin)
admin.site.register(relatedLexiconInfoType_model, SchemaModelAdmin)
admin.site.register(relationInfoType_model, SchemaModelAdmin)
admin.site.register(resolutionInfoType_model, SchemaModelAdmin)
admin.site.register(resourceComponentTypeType_model, SchemaModelAdmin)
admin.site.register(resourceCreationInfoType_model, SchemaModelAdmin)
admin.site.register(resourceDocumentationInfoType_model, SchemaModelAdmin)
admin.site.register(resourceInfoType_model, SchemaModelAdmin)
admin.site.register(runningEnvironmentInfoType_model, SchemaModelAdmin)
admin.site.register(settingInfoType_model, SchemaModelAdmin)
admin.site.register(sizeInfoType_model, SchemaModelAdmin)
admin.site.register(staticElementInfoType_model, SchemaModelAdmin)
admin.site.register(targetResourceInfoType_model, SchemaModelAdmin)
admin.site.register(textClassificationInfoType_model, SchemaModelAdmin)
admin.site.register(textFormatInfoType_model, SchemaModelAdmin)
admin.site.register(textNumericalContentInfoType_model, SchemaModelAdmin)
admin.site.register(textNumericalFormatInfoType_model, SchemaModelAdmin)
admin.site.register(timeCoverageInfoType_model, SchemaModelAdmin)
admin.site.register(toolServiceCreationInfoType_model, SchemaModelAdmin)
admin.site.register(toolServiceEvaluationInfoType_model, SchemaModelAdmin)
admin.site.register(toolServiceInfoType_model, SchemaModelAdmin)
admin.site.register(toolServiceOperationInfoType_model, SchemaModelAdmin)
admin.site.register(usageInfoType_model, SchemaModelAdmin)
admin.site.register(validationInfoType_model, SchemaModelAdmin)
admin.site.register(versionInfoType_model, SchemaModelAdmin)
admin.site.register(videoClassificationInfoType_model, SchemaModelAdmin)
admin.site.register(videoContentInfoType_model, SchemaModelAdmin)
admin.site.register(videoFormatInfoType_model, SchemaModelAdmin)


from metashare.repo2.editor import manual_admin_registration
manual_admin_registration.register()

