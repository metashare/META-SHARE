# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from metashare.bcp47 import iana
from metashare.repository.migrations import write_to_resources_to_be_modified_file
from metashare.settings import ROOT_PATH

LANGUAGENAME_MAP = {u'Englishu': [u'English', u''], u'Mandarin': [u'Mandarin Chinese', u''],
    u'Arab': [u'Arabic', u''], u'Hill Mari': [u'Western Mari', u''], u'Basque\xa0': [u'Basque', u''],
    u'Nepali': [u'Nepali (macrolanguage)',u''], u'Modern (-1453)': [u'Modern Greek (1453-)', u''],
    u'American English': [u'English', u'United States'],
    u'Izhorian': [u'Ingrian', u''], u'Romanian': [u'Romanian; Moldavian; Moldovan', u''],
    u'Bokm\\xe5l, Norwegian; Norwegian Bokm\\xe5l': [u'Norwegian Bokm\xe5l', u''],
    u'Norwegian, Norwegian Bokm\xe5l': [u'Norwegian Bokm\xe5l', u''],
    u'Occitan': [u'Occitan (post 1500)', u''],  u'Olonets': [u'Livvi', u''],
    u'Welsh - Cymraeg': [u'Welsh', u''], u'Slovakian': [u'Slovak', u''],
    u'Sinhalese': [u'Sinhala; Sinhalese', u''], u'Finland Swedish': [u'Swedish', u'Finland'],
    u'Slovene': [u'Slovenian', u''], u'Gaelic': [u'Scottish Gaelic; Gaelic', u''],
    u'Gaelic; Scottish Gaelic': [u'Scottish Gaelic; Gaelic', u''],
    u"Pedi; Sepedi; Northern Sotho": [u"Pedi, Northern Sotho, Sepedi", u""],
    u'Modern (1453-)Greek': [u'Modern Greek (1453-)', u''], u'Modern Greek': [u'Modern Greek (1453-)', u''],
    u'Greek': [u'Modern Greek (1453-)', u''],
    u'Greek, Ancient (to 1453)': [u'Ancient Greek (to 1453)', u''],
    u'No Language': [u'No linguistic content; Not applicable', u''], u'Oriya': [u'Oriya (macrolanguage)', u''],
    u'Greek, Modern (1453-)': [u'Modern Greek (1453-)', u''], u'Anatolian languages': [u'Multiple languages', u''],
    u'Tundra Nenets': [u'Nenets', u''], u'French, Middle (ca. 1400-1600)': [u'Middle French (ca. 1400-1600)', u''],
    u'Catalan': [u'Catalan; Valencian', u''], u'Malay': [u'Malay (macrolanguage)', u''],
    u'European Portuguese': [u'Portuguese', u'Europe'],
    u'Glosses (German)': [u'German', u''], u'Ingrian Finnish': [u'Finnish', u''],
    u'Chukchi': [u'Chukot', u''], u'Norwegian Nynorsk; Nynorsk, Norwegian': [u'Norwegian Nynorsk', u''],
    u'Nanay': [u'Nanai', u''], u'Nordic Sami': [u'Northern Sami', u''],
    u'Tocharian languages': [u'Tokharian A', u''],
    u'Old Church Slavonic': [u'Church Slavic; Church Slavonic; Old Bulgarian; Old Church Slavonic; Old Slavonic', u''],
    u'Romanian': [u'Romanian; Moldavian; Moldovan', u''], u'Catalan': [u'Catalan; Valencian', u''],
    u'Belarussian': [u'Belarusian', u''], u'Dutch': [u'Dutch; Flemish', u''],
    u'English Sign Language': [u'British Sign Language', u''],
    u'Euskera': [u'Basque', u''], u'Finnish\xa0': [u'Finnish', u''],
    u'Gallegan': [u'Galician', u''], u'Norwegian bokm\xe5l': [u'Norwegian Bokm\xe5l', u''],
    u'castellano': [u'Spanish; Castilian', u''],
    u'Rumanian': [u'Romanian; Moldavian; Moldovan', u''],
    u'Bokm\xe5l, Norwegian; Norwegian Bokm\xe5l': [u'Norwegian Bokm\xe5l', u''],
    u'Norvegian': [u'Norwegian', u''], u'Asturian': [u'Asturian; Asturleonese; Bable; Leonese', u''],
    u'Asturian; Bable; Leonese; Asturleonese': [u'Asturian; Asturleonese; Bable; Leonese', u''],
    u'Panjabi': [u'Panjabi; Punjabi', u''],
    u'Spanish': [u'Spanish; Castilian', u''], u'pt-BR': [u'Portuguese', u'Brazil'],
    u"Low German; Low Saxon; German, Low; Saxon, Low": [u"Low German, Low Saxon", u""],
    u'portuguese': [u'Portuguese', u""], u'italian': [u'Italian', u''],
    u'Greek sign language': [u'Greek Sign Language', u''],
    u"Greek, Modern (-1453)": [u"Modern Greek (1453-)", u""],
    u'Sami': [u'Sami languages', u''], u'english': [u'English', u''],
    u'Komi Zyrian': [u'Komi-Zyrian', u''], u"en": [u"English", u""],
    u'Sign Languages': [u'Sign languages', u''], u'Veps language': [u'Veps', u''],
    u'Uralic Languages': [u'Uralic languages', u''], u'Turkic Languages': [u'Turkic Languages', u'Turkic languages'],
    u'no,nb': [u'Norwegian Bokm\xe5l', u''], u"Livonian": [u"Liv", u""],
    u"Finland Swedish Sign Language": [u'Finland-Swedish Sign Language; finlandssvenskt teckenspr\xe5k; suomenruotsalainen viittomakieli', u""],
    u"Swahili": [u"Swahili (macrolanguage)", u""]}

LANGUAGENAME_CURATION_CASES = {u"Portuguese, English, Spanish, French": 
        ([u'Portuguese', u''], [u'English', u''], [u'Spanish', u''], [u'French', u'']),
    u"Spanish (Spain); German (Germany); German (Austria)":
        ([u"Spanish", u"Spain"], [u"German", u"Germany"], [u"German", u"Austria"])
    }

DEFAULT_LANGUAGENAME = u"Undetermined"

LANGUAGESCRIPT_MAP = {u"Latn": u"Latin", u"latin": u"Latin", u"pt-PT": u"Latin",
    u"Arab": u"Arabic", u"UTF-8": u"", u"ISO 639-1 Code": u"", u"UTF8": u"",
    u"Cyrl": u"Cyrillic", u"Cyrilic": u"Cyrillic", u"cyrillic": u"Cyrillic",
    u"Simplified Chinese": u"Han (Simplified variant)", u"Grek": u"Greek",}

# This is a special case where we create two languageInfo instances
LANGUAGESCIPT_CURATION_CASES = {u"Latin/Cyrillic": [u"Latin", u"Cyrillic"]}

DEFAULT_LANGUAGESCRIPT = u"Code for undetermined script"

DOCUMENTLANGUAGENAME_MAP = {u"en": u"English", u"english": u"English",
    u"Greek, Modern (1453-)": u"Modern Greek (1453-)", u"pt-BR": u"Portuguese",
    u'Greek, Ancient (to 1453)': u'Ancient Greek (to 1453)'}

METADATALANGUAGENAME_MAP = {u"Greek, Modern (1453-)": u"Modern Greek (1453-)",
    u"Cymraeg": u"Welsh", u"European Portuguese": u"Portuguese",
    u"Sami": u"Sami languages", u"english": u"English",
    u"Romanian": u"Romanian; Moldavian; Moldovan", u"Hill Mari": u"Western Mari",
    u"(Greek, Modern (1453-))": u"Modern Greek (1453-)", u"en": u"English"}

METADATALNAGUAGENAME_CURATION_CASES = {u"French and English": [u"French", u"English"],
    u"English Finnish": [u"English", u"Finnish"], u"English, Finnish": [u"English", u"Finnish"]}

