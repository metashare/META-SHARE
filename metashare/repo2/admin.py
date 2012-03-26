from django.contrib import admin
from metashare.repo2.editor.superadmin import SchemaModelInline
from metashare.repo2.editor.reverse_inline import ReverseModelAdmin

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

admin.site.register(actorInfoType_model, ReverseModelAdmin)
admin.site.register(actualUseInfoType_model, ReverseModelAdmin)
admin.site.register(annotationInfoType_model, ReverseModelAdmin)
admin.site.register(audioClassificationInfoType_model, ReverseModelAdmin)
admin.site.register(audioContentInfoType_model, ReverseModelAdmin)
admin.site.register(audioFormatInfoType_model, ReverseModelAdmin)
admin.site.register(audioSizeInfoType_model, ReverseModelAdmin)
admin.site.register(captureInfoType_model, ReverseModelAdmin)
admin.site.register(characterEncodingInfoType_model, ReverseModelAdmin)
admin.site.register(communicationInfoType_model, ReverseModelAdmin)
admin.site.register(compressionInfoType_model, ReverseModelAdmin)
admin.site.register(corpusAudioInfoType_model, ReverseModelAdmin)
admin.site.register(corpusImageInfoType_model, ReverseModelAdmin)
admin.site.register(corpusInfoType_model, ReverseModelAdmin)
admin.site.register(corpusMediaTypeType_model, ReverseModelAdmin)
admin.site.register(corpusTextInfoType_model, ReverseModelAdmin)
admin.site.register(corpusTextNgramInfoType_model, ReverseModelAdmin)
admin.site.register(corpusTextNumericalInfoType_model, ReverseModelAdmin)
admin.site.register(corpusVideoInfoType_model, ReverseModelAdmin)
admin.site.register(creationInfoType_model, ReverseModelAdmin)
admin.site.register(distributionInfoType_model, ReverseModelAdmin)
admin.site.register(documentInfoType_model, ReverseModelAdmin)
admin.site.register(documentListType_model, ReverseModelAdmin)
admin.site.register(documentationInfoType_model, ReverseModelAdmin)
admin.site.register(domainInfoType_model, ReverseModelAdmin)
admin.site.register(durationOfAudioInfoType_model, ReverseModelAdmin)
admin.site.register(durationOfEffectiveSpeechInfoType_model, ReverseModelAdmin)
admin.site.register(dynamicElementInfoType_model, ReverseModelAdmin)
admin.site.register(foreseenUseInfoType_model, ReverseModelAdmin)
admin.site.register(geographicCoverageInfoType_model, ReverseModelAdmin)
admin.site.register(identificationInfoType_model, ReverseModelAdmin)
admin.site.register(imageClassificationInfoType_model, ReverseModelAdmin)
admin.site.register(imageContentInfoType_model, ReverseModelAdmin)
admin.site.register(imageFormatInfoType_model, ReverseModelAdmin)
admin.site.register(inputInfoType_model, ReverseModelAdmin)
admin.site.register(languageDescriptionEncodingInfoType_model, ReverseModelAdmin)
admin.site.register(languageDescriptionImageInfoType_model, ReverseModelAdmin)
admin.site.register(languageDescriptionInfoType_model, ReverseModelAdmin)
admin.site.register(languageDescriptionMediaTypeType_model, ReverseModelAdmin)
admin.site.register(languageDescriptionOperationInfoType_model, ReverseModelAdmin)
admin.site.register(languageDescriptionPerformanceInfoType_model, ReverseModelAdmin)
admin.site.register(languageDescriptionTextInfoType_model, ReverseModelAdmin)
admin.site.register(languageDescriptionVideoInfoType_model, ReverseModelAdmin)
admin.site.register(languageInfoType_model, ReverseModelAdmin)
admin.site.register(languageVarietyInfoType_model, ReverseModelAdmin)
admin.site.register(lexicalConceptualResourceAudioInfoType_model, ReverseModelAdmin)
admin.site.register(lexicalConceptualResourceEncodingInfoType_model, ReverseModelAdmin)
admin.site.register(lexicalConceptualResourceImageInfoType_model, ReverseModelAdmin)
admin.site.register(lexicalConceptualResourceInfoType_model, ReverseModelAdmin)
admin.site.register(lexicalConceptualResourceMediaTypeType_model, ReverseModelAdmin)
admin.site.register(lexicalConceptualResourceTextInfoType_model, ReverseModelAdmin)
admin.site.register(lexicalConceptualResourceVideoInfoType_model, ReverseModelAdmin)
admin.site.register(licenceInfoType_model, ReverseModelAdmin)
admin.site.register(lingualityInfoType_model, ReverseModelAdmin)
admin.site.register(linkToOtherMediaInfoType_model, ReverseModelAdmin)
admin.site.register(membershipInfoType_model, ReverseModelAdmin)
admin.site.register(metadataInfoType_model, ReverseModelAdmin)
admin.site.register(modalityInfoType_model, ReverseModelAdmin)
admin.site.register(ngramInfoType_model, ReverseModelAdmin)
admin.site.register(organizationInfoType_model, ReverseModelAdmin)
admin.site.register(organizationListType_model, ReverseModelAdmin)
admin.site.register(outputInfoType_model, ReverseModelAdmin)
admin.site.register(participantInfoType_model, ReverseModelAdmin)
admin.site.register(personInfoType_model, ReverseModelAdmin)
admin.site.register(personListType_model, ReverseModelAdmin)
admin.site.register(personSourceSetInfoType_model, ReverseModelAdmin)
admin.site.register(projectInfoType_model, ReverseModelAdmin)
admin.site.register(projectListType_model, ReverseModelAdmin)
admin.site.register(recordingInfoType_model, ReverseModelAdmin)
admin.site.register(relatedLexiconInfoType_model, ReverseModelAdmin)
admin.site.register(relationInfoType_model, ReverseModelAdmin)
admin.site.register(resolutionInfoType_model, ReverseModelAdmin)
admin.site.register(resourceComponentTypeType_model, ReverseModelAdmin)
admin.site.register(resourceCreationInfoType_model, ReverseModelAdmin)
admin.site.register(resourceDocumentationInfoType_model, ReverseModelAdmin)
admin.site.register(resourceInfoType_model, ReverseModelAdmin)
admin.site.register(runningEnvironmentInfoType_model, ReverseModelAdmin)
admin.site.register(settingInfoType_model, ReverseModelAdmin)
admin.site.register(sizeInfoType_model, ReverseModelAdmin)
admin.site.register(staticElementInfoType_model, ReverseModelAdmin)
admin.site.register(targetResourceInfoType_model, ReverseModelAdmin)
admin.site.register(textClassificationInfoType_model, ReverseModelAdmin)
admin.site.register(textFormatInfoType_model, ReverseModelAdmin)
admin.site.register(textNumericalContentInfoType_model, ReverseModelAdmin)
admin.site.register(textNumericalFormatInfoType_model, ReverseModelAdmin)
admin.site.register(timeCoverageInfoType_model, ReverseModelAdmin)
admin.site.register(toolServiceCreationInfoType_model, ReverseModelAdmin)
admin.site.register(toolServiceEvaluationInfoType_model, ReverseModelAdmin)
admin.site.register(toolServiceInfoType_model, ReverseModelAdmin)
admin.site.register(toolServiceOperationInfoType_model, ReverseModelAdmin)
admin.site.register(usageInfoType_model, ReverseModelAdmin)
admin.site.register(validationInfoType_model, ReverseModelAdmin)
admin.site.register(versionInfoType_model, ReverseModelAdmin)
admin.site.register(videoClassificationInfoType_model, ReverseModelAdmin)
admin.site.register(videoContentInfoType_model, ReverseModelAdmin)
admin.site.register(videoFormatInfoType_model, ReverseModelAdmin)


from metashare.repo2.editor import manual_admin_registration
manual_admin_registration.register()