class Migration(DataMigration):

    def forwards(self, orm):
        path = "{0}/../misc/tools/migration/to_3_1/resources_to_be_modified.txt".format(ROOT_PATH)
        _file = open(path, 'a+')
        _file.write(u"\n\nThe following resources had language value that " \
            u"couldn't be matched to any choice, thus got the default value: 'Undetermined':.\n")

        valid_langnames = iana.get_most_used_languages() + iana.get_rest_of_languages()
        invalid_langnames = LANGUAGENAME_MAP.keys()

        valid_langscripts = iana.get_all_scripts()
        invalid_langscripts = LANGUAGESCRIPT_MAP.keys()
        for lang_info in orm.languageInfoType_model.objects.iterator():
            lang_name = u' '.join(lang_info.languageName.split())
            if lang_name in valid_langnames:
                lang_info.languageName = lang_name
            elif lang_name in invalid_langnames:
                lang_info.languageName = LANGUAGENAME_MAP[lang_name][0]
                lang_info.region = LANGUAGENAME_MAP[lang_name][1]
            else:
                write_to_resources_to_be_modified_file(_file, lang_info,
                    lang_name, 'languageInfo -- > languageName')
                lang_info.languageName = DEFAULT_LANGUAGENAME

            lang_script = lang_info.languageScript
            if not lang_script:
                pass
            elif lang_script in valid_langscripts:
                pass
            elif lang_script in invalid_langscripts:
                lang_info.languageScript = LANGUAGESCRIPT_MAP[lang_script]
            else:
                write_to_resources_to_be_modified_file(_file, lang_info,
                    lang_script, 'languageInfo -- > languageScript')
                lang_info.languageScript = DEFAULT_LANGUAGESCRIPT
                
            if lang_info.languageName:
                if not lang_info.languageScript:
                    lang_info.languageScript = \
                        iana.get_suppressed_script_description(lang_info.languageName)
                lang_info.languageId = \
                    iana.make_id(lang_info.languageName, lang_info.languageScript, lang_info.region, lang_info.variant)
            lang_info.save()
        
        
        invalid_doclangnames = DOCUMENTLANGUAGENAME_MAP.keys()
        for doc_info in orm.documentInfoType_model.objects.iterator():
            doclangname = u' '.join(doc_info.documentLanguageName.split())
            if not doclangname:
                continue
            elif doclangname in valid_langnames:
                doc_info.documentLanguageName = doclangname
            elif doclangname in invalid_doclangnames:
                doc_info.documentLanguageName = DOCUMENTLANGUAGENAME_MAP[doclangname]
            else:
                write_to_resources_to_be_modified_file(_file, doc_info,
                    doclangname, 'documentInfo --> documentLanguageName')
                doc_info.documentLanguageName = DEFAULT_LANGUAGENAME
            doc_info.documentLanguageId = iana.get_language_subtag(doc_info.documentLanguageName)
            doc_info.save()
                
        for anno_info in orm.annotationInfoType_model.objects.iterator():
            tagsetlangname = u' '.join(anno_info.tagsetLanguageName.split())
            if not tagsetlangname:
                continue
            elif tagsetlangname in valid_langnames:
                anno_info.tagsetLanguageName = tagsetlangname
            else:
                write_to_resources_to_be_modified_file(_file, anno_info,
                    tagsetlangname, 'annotationInfo --> tagsetLanguageName')
                anno_info.tagsetLanguageName = DEFAULT_LANGUAGENAME
            anno_info.tagsetLanguageId = iana.get_language_subtag(anno_info.tagsetLanguageName)
            anno_info.save()
        
        invalid_metalangnames = METADATALANGUAGENAME_MAP.keys()
        for metadata_info in orm.metadataInfoType_model.objects.iterator():
            metalangnames = []
            for metalangname in metadata_info.metadataLanguageName:
                metalangname = u' '.join(metalangname.split())
                if not metalangname:
                    continue
                elif metalangname in valid_langnames:
                    metalangnames.append(metalangname)
                elif metalangname in invalid_metalangnames:
                    metalangnames.append(METADATALANGUAGENAME_MAP[metalangname])
                elif METADATALNAGUAGENAME_CURATION_CASES.get(metalangname):
                    metalangnames.extend(METADATALNAGUAGENAME_CURATION_CASES.get(metalangname))
                else:
                    write_to_resources_to_be_modified_file(_file, metadata_info,
                        metalangname, 'metadataInfo --> metadataLanguageName')
                    metalangnames.append(DEFAULT_LANGUAGENAME)
            metadata_info.metadataLanguageName = metalangnames
            metalangids = [iana.get_language_subtag(metalangname) \
                        for metalangname in metadata_info.metadataLanguageName]
            metadata_info.metadataLanguageId = metalangids
            metadata_info.save()
        
        for input_info in orm.inputInfoType_model.objects.iterator():
            inputlangnames = []
            for inputlangname in input_info.languageName:
                inputlangname = u' '.join(inputlangname.split())
                if not inputlangname:
                    continue
                elif inputlangname in valid_langnames:
                    inputlangnames.append(inputlangname)
                elif inputlangname in invalid_langnames:
                    inputlangnames.append(LANGUAGENAME_MAP[inputlangname][0])
                else:
                    write_to_resources_to_be_modified_file(_file, input_info,
                        inputlangname, 'inputInfo --> languageName')
                    inputlangnames.append(DEFAULT_LANGUAGENAME)
            input_info.languageName = inputlangnames
            input_info.languageId = [iana.get_language_subtag(inputlangname) \
                                for inputlangname in input_info.languageName]
            input_info.save()
        
        for output_info in orm.outputInfoType_model.objects.iterator():
            outputlangnames = []
            for outputlangname in output_info.languageName:
                outputlangname = u' '.join(outputlangname.split())
                if not outputlangname:
                    continue
                elif outputlangname in valid_langnames:
                    outputlangnames.append(outputlangname)
                elif outputlangname in invalid_langnames:
                    outputlangnames.append(LANGUAGENAME_MAP[outputlangname][0])
                else:
                    write_to_resources_to_be_modified_file(_file, output_info,
                                outputlangname, 'outputInfo --> languageName')
                    outputlangnames.append(DEFAULT_LANGUAGENAME)
            output_info.languageName = outputlangnames
            output_info.languageId = [iana.get_language_subtag(outputlangname) \
                                for outputlangname in output_info.languageName]
            output_info.save()
        
        _file.close()

    def backwards(self, orm):
        pass

    models = {
        'accounts.editorgroup': {
            'Meta': {'object_name': 'EditorGroup', '_ormbases': ['auth.Group']},
            'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'repository.actorinfotype_model': {
            'Meta': {'object_name': 'actorInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'repository.actualuseinfotype_model': {
            'Meta': {'object_name': 'actualUseInfoType_model'},
            'actualUse': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'actualUseDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '250', 'blank': 'True'}),
            'back_to_usageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.usageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'derivedResource': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'derivedResource_actualuseinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'usageProject': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'usageProject_actualuseinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.projectInfoType_model']"}),
            'usageReport': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'usageReport_actualuseinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.documentationInfoType_model']"}),
            'useNLPSpecific': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'alignment', u'Alignment'), (u'annotation', u'Annotation'), (u'avatarSynthesis', u'Avatar Synthesis'), (u'bilingualLexiconInduction', u'Bilingual Lexicon Induction'), (u'contradictionDetection', u'Contradiction Detection'), (u'coreferenceResolution', u'Coreference Resolution'), (u'dependencyParsing', u'Dependency Parsing'), (u'derivationalMorphologicalAnalysis', u'Derivational Morphological Analysis'), (u'discourseAnalysis', u'Discourse Analysis'), (u'documentClassification', u'Document Classification'), (u'emotionGeneration', u'Emotion Generation'), (u'emotionRecognition', u'Emotion Recognition'), (u'entityMentionRecognition', u'Entity Mention Recognition'), (u'eventExtraction', u'Event Extraction'), (u'expressionRecognition', u'Expression Recognition'), (u'faceRecognition', u'Face Recognition'), (u'faceVerification', u'Face Verification'), (u'humanoidAgentSynthesis', u'Humanoid Agent Synthesis'), (u'informationExtraction', u'Information Extraction'), (u'informationRetrieval', u'Information Retrieval'), (u'intra-documentCoreferenceResolution', u'Intra - Document Coreference Resolution'), (u'knowledgeDiscovery', u'Knowledge Discovery'), (u'knowledgeRepresentation', u'Knowledge Representation'), (u'languageIdentification', u'Language Identification'), (u'languageModelling', u'Language Modelling'), (u'languageModelsTraining', u'Language Models Training'), (u'lemmatization', u'Lemmatization'), (u'lexiconAccess', u'Lexicon Access'), (u'lexiconAcquisitionFromCorpora', u'Lexicon Acquisition From Corpora'), (u'lexiconEnhancement', u'Lexicon Enhancement'), (u'lexiconExtractionFromLexica', u'Lexicon Extraction From Lexica'), (u'lexiconFormatConversion', u'Lexicon Format Conversion'), (u'lexiconVisualization', u'Lexicon Visualization'), (u'linguisticResearch', u'Linguistic Research'), (u'lipTrackingAnalysis', u'Lip Tracking Analysis'), (u'machineTranslation', u'Machine Translation'), (u'morphologicalAnalysis', u'Morphological Analysis'), (u'morphosyntacticAnnotation-bPosTagging', u'Morphosyntactic Annotation - B Pos Tagging'), (u'morphosyntacticAnnotation-posTagging', u'Morphosyntactic Annotation - Pos Tagging'), (u'multimediaDevelopment', u'Multimedia Development'), (u'multimediaDocumentProcessing', u'Multimedia Document Processing'), (u'namedEntityRecognition', u'Named Entity Recognition'), (u'naturalLanguageGeneration', u'Natural Language Generation'), (u'naturalLanguageUnderstanding', u'Natural Language Understanding'), (u'opinionMining', u'Opinion Mining'), (u'other', u'Other'), (u'personIdentification', u'Person Identification'), (u'personRecognition', u'Person Recognition'), (u'persuasiveExpressionMining', u'Persuasive Expression Mining'), (u'phraseAlignment', u'Phrase Alignment'), (u'qualitativeAnalysis', u'Qualitative Analysis'), (u'questionAnswering', u'Question Answering'), (u'readingAndWritingAidApplications', u'Reading And Writing Aid Applications'), (u'semanticRoleLabelling', u'Semantic Role Labelling'), (u'semanticWeb', u'Semantic Web'), (u'sentenceAlignment', u'Sentence Alignment'), (u'sentenceSplitting', u'Sentence Splitting'), (u'sentimentAnalysis', u'Sentiment Analysis'), (u'shallowParsing', u'Shallow Parsing'), (u'signLanguageGeneration', u'Sign Language Generation'), (u'signLanguageRecognition', u'Sign Language Recognition'), (u'speakerIdentification', u'Speaker Identification'), (u'speakerVerification', u'Speaker Verification'), (u'speechAnalysis', u'Speech Analysis'), (u'speechAssistedVideoControl', u'Speech Assisted Video Control'), (u'speechLipsCorrelationAnalysis', u'Speech Lips Correlation Analysis'), (u'speechRecognition', u'Speech Recognition'), (u'speechSynthesis', u'Speech Synthesis'), (u'speechToSpeechTranslation', u'Speech To Speech Translation'), (u'speechUnderstanding', u'Speech Understanding'), (u'speechVerification', u'Speech Verification'), (u'spellChecking', u'Spell Checking'), (u'spokenDialogueSystems', u'Spoken Dialogue Systems'), (u'summarization', u'Summarization'), (u'talkingHeadSynthesis', u'Talking Head Synthesis'), (u'temporalExpressionRecognition', u'Temporal Expression Recognition'), (u'terminologyExtraction', u'Terminology Extraction'), (u'textCategorisation', u'Text Categorisation'), (u'textGeneration', u'Text Generation'), (u'textMining', u'Text Mining'), (u'textToSpeechSynthesis', u'Text To Speech Synthesis'), (u'textualEntailment', u'Textual Entailment'), (u'tokenization', u'Tokenization'), (u'tokenizationAndSentenceSplitting', u'Tokenization And Sentence Splitting'), (u'topicDetection_Tracking', u'Topic Detection_ Tracking'), (u'userAuthentication', u'User Authentication'), (u'visualSceneUnderstanding', u'Visual Scene Understanding'), (u'voiceControl', u'Voice Control'), (u'wordAlignment', u'Word Alignment'), (u'wordSenseDisambiguation', u'Word Sense Disambiguation'), (u'lexiconMerging', u'Lexicon Merging'))", 'max_length': '23', 'blank': 'True'})
        },
        'repository.annotationinfotype_model': {
            'Meta': {'object_name': 'annotationInfoType_model'},
            'annotatedElements': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'speakerNoise', u'Speaker Noise'), (u'backgroundNoise', u'Background Noise'), (u'mispronunciations', u'Mispronunciations'), (u'truncation', u'Truncation'), (u'discourseMarkers', u'Discourse Markers'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'annotationEndDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'annotationFormat': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'annotationManual': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'annotationManual_annotationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.documentationInfoType_model']"}),
            'annotationMode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'annotationModeDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'annotationStandoff': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'annotationStartDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'annotationTool': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'annotationTool_annotationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"}),
            'annotationType': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'annotator': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'annotator_annotationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.actorInfoType_model']"}),
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextnumericalinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNumericalInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'conformanceToStandardsBestPractices': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'BML', u'BML'), (u'CES', u'CES'), (u'EAGLES', u'EAGLES'), (u'EML', u'EML'), (u'EMMA', u'EMMA'), (u'GMX', u'GMX'), (u'GrAF', u'GrAF'), (u'HamNoSys', u'Ham No Sys'), (u'InkML', u'InkML'), (u'ILSP_NLP', u'ILSP_NLP'), (u'ISO12620', u'ISO12620'), (u'ISO16642', u'ISO16642'), (u'ISO1987', u'ISO1987'), (u'ISO26162', u'ISO26162'), (u'ISO30042', u'ISO30042'), (u'ISO704', u'ISO704'), (u'LAF', u'LAF'), (u'LMF', u'LMF'), (u'MAF', u'MAF'), (u'MLIF', u'MLIF'), (u'MOSES', u'MOSES'), (u'MULTEXT', u'MULTEXT'), (u'MUMIN', u'MUMIN'), (u'multimodalInteractionFramework', u'Multimodal Interaction Framework'), (u'OAXAL', u'OAXAL'), (u'OWL', u'OWL'), (u'PANACEA', u'PANACEA'), (u'pennTreeBank', u'Penn Tree Bank'), (u'pragueTreebank', u'Prague Treebank'), (u'RDF', u'RDF'), (u'SemAF', u'SemAF'), (u'SemAF_DA', u'SemAF_DA'), (u'SemAF_NE', u'SemAF_NE'), (u'SemAF_SRL', u'SemAF_SRL'), (u'SemAF_DS', u'SemAF_DS'), (u'SKOS', u'SKOS'), (u'SRX', u'SRX'), (u'SynAF', u'SynAF'), (u'TBX', u'TBX'), (u'TMX', u'TMX'), (u'TEI', u'TEI'), (u'TEI_P3', u'TEI_P3'), (u'TEI_P4', u'TEI_P4'), (u'TEI_P5', u'TEI_P5'), (u'TimeML', u'TimeML'), (u'XCES', u'XCES'), (u'XLIFF', u'XLIFF'), (u'WordNet', u'Word Net'), (u'other', u'Other'))", 'max_length': '13', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interannotatorAgreement': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'intraannotatorAgreement': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'segmentationLevel': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'paragraph', u'Paragraph'), (u'sentence', u'Sentence'), (u'clause', u'Clause'), (u'word', u'Word'), (u'wordGroup', u'Word Group'), (u'utterance', u'Utterance'), (u'topic', u'Topic'), (u'signal', u'Signal'), (u'phoneme', u'Phoneme'), (u'syllable', u'Syllable'), (u'phrase', u'Phrase'), (u'diphone', u'Diphone'), (u'prosodicBoundaries', u'Prosodic Boundaries'), (u'frame', u'Frame'), (u'scene', u'Scene'), (u'shot', u'Shot'), (u'token', u'Token'), (u'other', u'Other'))", 'max_length': '5', 'blank': 'True'}),
            'sizePerAnnotation': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'tagset': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'tagsetLanguageId': ('metashare.repository.fields.XmlCharField', [], {'max_length': '20', 'blank': 'True'}),
            'tagsetLanguageName': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'theoreticModel': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'})
        },
        'repository.audioclassificationinfotype_model': {
            'Meta': {'object_name': 'audioClassificationInfoType_model'},
            'audioGenre': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'conformanceToClassificationScheme': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'register': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'sizePerAudioClassification': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'speechGenre': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'subject_topic': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'})
        },
        'repository.audiocontentinfotype_model': {
            'Meta': {'object_name': 'audioContentInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'noiseLevel': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'nonSpeechItems': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'notes', u'Notes'), (u'tempo', u'Tempo'), (u'sounds', u'Sounds'), (u'noise', u'Noise'), (u'music', u'Music'), (u'commercial ', u'Commercial'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'speechItems': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'isolatedWords', u'Isolated Words'), (u'isolatedDigits', u'Isolated Digits'), (u'naturalNumbers', u'Natural Numbers'), (u'properNouns', u'Proper Nouns'), (u'applicationWords', u'Application Words'), (u'phoneticallyRichSentences', u'Phonetically Rich Sentences'), (u'phoneticallyRichWords', u'Phonetically Rich Words'), (u'phoneticallyBalancedSentences', u'Phonetically Balanced Sentences'), (u'moneyAmounts', u'Money Amounts'), (u'creditCardNumbers', u'Credit Card Numbers'), (u'telephoneNumbers', u'Telephone Numbers'), (u'yesNoQuestions', u'Yes No Questions'), (u'vcvSequences', u'Vcv Sequences'), (u'freeSpeech', u'Free Speech'), (u'other', u'Other'))", 'max_length': '4', 'blank': 'True'}),
            'textualDescription': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'})
        },
        'repository.audioformatinfotype_model': {
            'Meta': {'object_name': 'audioFormatInfoType_model'},
            'audioQualityMeasuresIncluded': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'byteOrder': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'compressionInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.compressionInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimeType': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'numberOfTracks': ('django.db.models.fields.IntegerField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'quantization': ('django.db.models.fields.IntegerField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'recordingQuality': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'samplingRate': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'signConvention': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'signalEncoding': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'aLaw', u'A Law'), (u'linearPCM', u'LinearPCM'), (u'\\xb5-law', u'\\u039c - Law'), (u'ADPCM', u'ADPCM'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'sizePerAudioFormat': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.audiosizeinfotype_model': {
            'Meta': {'object_name': 'audioSizeInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'repository.captureinfotype_model': {
            'Meta': {'object_name': 'captureInfoType_model'},
            'capturingDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '400', 'blank': 'True'}),
            'capturingDeviceType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'studioEquipment', u'Studio Equipment'), (u'microphone', u'Microphone'), (u'closeTalkMicrophone', u'Close Talk Microphone'), (u'farfieldMicrophone', u'Farfield Microphone'), (u'lavalierMicrophone', u'Lavalier Microphone'), (u'microphoneArray', u'Microphone Array'), (u'embeddedMicrophone', u'Embedded Microphone'), (u'largeMembraneMicrophone', u'Large Membrane Microphone'), (u'laryngograph', u'Laryngograph'), (u'telephoneFixed', u'Telephone Fixed'), (u'telephoneMobile', u'Telephone Mobile'), (u'telephoneIP', u'TelephoneIP'), (u'camera', u'Camera'), (u'webcam', u'Webcam'), (u'other', u'Other'))", 'max_length': '4', 'blank': 'True'}),
            'capturingDeviceTypeDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '400', 'blank': 'True'}),
            'capturingEnvironment': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'personSourceSetInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.personSourceSetInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'sceneIllumination': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'sensorTechnology': ('metashare.repository.fields.MultiTextField', [], {'max_length': '200', 'blank': 'True'})
        },
        'repository.characterencodinginfotype_model': {
            'Meta': {'object_name': 'characterEncodingInfoType_model'},
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptiontextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcetextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'characterEncoding': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sizePerCharacterEncoding': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.communicationinfotype_model': {
            'Meta': {'object_name': 'communicationInfoType_model'},
            'address': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'city': ('metashare.repository.fields.XmlCharField', [], {'max_length': '50', 'blank': 'True'}),
            'country': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'countryId': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000'}),
            'email': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100'}),
            'faxNumber': ('metashare.repository.fields.MultiTextField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'telephoneNumber': ('metashare.repository.fields.MultiTextField', [], {'max_length': '30', 'blank': 'True'}),
            'url': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'zipCode': ('metashare.repository.fields.XmlCharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'repository.compressioninfotype_model': {
            'Meta': {'object_name': 'compressionInfoType_model'},
            'compression': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True'}),
            'compressionLoss': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'compressionName': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'mpg', u'Mpg'), (u'avi', u'Avi'), (u'mov', u'Mov'), (u'flac', u'Flac'), (u'shorten', u'Shorten'), (u'mp3', u'Mp3'), (u'oggVorbis', u'Ogg Vorbis'), (u'atrac', u'Atrac'), (u'aac', u'Aac'), (u'mpeg', u'Mpeg'), (u'realAudio', u'Real Audio'), (u'other', u'Other'))", 'max_length': '4', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'repository.corpusaudioinfotype_model': {
            'Meta': {'object_name': 'corpusAudioInfoType_model'},
            'audioContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.audioContentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'audioSizeInfo': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'audioSizeInfo_corpusaudioinfotype_model_related'", 'symmetrical': 'False', 'to': "orm['repository.audioSizeInfoType_model']"}),
            'captureInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.captureInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'audio'", 'max_length': '1000'}),
            'recordingInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.recordingInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'settingInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.settingInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.corpusimageinfotype_model': {
            'Meta': {'object_name': 'corpusImageInfoType_model'},
            'captureInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.captureInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imageContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.imageContentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'image'", 'max_length': '1000'})
        },
        'repository.corpusinfotype_model': {
            'Meta': {'object_name': 'corpusInfoType_model', '_ormbases': ['repository.resourceComponentTypeType_model']},
            'corpusMediaType': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.corpusMediaTypeType_model']", 'unique': 'True'}),
            'resourceType': ('metashare.repository.fields.XmlCharField', [], {'default': "'corpus'", 'max_length': '1000'}),
            'resourcecomponenttypetype_model_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.resourceComponentTypeType_model']", 'unique': 'True', 'primary_key': 'True'})
        },
        'repository.corpusmediatypetype_model': {
            'Meta': {'object_name': 'corpusMediaTypeType_model'},
            'corpusAudioInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'corpusImageInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.corpusImageInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'corpusTextNgramInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'corpusTextNumericalInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.corpusTextNumericalInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'repository.corpustextinfotype_model': {
            'Meta': {'object_name': 'corpusTextInfoType_model'},
            'back_to_corpusmediatypetype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusMediaTypeType_model']", 'null': 'True', 'blank': 'True'}),
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'text'", 'max_length': '1000'})
        },
        'repository.corpustextngraminfotype_model': {
            'Meta': {'object_name': 'corpusTextNgramInfoType_model'},
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'textNgram'", 'max_length': '1000'}),
            'modalityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.modalityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'ngramInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.ngramInfoType_model']", 'unique': 'True'})
        },
        'repository.corpustextnumericalinfotype_model': {
            'Meta': {'object_name': 'corpusTextNumericalInfoType_model'},
            'captureInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.captureInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'textNumerical'", 'max_length': '1000'}),
            'recordingInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.recordingInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'textNumericalContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.textNumericalContentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.corpusvideoinfotype_model': {
            'Meta': {'object_name': 'corpusVideoInfoType_model'},
            'back_to_corpusmediatypetype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusMediaTypeType_model']", 'null': 'True', 'blank': 'True'}),
            'captureInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.captureInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'video'", 'max_length': '1000'}),
            'recordingInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.recordingInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'settingInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.settingInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'videoContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.videoContentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.creationinfotype_model': {
            'Meta': {'object_name': 'creationInfoType_model'},
            'creationMode': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'creationModeDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'creationTool': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'creationTool_creationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'originalSource': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'originalSource_creationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"})
        },
        'repository.distributioninfotype_model': {
            'Meta': {'object_name': 'distributionInfoType_model'},
            'availability': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'availabilityEndDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'availabilityStartDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iprHolder': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'iprHolder_distributioninfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.actorInfoType_model']"})
        },
        'repository.documentationinfotype_model': {
            'Meta': {'object_name': 'documentationInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'repository.documentinfotype_model': {
            'ISBN': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'ISSN': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'Meta': {'object_name': 'documentInfoType_model', '_ormbases': ['repository.documentationInfoType_model']},
            'author': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'bookTitle': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'conference': ('metashare.repository.fields.XmlCharField', [], {'max_length': '300', 'blank': 'True'}),
            'copy_status': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'documentLanguageId': ('metashare.repository.fields.XmlCharField', [], {'max_length': '20', 'blank': 'True'}),
            'documentLanguageName': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'documentType': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'documentationinfotype_model_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.documentationInfoType_model']", 'unique': 'True', 'primary_key': 'True'}),
            'doi': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'edition': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'editor': ('metashare.repository.fields.MultiTextField', [], {'max_length': '200', 'blank': 'True'}),
            'journal': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'keywords': ('metashare.repository.fields.MultiTextField', [], {'max_length': '250', 'blank': 'True'}),
            'pages': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'publisher': ('metashare.repository.fields.MultiTextField', [], {'max_length': '200', 'blank': 'True'}),
            'series': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'default': "'http://127.0.0.1:8000'", 'max_length': '200'}),
            'title': ('metashare.repository.fields.DictField', [], {'null': 'True'}),
            'url': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'volume': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'year': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.documentlisttype_model': {
            'Meta': {'object_name': 'documentListType_model'},
            'documentInfo': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'documentInfo_documentlisttype_model_related'", 'symmetrical': 'False', 'to': "orm['repository.documentInfoType_model']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'repository.documentunstructuredstring_model': {
            'Meta': {'object_name': 'documentUnstructuredString_model', '_ormbases': ['repository.InvisibleStringModel', 'repository.documentationInfoType_model']},
            'documentationinfotype_model_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.documentationInfoType_model']", 'unique': 'True'}),
            'invisiblestringmodel_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.InvisibleStringModel']", 'unique': 'True', 'primary_key': 'True'})
        },
        'repository.domaininfotype_model': {
            'Meta': {'object_name': 'domainInfoType_model'},
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptiontextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcetextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcevideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'conformanceToClassificationScheme': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'domain': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sizePerDomain': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.durationofaudioinfotype_model': {
            'Meta': {'object_name': 'durationOfAudioInfoType_model'},
            'back_to_audiosizeinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.audioSizeInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'durationUnit': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {})
        },
        'repository.durationofeffectivespeechinfotype_model': {
            'Meta': {'object_name': 'durationOfEffectiveSpeechInfoType_model'},
            'back_to_audiosizeinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.audioSizeInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'durationUnit': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {})
        },
        'repository.dynamicelementinfotype_model': {
            'Meta': {'object_name': 'dynamicElementInfoType_model'},
            'bodyMovement': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'bodyParts': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'arms', u'Arms'), (u'face', u'Face'), (u'feet', u'Feet'), (u'hands', u'Hands'), (u'head', u'Head'), (u'legs', u'Legs'), (u'mouth', u'Mouth'), (u'wholeBody', u'Whole Body'), (u'none', u'None'))", 'max_length': '3', 'blank': 'True'}),
            'distractors': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'eyeMovement': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'faceExpressions': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'faceViews': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'gestures': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'handArmMovement': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'handManipulation': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'headMovement': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interactiveMedia': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'posesPerSubject': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'typeOfElement': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.foreseenuseinfotype_model': {
            'Meta': {'object_name': 'foreseenUseInfoType_model'},
            'back_to_usageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.usageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'foreseenUse': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'useNLPSpecific': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'alignment', u'Alignment'), (u'annotation', u'Annotation'), (u'avatarSynthesis', u'Avatar Synthesis'), (u'bilingualLexiconInduction', u'Bilingual Lexicon Induction'), (u'contradictionDetection', u'Contradiction Detection'), (u'coreferenceResolution', u'Coreference Resolution'), (u'dependencyParsing', u'Dependency Parsing'), (u'derivationalMorphologicalAnalysis', u'Derivational Morphological Analysis'), (u'discourseAnalysis', u'Discourse Analysis'), (u'documentClassification', u'Document Classification'), (u'emotionGeneration', u'Emotion Generation'), (u'emotionRecognition', u'Emotion Recognition'), (u'entityMentionRecognition', u'Entity Mention Recognition'), (u'eventExtraction', u'Event Extraction'), (u'expressionRecognition', u'Expression Recognition'), (u'faceRecognition', u'Face Recognition'), (u'faceVerification', u'Face Verification'), (u'humanoidAgentSynthesis', u'Humanoid Agent Synthesis'), (u'informationExtraction', u'Information Extraction'), (u'informationRetrieval', u'Information Retrieval'), (u'intra-documentCoreferenceResolution', u'Intra - Document Coreference Resolution'), (u'knowledgeDiscovery', u'Knowledge Discovery'), (u'knowledgeRepresentation', u'Knowledge Representation'), (u'languageIdentification', u'Language Identification'), (u'languageModelling', u'Language Modelling'), (u'languageModelsTraining', u'Language Models Training'), (u'lemmatization', u'Lemmatization'), (u'lexiconAccess', u'Lexicon Access'), (u'lexiconAcquisitionFromCorpora', u'Lexicon Acquisition From Corpora'), (u'lexiconEnhancement', u'Lexicon Enhancement'), (u'lexiconExtractionFromLexica', u'Lexicon Extraction From Lexica'), (u'lexiconFormatConversion', u'Lexicon Format Conversion'), (u'lexiconVisualization', u'Lexicon Visualization'), (u'linguisticResearch', u'Linguistic Research'), (u'lipTrackingAnalysis', u'Lip Tracking Analysis'), (u'machineTranslation', u'Machine Translation'), (u'morphologicalAnalysis', u'Morphological Analysis'), (u'morphosyntacticAnnotation-bPosTagging', u'Morphosyntactic Annotation - B Pos Tagging'), (u'morphosyntacticAnnotation-posTagging', u'Morphosyntactic Annotation - Pos Tagging'), (u'multimediaDevelopment', u'Multimedia Development'), (u'multimediaDocumentProcessing', u'Multimedia Document Processing'), (u'namedEntityRecognition', u'Named Entity Recognition'), (u'naturalLanguageGeneration', u'Natural Language Generation'), (u'naturalLanguageUnderstanding', u'Natural Language Understanding'), (u'opinionMining', u'Opinion Mining'), (u'other', u'Other'), (u'personIdentification', u'Person Identification'), (u'personRecognition', u'Person Recognition'), (u'persuasiveExpressionMining', u'Persuasive Expression Mining'), (u'phraseAlignment', u'Phrase Alignment'), (u'qualitativeAnalysis', u'Qualitative Analysis'), (u'questionAnswering', u'Question Answering'), (u'readingAndWritingAidApplications', u'Reading And Writing Aid Applications'), (u'semanticRoleLabelling', u'Semantic Role Labelling'), (u'semanticWeb', u'Semantic Web'), (u'sentenceAlignment', u'Sentence Alignment'), (u'sentenceSplitting', u'Sentence Splitting'), (u'sentimentAnalysis', u'Sentiment Analysis'), (u'shallowParsing', u'Shallow Parsing'), (u'signLanguageGeneration', u'Sign Language Generation'), (u'signLanguageRecognition', u'Sign Language Recognition'), (u'speakerIdentification', u'Speaker Identification'), (u'speakerVerification', u'Speaker Verification'), (u'speechAnalysis', u'Speech Analysis'), (u'speechAssistedVideoControl', u'Speech Assisted Video Control'), (u'speechLipsCorrelationAnalysis', u'Speech Lips Correlation Analysis'), (u'speechRecognition', u'Speech Recognition'), (u'speechSynthesis', u'Speech Synthesis'), (u'speechToSpeechTranslation', u'Speech To Speech Translation'), (u'speechUnderstanding', u'Speech Understanding'), (u'speechVerification', u'Speech Verification'), (u'spellChecking', u'Spell Checking'), (u'spokenDialogueSystems', u'Spoken Dialogue Systems'), (u'summarization', u'Summarization'), (u'talkingHeadSynthesis', u'Talking Head Synthesis'), (u'temporalExpressionRecognition', u'Temporal Expression Recognition'), (u'terminologyExtraction', u'Terminology Extraction'), (u'textCategorisation', u'Text Categorisation'), (u'textGeneration', u'Text Generation'), (u'textMining', u'Text Mining'), (u'textToSpeechSynthesis', u'Text To Speech Synthesis'), (u'textualEntailment', u'Textual Entailment'), (u'tokenization', u'Tokenization'), (u'tokenizationAndSentenceSplitting', u'Tokenization And Sentence Splitting'), (u'topicDetection_Tracking', u'Topic Detection_ Tracking'), (u'userAuthentication', u'User Authentication'), (u'visualSceneUnderstanding', u'Visual Scene Understanding'), (u'voiceControl', u'Voice Control'), (u'wordAlignment', u'Word Alignment'), (u'wordSenseDisambiguation', u'Word Sense Disambiguation'), (u'lexiconMerging', u'Lexicon Merging'))", 'max_length': '23', 'blank': 'True'}),
        },
        'repository.geographiccoverageinfotype_model': {
            'Meta': {'object_name': 'geographicCoverageInfoType_model'},
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptiontextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcetextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcevideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'geographicCoverage': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sizePerGeographicCoverage': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.identificationinfotype_model': {
            'Meta': {'object_name': 'identificationInfoType_model'},
            'description': ('metashare.repository.fields.DictField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'metaShareId': ('metashare.repository.fields.XmlCharField', [], {'default': "'NOT_DEFINED_FOR_V2'", 'max_length': '100'}),
            'resourceName': ('metashare.repository.fields.DictField', [], {'null': 'True'}),
            'resourceShortName': ('metashare.repository.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'url': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.imageclassificationinfotype_model': {
            'Meta': {'object_name': 'imageClassificationInfoType_model'},
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'conformanceToClassificationScheme': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imageGenre': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'sizePerImageClassification': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'subject_topic': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.imagecontentinfotype_model': {
            'Meta': {'object_name': 'imageContentInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'staticElementInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.staticElementInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'textIncludedInImage': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'captions', u'Captions'), (u'subtitles', u'Subtitles'), (u'captureTime', u'Capture Time'), (u'none', u'None'))", 'max_length': '2', 'blank': 'True'}),
            'typeOfImageContent': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000'})
        },
        'repository.imageformatinfotype_model': {
            'Meta': {'object_name': 'imageFormatInfoType_model'},
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'colourDepth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'colourSpace': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'RGB', u'RGB'), (u'CMYK', u'CMYK'), (u'4:2:2', u'4:2:2'), (u'YUV', u'YUV'))", 'max_length': '2', 'blank': 'True'}),
            'compressionInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.compressionInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimeType': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'quality': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'rasterOrVectorGraphics': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'resolutionInfo': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'resolutionInfo_imageformatinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.resolutionInfoType_model']"}),
            'sizePerImageFormat': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'visualModelling': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'repository.inputinfotype_model': {
            'Meta': {'object_name': 'inputInfoType_model'},
            'annotationFormat': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'annotationType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'alignment', u'Alignment'), (u'discourseAnnotation', u'Discourse Annotation'), (u'discourseAnnotation-audienceReactions', u'Discourse Annotation - Audience Reactions'), (u'discourseAnnotation-coreference', u'Discourse Annotation - Coreference'), (u'discourseAnnotation-dialogueActs', u'Discourse Annotation - Dialogue Acts'), (u'discourseAnnotation-discourseRelations', u'Discourse Annotation - Discourse Relations'), (u'lemmatization', u'Lemmatization'), (u'morphosyntacticAnnotation-bPosTagging', u'Morphosyntactic Annotation - B Pos Tagging'), (u'morphosyntacticAnnotation-posTagging', u'Morphosyntactic Annotation - Pos Tagging'), (u'segmentation', u'Segmentation'), (u'semanticAnnotation', u'Semantic Annotation'), (u'semanticAnnotation-certaintyLevel', u'Semantic Annotation - Certainty Level'), (u'semanticAnnotation-emotions', u'Semantic Annotation - Emotions'), (u'semanticAnnotation-entityMentions', u'Semantic Annotation - Entity Mentions'), (u'semanticAnnotation-events', u'Semantic Annotation - Events'), (u'semanticAnnotation-namedEntities', u'Semantic Annotation - Named Entities'), (u'semanticAnnotation-polarity', u'Semantic Annotation - Polarity'), (u'semanticAnnotation-questionTopicalTarget', u'Semantic Annotation - Question Topical Target'), (u'semanticAnnotation-semanticClasses', u'Semantic Annotation - Semantic Classes'), (u'semanticAnnotation-semanticRelations', u'Semantic Annotation - Semantic Relations'), (u'semanticAnnotation-semanticRoles', u'Semantic Annotation - Semantic Roles'), (u'semanticAnnotation-speechActs', u'Semantic Annotation - Speech Acts'), (u'semanticAnnotation-temporalExpressions', u'Semantic Annotation - Temporal Expressions'), (u'semanticAnnotation-textualEntailment', u'Semantic Annotation - Textual Entailment'), (u'semanticAnnotation-wordSenses', u'Semantic Annotation - Word Senses'), (u'speechAnnotation', u'Speech Annotation'), (u'speechAnnotation-orthographicTranscription', u'Speech Annotation - Orthographic Transcription'), (u'speechAnnotation-paralanguageAnnotation', u'Speech Annotation - Paralanguage Annotation'), (u'speechAnnotation-phoneticTranscription', u'Speech Annotation - Phonetic Transcription'), (u'speechAnnotation-prosodicAnnotation', u'Speech Annotation - Prosodic Annotation'), (u'speechAnnotation-soundEvents', u'Speech Annotation - Sound Events'), (u'speechAnnotation-soundToTextAlignment', u'Speech Annotation - Sound To Text Alignment'), (u'speechAnnotation-speakerIdentification', u'Speech Annotation - Speaker Identification'), (u'speechAnnotation-speakerTurns', u'Speech Annotation - Speaker Turns'), (u'stemming', u'Stemming'), (u'structuralAnnotation', u'Structural Annotation'), (u'syntacticAnnotation-subcategorizationFrames', u'Syntactic Annotation - Subcategorization Frames'), (u'syntacticAnnotation-dependencyTrees', u'Syntactic Annotation - Dependency Trees'), (u'syntacticAnnotation-constituencyTrees', u'Syntactic Annotation - Constituency Trees'), (u'syntacticosemanticAnnotation-links', u'Syntacticosemantic Annotation - Links'), (u'translation', u'Translation'), (u'transliteration', u'Transliteration'), (u'modalityAnnotation-bodyMovements', u'Modality Annotation - Body Movements'), (u'modalityAnnotation-facialExpressions', u'Modality Annotation - Facial Expressions'), (u'modalityAnnotation-gazeEyeMovements', u'Modality Annotation - Gaze Eye Movements'), (u'modalityAnnotation-handArmGestures', u'Modality Annotation - Hand Arm Gestures'), (u'modalityAnnotation-handManipulationOfObjects', u'Modality Annotation - Hand Manipulation Of Objects'), (u'modalityAnnotation-headMovements', u'Modality Annotation - Head Movements'), (u'modalityAnnotation-lipMovements', u'Modality Annotation - Lip Movements'), (u'other', u'Other'))", 'max_length': '13', 'blank': 'True'}),
            'characterEncoding': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'US-ASCII', u'US - ASCII'), (u'windows-1250', u'Windows - 1250'), (u'windows-1251', u'Windows - 1251'), (u'windows-1252', u'Windows - 1252'), (u'windows-1253', u'Windows - 1253'), (u'windows-1254', u'Windows - 1254'), (u'windows-1257', u'Windows - 1257'), (u'ISO-8859-1', u'ISO - 8859 - 1'), (u'ISO-8859-2', u'ISO - 8859 - 2'), (u'ISO-8859-4', u'ISO - 8859 - 4'), (u'ISO-8859-5', u'ISO - 8859 - 5'), (u'ISO-8859-7', u'ISO - 8859 - 7'), (u'ISO-8859-9', u'ISO - 8859 - 9'), (u'ISO-8859-13', u'ISO - 8859 - 13'), (u'ISO-8859-15', u'ISO - 8859 - 15'), (u'KOI8-R', u'KOI8 - R'), (u'UTF-8', u'UTF - 8'), (u'UTF-16', u'UTF - 16'), (u'UTF-16BE', u'UTF - 16BE'), (u'UTF-16LE', u'UTF - 16LE'), (u'windows-1255', u'Windows - 1255'), (u'windows-1256', u'Windows - 1256'), (u'windows-1258', u'Windows - 1258'), (u'ISO-8859-3', u'ISO - 8859 - 3'), (u'ISO-8859-6', u'ISO - 8859 - 6'), (u'ISO-8859-8', u'ISO - 8859 - 8'), (u'windows-31j', u'Windows - 31j'), (u'EUC-JP', u'EUC - JP'), (u'x-EUC-JP-LINUX', u'X - EUC - JP - LINUX'), (u'Shift_JIS', u'Shift_JIS'), (u'ISO-2022-JP', u'ISO - 2022 - JP'), (u'x-mswin-936', u'X - Mswin - 936'), (u'GB18030', u'GB18030'), (u'x-EUC-CN', u'X - EUC - CN'), (u'GBK', u'GBK'), (u'ISCII91', u'ISCII91'), (u'x-windows-949', u'X - Windows - 949'), (u'EUC-KR', u'EUC - KR'), (u'ISO-2022-KR', u'ISO - 2022 - KR'), (u'x-windows-950', u'X - Windows - 950'), (u'x-MS950-HKSCS', u'X - MS950 - HKSCS'), (u'x-EUC-TW', u'X - EUC - TW'), (u'Big5', u'Big5'), (u'Big5-HKSCS', u'Big5 - HKSCS'), (u'TIS-620', u'TIS - 620'), (u'Big5_Solaris', u'Big5_ Solaris'), (u'Cp037', u'Cp037'), (u'Cp273', u'Cp273'), (u'Cp277', u'Cp277'), (u'Cp278', u'Cp278'), (u'Cp280', u'Cp280'), (u'Cp284', u'Cp284'), (u'Cp285', u'Cp285'), (u'Cp297', u'Cp297'), (u'Cp420', u'Cp420'), (u'Cp424', u'Cp424'), (u'Cp437', u'Cp437'), (u'Cp500', u'Cp500'), (u'Cp737', u'Cp737'), (u'Cp775', u'Cp775'), (u'Cp838', u'Cp838'), (u'Cp850', u'Cp850'), (u'Cp852', u'Cp852'), (u'Cp855', u'Cp855'), (u'Cp856', u'Cp856'), (u'Cp857', u'Cp857'), (u'Cp858', u'Cp858'), (u'Cp860', u'Cp860'), (u'Cp861', u'Cp861'), (u'Cp862', u'Cp862'), (u'Cp863', u'Cp863'), (u'Cp864', u'Cp864'), (u'Cp865', u'Cp865'), (u'Cp866', u'Cp866'), (u'Cp868', u'Cp868'), (u'Cp869', u'Cp869'), (u'Cp870', u'Cp870'), (u'Cp871', u'Cp871'), (u'Cp874', u'Cp874'), (u'Cp875', u'Cp875'), (u'Cp918', u'Cp918'), (u'Cp921', u'Cp921'), (u'Cp922', u'Cp922'), (u'Cp930', u'Cp930'), (u'Cp933', u'Cp933'), (u'Cp935', u'Cp935'), (u'Cp937', u'Cp937'), (u'Cp939', u'Cp939'), (u'Cp942', u'Cp942'), (u'Cp942C', u'Cp942C'), (u'Cp943', u'Cp943'), (u'Cp943C', u'Cp943C'), (u'Cp948', u'Cp948'), (u'Cp949', u'Cp949'), (u'Cp949C', u'Cp949C'), (u'Cp950', u'Cp950'), (u'Cp964', u'Cp964'), (u'Cp970', u'Cp970'), (u'Cp1006', u'Cp1006'), (u'Cp1025', u'Cp1025'), (u'Cp1026', u'Cp1026'), (u'Cp1046', u'Cp1046'), (u'Cp1047', u'Cp1047'), (u'Cp1097', u'Cp1097'), (u'Cp1098', u'Cp1098'), (u'Cp1112', u'Cp1112'), (u'Cp1122', u'Cp1122'), (u'Cp1123', u'Cp1123'), (u'Cp1124', u'Cp1124'), (u'Cp1140', u'Cp1140'), (u'Cp1141', u'Cp1141'), (u'Cp1142', u'Cp1142'), (u'Cp1143', u'Cp1143'), (u'Cp1144', u'Cp1144'), (u'Cp1145', u'Cp1145'), (u'Cp1146', u'Cp1146'), (u'Cp1147', u'Cp1147'), (u'Cp1148', u'Cp1148'), (u'Cp1149', u'Cp1149'), (u'Cp1381', u'Cp1381'), (u'Cp1383', u'Cp1383'), (u'Cp33722', u'Cp33722'), (u'ISO2022_CN_CNS', u'ISO2022_CN_CNS'), (u'ISO2022_CN_GB', u'ISO2022_CN_GB'), (u'JISAutoDetect', u'JIS Auto Detect'), (u'MS874', u'MS874'), (u'MacArabic', u'Mac Arabic'), (u'MacCentralEurope', u'Mac Central Europe'), (u'MacCroatian', u'Mac Croatian'), (u'MacCyrillic', u'Mac Cyrillic'), (u'MacDingbat', u'Mac Dingbat'), (u'MacGreek', u'Mac Greek'), (u'MacHebrew', u'Mac Hebrew'), (u'MacIceland', u'Mac Iceland'), (u'MacRoman', u'Mac Roman'), (u'MacRomania', u'Mac Romania'), (u'MacSymbol', u'Mac Symbol'), (u'MacThai', u'Mac Thai'), (u'MacTurkish', u'Mac Turkish'), (u'MacUkraine', u'Mac Ukraine'))", 'max_length': '36', 'blank': 'True'}),
            'conformanceToStandardsBestPractices': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'BML', u'BML'), (u'CES', u'CES'), (u'EAGLES', u'EAGLES'), (u'EML', u'EML'), (u'EMMA', u'EMMA'), (u'GMX', u'GMX'), (u'GrAF', u'GrAF'), (u'HamNoSys', u'Ham No Sys'), (u'InkML', u'InkML'), (u'ILSP_NLP', u'ILSP_NLP'), (u'ISO12620', u'ISO12620'), (u'ISO16642', u'ISO16642'), (u'ISO1987', u'ISO1987'), (u'ISO26162', u'ISO26162'), (u'ISO30042', u'ISO30042'), (u'ISO704', u'ISO704'), (u'LAF', u'LAF'), (u'LMF', u'LMF'), (u'MAF', u'MAF'), (u'MLIF', u'MLIF'), (u'MOSES', u'MOSES'), (u'MULTEXT', u'MULTEXT'), (u'MUMIN', u'MUMIN'), (u'multimodalInteractionFramework', u'Multimodal Interaction Framework'), (u'OAXAL', u'OAXAL'), (u'OWL', u'OWL'), (u'PANACEA', u'PANACEA'), (u'pennTreeBank', u'Penn Tree Bank'), (u'pragueTreebank', u'Prague Treebank'), (u'RDF', u'RDF'), (u'SemAF', u'SemAF'), (u'SemAF_DA', u'SemAF_DA'), (u'SemAF_NE', u'SemAF_NE'), (u'SemAF_SRL', u'SemAF_SRL'), (u'SemAF_DS', u'SemAF_DS'), (u'SKOS', u'SKOS'), (u'SRX', u'SRX'), (u'SynAF', u'SynAF'), (u'TBX', u'TBX'), (u'TMX', u'TMX'), (u'TEI', u'TEI'), (u'TEI_P3', u'TEI_P3'), (u'TEI_P4', u'TEI_P4'), (u'TEI_P5', u'TEI_P5'), (u'TimeML', u'TimeML'), (u'XCES', u'XCES'), (u'XLIFF', u'XLIFF'), (u'WordNet', u'Word Net'), (u'other', u'Other'))", 'max_length': '13', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'languageId': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'languageName': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'languageVarietyName': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '2', 'choices': "((u'text', u'Text'), (u'audio', u'Audio'), (u'video', u'Video'), (u'image', u'Image'), (u'textNumerical', u'Text Numerical'))"}),
            'mimeType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'text/plain', u'Text/plain'), (u'application/vnd.xmi+xml', u'Application/vnd.xmi+xml'), (u'text/xml', u'Text/xml'), (u'application/x-tmx+xml', u'Application/x - Tmx+xml'), (u'application/x-xces+xml', u'Application/x - Xces+xml'), (u'application/tei+xml', u'Application/tei+xml'), (u'application/rdf+xml', u'Application/rdf+xml'), (u'application/xhtml+xml', u'Application/xhtml+xml'), (u'application/emma+xml', u'Application/emma+xml'), (u'application/pls+xml', u'Application/pls+xml'), (u'application/voicexml+xml', u'Application/voicexml+xml'), (u'text/sgml', u'Text/sgml'), (u'text/html', u'Text/html'), (u'application/x-tex', u'Application/x - Tex'), (u'application/rtf', u'Application/rtf'), (u'application/x-latex', u'Application/x - Latex'), (u'text/csv', u'Text/csv'), (u'text/tab-separated-values', u'Text/tab - Separated - Values'), (u'application/pdf', u'Application/pdf'), (u'application/x-msaccess', u'Application/x - Msaccess'), (u'audio/mp4', u'Audio/mp4'), (u'audio/mpeg', u'Audio/mpeg'), (u'audio/wav', u'Audio/wav'), (u'image/bmp', u'Image/bmp'), (u'image/gif', u'Image/gif'), (u'image/jpeg', u'Image/jpeg'), (u'image/png', u'Image/png'), (u'image/svg+xml', u'Image/svg+xml'), (u'image/tiff', u'Image/tiff'), (u'video/jpeg', u'Video/jpeg'), (u'video/mp4', u'Video/mp4'), (u'video/mpeg', u'Video/mpeg'), (u'video/x-flv', u'Video/x - Flv'), (u'video/x-msvideo', u'Video/x - Msvideo'), (u'video/x-ms-wmv', u'Video/x - Ms - Wmv'), (u'application/msword', u'Application/msword'), (u'application/vnd.ms-excel', u'Application/vnd.ms - Excel'), (u'audio/mpeg3', u'Audio/mpeg3'), (u'text/turtle', u'Text/turtle'), (u'audio/flac', u'Audio/flac'), (u'audio/PCMA', u'Audio/PCMA'), (u'audio/speex', u'Audio/speex'), (u'audio/vorbis', u'Audio/vorbis'), (u'video/mp2t', u'Video/mp2t'), (u'other', u'Other'))", 'max_length': '12', 'blank': 'True'}),
            'modalityType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'bodyGesture', u'Body Gesture'), (u'facialExpression', u'Facial Expression'), (u'voice', u'Voice'), (u'combinationOfModalities', u'Combination Of Modalities'), (u'signLanguage', u'Sign Language'), (u'spokenLanguage', u'Spoken Language'), (u'writtenLanguage', u'Written Language'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'}),
            'resourceType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'corpus', u'Corpus'), (u'lexicalConceptualResource', u'Lexical Conceptual Resource'), (u'languageDescription', u'Language Description'))", 'max_length': '1', 'blank': 'True'}),
            'segmentationLevel': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'paragraph', u'Paragraph'), (u'sentence', u'Sentence'), (u'clause', u'Clause'), (u'word', u'Word'), (u'wordGroup', u'Word Group'), (u'utterance', u'Utterance'), (u'topic', u'Topic'), (u'signal', u'Signal'), (u'phoneme', u'Phoneme'), (u'syllable', u'Syllable'), (u'phrase', u'Phrase'), (u'diphone', u'Diphone'), (u'prosodicBoundaries', u'Prosodic Boundaries'), (u'frame', u'Frame'), (u'scene', u'Scene'), (u'shot', u'Shot'), (u'token', u'Token'), (u'other', u'Other'))", 'max_length': '5', 'blank': 'True'}),
            'tagset': ('metashare.repository.fields.MultiTextField', [], {'max_length': '500', 'blank': 'True'})
        },
        'repository.invisiblestringmodel': {
            'Meta': {'object_name': 'InvisibleStringModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'repository.languagedescriptionencodinginfotype_model': {
            'Meta': {'object_name': 'languageDescriptionEncodingInfoType_model'},
            'conformanceToStandardsBestPractices': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'BML', u'BML'), (u'CES', u'CES'), (u'EAGLES', u'EAGLES'), (u'EML', u'EML'), (u'EMMA', u'EMMA'), (u'GMX', u'GMX'), (u'GrAF', u'GrAF'), (u'HamNoSys', u'Ham No Sys'), (u'InkML', u'InkML'), (u'ILSP_NLP', u'ILSP_NLP'), (u'ISO12620', u'ISO12620'), (u'ISO16642', u'ISO16642'), (u'ISO1987', u'ISO1987'), (u'ISO26162', u'ISO26162'), (u'ISO30042', u'ISO30042'), (u'ISO704', u'ISO704'), (u'LAF', u'LAF'), (u'LMF', u'LMF'), (u'MAF', u'MAF'), (u'MLIF', u'MLIF'), (u'MOSES', u'MOSES'), (u'MULTEXT', u'MULTEXT'), (u'MUMIN', u'MUMIN'), (u'multimodalInteractionFramework', u'Multimodal Interaction Framework'), (u'OAXAL', u'OAXAL'), (u'OWL', u'OWL'), (u'PANACEA', u'PANACEA'), (u'pennTreeBank', u'Penn Tree Bank'), (u'pragueTreebank', u'Prague Treebank'), (u'RDF', u'RDF'), (u'SemAF', u'SemAF'), (u'SemAF_DA', u'SemAF_DA'), (u'SemAF_NE', u'SemAF_NE'), (u'SemAF_SRL', u'SemAF_SRL'), (u'SemAF_DS', u'SemAF_DS'), (u'SKOS', u'SKOS'), (u'SRX', u'SRX'), (u'SynAF', u'SynAF'), (u'TBX', u'TBX'), (u'TMX', u'TMX'), (u'TEI', u'TEI'), (u'TEI_P3', u'TEI_P3'), (u'TEI_P4', u'TEI_P4'), (u'TEI_P5', u'TEI_P5'), (u'TimeML', u'TimeML'), (u'XCES', u'XCES'), (u'XLIFF', u'XLIFF'), (u'WordNet', u'Word Net'), (u'other', u'Other'))", 'max_length': '13', 'blank': 'True'}),
            'encodingLevel': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '2', 'choices': "((u'phonetics', u'Phonetics'), (u'phonology', u'Phonology'), (u'semantics', u'Semantics'), (u'morphology', u'Morphology'), (u'syntax', u'Syntax'), (u'pragmatics', u'Pragmatics'), (u'other', u'Other'))"}),
            'formalism': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'grammaticalPhenomenaCoverage': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'clauseStructure', u'Clause Structure'), (u'ppAttachment', u'Pp Attachment'), (u'npStructure', u'Np Structure'), (u'coordination', u'Coordination'), (u'anaphora', u'Anaphora'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'anaphoraResolution', u'Anaphora Resolution'), (u'chunking', u'Chunking'), (u'parsing', u'Parsing'), (u'npRecognition', u'Np Recognition'), (u'titlesParsing', u'Titles Parsing'), (u'definitionsParsing', u'Definitions Parsing'), (u'analysis', u'Analysis'), (u'generation', u'Generation'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'}),
            'theoreticModel': ('metashare.repository.fields.MultiTextField', [], {'max_length': '500', 'blank': 'True'}),
            'weightedGrammar': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'repository.languagedescriptionimageinfotype_model': {
            'Meta': {'object_name': 'languageDescriptionImageInfoType_model'},
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imageContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.imageContentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'image'", 'max_length': '1000'})
        },
        'repository.languagedescriptioninfotype_model': {
            'Meta': {'object_name': 'languageDescriptionInfoType_model', '_ormbases': ['repository.resourceComponentTypeType_model']},
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'languageDescriptionEncodingInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.languageDescriptionEncodingInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'languageDescriptionMediaType': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.languageDescriptionMediaTypeType_model']", 'unique': 'True'}),
            'languageDescriptionOperationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.languageDescriptionOperationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'languageDescriptionPerformanceInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.languageDescriptionPerformanceInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'languageDescriptionType': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'resourceType': ('metashare.repository.fields.XmlCharField', [], {'default': "'languageDescription'", 'max_length': '30'}),
            'resourcecomponenttypetype_model_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.resourceComponentTypeType_model']", 'unique': 'True', 'primary_key': 'True'})
        },
        'repository.languagedescriptionmediatypetype_model': {
            'Meta': {'object_name': 'languageDescriptionMediaTypeType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'languageDescriptionImageInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'languageDescriptionTextInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'languageDescriptionVideoInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.languagedescriptionoperationinfotype_model': {
            'Meta': {'object_name': 'languageDescriptionOperationInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'relatedLexiconInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.relatedLexiconInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'runningEnvironmentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.runningEnvironmentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.languagedescriptionperformanceinfotype_model': {
            'Meta': {'object_name': 'languageDescriptionPerformanceInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'output': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'robustness': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'shallowness': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'repository.languagedescriptiontextinfotype_model': {
            'Meta': {'object_name': 'languageDescriptionTextInfoType_model'},
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'text'", 'max_length': '1000'}),
            'modalityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.modalityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.languagedescriptionvideoinfotype_model': {
            'Meta': {'object_name': 'languageDescriptionVideoInfoType_model'},
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'video'", 'max_length': '1000'}),
            'videoContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.videoContentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.languageinfotype_model': {
            'Meta': {'object_name': 'languageInfoType_model'},
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptiontextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcetextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcevideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'languageId': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100'}),
            'languageName': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'languageScript': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'languageVarietyInfo': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'languageVarietyInfo_languageinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.languageVarietyInfoType_model']"}),
            'region': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'sizePerLanguage': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'variant': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.languagevarietyinfotype_model': {
            'Meta': {'object_name': 'languageVarietyInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'languageVarietyName': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100'}),
            'languageVarietyType': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'sizePerLanguageVariety': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.lexicalconceptualresourceaudioinfotype_model': {
            'Meta': {'object_name': 'lexicalConceptualResourceAudioInfoType_model'},
            'audioContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.audioContentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'audio'", 'max_length': '1000'})
        },
        'repository.lexicalconceptualresourceencodinginfotype_model': {
            'Meta': {'object_name': 'lexicalConceptualResourceEncodingInfoType_model'},
            'conformanceToStandardsBestPractices': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'BML', u'BML'), (u'CES', u'CES'), (u'EAGLES', u'EAGLES'), (u'EML', u'EML'), (u'EMMA', u'EMMA'), (u'GMX', u'GMX'), (u'GrAF', u'GrAF'), (u'HamNoSys', u'Ham No Sys'), (u'InkML', u'InkML'), (u'ILSP_NLP', u'ILSP_NLP'), (u'ISO12620', u'ISO12620'), (u'ISO16642', u'ISO16642'), (u'ISO1987', u'ISO1987'), (u'ISO26162', u'ISO26162'), (u'ISO30042', u'ISO30042'), (u'ISO704', u'ISO704'), (u'LAF', u'LAF'), (u'LMF', u'LMF'), (u'MAF', u'MAF'), (u'MLIF', u'MLIF'), (u'MOSES', u'MOSES'), (u'MULTEXT', u'MULTEXT'), (u'MUMIN', u'MUMIN'), (u'multimodalInteractionFramework', u'Multimodal Interaction Framework'), (u'OAXAL', u'OAXAL'), (u'OWL', u'OWL'), (u'PANACEA', u'PANACEA'), (u'pennTreeBank', u'Penn Tree Bank'), (u'pragueTreebank', u'Prague Treebank'), (u'RDF', u'RDF'), (u'SemAF', u'SemAF'), (u'SemAF_DA', u'SemAF_DA'), (u'SemAF_NE', u'SemAF_NE'), (u'SemAF_SRL', u'SemAF_SRL'), (u'SemAF_DS', u'SemAF_DS'), (u'SKOS', u'SKOS'), (u'SRX', u'SRX'), (u'SynAF', u'SynAF'), (u'TBX', u'TBX'), (u'TMX', u'TMX'), (u'TEI', u'TEI'), (u'TEI_P3', u'TEI_P3'), (u'TEI_P4', u'TEI_P4'), (u'TEI_P5', u'TEI_P5'), (u'TimeML', u'TimeML'), (u'XCES', u'XCES'), (u'XLIFF', u'XLIFF'), (u'WordNet', u'Word Net'), (u'other', u'Other'))", 'max_length': '13', 'blank': 'True'}),
            'encodingLevel': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '2', 'choices': "((u'phonetics', u'Phonetics'), (u'phonology', u'Phonology'), (u'semantics', u'Semantics'), (u'morphology', u'Morphology'), (u'syntax', u'Syntax'), (u'pragmatics', u'Pragmatics'), (u'other', u'Other'))"}),
            'externalRef': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'extraTextualInformationUnit': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'word', u'Word'), (u'lemma', u'Lemma'), (u'semantics', u'Semantics'), (u'example', u'Example'), (u'syntax', u'Syntax'), (u'lexicalUnit', u'Lexical Unit'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'extratextualInformation': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'images', u'Images'), (u'videos', u'Videos'), (u'soundRecordings', u'Sound Recordings'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linguisticInformation': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'accentuation', u'Accentuation'), (u'lemma', u'Lemma'), (u'lemma-MultiWordUnits', u'Lemma - Multi Word Units'), (u'lemma-Variants', u'Lemma - Variants'), (u'lemma-Abbreviations', u'Lemma - Abbreviations'), (u'lemma-Compounds', u'Lemma - Compounds'), (u'lemma-CliticForms', u'Lemma - Clitic Forms'), (u'partOfSpeech', u'Part Of Speech'), (u'morpho-Case', u'Morpho - Case'), (u'morpho-Gender', u'Morpho - Gender'), (u'morpho-Number', u'Morpho - Number'), (u'morpho-Degree', u'Morpho - Degree'), (u'morpho-IrregularForms', u'Morpho - Irregular Forms'), (u'morpho-Mood', u'Morpho - Mood'), (u'morpho-Tense', u'Morpho - Tense'), (u'morpho-Person', u'Morpho - Person'), (u'morpho-Aspect', u'Morpho - Aspect'), (u'morpho-Voice', u'Morpho - Voice'), (u'morpho-Auxiliary', u'Morpho - Auxiliary'), (u'morpho-Inflection', u'Morpho - Inflection'), (u'morpho-Reflexivity', u'Morpho - Reflexivity'), (u'syntax-SubcatFrame', u'Syntax - Subcat Frame'), (u'semantics-Traits', u'Semantics - Traits'), (u'semantics-SemanticClass', u'Semantics - Semantic Class'), (u'semantics-CrossReferences', u'Semantics - Cross References'), (u'semantics-Relations', u'Semantics - Relations'), (u'semantics-Relations-Hyponyms', u'Semantics - Relations - Hyponyms'), (u'semantics-Relations-Hyperonyms', u'Semantics - Relations - Hyperonyms'), (u'semantics-Relations-Synonyms', u'Semantics - Relations - Synonyms'), (u'semantics-Relations-Antonyms', u'Semantics - Relations - Antonyms'), (u'semantics-Relations-Troponyms', u'Semantics - Relations - Troponyms'), (u'semantics-Relations-Meronyms', u'Semantics - Relations - Meronyms'), (u'usage-Frequency', u'Usage - Frequency'), (u'usage-Register', u'Usage - Register'), (u'usage-Collocations', u'Usage - Collocations'), (u'usage-Examples', u'Usage - Examples'), (u'usage-Notes', u'Usage - Notes'), (u'definition/gloss', u'Definition/gloss'), (u'translationEquivalent', u'Translation Equivalent'), (u'phonetics-Transcription', u'Phonetics - Transcription'), (u'semantics-Domain', u'Semantics - Domain'), (u'semantics-EventType', u'Semantics - Event Type'), (u'semantics-SemanticRoles', u'Semantics - Semantic Roles'), (u'statisticalProperties', u'Statistical Properties'), (u'morpho-Derivation', u'Morpho - Derivation'), (u'semantics-QualiaStructure', u'Semantics - Qualia Structure'), (u'syntacticoSemanticLinks', u'Syntactico Semantic Links'), (u'other', u'Other'))", 'max_length': '13', 'blank': 'True'}),
            'theoreticModel': ('metashare.repository.fields.MultiTextField', [], {'max_length': '500', 'blank': 'True'})
        },
        'repository.lexicalconceptualresourceimageinfotype_model': {
            'Meta': {'object_name': 'lexicalConceptualResourceImageInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imageContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.imageContentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'image'", 'max_length': '1000'})
        },
        'repository.lexicalconceptualresourceinfotype_model': {
            'Meta': {'object_name': 'lexicalConceptualResourceInfoType_model', '_ormbases': ['repository.resourceComponentTypeType_model']},
            'creationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.creationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lexicalConceptualResourceEncodingInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lexicalConceptualResourceEncodingInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lexicalConceptualResourceMediaType': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lexicalConceptualResourceMediaTypeType_model']", 'unique': 'True'}),
            'lexicalConceptualResourceType': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'resourceType': ('metashare.repository.fields.XmlCharField', [], {'default': "'lexicalConceptualResource'", 'max_length': '1000'}),
            'resourcecomponenttypetype_model_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.resourceComponentTypeType_model']", 'unique': 'True', 'primary_key': 'True'})
        },
        'repository.lexicalconceptualresourcemediatypetype_model': {
            'Meta': {'object_name': 'lexicalConceptualResourceMediaTypeType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lexicalConceptualResourceAudioInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lexicalConceptualResourceAudioInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lexicalConceptualResourceImageInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lexicalConceptualResourceImageInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lexicalConceptualResourceTextInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'lexicalConceptualResourceVideoInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lexicalConceptualResourceVideoInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.lexicalconceptualresourcetextinfotype_model': {
            'Meta': {'object_name': 'lexicalConceptualResourceTextInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'text'", 'max_length': '1000'})
        },
        'repository.lexicalconceptualresourcevideoinfotype_model': {
            'Meta': {'object_name': 'lexicalConceptualResourceVideoInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.lingualityInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.XmlCharField', [], {'default': "'video'", 'max_length': '1000'}),
            'videoContentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.videoContentInfoType_model']", 'unique': 'True'})
        },
        'repository.licenceinfotype_model': {
            'Meta': {'object_name': 'licenceInfoType_model'},
            'attributionText': ('metashare.repository.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'back_to_distributioninfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.distributionInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'distributionAccessMedium': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'webExecutable', u'Web Executable'), (u'paperCopy', u'Paper Copy'), (u'hardDisk', u'Hard Disk'), (u'bluRay', u'Blu Ray'), (u'DVD-R', u'DVD - R'), (u'CD-ROM', u'CD - ROM'), (u'downloadable', u'Downloadable'), (u'accessibleThroughInterface', u'Accessible Through Interface'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'}),
            'distributionRightsHolder': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'distributionRightsHolder_licenceinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.actorInfoType_model']"}),
            'downloadLocation': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'executionLocation': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'fee': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'licence': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '10', 'choices': "((u'CC-BY', u'CC - BY'), (u'CC-BY-NC', u'CC - BY - NC'), (u'CC-BY-NC-ND', u'CC - BY - NC - ND'), (u'CC-BY-NC-SA', u'CC - BY - NC - SA'), (u'CC-BY-ND', u'CC - BY - ND'), (u'CC-BY-SA', u'CC - BY - SA'), (u'CC-ZERO', u'CC - ZERO'), (u'MS-C-NoReD', u'MS - C - No ReD'), (u'MS-C-NoReD-FF', u'MS - C - No ReD - FF'), (u'MS-C-NoReD-ND', u'MS - C - No ReD - ND'), (u'MS-C-NoReD-ND-FF', u'MS - C - No ReD - ND - FF'), (u'MS-NC-NoReD', u'MS - NC - No ReD'), (u'MS-NC-NoReD-FF', u'MS - NC - No ReD - FF'), (u'MS-NC-NoReD-ND', u'MS - NC - No ReD - ND'), (u'MS-NC-NoReD-ND-FF', u'MS - NC - No ReD - ND - FF'), (u'MSCommons-BY', u'MS Commons - BY'), (u'MSCommons-BY-NC', u'MS Commons - BY - NC'), (u'MSCommons-BY-NC-ND', u'MS Commons - BY - NC - ND'), (u'MSCommons-BY-NC-SA', u'MS Commons - BY - NC - SA'), (u'MSCommons-BY-ND', u'MS Commons - BY - ND'), (u'MSCommons-BY-SA', u'MS Commons - BY - SA'), (u'CLARIN_ACA', u'CLARIN_ACA'), (u'CLARIN_ACA-NC', u'CLARIN_ACA - NC'), (u'CLARIN_PUB', u'CLARIN_PUB'), (u'CLARIN_RES', u'CLARIN_RES'), (u'ELRA_END_USER', u'ELRA_END_USER'), (u'ELRA_EVALUATION', u'ELRA_EVALUATION'), (u'ELRA_VAR', u'ELRA_VAR'), (u'AGPL', u'AGPL'), (u'ApacheLicence_2.0', u'Apache Licence_2.0'), (u'BSD', u'BSD'), (u'BSD-style', u'BSD - Style'), (u'GFDL', u'GFDL'), (u'GPL', u'GPL'), (u'LGPL', u'LGPL'), (u'Princeton_Wordnet', u'Princeton_ Wordnet'), (u'proprietary', u'Proprietary'), (u'underNegotiation', u'Under Negotiation'), (u'other', u'Other'))"}),
            'licensor': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'licensor_licenceinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.actorInfoType_model']"}),
            'membershipInfo': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'membershipInfo_licenceinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.membershipInfoType_model']"}),
            'restrictionsOfUse': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'informLicensor', u'Inform Licensor'), (u'redeposit', u'Redeposit'), (u'onlyMSmembers', u'OnlyM Smembers'), (u'academic-nonCommercialUse', u'Academic - Non Commercial Use'), (u'evaluationUse', u'Evaluation Use'), (u'commercialUse', u'Commercial Use'), (u'attribution', u'Attribution'), (u'shareAlike', u'Share Alike'), (u'noDerivatives', u'No Derivatives'), (u'noRedistribution', u'No Redistribution'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'}),
            'userNature': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'academic', u'Academic'), (u'commercial', u'Commercial'))", 'max_length': '1', 'blank': 'True'})
        },
        'repository.lingualityinfotype_model': {
            'Meta': {'object_name': 'lingualityInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lingualityType': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'multilingualityType': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'multilingualityTypeDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '512', 'blank': 'True'})
        },
        'repository.linktoothermediainfotype_model': {
            'Meta': {'object_name': 'linkToOtherMediaInfoType_model'},
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextnumericalinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNumericalInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptiontextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mediaTypeDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'otherMedia': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'synchronizedWithAudio': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'synchronizedWithImage': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'synchronizedWithText': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'synchronizedWithTextNumerical': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'synchronizedWithVideo': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'repository.membershipinfotype_model': {
            'Meta': {'object_name': 'membershipInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True'}),
            'membershipInstitution': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '2', 'choices': "((u'ELRA', u'ELRA'), (u'LDC', u'LDC'), (u'TST-CENTRALE', u'TST - CENTRALE'), (u'other', u'Other'))"})
        },
        'repository.metadatainfotype_model': {
            'Meta': {'object_name': 'metadataInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadataCreationDate': ('django.db.models.fields.DateField', [], {}),
            'metadataCreator': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'metadataCreator_metadatainfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.personInfoType_model']"}),
            'metadataLanguageId': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'metadataLanguageName': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'metadataLastDateUpdated': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'originalMetadataLink': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'originalMetadataSchema': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'revision': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'source': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'})
        },
        'repository.modalityinfotype_model': {
            'Meta': {'object_name': 'modalityInfoType_model'},
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextnumericalinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNumericalInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcetextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcevideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modalityType': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '3', 'choices': "((u'bodyGesture', u'Body Gesture'), (u'facialExpression', u'Facial Expression'), (u'voice', u'Voice'), (u'combinationOfModalities', u'Combination Of Modalities'), (u'signLanguage', u'Sign Language'), (u'spokenLanguage', u'Spoken Language'), (u'writtenLanguage', u'Written Language'), (u'other', u'Other'))"}),
            'modalityTypeDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'sizePerModality': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.ngraminfotype_model': {
            'Meta': {'object_name': 'ngramInfoType_model'},
            'baseItem': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '2', 'choices': "((u'word', u'Word'), (u'syllable', u'Syllable'), (u'letter', u'Letter'), (u'phoneme', u'Phoneme'), (u'other', u'Other'))"}),
            'factors': ('metashare.repository.fields.MultiTextField', [], {'max_length': '150', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interpolated': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'isFactored': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'perplexity': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'smoothing': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.organizationinfotype_model': {
            'Meta': {'object_name': 'organizationInfoType_model', '_ormbases': ['repository.actorInfoType_model']},
            'actorinfotype_model_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.actorInfoType_model']", 'unique': 'True', 'primary_key': 'True'}),
            'communicationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.communicationInfoType_model']", 'unique': 'True'}),
            'copy_status': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'departmentName': ('metashare.repository.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'organizationName': ('metashare.repository.fields.DictField', [], {'null': 'True'}),
            'organizationShortName': ('metashare.repository.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'default': "'http://127.0.0.1:8000'", 'max_length': '200'})
        },
        'repository.organizationlisttype_model': {
            'Meta': {'object_name': 'organizationListType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organizationInfo': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'organizationInfo_organizationlisttype_model_related'", 'symmetrical': 'False', 'to': "orm['repository.organizationInfoType_model']"})
        },
        'repository.outputinfotype_model': {
            'Meta': {'object_name': 'outputInfoType_model'},
            'annotationFormat': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'annotationType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'alignment', u'Alignment'), (u'discourseAnnotation', u'Discourse Annotation'), (u'discourseAnnotation-audienceReactions', u'Discourse Annotation - Audience Reactions'), (u'discourseAnnotation-coreference', u'Discourse Annotation - Coreference'), (u'discourseAnnotation-dialogueActs', u'Discourse Annotation - Dialogue Acts'), (u'discourseAnnotation-discourseRelations', u'Discourse Annotation - Discourse Relations'), (u'lemmatization', u'Lemmatization'), (u'morphosyntacticAnnotation-bPosTagging', u'Morphosyntactic Annotation - B Pos Tagging'), (u'morphosyntacticAnnotation-posTagging', u'Morphosyntactic Annotation - Pos Tagging'), (u'segmentation', u'Segmentation'), (u'semanticAnnotation', u'Semantic Annotation'), (u'semanticAnnotation-certaintyLevel', u'Semantic Annotation - Certainty Level'), (u'semanticAnnotation-emotions', u'Semantic Annotation - Emotions'), (u'semanticAnnotation-entityMentions', u'Semantic Annotation - Entity Mentions'), (u'semanticAnnotation-events', u'Semantic Annotation - Events'), (u'semanticAnnotation-namedEntities', u'Semantic Annotation - Named Entities'), (u'semanticAnnotation-polarity', u'Semantic Annotation - Polarity'), (u'semanticAnnotation-questionTopicalTarget', u'Semantic Annotation - Question Topical Target'), (u'semanticAnnotation-semanticClasses', u'Semantic Annotation - Semantic Classes'), (u'semanticAnnotation-semanticRelations', u'Semantic Annotation - Semantic Relations'), (u'semanticAnnotation-semanticRoles', u'Semantic Annotation - Semantic Roles'), (u'semanticAnnotation-speechActs', u'Semantic Annotation - Speech Acts'), (u'semanticAnnotation-temporalExpressions', u'Semantic Annotation - Temporal Expressions'), (u'semanticAnnotation-textualEntailment', u'Semantic Annotation - Textual Entailment'), (u'semanticAnnotation-wordSenses', u'Semantic Annotation - Word Senses'), (u'speechAnnotation', u'Speech Annotation'), (u'speechAnnotation-orthographicTranscription', u'Speech Annotation - Orthographic Transcription'), (u'speechAnnotation-paralanguageAnnotation', u'Speech Annotation - Paralanguage Annotation'), (u'speechAnnotation-phoneticTranscription', u'Speech Annotation - Phonetic Transcription'), (u'speechAnnotation-prosodicAnnotation', u'Speech Annotation - Prosodic Annotation'), (u'speechAnnotation-soundEvents', u'Speech Annotation - Sound Events'), (u'speechAnnotation-soundToTextAlignment', u'Speech Annotation - Sound To Text Alignment'), (u'speechAnnotation-speakerIdentification', u'Speech Annotation - Speaker Identification'), (u'speechAnnotation-speakerTurns', u'Speech Annotation - Speaker Turns'), (u'stemming', u'Stemming'), (u'structuralAnnotation', u'Structural Annotation'), (u'syntacticAnnotation-subcategorizationFrames', u'Syntactic Annotation - Subcategorization Frames'), (u'syntacticAnnotation-dependencyTrees', u'Syntactic Annotation - Dependency Trees'), (u'syntacticAnnotation-constituencyTrees', u'Syntactic Annotation - Constituency Trees'), (u'syntacticosemanticAnnotation-links', u'Syntacticosemantic Annotation - Links'), (u'translation', u'Translation'), (u'transliteration', u'Transliteration'), (u'modalityAnnotation-bodyMovements', u'Modality Annotation - Body Movements'), (u'modalityAnnotation-facialExpressions', u'Modality Annotation - Facial Expressions'), (u'modalityAnnotation-gazeEyeMovements', u'Modality Annotation - Gaze Eye Movements'), (u'modalityAnnotation-handArmGestures', u'Modality Annotation - Hand Arm Gestures'), (u'modalityAnnotation-handManipulationOfObjects', u'Modality Annotation - Hand Manipulation Of Objects'), (u'modalityAnnotation-headMovements', u'Modality Annotation - Head Movements'), (u'modalityAnnotation-lipMovements', u'Modality Annotation - Lip Movements'), (u'other', u'Other'))", 'max_length': '13', 'blank': 'True'}),
            'characterEncoding': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'US-ASCII', u'US - ASCII'), (u'windows-1250', u'Windows - 1250'), (u'windows-1251', u'Windows - 1251'), (u'windows-1252', u'Windows - 1252'), (u'windows-1253', u'Windows - 1253'), (u'windows-1254', u'Windows - 1254'), (u'windows-1257', u'Windows - 1257'), (u'ISO-8859-1', u'ISO - 8859 - 1'), (u'ISO-8859-2', u'ISO - 8859 - 2'), (u'ISO-8859-4', u'ISO - 8859 - 4'), (u'ISO-8859-5', u'ISO - 8859 - 5'), (u'ISO-8859-7', u'ISO - 8859 - 7'), (u'ISO-8859-9', u'ISO - 8859 - 9'), (u'ISO-8859-13', u'ISO - 8859 - 13'), (u'ISO-8859-15', u'ISO - 8859 - 15'), (u'KOI8-R', u'KOI8 - R'), (u'UTF-8', u'UTF - 8'), (u'UTF-16', u'UTF - 16'), (u'UTF-16BE', u'UTF - 16BE'), (u'UTF-16LE', u'UTF - 16LE'), (u'windows-1255', u'Windows - 1255'), (u'windows-1256', u'Windows - 1256'), (u'windows-1258', u'Windows - 1258'), (u'ISO-8859-3', u'ISO - 8859 - 3'), (u'ISO-8859-6', u'ISO - 8859 - 6'), (u'ISO-8859-8', u'ISO - 8859 - 8'), (u'windows-31j', u'Windows - 31j'), (u'EUC-JP', u'EUC - JP'), (u'x-EUC-JP-LINUX', u'X - EUC - JP - LINUX'), (u'Shift_JIS', u'Shift_JIS'), (u'ISO-2022-JP', u'ISO - 2022 - JP'), (u'x-mswin-936', u'X - Mswin - 936'), (u'GB18030', u'GB18030'), (u'x-EUC-CN', u'X - EUC - CN'), (u'GBK', u'GBK'), (u'ISCII91', u'ISCII91'), (u'x-windows-949', u'X - Windows - 949'), (u'EUC-KR', u'EUC - KR'), (u'ISO-2022-KR', u'ISO - 2022 - KR'), (u'x-windows-950', u'X - Windows - 950'), (u'x-MS950-HKSCS', u'X - MS950 - HKSCS'), (u'x-EUC-TW', u'X - EUC - TW'), (u'Big5', u'Big5'), (u'Big5-HKSCS', u'Big5 - HKSCS'), (u'TIS-620', u'TIS - 620'), (u'Big5_Solaris', u'Big5_ Solaris'), (u'Cp037', u'Cp037'), (u'Cp273', u'Cp273'), (u'Cp277', u'Cp277'), (u'Cp278', u'Cp278'), (u'Cp280', u'Cp280'), (u'Cp284', u'Cp284'), (u'Cp285', u'Cp285'), (u'Cp297', u'Cp297'), (u'Cp420', u'Cp420'), (u'Cp424', u'Cp424'), (u'Cp437', u'Cp437'), (u'Cp500', u'Cp500'), (u'Cp737', u'Cp737'), (u'Cp775', u'Cp775'), (u'Cp838', u'Cp838'), (u'Cp850', u'Cp850'), (u'Cp852', u'Cp852'), (u'Cp855', u'Cp855'), (u'Cp856', u'Cp856'), (u'Cp857', u'Cp857'), (u'Cp858', u'Cp858'), (u'Cp860', u'Cp860'), (u'Cp861', u'Cp861'), (u'Cp862', u'Cp862'), (u'Cp863', u'Cp863'), (u'Cp864', u'Cp864'), (u'Cp865', u'Cp865'), (u'Cp866', u'Cp866'), (u'Cp868', u'Cp868'), (u'Cp869', u'Cp869'), (u'Cp870', u'Cp870'), (u'Cp871', u'Cp871'), (u'Cp874', u'Cp874'), (u'Cp875', u'Cp875'), (u'Cp918', u'Cp918'), (u'Cp921', u'Cp921'), (u'Cp922', u'Cp922'), (u'Cp930', u'Cp930'), (u'Cp933', u'Cp933'), (u'Cp935', u'Cp935'), (u'Cp937', u'Cp937'), (u'Cp939', u'Cp939'), (u'Cp942', u'Cp942'), (u'Cp942C', u'Cp942C'), (u'Cp943', u'Cp943'), (u'Cp943C', u'Cp943C'), (u'Cp948', u'Cp948'), (u'Cp949', u'Cp949'), (u'Cp949C', u'Cp949C'), (u'Cp950', u'Cp950'), (u'Cp964', u'Cp964'), (u'Cp970', u'Cp970'), (u'Cp1006', u'Cp1006'), (u'Cp1025', u'Cp1025'), (u'Cp1026', u'Cp1026'), (u'Cp1046', u'Cp1046'), (u'Cp1047', u'Cp1047'), (u'Cp1097', u'Cp1097'), (u'Cp1098', u'Cp1098'), (u'Cp1112', u'Cp1112'), (u'Cp1122', u'Cp1122'), (u'Cp1123', u'Cp1123'), (u'Cp1124', u'Cp1124'), (u'Cp1140', u'Cp1140'), (u'Cp1141', u'Cp1141'), (u'Cp1142', u'Cp1142'), (u'Cp1143', u'Cp1143'), (u'Cp1144', u'Cp1144'), (u'Cp1145', u'Cp1145'), (u'Cp1146', u'Cp1146'), (u'Cp1147', u'Cp1147'), (u'Cp1148', u'Cp1148'), (u'Cp1149', u'Cp1149'), (u'Cp1381', u'Cp1381'), (u'Cp1383', u'Cp1383'), (u'Cp33722', u'Cp33722'), (u'ISO2022_CN_CNS', u'ISO2022_CN_CNS'), (u'ISO2022_CN_GB', u'ISO2022_CN_GB'), (u'JISAutoDetect', u'JIS Auto Detect'), (u'MS874', u'MS874'), (u'MacArabic', u'Mac Arabic'), (u'MacCentralEurope', u'Mac Central Europe'), (u'MacCroatian', u'Mac Croatian'), (u'MacCyrillic', u'Mac Cyrillic'), (u'MacDingbat', u'Mac Dingbat'), (u'MacGreek', u'Mac Greek'), (u'MacHebrew', u'Mac Hebrew'), (u'MacIceland', u'Mac Iceland'), (u'MacRoman', u'Mac Roman'), (u'MacRomania', u'Mac Romania'), (u'MacSymbol', u'Mac Symbol'), (u'MacThai', u'Mac Thai'), (u'MacTurkish', u'Mac Turkish'), (u'MacUkraine', u'Mac Ukraine'))", 'max_length': '36', 'blank': 'True'}),
            'conformanceToStandardsBestPractices': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'BML', u'BML'), (u'CES', u'CES'), (u'EAGLES', u'EAGLES'), (u'EML', u'EML'), (u'EMMA', u'EMMA'), (u'GMX', u'GMX'), (u'GrAF', u'GrAF'), (u'HamNoSys', u'Ham No Sys'), (u'InkML', u'InkML'), (u'ILSP_NLP', u'ILSP_NLP'), (u'ISO12620', u'ISO12620'), (u'ISO16642', u'ISO16642'), (u'ISO1987', u'ISO1987'), (u'ISO26162', u'ISO26162'), (u'ISO30042', u'ISO30042'), (u'ISO704', u'ISO704'), (u'LAF', u'LAF'), (u'LMF', u'LMF'), (u'MAF', u'MAF'), (u'MLIF', u'MLIF'), (u'MOSES', u'MOSES'), (u'MULTEXT', u'MULTEXT'), (u'MUMIN', u'MUMIN'), (u'multimodalInteractionFramework', u'Multimodal Interaction Framework'), (u'OAXAL', u'OAXAL'), (u'OWL', u'OWL'), (u'PANACEA', u'PANACEA'), (u'pennTreeBank', u'Penn Tree Bank'), (u'pragueTreebank', u'Prague Treebank'), (u'RDF', u'RDF'), (u'SemAF', u'SemAF'), (u'SemAF_DA', u'SemAF_DA'), (u'SemAF_NE', u'SemAF_NE'), (u'SemAF_SRL', u'SemAF_SRL'), (u'SemAF_DS', u'SemAF_DS'), (u'SKOS', u'SKOS'), (u'SRX', u'SRX'), (u'SynAF', u'SynAF'), (u'TBX', u'TBX'), (u'TMX', u'TMX'), (u'TEI', u'TEI'), (u'TEI_P3', u'TEI_P3'), (u'TEI_P4', u'TEI_P4'), (u'TEI_P5', u'TEI_P5'), (u'TimeML', u'TimeML'), (u'XCES', u'XCES'), (u'XLIFF', u'XLIFF'), (u'WordNet', u'Word Net'), (u'other', u'Other'))", 'max_length': '13', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'languageId': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'languageName': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'languageVarietyName': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'mediaType': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '2', 'choices': "((u'text', u'Text'), (u'audio', u'Audio'), (u'video', u'Video'), (u'image', u'Image'), (u'textNumerical', u'Text Numerical'))"}),
            'mimeType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'text/plain', u'Text/plain'), (u'application/vnd.xmi+xml', u'Application/vnd.xmi+xml'), (u'text/xml', u'Text/xml'), (u'application/x-tmx+xml', u'Application/x - Tmx+xml'), (u'application/x-xces+xml', u'Application/x - Xces+xml'), (u'application/tei+xml', u'Application/tei+xml'), (u'application/rdf+xml', u'Application/rdf+xml'), (u'application/xhtml+xml', u'Application/xhtml+xml'), (u'application/emma+xml', u'Application/emma+xml'), (u'application/pls+xml', u'Application/pls+xml'), (u'application/voicexml+xml', u'Application/voicexml+xml'), (u'text/sgml', u'Text/sgml'), (u'text/html', u'Text/html'), (u'application/x-tex', u'Application/x - Tex'), (u'application/rtf', u'Application/rtf'), (u'application/x-latex', u'Application/x - Latex'), (u'text/csv', u'Text/csv'), (u'text/tab-separated-values', u'Text/tab - Separated - Values'), (u'application/pdf', u'Application/pdf'), (u'application/x-msaccess', u'Application/x - Msaccess'), (u'audio/mp4', u'Audio/mp4'), (u'audio/mpeg', u'Audio/mpeg'), (u'audio/wav', u'Audio/wav'), (u'image/bmp', u'Image/bmp'), (u'image/gif', u'Image/gif'), (u'image/jpeg', u'Image/jpeg'), (u'image/png', u'Image/png'), (u'image/svg+xml', u'Image/svg+xml'), (u'image/tiff', u'Image/tiff'), (u'video/jpeg', u'Video/jpeg'), (u'video/mp4', u'Video/mp4'), (u'video/mpeg', u'Video/mpeg'), (u'video/x-flv', u'Video/x - Flv'), (u'video/x-msvideo', u'Video/x - Msvideo'), (u'video/x-ms-wmv', u'Video/x - Ms - Wmv'), (u'application/msword', u'Application/msword'), (u'application/vnd.ms-excel', u'Application/vnd.ms - Excel'), (u'audio/mpeg3', u'Audio/mpeg3'), (u'text/turtle', u'Text/turtle'), (u'audio/flac', u'Audio/flac'), (u'audio/PCMA', u'Audio/PCMA'), (u'audio/speex', u'Audio/speex'), (u'audio/vorbis', u'Audio/vorbis'), (u'video/mp2t', u'Video/mp2t'), (u'other', u'Other'))", 'max_length': '12', 'blank': 'True'}),
            'modalityType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'bodyGesture', u'Body Gesture'), (u'facialExpression', u'Facial Expression'), (u'voice', u'Voice'), (u'combinationOfModalities', u'Combination Of Modalities'), (u'signLanguage', u'Sign Language'), (u'spokenLanguage', u'Spoken Language'), (u'writtenLanguage', u'Written Language'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'}),
            'resourceType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'corpus', u'Corpus'), (u'lexicalConceptualResource', u'Lexical Conceptual Resource'), (u'languageDescription', u'Language Description'))", 'max_length': '1', 'blank': 'True'}),
            'segmentationLevel': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'paragraph', u'Paragraph'), (u'sentence', u'Sentence'), (u'clause', u'Clause'), (u'word', u'Word'), (u'wordGroup', u'Word Group'), (u'utterance', u'Utterance'), (u'topic', u'Topic'), (u'signal', u'Signal'), (u'phoneme', u'Phoneme'), (u'syllable', u'Syllable'), (u'phrase', u'Phrase'), (u'diphone', u'Diphone'), (u'prosodicBoundaries', u'Prosodic Boundaries'), (u'frame', u'Frame'), (u'scene', u'Scene'), (u'shot', u'Shot'), (u'token', u'Token'), (u'other', u'Other'))", 'max_length': '5', 'blank': 'True'}),
            'tagset': ('metashare.repository.fields.MultiTextField', [], {'max_length': '500', 'blank': 'True'})
        },
        'repository.participantinfotype_model': {
            'Meta': {'object_name': 'participantInfoType_model'},
            'age': ('metashare.repository.fields.XmlCharField', [], {'max_length': '50', 'blank': 'True'}),
            'ageGroup': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'alias': ('metashare.repository.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'back_to_personsourcesetinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.personSourceSetInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'dialectAccent': ('metashare.repository.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'educationLevel': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'hearingImpairment': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'height': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'origin': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'placeOfBirth': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'placeOfChildhood': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'placeOfLiving': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'placeOfSecondEducation': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'profession': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'sex': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'smokingHabits': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'speakingImpairment': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'trainedSpeaker': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'vocalTractConditions': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'weight': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'repository.personinfotype_model': {
            'Meta': {'object_name': 'personInfoType_model', '_ormbases': ['repository.actorInfoType_model']},
            'actorinfotype_model_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.actorInfoType_model']", 'unique': 'True', 'primary_key': 'True'}),
            'affiliation': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'affiliation_personinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.organizationInfoType_model']"}),
            'communicationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.communicationInfoType_model']", 'unique': 'True'}),
            'copy_status': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'givenName': ('metashare.repository.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'position': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'sex': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'default': "'http://127.0.0.1:8000'", 'max_length': '200'}),
            'surname': ('metashare.repository.fields.DictField', [], {'null': 'True'})
        },
        'repository.personlisttype_model': {
            'Meta': {'object_name': 'personListType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'personInfo': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'personInfo_personlisttype_model_related'", 'symmetrical': 'False', 'to': "orm['repository.personInfoType_model']"})
        },
        'repository.personsourcesetinfotype_model': {
            'Meta': {'object_name': 'personSourceSetInfoType_model'},
            'ageOfPersons': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'child', u'Child'), (u'teenager', u'Teenager'), (u'adult', u'Adult'), (u'elderly', u'Elderly'))", 'max_length': '2', 'blank': 'True'}),
            'ageRangeEnd': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ageRangeStart': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'dialectAccentOfPersons': ('metashare.repository.fields.MultiTextField', [], {'max_length': '500', 'blank': 'True'}),
            'geographicDistributionOfPersons': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'hearingImpairmentOfPersons': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numberOfPersons': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'numberOfTrainedSpeakers': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'originOfPersons': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'sexOfPersons': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'speakingImpairmentOfPersons': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'speechInfluences': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'alcohol', u'Alcohol'), (u'sleepDeprivation', u'Sleep Deprivation'), (u'hyperbaric', u'Hyperbaric'), (u'medication', u'Medication'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'})
        },
        'repository.projectinfotype_model': {
            'Meta': {'object_name': 'projectInfoType_model'},
            'copy_status': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'funder': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'fundingCountry': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'fundingCountryId': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'fundingType': ('metashare.repository.fields.MultiSelectField', [], {'max_length': '2', 'choices': "((u'other', u'Other'), (u'ownFunds', u'Own Funds'), (u'nationalFunds', u'National Funds'), (u'euFunds', u'Eu Funds'))"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'projectEndDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'projectID': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'projectName': ('metashare.repository.fields.DictField', [], {'null': 'True'}),
            'projectShortName': ('metashare.repository.fields.DictField', [], {'null': 'True', 'blank': 'True'}),
            'projectStartDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'default': "'http://127.0.0.1:8000'", 'max_length': '200'}),
            'url': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.projectlisttype_model': {
            'Meta': {'object_name': 'projectListType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'projectInfo': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'projectInfo_projectlisttype_model_related'", 'symmetrical': 'False', 'to': "orm['repository.projectInfoType_model']"})
        },
        'repository.recordinginfotype_model': {
            'Meta': {'object_name': 'recordingInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recorder': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'recorder_recordinginfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.actorInfoType_model']"}),
            'recordingDeviceType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'hardDisk', u'Hard Disk'), (u'dv', u'Dv'), (u'tapeVHS', u'TapeVHS'), (u'flash', u'Flash'), (u'DAT', u'DAT'), (u'soundBlasterCard', u'Sound Blaster Card'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'recordingDeviceTypeDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'recordingEnvironment': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'office', u'Office'), (u'inCar', u'In Car'), (u'studio', u'Studio'), (u'conferenceRoom', u'Conference Room'), (u'lectureRoom', u'Lecture Room'), (u'industrial', u'Industrial'), (u'transport', u'Transport'), (u'openPublicPlace', u'Open Public Place'), (u'closedPublicPlace', u'Closed Public Place'), (u'anechoicChamber', u'Anechoic Chamber'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'}),
            'recordingPlatformSoftware': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'sourceChannel': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'internet', u'Internet'), (u'radio', u'Radio'), (u'tv', u'Tv'), (u'telephone', u'Telephone'), (u'laryngograph', u'Laryngograph'), (u'airflow', u'Airflow'), (u'EMA', u'EMA'), (u'webCam', u'Web Cam'), (u'camcorder', u'Camcorder'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'}),
            'sourceChannelDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'}),
            'sourceChannelName': ('metashare.repository.fields.MultiTextField', [], {'max_length': '30', 'blank': 'True'}),
            'sourceChannelType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'ISDN', u'ISDN'), (u'GSM', u'GSM'), (u'3G', u'3G'), (u'CDMA', u'CDMA'), (u'DVB-T', u'DVB - T'), (u'DVB-S', u'DVB - S'), (u'DVB-C', u'DVB - C'), (u'VOIP', u'VOIP'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'})
        },
        'repository.relatedlexiconinfotype_model': {
            'Meta': {'object_name': 'relatedLexiconInfoType_model'},
            'attachedLexiconPosition': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'compatibleLexiconType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'wordnet', u'Wordnet'), (u'wordlist', u'Wordlist'), (u'morphologicalLexicon', u'Morphological Lexicon'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'relatedLexiconType': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'repository.relationinfotype_model': {
            'Meta': {'object_name': 'relationInfoType_model'},
            'back_to_resourceinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.resourceInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'relatedResource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.targetResourceInfoType_model']"}),
            'relationType': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100'})
        },
        'repository.resolutioninfotype_model': {
            'Meta': {'object_name': 'resolutionInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resolutionStandard': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'sizeHeight': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sizeWidth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'repository.resourcecomponenttypetype_model': {
            'Meta': {'object_name': 'resourceComponentTypeType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'repository.resourcecreationinfotype_model': {
            'Meta': {'object_name': 'resourceCreationInfoType_model'},
            'creationEndDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'creationStartDate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'fundingProject': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'fundingProject_resourcecreationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.projectInfoType_model']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resourceCreator': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'resourceCreator_resourcecreationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.actorInfoType_model']"})
        },
        'repository.resourcedocumentationinfotype_model': {
            'Meta': {'object_name': 'resourceDocumentationInfoType_model'},
            'documentation': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'documentation_resourcedocumentationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.documentationInfoType_model']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'samplesLocation': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'toolDocumentationType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'online', u'Online'), (u'manual', u'Manual'), (u'helpFunctions', u'Help Functions'), (u'none', u'None'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'})
        },
        'repository.resourceinfotype_model': {
            'Meta': {'object_name': 'resourceInfoType_model'},
            'contactPerson': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'contactPerson_resourceinfotype_model_related'", 'symmetrical': 'False', 'to': "orm['repository.personInfoType_model']"}),
            'distributionInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.distributionInfoType_model']", 'unique': 'True'}),
            'editor_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['accounts.EditorGroup']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identificationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.identificationInfoType_model']", 'unique': 'True'}),
            'metadataInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.metadataInfoType_model']", 'unique': 'True'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'}),
            'resourceComponentType': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.resourceComponentTypeType_model']", 'unique': 'True'}),
            'resourceCreationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.resourceCreationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'resourceDocumentationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.resourceDocumentationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'storage_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storage.StorageObject']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'usageInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.usageInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'versionInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.versionInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.runningenvironmentinfotype_model': {
            'Meta': {'object_name': 'runningEnvironmentInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requiredHardware': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'graphicCard', u'Graphic Card'), (u'microphone', u'Microphone'), (u'ocrSystem', u'Ocr System'), (u'specialHardwareEquipment', u'Special Hardware Equipment'), (u'none', u'None'), (u'other', u'Other'))", 'max_length': '2', 'blank': 'True'}),
            'requiredLRs': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'requiredLRs_runningenvironmentinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"}),
            'requiredSoftware': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'requiredSoftware_runningenvironmentinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"}),
            'runningEnvironmentDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'repository.settinginfotype_model': {
            'Meta': {'object_name': 'settingInfoType_model'},
            'audience': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'conversationalType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'monologue', u'Monologue'), (u'dialogue', u'Dialogue'), (u'multilogue', u'Multilogue'))", 'max_length': '1', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interaction': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'interactivity': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'naturality': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'scenarioType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'frogStory', u'Frog Story'), (u'mapTask', u'Map Task'), (u'onlineEducationalGame', u'Online Educational Game'), (u'pearStory', u'Pear Story'), (u'rolePlay', u'Role Play'), (u'wordGame', u'Word Game'), (u'wizardOfOz', u'Wizard Of Oz'), (u'other', u'Other'))", 'max_length': '3', 'blank': 'True'})
        },
        'repository.sizeinfotype_model': {
            'Meta': {'object_name': 'sizeInfoType_model'},
            'back_to_audiosizeinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.audioSizeInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextnumericalinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNumericalInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptiontextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcetextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcevideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'size': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100'}),
            'sizeUnit': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'repository.staticelementinfotype_model': {
            'Meta': {'object_name': 'staticElementInfoType_model'},
            'artifactParts': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'bodyParts': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'arms', u'Arms'), (u'face', u'Face'), (u'feet', u'Feet'), (u'hands', u'Hands'), (u'head', u'Head'), (u'legs', u'Legs'), (u'mouth', u'Mouth'), (u'wholeBody', u'Whole Body'), (u'none', u'None'))", 'max_length': '3', 'blank': 'True'}),
            'eventDescription': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'faceExpressions': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'faceViews': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'landscapeParts': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'organizationDescription': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'personDescription': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'thingDescription': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'}),
            'typeOfElement': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.targetresourceinfotype_model': {
            'Meta': {'object_name': 'targetResourceInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'targetResourceNameURI': ('metashare.repository.fields.XmlCharField', [], {'max_length': '4500'})
        },
        'repository.textclassificationinfotype_model': {
            'Meta': {'object_name': 'textClassificationInfoType_model'},
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'conformanceToClassificationScheme': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'register': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'sizePerTextClassification': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'subject_topic': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'textGenre': ('metashare.repository.fields.XmlCharField', [], {'max_length': '50', 'blank': 'True'}),
            'textType': ('metashare.repository.fields.XmlCharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'repository.textformatinfotype_model': {
            'Meta': {'object_name': 'textFormatInfoType_model'},
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptiontextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcetextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimeType': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'sizePerTextFormat': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.textnumericalcontentinfotype_model': {
            'Meta': {'object_name': 'textNumericalContentInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'typeOfTextNumericalContent': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000'})
        },
        'repository.textnumericalformatinfotype_model': {
            'Meta': {'object_name': 'textNumericalFormatInfoType_model'},
            'back_to_corpustextnumericalinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNumericalInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimeType': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'sizePerTextNumericalFormat': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'repository.timecoverageinfotype_model': {
            'Meta': {'object_name': 'timeCoverageInfoType_model'},
            'back_to_corpusaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpustextngraminfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusTextNgramInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptiontextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceaudioinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceAudioInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourceimageinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceImageInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcetextinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceTextInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcevideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sizePerTimeCoverage': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'timeCoverage': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100'})
        },
        'repository.toolservicecreationinfotype_model': {
            'Meta': {'object_name': 'toolServiceCreationInfoType_model'},
            'creationDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'formalism': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'implementationLanguage': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'originalSource': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'originalSource_toolservicecreationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"})
        },
        'repository.toolserviceevaluationinfotype_model': {
            'Meta': {'object_name': 'toolServiceEvaluationInfoType_model'},
            'evaluated': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True'}),
            'evaluationCriteria': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'extrinsic', u'Extrinsic'), (u'intrinsic', u'Intrinsic'))", 'max_length': '1', 'blank': 'True'}),
            'evaluationDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'evaluationLevel': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'technological', u'Technological'), (u'usage', u'Usage'), (u'impact', u'Impact'), (u'diagnostic', u'Diagnostic'))", 'max_length': '2', 'blank': 'True'}),
            'evaluationMeasure': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'human', u'Human'), (u'automatic', u'Automatic'))", 'max_length': '1', 'blank': 'True'}),
            'evaluationReport': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'evaluationReport_toolserviceevaluationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.documentationInfoType_model']"}),
            'evaluationTool': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'evaluationTool_toolserviceevaluationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"}),
            'evaluationType': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'glassBox', u'Glass Box'), (u'blackBox', u'Black Box'))", 'max_length': '1', 'blank': 'True'}),
            'evaluator': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'evaluator_toolserviceevaluationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.actorInfoType_model']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'repository.toolserviceinfotype_model': {
            'Meta': {'object_name': 'toolServiceInfoType_model', '_ormbases': ['repository.resourceComponentTypeType_model']},
            'inputInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.inputInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'languageDependent': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True'}),
            'outputInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.outputInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'resourceType': ('metashare.repository.fields.XmlCharField', [], {'default': "'toolService'", 'max_length': '1000'}),
            'resourcecomponenttypetype_model_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.resourceComponentTypeType_model']", 'unique': 'True', 'primary_key': 'True'}),
            'toolServiceCreationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.toolServiceCreationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'toolServiceEvaluationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.toolServiceEvaluationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'toolServiceOperationInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.toolServiceOperationInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'toolServiceSubtype': ('metashare.repository.fields.MultiTextField', [], {'max_length': '100', 'blank': 'True'}),
            'toolServiceType': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'repository.toolserviceoperationinfotype_model': {
            'Meta': {'object_name': 'toolServiceOperationInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operatingSystem': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'os-independent', u'Os - Independent'), (u'windows', u'Windows'), (u'linux', u'Linux'), (u'unix', u'Unix'), (u'mac-OS', u'Mac - OS'), (u'googleChromeOS', u'Google ChromeOS'), (u'iOS', u'IOS'), (u'android', u'Android'), (u'other', u'Other'), (u'', u''))", 'max_length': '3', 'blank': 'True'}),
            'runningEnvironmentInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.runningEnvironmentInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'runningTime': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'repository.usageinfotype_model': {
            'Meta': {'object_name': 'usageInfoType_model'},
            'accessTool': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'accessTool_usageinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resourceAssociatedWith': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'resourceAssociatedWith_usageinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"})
        },
        'repository.validationinfotype_model': {
            'Meta': {'object_name': 'validationInfoType_model'},
            'back_to_resourceinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.resourceInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sizePerValidation': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'validated': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True'}),
            'validationExtent': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'validationExtentDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'validationMode': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'validationModeDetails': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'validationReport': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'validationReport_validationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.documentationInfoType_model']"}),
            'validationTool': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'validationTool_validationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.targetResourceInfoType_model']"}),
            'validationType': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'validator': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'validator_validationinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.actorInfoType_model']"})
        },
        'repository.versioninfotype_model': {
            'Meta': {'object_name': 'versionInfoType_model'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastDateUpdated': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'revision': ('metashare.repository.fields.XmlCharField', [], {'max_length': '500', 'blank': 'True'}),
            'updateFrequency': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100', 'blank': 'True'}),
            'version': ('metashare.repository.fields.XmlCharField', [], {'max_length': '100'})
        },
        'repository.videoclassificationinfotype_model': {
            'Meta': {'object_name': 'videoClassificationInfoType_model'},
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'conformanceToClassificationScheme': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sizePerVideoClassification': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'subject_topic': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'}),
            'videoGenre': ('metashare.repository.fields.XmlCharField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'repository.videocontentinfotype_model': {
            'Meta': {'object_name': 'videoContentInfoType_model'},
            'dynamicElementInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.dynamicElementInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'textIncludedInVideo': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'captions', u'Captions'), (u'subtitles', u'Subtitles'), (u'none', u'None'))", 'max_length': '1', 'blank': 'True'}),
            'typeOfVideoContent': ('metashare.repository.fields.MultiTextField', [], {'max_length': '1000'})
        },
        'repository.videoformatinfotype_model': {
            'Meta': {'object_name': 'videoFormatInfoType_model'},
            'back_to_corpusvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.corpusVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_languagedescriptionvideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.languageDescriptionVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'back_to_lexicalconceptualresourcevideoinfotype_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.lexicalConceptualResourceVideoInfoType_model']", 'null': 'True', 'blank': 'True'}),
            'colourDepth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'colourSpace': ('metashare.repository.fields.MultiSelectField', [], {'choices': "((u'RGB', u'RGB'), (u'CMYK', u'CMYK'), (u'4:2:2', u'4:2:2'), (u'YUV', u'YUV'))", 'max_length': '2', 'blank': 'True'}),
            'compressionInfo': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.compressionInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'fidelity': ('metashare.repository.fields.MetaBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'frameRate': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mimeType': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'resolutionInfo': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'resolutionInfo_videoformatinfotype_model_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['repository.resolutionInfoType_model']"}),
            'sizePerVideoFormat': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['repository.sizeInfoType_model']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'visualModelling': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'storage.storageobject': {
            'Meta': {'object_name': 'StorageObject'},
            'checksum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'copy_status': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'digest_checksum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'digest_last_checked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'digest_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'global_storage': ('django.db.models.fields.TextField', [], {'default': "'not set yet'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'bc45b514d93c11e5a4b9f04da2da8af8af5b818d7f37468d9015230e9b2d26ba'", 'unique': 'True', 'max_length': '64'}),
            'local_storage': ('django.db.models.fields.TextField', [], {'default': "'not set yet'"}),
            'metadata': ('django.db.models.fields.TextField', [], {}),
            'metashare_version': ('django.db.models.fields.CharField', [], {'default': "'3.0'", 'max_length': '32'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2016, 2, 22, 0, 0)'}),
            'publication_status': ('django.db.models.fields.CharField', [], {'default': "'i'", 'max_length': '1'}),
            'revision': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'source_node': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'default': "'http://127.0.0.1:8000'", 'max_length': '200'})
        }
    }

    complete_apps = ['repository']
    symmetrical = True
