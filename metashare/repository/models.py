# pylint: disable-msg=C0302
import logging
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.template.defaultfilters import slugify
from metashare.bcp47 import iana

from metashare.accounts.models import EditorGroup
# pylint: disable-msg=W0611
from metashare.repository.supermodel import SchemaModel, SubclassableModel, \
  _make_choices_from_list, InvisibleStringModel, \
  REQUIRED, OPTIONAL, RECOMMENDED, \
  _make_choices_from_int_list
from metashare.repository.editor.widgets import MultiFieldWidget, MultiChoiceWidget
from metashare.repository.fields import MultiTextField, MetaBooleanField, \
  MultiSelectField, DictField, XmlCharField, best_lang_value_retriever
from metashare.repository.validators import validate_lang_code_keys, \
  validate_dict_values, validate_xml_schema_year, \
  validate_matches_xml_char_production
from metashare.settings import DJANGO_BASE, LOG_HANDLER, DJANGO_URL
from metashare.stats.model_utils import saveLRStats, DELETE_STAT, UPDATE_STAT
from metashare.storage.models import StorageObject, MASTER, COPY_CHOICES
from metashare.recommendations.models import ResourceCountPair, \
    ResourceCountDict


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

# Note: we have to use the '^' and '$' anchors in the following regular
# expressions as for some reason the RegexValidator does not try to match the
# whole string against the regex but it just searches for a matching substring;
# in addition we have to use the negative lookahead assertion at the end of the
# regular expressions as Python's regex engine otherwise always ignores a single
# trailing newline
EMAILADDRESS_VALIDATOR = RegexValidator(r'^[^@]+@[^\.]+\..+(?!\r?\n)$',
  'Not a valid emailAddress value.', ValidationError)
HTTPURI_VALIDATOR = RegexValidator(r"^(?i)((http|ftp)s?):\/\/"
        r"(([a-z0-9.-]|%[0-9A-F]{2}){3,})(:(\d+))?"
        r"((\/([a-z0-9-._~!$&'()*+,;=:@]|%[0-9A-F]{2})*)*)"
        r"(\?(([a-z0-9-._~!$&'()*+,;=:\/?@]|%[0-9A-F]{2})*))?"
        r"(#(([a-z0-9-._~!$&'()*+,;=:\/?@]|%[0-9A-F]{2})*))?(?!\r?\n)$",
    "Not a valid URL value (must not contain non-ASCII characters, for example;"
        " see also RFC 2396).", ValidationError)

# namespace of the META-SHARE metadata XML Schema
SCHEMA_NAMESPACE = 'http://www.meta-share.org/META-SHARE_XMLSchema'
# version of the META-SHARE metadata XML Schema
SCHEMA_VERSION = '3.1'

def _compute_documentationInfoType_key():
    '''
    Prevents id collisions for documentationInfoType_model sub classes.

    These are:
    - documentInfoType_model;
    - documentUnstructuredString_model.

    '''
    _k1 = list(documentInfoType_model.objects.all().order_by('-id'))
    _k2 = list(documentUnstructuredString_model.objects.all().order_by('-id'))

    LOGGER.debug('k1: {}, k2: {}'.format(_k1, _k2))

    _k1_id = 0
    if len(_k1) > 0:
        _k1_id = _k1[0].id
    _k2_id = 0
    if len(_k2) > 0:
        _k2_id = _k2[0].id

    return max(_k1_id, _k2_id) + 1


# pylint: disable-msg=C0103
class resourceInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Resource"


    __schema_name__ = 'resourceInfo'
    __schema_fields__ = (
      ( u'identificationInfo', u'identificationInfo', REQUIRED ),
      ( u'distributionInfo', u'distributionInfo', REQUIRED ),
      ( u'contactPerson', u'contactPerson', REQUIRED ),
      ( u'metadataInfo', u'metadataInfo', REQUIRED ),
      ( u'versionInfo', u'versionInfo', RECOMMENDED ),
      ( u'validationInfo', u'validationinfotype_model_set', RECOMMENDED ),
      ( u'usageInfo', u'usageInfo', RECOMMENDED ),
      ( u'resourceDocumentationInfo', u'resourceDocumentationInfo', RECOMMENDED ),
      ( u'resourceCreationInfo', u'resourceCreationInfo', RECOMMENDED ),
      ( u'relationInfo', u'relationinfotype_model_set', RECOMMENDED ),
      ( 'resourceComponentType/corpusInfo', 'resourceComponentType', REQUIRED ),
      ( 'resourceComponentType/toolServiceInfo', 'resourceComponentType', REQUIRED ),
      ( 'resourceComponentType/languageDescriptionInfo', 'resourceComponentType', REQUIRED ),
      ( 'resourceComponentType/lexicalConceptualResourceInfo', 'resourceComponentType', REQUIRED ),
    )
    __schema_classes__ = {
      u'contactPerson': "personInfoType_model",
      u'corpusInfo': "corpusInfoType_model",
      u'distributionInfo': "distributionInfoType_model",
      u'identificationInfo': "identificationInfoType_model",
      u'languageDescriptionInfo': "languageDescriptionInfoType_model",
      u'lexicalConceptualResourceInfo': "lexicalConceptualResourceInfoType_model",
      u'metadataInfo': "metadataInfoType_model",
      u'relationInfo': "relationInfoType_model",
      u'resourceCreationInfo': "resourceCreationInfoType_model",
      u'resourceDocumentationInfo': "resourceDocumentationInfoType_model",
      u'toolServiceInfo': "toolServiceInfoType_model",
      u'usageInfo': "usageInfoType_model",
      u'validationInfo': "validationInfoType_model",
      u'versionInfo': "versionInfoType_model",
    }

    identificationInfo = models.OneToOneField("identificationInfoType_model",
      verbose_name='Identification',
      help_text='Groups together information needed to identify the reso' \
      'urce',
      )

    distributionInfo = models.OneToOneField("distributionInfoType_model",
      verbose_name='Distribution',
      help_text='Groups information on the distribution of the resource',
      )

    contactPerson = models.ManyToManyField("personInfoType_model",
      verbose_name='Contact person',
      help_text='Groups information on the person(s) that is/are respons' \
      'ible for providing further information regarding the resource',
      related_name="contactPerson_%(class)s_related", )

    metadataInfo = models.OneToOneField("metadataInfoType_model",
      verbose_name='Metadata',
      help_text='Groups information on the metadata record itself',
      )

    versionInfo = models.OneToOneField("versionInfoType_model",
      verbose_name='Version',
      help_text='Groups information on a specific version or release of ' \
      'the resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: validationInfo

    usageInfo = models.OneToOneField("usageInfoType_model",
      verbose_name='Usage',
      help_text='Groups information on usage of the resource (both inten' \
      'ded and actual use)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    resourceDocumentationInfo = models.OneToOneField("resourceDocumentationInfoType_model",
      verbose_name='Resource documentation',
      help_text='Groups together information on any document describing ' \
      'the resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    resourceCreationInfo = models.OneToOneField("resourceCreationInfoType_model",
      verbose_name='Resource creation',
      help_text='Groups information on the creation procedure of a resou' \
      'rce',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: relationInfo

    resourceComponentType = models.OneToOneField("resourceComponentTypeType_model",
      verbose_name='Resource component type',
      help_text='Used for distinguishing between resource types',
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['identificationInfo/resourceName', ]
        formatstring = u'{}'
        return self.unicode_(formatstring, formatargs)

    editor_groups = models.ManyToManyField(EditorGroup, blank=True)

    owners = models.ManyToManyField(User, blank=True)

    storage_object = models.ForeignKey(StorageObject, blank=True, null=True,
      unique=True)

    def save(self, *args, **kwargs):
        """
        Overrides the predefined save() method to ensure that a corresponding
        StorageObject instance is existing, creating it if missing.  Also, we
        check that the storage object instance is a local master copy.
        """
        # If we have not yet created a StorageObject for this resource, do so.
        if not self.storage_object:
            self.storage_object = StorageObject.objects.create(
            metadata='<NOT_READY_YET/>')

        # Check that the storage object instance is a local master copy.
        if not self.storage_object.master_copy:
            LOGGER.warning('Trying to modify non master copy {0}, ' \
              'aborting!'.format(self.storage_object))
            return

        self.storage_object.save()
        # REMINDER: the SOLR indexer in search_indexes.py relies on us
        # calling storage_object.save() from resourceInfoType_model.save().
        # Should we ever change that, we must modify
        # resourceInfoType_modelIndex._setup_save() accordingly!

        #get the resource description languages
        resource_lang = list(self.identificationInfo.description.iterkeys())
        # Call save() method from super class with all arguments.
        super(resourceInfoType_model, self).save(*args, **kwargs)
        self.metadataInfo.save(langs = resource_lang)
        # update statistics
        saveLRStats(self, UPDATE_STAT)

    def delete(self, keep_stats=False, *args, **kwargs):
        """
        Overrides the predefined delete() method to update the statistics.
        Includes deletion of statistics; use keep_stats optional parameter to
        suppress deletion of statistics
        """
        if not keep_stats:
            # delete statistics
            saveLRStats(self, DELETE_STAT)
            # delete recommendations
            ResourceCountPair.objects.filter(lrid=self.storage_object.identifier).delete()
            ResourceCountDict.objects.filter(lrid=self.storage_object.identifier).delete()

        # Call delete() method from super class with all arguments but keep_stats
        super(resourceInfoType_model, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return '/{0}{1}'.format(DJANGO_BASE, self.get_relative_url())

    def get_relative_url(self):
        """
        Returns part of the complete URL which resembles the single resource
        view for this resource.

        The returned part prepended with a '/' can be appended to `DJANGO_URL`
        in order to get the complete URL.
        """
        return 'repository/browse/{}/{}/'.format(slugify(self.__unicode__()),
                                                 self.storage_object.identifier)

    def publication_status(self):
        """
        Method used for changelist view for resources.
        """
        storage_object = getattr(self, 'storage_object', None)
        if storage_object:
            return storage_object.get_publication_status_display()

        return ''

    def resource_type(self):
        """
        Method used for changelist view for resources.
        """
        resource_component = getattr(self, 'resourceComponentType', None)
        if not resource_component:
            return None

        return resource_component.as_subclass()._meta.verbose_name


SIZEINFOTYPE_SIZEUNIT_CHOICES = _make_choices_from_list([
  u'terms', u'entries', u'turns', u'utterances', u'articles', u'files',
  u'items',u'seconds', u'elements', u'units', u'minutes', u'hours',
  u'texts',u'sentences', u'bytes', u'tokens', u'words', u'keywords',
  u'idiomaticExpressions',u'neologisms', u'multiWordUnits', u'expressions',
  u'synsets',u'classes', u'concepts', u'lexicalTypes', u'phoneticUnits',
  u'syntacticUnits',u'semanticUnits', u'predicates', u'phonemes',
  u'diphones',u'T-HPairs', u'syllables', u'frames', u'images', u'kb', u'mb',
  u'gb',u'rb', u'shots', u'unigrams', u'bigrams', u'trigrams', u'4-grams',
  u'5-grams',u'rules', u'questions', u'other',
])

# pylint: disable-msg=C0103
class sizeInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Size"


    __schema_name__ = 'sizeInfoType'
    __schema_fields__ = (
      ( u'size', u'size', REQUIRED ),
      ( u'sizeUnit', u'sizeUnit', REQUIRED ),
    )

    size = XmlCharField(
      verbose_name='Size',
      help_text='Specifies the size of the resource with regard to the S' \
      'izeUnit measurement in form of a number',
      max_length=100, )

    sizeUnit = models.CharField(
      verbose_name='Size unit',
      help_text='Specifies the unit that is used when providing informat' \
      'ion on the size of the resource or of resource parts',

      max_length=30,
      choices=sorted(SIZEINFOTYPE_SIZEUNIT_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    back_to_audiosizeinfotype_model = models.ForeignKey("audioSizeInfoType_model",  blank=True, null=True)

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_corpustextnumericalinfotype_model = models.ForeignKey("corpusTextNumericalInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    back_to_languagedescriptiontextinfotype_model = models.ForeignKey("languageDescriptionTextInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionvideoinfotype_model = models.ForeignKey("languageDescriptionVideoInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionimageinfotype_model = models.ForeignKey("languageDescriptionImageInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceaudioinfotype_model = models.ForeignKey("lexicalConceptualResourceAudioInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcetextinfotype_model = models.ForeignKey("lexicalConceptualResourceTextInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcevideoinfotype_model = models.ForeignKey("lexicalConceptualResourceVideoInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceimageinfotype_model = models.ForeignKey("lexicalConceptualResourceImageInfoType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['size', 'sizeUnit', ]
        formatstring = u'{} {}'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class identificationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Identification"


    __schema_name__ = 'identificationInfoType'
    __schema_fields__ = (
      ( u'resourceName', u'resourceName', REQUIRED ),
      ( u'description', u'description', REQUIRED ),
      ( u'resourceShortName', u'resourceShortName', OPTIONAL ),
      ( u'url', u'url', RECOMMENDED ),
      ( u'metaShareId', u'metaShareId', REQUIRED ),
      ( u'ISLRN', u'ISLRN', OPTIONAL ),
      ( u'identifier', u'identifier', OPTIONAL ),
    )

    resourceName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Resource name',
      max_val_length=500,
      help_text='The full name by which the resource is known; the eleme' \
      'nt can be repeated for the different language versions using the ' \
      '"lang" attribute to specify the language.',
      )

    description = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Description',
      max_val_length=10000,
      help_text='Provides the description of the resource in prose; the ' \
      'element can be repeated for the different language versions using' \
      ' the "lang" attribute to specify the language.',
      )

    resourceShortName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Resource short name',
      max_val_length=500,
      help_text='The short form (abbreviation, acronym etc.) used to ide' \
      'ntify the resource; the element can be repeated for the different' \
      ' language versions using the "lang" attribute to specify the lang' \
      'uage.',
      blank=True)

    url = MultiTextField(max_length=150, widget=MultiFieldWidget(widget_id=0, max_length=150),
      verbose_name='URL (Landing page)', validators=[HTTPURI_VALIDATOR],
      help_text='A URL used as homepage of an entity (e.g. of a person, ' \
      'organization, resource etc.); it provides general information (fo' \
      'r instance in the case of a resource, it may present a descriptio' \
      'n of the resource, its creators and possibly include links to the' \
      ' URL where it can be accessed from)',
      blank=True, )

    metaShareId = XmlCharField(
      verbose_name='Meta-Share ID',
      help_text='An unambiguous referent to the resource within META-SHA' \
      'RE; it reflects to the unique system id provided automatically by' \
      ' the MetaShare software',
      max_length=100, default="NOT_DEFINED_FOR_V2", )

    ISLRN = XmlCharField(
      verbose_name='ISLRN',
      help_text='Reference to the unique ISLRN number of the resource; i' \
      'f the resource has not been assigned an ISLRN yet, you may reques' \
      't for one at: http://www.islrn.org/',
      blank=True, max_length=17, )

    identifier = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=1, max_length=100),
      verbose_name='Identifier',
      help_text='Reference to a PID, DOI or an internal identifier used ' \
      'by the resource provider for the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class versionInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Version"


    __schema_name__ = 'versionInfoType'
    __schema_fields__ = (
      ( u'version', u'version', REQUIRED ),
      ( u'revision', u'revision', OPTIONAL ),
      ( u'lastDateUpdated', u'lastDateUpdated', OPTIONAL ),
      ( u'updateFrequency', u'updateFrequency', OPTIONAL ),
    )

    version = XmlCharField(
      verbose_name='Version',
      help_text='Any string, usually a number, that identifies the versi' \
      'on of a resource',
      max_length=100, )

    revision = XmlCharField(
      verbose_name='Revision',
      help_text='Provides an account of the revisions in free text or a ' \
      'link to a document with revisions',
      blank=True, max_length=500, )

    lastDateUpdated = models.DateField(
      verbose_name='Last date updated',
      help_text='Date of the last update of the version of the resource',
      blank=True, null=True, )

    updateFrequency = XmlCharField(
      verbose_name='Update frequency',
      help_text='Specifies the frequency with which the resource is upda' \
      'ted',
      blank=True, max_length=100, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['version', 'revision', 'lastDateUpdated', ]
        formatstring = u'{} {} {}'
        return self.unicode_(formatstring, formatargs)

VALIDATIONINFOTYPE_VALIDATIONTYPE_CHOICES = _make_choices_from_list([
  u'formal', u'content',
])

VALIDATIONINFOTYPE_VALIDATIONMODE_CHOICES = _make_choices_from_list([
  u'manual', u'automatic', u'mixed', u'interactive',
])

VALIDATIONINFOTYPE_VALIDATIONEXTENT_CHOICES = _make_choices_from_list([
  u'full', u'partial',
])

# pylint: disable-msg=C0103
class validationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Validation"


    __schema_name__ = 'validationInfoType'
    __schema_fields__ = (
      ( u'validated', u'validated', REQUIRED ),
      ( u'validationType', u'validationType', OPTIONAL ),
      ( u'validationMode', u'validationMode', OPTIONAL ),
      ( u'validationModeDetails', u'validationModeDetails', OPTIONAL ),
      ( u'validationExtent', u'validationExtent', OPTIONAL ),
      ( u'validationExtentDetails', u'validationExtentDetails', OPTIONAL ),
      ( u'sizePerValidation', u'sizePerValidation', OPTIONAL ),
      ( 'validationReport/documentUnstructured', 'validationReport', OPTIONAL ),
      ( 'validationReport/documentInfo', 'validationReport', OPTIONAL ),
      ( u'validationTool', u'validationTool', OPTIONAL ),
      ( 'validator/personInfo', 'validator', OPTIONAL ),
      ( 'validator/organizationInfo', 'validator', OPTIONAL ),
    )
    __schema_classes__ = {
      u'documentInfo': "documentInfoType_model",
      u'documentUnstructured': "documentUnstructuredString_model",
      u'organizationInfo': "organizationInfoType_model",
      u'personInfo': "personInfoType_model",
      u'sizePerValidation': "sizeInfoType_model",
      u'validationTool': "targetResourceInfoType_model",
    }

    validated = MetaBooleanField(
      verbose_name='Validated',
      help_text='Specifies the validation status of the resource',
      )

    validationType = models.CharField(
      verbose_name='Validation type',
      help_text='Specifies the type of the validation that have been per' \
      'formed',
      blank=True,
      max_length=20,
      choices=sorted(VALIDATIONINFOTYPE_VALIDATIONTYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    validationMode = models.CharField(
      verbose_name='Validation mode',
      help_text='Specifies the validation methodology applied',
      blank=True,
      max_length=20,
      choices=sorted(VALIDATIONINFOTYPE_VALIDATIONMODE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    validationModeDetails = XmlCharField(
      verbose_name='Validation mode details',
      help_text='Textual field for additional information on validation',
      blank=True, max_length=500, )

    validationExtent = models.CharField(
      verbose_name='Validation extent',
      help_text='The resource coverage in terms of validated data',
      blank=True,
      max_length=20,
      choices=sorted(VALIDATIONINFOTYPE_VALIDATIONEXTENT_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    validationExtentDetails = XmlCharField(
      verbose_name='Validation extent details',
      help_text='Provides information on size or other details of partia' \
      'lly validated data; to be used if only part of the resource has b' \
      'een validated and as an alternative to SizeInfo if the validated ' \
      'part cannot be counted otherwise',
      blank=True, max_length=500, )

    sizePerValidation = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per validation',
      help_text='Specifies the size of the validated part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    validationReport = models.ManyToManyField("documentationInfoType_model",
      verbose_name='Validation report',
      help_text='A short account of the validation details or a bibliogr' \
      'aphic reference to a document with detailed information on the va' \
      'lidation process and results',
      blank=True, null=True, related_name="validationReport_%(class)s_related", )

    validationTool = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Validation tool',
      help_text='The name, the identifier or the url of the tool used fo' \
      'r the validation of the resource',
      blank=True, null=True, related_name="validationTool_%(class)s_related", )

    validator = models.ManyToManyField("actorInfoType_model",
      verbose_name='Validator',
      help_text='Groups information on the person(s) or the organization' \
      '(s) that validated the resource',
      blank=True, null=True, related_name="validator_%(class)s_related", )

    back_to_resourceinfotype_model = models.ForeignKey("resourceInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class resourceCreationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Resource creation"


    __schema_name__ = 'resourceCreationInfoType'
    __schema_fields__ = (
      ( 'resourceCreator/personInfo', 'resourceCreator', RECOMMENDED ),
      ( 'resourceCreator/organizationInfo', 'resourceCreator', RECOMMENDED ),
      ( u'fundingProject', u'fundingProject', OPTIONAL ),
      ( u'creationStartDate', u'creationStartDate', RECOMMENDED ),
      ( u'creationEndDate', u'creationEndDate', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'fundingProject': "projectInfoType_model",
      u'organizationInfo': "organizationInfoType_model",
      u'personInfo': "personInfoType_model",
    }

    resourceCreator = models.ManyToManyField("actorInfoType_model",
      verbose_name='Resource creator',
      help_text='Groups information on the person or the organization th' \
      'at has created the resource',
      blank=True, null=True, related_name="resourceCreator_%(class)s_related", )

    fundingProject = models.ManyToManyField("projectInfoType_model",
      verbose_name='Funding project',
      help_text='Groups information on the project that has funded the r' \
      'esource',
      blank=True, null=True, related_name="fundingProject_%(class)s_related", )

    creationStartDate = models.DateField(
      verbose_name='Creation start date',
      help_text='The date in which the creation process was started',
      blank=True, null=True, )

    creationEndDate = models.DateField(
      verbose_name='Creation end date',
      help_text='The date in which the creation process was completed',
      blank=True, null=True, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['resourceCreator', 'fundingProject', 'creationStartDate', 'creationEndDate', ]
        formatstring = u'{} {} {}-{}'
        return self.unicode_(formatstring, formatargs)

CREATIONINFOTYPE_CREATIONMODE_CHOICES = _make_choices_from_list([
  u'automatic', u'manual', u'mixed', u'interactive',
])

# pylint: disable-msg=C0103
class creationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Creation"


    __schema_name__ = 'creationInfoType'
    __schema_fields__ = (
      ( u'originalSource', u'originalSource', RECOMMENDED ),
      ( u'creationMode', u'creationMode', RECOMMENDED ),
      ( u'creationModeDetails', u'creationModeDetails', OPTIONAL ),
      ( u'creationTool', u'creationTool', OPTIONAL ),
    )
    __schema_classes__ = {
      u'creationTool': "targetResourceInfoType_model",
      u'originalSource': "targetResourceInfoType_model",
    }

    originalSource = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Original source',
      help_text='The name, the identifier or the url of thethe original ' \
      'resources that were at the base of the creation process of the re' \
      'source',
      blank=True, null=True, related_name="originalSource_%(class)s_related", )

    creationMode = models.CharField(
      verbose_name='Creation mode',
      help_text='Specifies whether the resource is created automatically' \
      ' or in a manual or interactive mode',
      blank=True,
      max_length=30,
      choices=sorted(CREATIONINFOTYPE_CREATIONMODE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    creationModeDetails = XmlCharField(
      verbose_name='Creation mode details',
      help_text='Provides further information on the creation methods an' \
      'd processes',
      blank=True, max_length=200, )

    creationTool = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Creation tool',
      help_text='The name, the identifier or the url of the tool used in' \
      ' the creation process',
      blank=True, null=True, related_name="creationTool_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

def languagename_optgroup_choices():
    """
    Group the choices in groups. The first group the EU languages
    and the second group contains the rest.
    """
    most_used_choices = ('', _make_choices_from_list(iana.get_most_used_languages())['choices'])
    more_choices = ('More', _make_choices_from_list(sorted(iana.get_rest_of_languages()))['choices'])
    optgroup = [most_used_choices, more_choices]
    return optgroup

# pylint: disable-msg=C0103
class metadataInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Metadata"


    __schema_name__ = 'metadataInfoType'
    __schema_fields__ = (
      ( u'metadataCreationDate', u'metadataCreationDate', REQUIRED ),
      ( u'metadataCreator', u'metadataCreator', OPTIONAL ),
      ( u'source', u'source', OPTIONAL ),
      ( u'sourceRepository', u'sourceRepository', OPTIONAL ),
      ( u'originalMetadataSchema', u'originalMetadataSchema', OPTIONAL ),
      ( u'originalMetadataLink', u'originalMetadataLink', OPTIONAL ),
      ( u'metadataLanguageName', u'metadataLanguageName', OPTIONAL ),
      ( u'metadataLanguageId', u'metadataLanguageId', OPTIONAL ),
      ( u'metadataLastDateUpdated', u'metadataLastDateUpdated', OPTIONAL ),
      ( u'revision', u'revision', OPTIONAL ),
    )
    __schema_classes__ = {
      u'metadataCreator': "personInfoType_model",
    }

    metadataCreationDate = models.DateField(
      verbose_name='Metadata creation date',
      help_text='The date of creation of this metadata description (auto' \
      'matically inserted by the MetaShare software)',
      )

    metadataCreator = models.ManyToManyField("personInfoType_model",
      verbose_name='Metadata creator',
      help_text='Groups information on the person that has created the m' \
      'etadata record',
      blank=True, null=True, related_name="metadataCreator_%(class)s_related", )

    source = XmlCharField(
      verbose_name='Source',
      help_text='Refers to the catalogue or repository from which the me' \
      'tadata has been originated',
      blank=True, max_length=500, )

    sourceRepository = XmlCharField(
      verbose_name='Source repository (URL)', validators=[HTTPURI_VALIDATOR],
      help_text='Refers to the repository from which the metadata record' \
      ' has been harvested',
      blank=True, max_length=1000, )

    originalMetadataSchema = XmlCharField(
      verbose_name='Original metadata schema',
      help_text='Refers to the metadata schema originally used for the d' \
      'escription of the resource',
      blank=True, max_length=500, )

    originalMetadataLink = XmlCharField(
      verbose_name='Original metadata record link', validators=[HTTPURI_VALIDATOR],
      help_text='A link to the original metadata record, in cases of har' \
      'vesting',
      blank=True, max_length=1000, )

    metadataLanguageName = MultiTextField(max_length=100, widget=MultiChoiceWidget(widget_id=2),
      verbose_name='Metadata language',
      help_text='The language in which the metadata description is writt' \
      'en according to IETF BCP47 (ISO 639-1 or ISO 639-3 for languages ' \
      'not covered by the first standard)',
      blank=True, validators=[validate_matches_xml_char_production], editable=False)

    metadataLanguageId = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=3, max_length=1000),
      verbose_name='Metadata language identifier',
      help_text='The id of the language in which the metadata descriptio' \
      'n is written, as specified by BCP47',
      blank=True, validators=[validate_matches_xml_char_production], editable=False)

    metadataLastDateUpdated = models.DateField(
      verbose_name='Metadata last date updated',
      help_text='The date of the last updating of the metadata record (a' \
      'utomatically inserted by the MetaShare software)',
      blank=True, null=True, )

    revision = XmlCharField(
      verbose_name='Revision',
      help_text='Provides an account of the revisions in free text or a ' \
      'link to a document with revisions',
      blank=True, max_length=500, )

    def save(self, *args, **kwargs):
        # Since this field is hidden, language information is drawn from
        # the resource description dictionary and are converted to bcp47 valid
        # values
        self.metadataLanguageName[:] = []
        self.metadataLanguageId[:] = []
        if 'langs' in kwargs:
            ls = kwargs.pop('langs')
            for i in ls:
                langName = iana.get_language_by_subtag(i)
                self.metadataLanguageName.append(langName)
                self.metadataLanguageId.append(iana.get_language_subtag(langName))
        super(metadataInfoType_model, self).save(*args, **kwargs)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class documentationInfoType_model(SubclassableModel):

    __schema_name__ = 'SUBCLASSABLE'

    class Meta:
        verbose_name = "Documentation"


DOCUMENTINFOTYPE_DOCUMENTTYPE_CHOICES = _make_choices_from_list([
  u'article', u'book', u'booklet', u'manual', u'techReport',
  u'mastersThesis',u'phdThesis', u'inBook', u'inCollection', u'proceedings',
  u'inProceedings',u'unpublished', u'other',
])

# pylint: disable-msg=C0103
class documentInfoType_model(documentationInfoType_model):

    class Meta:
        verbose_name = "Document"


    __schema_name__ = 'documentInfoType'
    __schema_fields__ = (
      ( u'documentType', u'documentType', REQUIRED ),
      ( u'title', u'title', REQUIRED ),
      ( u'author', u'author', OPTIONAL ),
      ( u'editor', u'editor', OPTIONAL ),
      ( u'year', u'year', OPTIONAL ),
      ( u'publisher', u'publisher', OPTIONAL ),
      ( u'bookTitle', u'bookTitle', OPTIONAL ),
      ( u'journal', u'journal', OPTIONAL ),
      ( u'volume', u'volume', OPTIONAL ),
      ( u'series', u'series', OPTIONAL ),
      ( u'pages', u'pages', OPTIONAL ),
      ( u'edition', u'edition', OPTIONAL ),
      ( u'conference', u'conference', OPTIONAL ),
      ( u'doi', u'doi', OPTIONAL ),
      ( u'url', u'url', RECOMMENDED ),
      ( u'ISSN', u'ISSN', OPTIONAL ),
      ( u'ISBN', u'ISBN', OPTIONAL ),
      ( u'keywords', u'keywords', OPTIONAL ),
      ( u'documentLanguageName', u'documentLanguageName', OPTIONAL ),
      ( u'documentLanguageId', u'documentLanguageId', OPTIONAL ),
    )

    documentType = models.CharField(
      verbose_name='Document type',
      help_text='Specifies the type of the document provided with or rel' \
      'ated to the resource',

      max_length=30,
      choices=sorted(DOCUMENTINFOTYPE_DOCUMENTTYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    title = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Title',
      max_val_length=500,
      help_text='The title of the document reporting on the resource',
      )

    author = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=4, max_length=1000),
      verbose_name='Author',
      help_text='The name(s) of the author(s), in the format described i' \
      'n the document',
      blank=True, validators=[validate_matches_xml_char_production], )

    editor = MultiTextField(max_length=200, widget=MultiFieldWidget(widget_id=5, max_length=200),
      verbose_name='Editor',
      help_text='The name of the editor as mentioned in the document',
      blank=True, validators=[validate_matches_xml_char_production], )

    year = XmlCharField(
      verbose_name='Year (of publication)',
      help_text='The year of publication or, for an unpublished work, th' \
      'e year it was written',
      blank=True, validators=[validate_xml_schema_year], max_length=1000, )

    publisher = MultiTextField(max_length=200, widget=MultiFieldWidget(widget_id=6, max_length=200),
      verbose_name='Publisher',
      help_text='The name of the publisher',
      blank=True, validators=[validate_matches_xml_char_production], )

    bookTitle = XmlCharField(
      verbose_name='Book title',
      help_text='The title of a book, part of which is being cited',
      blank=True, max_length=200, )

    journal = XmlCharField(
      verbose_name='Journal',
      help_text='A journal name. Abbreviations could also be provided',
      blank=True, max_length=200, )

    volume = XmlCharField(
      verbose_name='Volume',
      help_text='Specifies the volume of a journal or multivolume book',
      blank=True, max_length=1000, )

    series = XmlCharField(
      verbose_name='Series',
      help_text='The name of a series or set of books. When citing an en' \
      'tire book, the title field gives its title and an optional series' \
      ' field gives the name of a series or multi-volume set in which th' \
      'e book is published',
      blank=True, max_length=200, )

    pages = XmlCharField(
      verbose_name='Pages',
      help_text='One or more page numbers or range of page numbers',
      blank=True, max_length=100, )

    edition = XmlCharField(
      verbose_name='Edition',
      help_text='The edition of a book',
      blank=True, max_length=100, )

    conference = XmlCharField(
      verbose_name='Conference',
      help_text='The name of the conference in which the document has be' \
      'en presented',
      blank=True, max_length=300, )

    doi = XmlCharField(
      verbose_name='DOI',
      help_text='A digital object identifier assigned to the document',
      blank=True, max_length=100, )

    url = XmlCharField(
      verbose_name='URL (Landing page)', validators=[HTTPURI_VALIDATOR],
      help_text='A URL used as homepage of an entity (e.g. of a person, ' \
      'organization, resource etc.); it provides general information (fo' \
      'r instance in the case of a resource, it may present a descriptio' \
      'n of the resource, its creators and possibly include links to the' \
      ' URL where it can be accessed from)',
      blank=True, max_length=1000, )

    ISSN = XmlCharField(
      verbose_name='ISSN',
      help_text='The International Standard Serial Number used to identi' \
      'fy a journal',
      blank=True, max_length=100, )

    ISBN = XmlCharField(
      verbose_name='ISBN',
      help_text='The International Standard Book Number',
      blank=True, max_length=100, )

    keywords = MultiTextField(max_length=250, widget=MultiFieldWidget(widget_id=7, max_length=250),
      verbose_name='Keywords',
      help_text='The keyword(s) for indexing and classification of the d' \
      'ocument',
      blank=True, validators=[validate_matches_xml_char_production], )

    documentLanguageName = models.CharField(
      verbose_name='Document language',
      help_text='The language the document is written in (according to t' \
      'he IETF BCP47 guidelines)',
      blank=True, max_length=150,
      choices=languagename_optgroup_choices(),)

    documentLanguageId = XmlCharField(
      verbose_name='Document language identifier',
      help_text='The id of the language the document is written in; an a' \
      'utocompletion mechanism with values from the ISO 639 is provided ' \
      'in the editor, but the values can be subsequently edited for furt' \
      'her specification (according to the IETF BCP47 guidelines)',
      blank=True, max_length=20, editable=False)


    source_url = models.URLField(verify_exists=False,
      default=DJANGO_URL,
      help_text="(Read-only) base URL for the server where the master copy of " \
      "the associated entity instance is located.")

    copy_status = models.CharField(default=MASTER, max_length=1, choices=COPY_CHOICES,
        help_text="Generalized copy status flag for this entity instance.")

    def save(self, *args, **kwargs):
        """
        Prevents id collisions for documentationInfoType_model sub classes.
        """
        # pylint: disable-msg=E0203
        if not self.id:
            # pylint: disable-msg=W0201
            self.id = _compute_documentationInfoType_key()
        if self.documentLanguageName:
            self.documentLanguageId = iana.get_language_subtag(self.documentLanguageName)
        super(documentInfoType_model, self).save(*args, **kwargs)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['author', 'title', ]
        formatstring = u'{}: {}'
        return self.unicode_(formatstring, formatargs)

RESOURCEDOCUMENTATIONINFOTYPE_TOOLDOCUMENTATIONTYPE_CHOICES = _make_choices_from_list([
  u'online', u'manual', u'helpFunctions', u'none', u'other',
])

# pylint: disable-msg=C0103
class resourceDocumentationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Resource documentation"


    __schema_name__ = 'resourceDocumentationInfoType'
    __schema_fields__ = (
      ( 'citation/documentUnstructured', 'citation', RECOMMENDED ),
      ( 'citation/documentInfo', 'citation', RECOMMENDED ),
      ( 'documentation/documentUnstructured', 'documentation', RECOMMENDED ),
      ( 'documentation/documentInfo', 'documentation', RECOMMENDED ),
      ( u'samplesLocation', u'samplesLocation', RECOMMENDED ),
      ( u'toolDocumentationType', u'toolDocumentationType', OPTIONAL ),
    )
    __schema_classes__ = {
      u'documentInfo': "documentInfoType_model",
      u'documentUnstructured': "documentUnstructuredString_model",
    }

    citation =  models.ForeignKey("documentationInfoType_model",
      verbose_name='Citation',
      help_text='Publication to be used for citation purposes',
      blank=True, null=True, on_delete=models.SET_NULL, )

    documentation = models.ManyToManyField("documentationInfoType_model",
      verbose_name='Documentation',
      help_text='Refers to papers, manuals, reports etc. describing the ' \
      'resource',
      blank=True, null=True, related_name="documentation_%(class)s_related", )

    samplesLocation = MultiTextField(max_length=150, widget=MultiFieldWidget(widget_id=8, max_length=150),
      verbose_name='Samples location', validators=[HTTPURI_VALIDATOR],
      help_text='A url with samples of the resource or, in the case of t' \
      'ools, of samples of the output',
      blank=True, )

    toolDocumentationType = MultiSelectField(
      verbose_name='Type of documentation for tools',
      help_text='Specifies the type of documentation for tool or service' \
      '',
      blank=True,
      max_length=1 + len(RESOURCEDOCUMENTATIONINFOTYPE_TOOLDOCUMENTATIONTYPE_CHOICES['choices']) / 4,
      choices=RESOURCEDOCUMENTATIONINFOTYPE_TOOLDOCUMENTATIONTYPE_CHOICES['choices'],
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['documentation', ]
        formatstring = u'{}'
        return self.unicode_(formatstring, formatargs)

DOMAININFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'DK-5', u'EUROVOC',
  u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other',
])

# pylint: disable-msg=C0103
class domainInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Domain"


    __schema_name__ = 'domainInfoType'
    __schema_fields__ = (
      ( u'domain', u'domain', REQUIRED ),
      ( u'sizePerDomain', u'sizePerDomain', OPTIONAL ),
      ( u'conformanceToClassificationScheme', u'conformanceToClassificationScheme', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerDomain': "sizeInfoType_model",
    }

    domain = XmlCharField(
      verbose_name='Domain',
      help_text='Specifies the application domain of the resource or the' \
      ' tool/service',
      max_length=100, )

    sizePerDomain = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per domain',
      help_text='Specifies the size of resource parts per domain',
      blank=True, null=True, on_delete=models.SET_NULL, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme',
      help_text='Specifies the external classification schemes',
      blank=True,
      max_length=100,
      choices=sorted(DOMAININFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    back_to_languagedescriptiontextinfotype_model = models.ForeignKey("languageDescriptionTextInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionvideoinfotype_model = models.ForeignKey("languageDescriptionVideoInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionimageinfotype_model = models.ForeignKey("languageDescriptionImageInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceaudioinfotype_model = models.ForeignKey("lexicalConceptualResourceAudioInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcetextinfotype_model = models.ForeignKey("lexicalConceptualResourceTextInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcevideoinfotype_model = models.ForeignKey("lexicalConceptualResourceVideoInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceimageinfotype_model = models.ForeignKey("lexicalConceptualResourceImageInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

ANNOTATIONINFOTYPE_ANNOTATIONTYPE_CHOICES = _make_choices_from_list([
  u'alignment', u'discourseAnnotation',
  u'discourseAnnotation-audienceReactions',
  u'discourseAnnotation-coreference',u'discourseAnnotation-dialogueActs',
  u'discourseAnnotation-discourseRelations',u'lemmatization',
  u'morphosyntacticAnnotation-bPosTagging',
  u'morphosyntacticAnnotation-posTagging',u'segmentation',
  u'semanticAnnotation',u'semanticAnnotation-certaintyLevel',
  u'semanticAnnotation-emotions',u'semanticAnnotation-entityMentions',
  u'semanticAnnotation-events',u'semanticAnnotation-namedEntities',
  u'semanticAnnotation-polarity',
  u'semanticAnnotation-questionTopicalTarget',
  u'semanticAnnotation-semanticClasses',
  u'semanticAnnotation-semanticRelations',
  u'semanticAnnotation-semanticRoles',u'semanticAnnotation-speechActs',
  u'semanticAnnotation-temporalExpressions',
  u'semanticAnnotation-textualEntailment',u'semanticAnnotation-wordSenses',
  u'speechAnnotation',u'speechAnnotation-orthographicTranscription',
  u'speechAnnotation-paralanguageAnnotation',
  u'speechAnnotation-phoneticTranscription',
  u'speechAnnotation-prosodicAnnotation',u'speechAnnotation-soundEvents',
  u'speechAnnotation-soundToTextAlignment',
  u'speechAnnotation-speakerIdentification',
  u'speechAnnotation-speakerTurns',u'stemming', u'structuralAnnotation',
  u'syntacticAnnotation-subcategorizationFrames',
  u'syntacticAnnotation-dependencyTrees',
  u'syntacticAnnotation-constituencyTrees',
  u'syntacticosemanticAnnotation-links',u'translation', u'transliteration',
  u'modalityAnnotation-bodyMovements',
  u'modalityAnnotation-facialExpressions',
  u'modalityAnnotation-gazeEyeMovements',
  u'modalityAnnotation-handArmGestures',
  u'modalityAnnotation-handManipulationOfObjects',
  u'modalityAnnotation-headMovements',u'modalityAnnotation-lipMovements',
  u'other',
])

ANNOTATIONINFOTYPE_ANNOTATEDELEMENTS_CHOICES = _make_choices_from_list([
  u'speakerNoise', u'backgroundNoise', u'mispronunciations', u'truncation',
  u'discourseMarkers',u'other',
])

ANNOTATIONINFOTYPE_SEGMENTATIONLEVEL_CHOICES = _make_choices_from_list([
  u'paragraph', u'sentence', u'clause', u'word', u'wordGroup', u'utterance',
  u'topic',u'signal', u'phoneme', u'syllable', u'phrase', u'diphone',
  u'prosodicBoundaries',u'frame', u'scene', u'shot', u'token', u'other',
])

ANNOTATIONINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES = _make_choices_from_list([
  u'BML', u'CES', u'EAGLES', u'EML', u'EMMA', u'GMX', u'GrAF', u'HamNoSys',
  u'InkML',u'ILSP_NLP', u'ISO12620', u'ISO16642', u'ISO1987', u'ISO26162',
  u'ISO30042',u'ISO704', u'LAF', u'LMF', u'MAF', u'MLIF', u'MOSES',
  u'MULTEXT',u'MUMIN', u'multimodalInteractionFramework', u'OAXAL', u'OWL',
  u'PANACEA',u'pennTreeBank', u'pragueTreebank', u'RDF', u'SemAF',
  u'SemAF_DA',u'SemAF_NE', u'SemAF_SRL', u'SemAF_DS', u'SKOS', u'SRX',
  u'SynAF',u'TBX', u'TMX', u'TEI', u'TEI_P3', u'TEI_P4', u'TEI_P5',
  u'TimeML',u'XCES', u'XLIFF', u'WordNet', u'other',
])

ANNOTATIONINFOTYPE_ANNOTATIONMODE_CHOICES = _make_choices_from_list([
  u'automatic', u'manual', u'mixed', u'interactive',
])

# pylint: disable-msg=C0103
class annotationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Annotation"


    __schema_name__ = 'annotationInfoType'
    __schema_fields__ = (
      ( u'annotationType', u'annotationType', REQUIRED ),
      ( u'annotatedElements', u'annotatedElements', OPTIONAL ),
      ( u'annotationStandoff', u'annotationStandoff', OPTIONAL ),
      ( u'segmentationLevel', u'segmentationLevel', OPTIONAL ),
      ( u'annotationFormat', u'annotationFormat', RECOMMENDED ),
      ( u'tagset', u'tagset', RECOMMENDED ),
      ( u'tagsetLanguageId', u'tagsetLanguageId', OPTIONAL ),
      ( u'tagsetLanguageName', u'tagsetLanguageName', OPTIONAL ),
      ( u'conformanceToStandardsBestPractices', u'conformanceToStandardsBestPractices', OPTIONAL ),
      ( u'theoreticModel', u'theoreticModel', OPTIONAL ),
      ( 'annotationManual/documentUnstructured', 'annotationManual', OPTIONAL ),
      ( 'annotationManual/documentInfo', 'annotationManual', OPTIONAL ),
      ( u'annotationMode', u'annotationMode', RECOMMENDED ),
      ( u'annotationModeDetails', u'annotationModeDetails', OPTIONAL ),
      ( u'annotationTool', u'annotationTool', RECOMMENDED ),
      ( u'annotationStartDate', u'annotationStartDate', OPTIONAL ),
      ( u'annotationEndDate', u'annotationEndDate', OPTIONAL ),
      ( u'sizePerAnnotation', u'sizePerAnnotation', OPTIONAL ),
      ( u'interannotatorAgreement', u'interannotatorAgreement', OPTIONAL ),
      ( u'intraannotatorAgreement', u'intraannotatorAgreement', OPTIONAL ),
      ( 'annotator/personInfo', 'annotator', OPTIONAL ),
      ( 'annotator/organizationInfo', 'annotator', OPTIONAL ),
    )
    __schema_classes__ = {
      u'annotationTool': "targetResourceInfoType_model",
      u'documentInfo': "documentInfoType_model",
      u'documentUnstructured': "documentUnstructuredString_model",
      u'organizationInfo': "organizationInfoType_model",
      u'personInfo': "personInfoType_model",
      u'sizePerAnnotation': "sizeInfoType_model",
    }

    annotationType = models.CharField(
      verbose_name='Annotation type',
      help_text='Specifies the annotation level of the resource or the a' \
      'nnotation type a tool/ service requires or produces as an output',

      max_length=150,
      choices=sorted(ANNOTATIONINFOTYPE_ANNOTATIONTYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    annotatedElements = MultiSelectField(
      verbose_name='Annotated elements',
      help_text='Specifies the elements annotated in each annotation lev' \
      'el',
      blank=True,
      max_length=1 + len(ANNOTATIONINFOTYPE_ANNOTATEDELEMENTS_CHOICES['choices']) / 4,
      choices=ANNOTATIONINFOTYPE_ANNOTATEDELEMENTS_CHOICES['choices'],
      )

    annotationStandoff = MetaBooleanField(
      verbose_name='Annotation standoff',
      help_text='Indicates whether the annotation is created inline or i' \
      'n a stand-off fashion',
      blank=True, )

    segmentationLevel = MultiSelectField(
      verbose_name='Segmentation level',
      help_text='Specifies the segmentation unit in terms of which the r' \
      'esource has been segmented or the level of segmentation a tool/se' \
      'rvice requires/outputs',
      blank=True,
      max_length=1 + len(ANNOTATIONINFOTYPE_SEGMENTATIONLEVEL_CHOICES['choices']) / 4,
      choices=ANNOTATIONINFOTYPE_SEGMENTATIONLEVEL_CHOICES['choices'],
      )

    annotationFormat = XmlCharField(
      verbose_name='Annotation format',
      help_text='Specifies the format that is used in the annotation pro' \
      'cess since often the mime type will not be sufficient for machine' \
      ' processing',
      blank=True, max_length=100, )

    tagset = XmlCharField(
      verbose_name='Tagset',
      help_text='A name or a url reference to the tagset used in the ann' \
      'otation of the resource or used by the tool/service',
      blank=True, max_length=500, )

    tagsetLanguageId = XmlCharField(
      verbose_name='Tagset language identifier',
      help_text='The identifier of the tagset language (according to the IETF BCP47 guidelines)',
      blank=True, max_length=20, editable=False)

    tagsetLanguageName = models.CharField(
      verbose_name='Tagset language',
      help_text='The name of the tagset language (according to the IETF BCP47 guidelines)',
      blank=True, max_length=150,
      choices=languagename_optgroup_choices(),)

    conformanceToStandardsBestPractices = MultiSelectField(
      verbose_name='Conformance to standards / best practices',
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True,
      max_length=1 + len(ANNOTATIONINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices']) / 4,
      choices=ANNOTATIONINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices'],
      )

    theoreticModel = XmlCharField(
      verbose_name='Theoretic model',
      help_text='Name of the theoretic model applied for the creation or' \
      ' enrichment of the resource, and/or a reference (URL or bibliogra' \
      'phic reference) to informative material about the theoretic model' \
      ' used',
      blank=True, max_length=500, )

    annotationManual = models.ManyToManyField("documentationInfoType_model",
      verbose_name='Annotation manual',
      help_text='A bibliographic reference or ms:httpURI link to the ann' \
      'otation manual',
      blank=True, null=True, related_name="annotationManual_%(class)s_related", )

    annotationMode = models.CharField(
      verbose_name='Annotation mode',
      help_text='Indicates whether the resource is annotated manually or' \
      ' by automatic processes',
      blank=True,
      max_length=100,
      choices=sorted(ANNOTATIONINFOTYPE_ANNOTATIONMODE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    annotationModeDetails = XmlCharField(
      verbose_name='Annotation mode details',
      help_text='Provides further information on annotation process',
      blank=True, max_length=1000, )

    annotationTool = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Annotation tool',
      help_text='The name, the identifier or the url of the tool used fo' \
      'r the annotation of the resource',
      blank=True, null=True, related_name="annotationTool_%(class)s_related", )

    annotationStartDate = models.DateField(
      verbose_name='Annotation start date',
      help_text='The date in which the annotation process has started',
      blank=True, null=True, )

    annotationEndDate = models.DateField(
      verbose_name='Annotation end date',
      help_text='The date in which the annotation process has ended',
      blank=True, null=True, )

    sizePerAnnotation = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per annotation',
      help_text='Provides information on size for the annotated parts of' \
      ' the resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    interannotatorAgreement = XmlCharField(
      verbose_name='Interannotator agreement',
      help_text='Provides information on the interannotator agreement an' \
      'd the methods/metrics applied',
      blank=True, max_length=1000, )

    intraannotatorAgreement = XmlCharField(
      verbose_name='Intraannotator agreement',
      help_text='Provides information on the intra-annotator agreement a' \
      'nd the methods/metrics applied',
      blank=True, max_length=1000, )

    annotator = models.ManyToManyField("actorInfoType_model",
      verbose_name='Annotator',
      help_text='Groups information on the annotators of the specific an' \
      'notation type',
      blank=True, null=True, related_name="annotator_%(class)s_related", )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_corpustextnumericalinfotype_model = models.ForeignKey("corpusTextNumericalInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.tagsetLanguageName:
            self.tagsetLanguageId = iana.get_language_subtag(self.tagsetLanguageName)
        super(annotationInfoType_model, self).save(*args, **kwargs)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class targetResourceInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Target resource"


    __schema_name__ = 'targetResourceInfoType'
    __schema_fields__ = (
      ( u'targetResourceNameURI', u'targetResourceNameURI', REQUIRED ),
    )

    targetResourceNameURI = XmlCharField(
      verbose_name='Target resource',
      help_text='The full name or a url to a resource related to the one' \
      ' being described; to be used for identifiers also for this versio' \
      'n',
      max_length=4500, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['targetResourceNameURI', ]
        formatstring = u'{}'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class relationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Relation"


    __schema_name__ = 'relationInfoType'
    __schema_fields__ = (
      ( u'relationType', u'relationType', REQUIRED ),
      ( u'relatedResource', u'relatedResource', REQUIRED ),
    )
    __schema_classes__ = {
      u'relatedResource': "targetResourceInfoType_model",
    }

    relationType = XmlCharField(
      verbose_name='Relation type',
      help_text='Specifies the type of relation not covered by the ones ' \
      'proposed by META-SHARE',
      max_length=100, )

    relatedResource = models.ForeignKey("targetResourceInfoType_model",
      verbose_name='Related resource',
      help_text='The full name, the identifier or the url of the related' \
      ' resource',
      )

    back_to_resourceinfotype_model = models.ForeignKey("resourceInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

MODALITYINFOTYPE_MODALITYTYPE_CHOICES = _make_choices_from_list([
  u'bodyGesture', u'facialExpression', u'voice', u'combinationOfModalities',
  u'signLanguage',u'spokenLanguage', u'writtenLanguage', u'other',
])

# pylint: disable-msg=C0103
class modalityInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Modality"
        verbose_name_plural = "Modalities"


    __schema_name__ = 'modalityInfoType'
    __schema_fields__ = (
      ( u'modalityType', u'modalityType', REQUIRED ),
      ( u'modalityTypeDetails', u'modalityTypeDetails', OPTIONAL ),
      ( u'sizePerModality', u'sizePerModality', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerModality': "sizeInfoType_model",
    }

    modalityType = MultiSelectField(
      verbose_name='Modality type',
      help_text='Specifies the type of the modality represented in the r' \
      'esource or processed by a tool/service',

      max_length=1 + len(MODALITYINFOTYPE_MODALITYTYPE_CHOICES['choices']) / 4,
      choices=MODALITYINFOTYPE_MODALITYTYPE_CHOICES['choices'],
      )

    modalityTypeDetails = XmlCharField(
      verbose_name='Modality type details',
      help_text='Provides further information on modalities',
      blank=True, max_length=500, )

    sizePerModality = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per modality',
      help_text='Provides information on the size per modality component' \
      '',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_corpustextnumericalinfotype_model = models.ForeignKey("corpusTextNumericalInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionvideoinfotype_model = models.ForeignKey("languageDescriptionVideoInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionimageinfotype_model = models.ForeignKey("languageDescriptionImageInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceaudioinfotype_model = models.ForeignKey("lexicalConceptualResourceAudioInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcetextinfotype_model = models.ForeignKey("lexicalConceptualResourceTextInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcevideoinfotype_model = models.ForeignKey("lexicalConceptualResourceVideoInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceimageinfotype_model = models.ForeignKey("lexicalConceptualResourceImageInfoType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['modalityType', 'modalityTypeDetails', ]
        formatstring = u'{} {}'
        return self.unicode_(formatstring, formatargs)

PARTICIPANTINFOTYPE_AGEGROUP_CHOICES = _make_choices_from_list([
  u'child', u'teenager', u'adult', u'elderly',
])

PARTICIPANTINFOTYPE_SEX_CHOICES = _make_choices_from_list([
  u'male', u'female', u'unknown',
])

PARTICIPANTINFOTYPE_ORIGIN_CHOICES = _make_choices_from_list([
  u'native', u'nonNative', u'unknown',
])

PARTICIPANTINFOTYPE_VOCALTRACTCONDITIONS_CHOICES = _make_choices_from_list([
  u'dentalProsthesis', u'other',
])

# pylint: disable-msg=C0103
class participantInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Participant"


    __schema_name__ = 'participantInfoType'
    __schema_fields__ = (
      ( u'alias', u'alias', OPTIONAL ),
      ( u'ageGroup', u'ageGroup', OPTIONAL ),
      ( u'age', u'age', OPTIONAL ),
      ( u'sex', u'sex', OPTIONAL ),
      ( u'origin', u'origin', OPTIONAL ),
      ( u'placeOfLiving', u'placeOfLiving', OPTIONAL ),
      ( u'placeOfBirth', u'placeOfBirth', OPTIONAL ),
      ( u'placeOfChildhood', u'placeOfChildhood', OPTIONAL ),
      ( u'dialectAccent', u'dialectAccent', OPTIONAL ),
      ( u'speakingImpairment', u'speakingImpairment', OPTIONAL ),
      ( u'hearingImpairment', u'hearingImpairment', OPTIONAL ),
      ( u'smokingHabits', u'smokingHabits', OPTIONAL ),
      ( u'vocalTractConditions', u'vocalTractConditions', OPTIONAL ),
      ( u'profession', u'profession', OPTIONAL ),
      ( u'height', u'height', OPTIONAL ),
      ( u'weight', u'weight', OPTIONAL ),
      ( u'trainedSpeaker', u'trainedSpeaker', OPTIONAL ),
      ( u'placeOfSecondEducation', u'placeOfSecondEducation', OPTIONAL ),
      ( u'educationLevel', u'educationLevel', OPTIONAL ),
    )

    alias = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Alias',
      max_val_length=500,
      help_text='The name of the person used instead of the real one',
      blank=True)

    ageGroup = models.CharField(
      verbose_name='Age group',
      help_text='The age group to which the participant belongs',
      blank=True,
      max_length=30,
      choices=sorted(PARTICIPANTINFOTYPE_AGEGROUP_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    age = XmlCharField(
      verbose_name='Age',
      help_text='The age of the participant',
      blank=True, max_length=50, )

    sex = models.CharField(
      verbose_name='Sex',
      help_text='The gender of a person related to or participating in t' \
      'he resource',
      blank=True,
      max_length=30,
      choices=sorted(PARTICIPANTINFOTYPE_SEX_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    origin = models.CharField(
      verbose_name='Origin (for language)',
      help_text='The language origin of the participant',
      blank=True,
      max_length=30,
      choices=sorted(PARTICIPANTINFOTYPE_ORIGIN_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    placeOfLiving = XmlCharField(
      verbose_name='Place  of living',
      help_text='The participant\'s place of living',
      blank=True, max_length=100, )

    placeOfBirth = XmlCharField(
      verbose_name='Place of birth',
      help_text='The place in which the participant has been born',
      blank=True, max_length=100, )

    placeOfChildhood = XmlCharField(
      verbose_name='Place of childhood',
      help_text='The place in which the participant lived as a child',
      blank=True, max_length=100, )

    dialectAccent = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Dialect accent',
      max_val_length=500,
      help_text='Provides information on the dialect of the participant',
      blank=True)

    speakingImpairment = XmlCharField(
      verbose_name='Speaking impairment',
      help_text='Provides information on any speaking impairment the par' \
      'ticipant may have',
      blank=True, max_length=200, )

    hearingImpairment = XmlCharField(
      verbose_name='Hearing impairment',
      help_text='Provides information on any hearing impairment the part' \
      'icipant may have',
      blank=True, max_length=200, )

    smokingHabits = XmlCharField(
      verbose_name='Smoking habits',
      help_text='Provides information on whether the participants smokes' \
      ' and on his/her smoking habits in general',
      blank=True, max_length=100, )

    vocalTractConditions = models.CharField(
      verbose_name='Vocal tract conditions',
      help_text='Provides information on the vocal tract conditions that' \
      ' may influence the speech of the participant',
      blank=True,
      max_length=30,
      choices=sorted(PARTICIPANTINFOTYPE_VOCALTRACTCONDITIONS_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    profession = XmlCharField(
      verbose_name='Profession',
      help_text='Provides information on the participant\'s profession',
      blank=True, max_length=100, )

    height = models.BigIntegerField(
      verbose_name='Height',
      help_text='Provides information on the height of the participant i' \
      'n cm',
      blank=True, null=True, )

    weight = models.BigIntegerField(
      verbose_name='Weight',
      help_text='Provides information on the weight of the participant',
      blank=True, null=True, )

    trainedSpeaker = MetaBooleanField(
      verbose_name='Trained speaker',
      help_text='Provides information on whether the participant is trai' \
      'ned in a specific task',
      blank=True, )

    placeOfSecondEducation = XmlCharField(
      verbose_name='Place of second education',
      help_text='Specifies the place of the secondary education of the p' \
      'articipant',
      blank=True, max_length=100, )

    educationLevel = XmlCharField(
      verbose_name='Education level',
      help_text='Provides information on the education level of the part' \
      'icipant',
      blank=True, max_length=100, )

    back_to_personsourcesetinfotype_model = models.ForeignKey("personSourceSetInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

CAPTUREINFOTYPE_CAPTURINGDEVICETYPE_CHOICES = _make_choices_from_list([
  u'studioEquipment', u'microphone', u'closeTalkMicrophone',
  u'farfieldMicrophone',u'lavalierMicrophone', u'microphoneArray',
  u'embeddedMicrophone',u'largeMembraneMicrophone', u'laryngograph',
  u'telephoneFixed',u'telephoneMobile', u'telephoneIP', u'camera',
  u'webcam',u'other',
])

CAPTUREINFOTYPE_CAPTURINGENVIRONMENT_CHOICES = _make_choices_from_list([
  u'complex', u'plain',
])

CAPTUREINFOTYPE_SCENEILLUMINATION_CHOICES = _make_choices_from_list([
  u'daylight', u'fix', u'multipleSources', u'singleSource', u'variable',
  u'other',
])

# pylint: disable-msg=C0103
class captureInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Capture"


    __schema_name__ = 'captureInfoType'
    __schema_fields__ = (
      ( u'capturingDeviceType', u'capturingDeviceType', OPTIONAL ),
      ( u'capturingDeviceTypeDetails', u'capturingDeviceTypeDetails', OPTIONAL ),
      ( u'capturingDetails', u'capturingDetails', OPTIONAL ),
      ( u'capturingEnvironment', u'capturingEnvironment', OPTIONAL ),
      ( u'sensorTechnology', u'sensorTechnology', OPTIONAL ),
      ( u'sceneIllumination', u'sceneIllumination', OPTIONAL ),
      ( u'personSourceSetInfo', u'personSourceSetInfo', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'personSourceSetInfo': "personSourceSetInfoType_model",
    }

    capturingDeviceType = MultiSelectField(
      verbose_name='Capturing device type',
      help_text='The transducers through which the data is captured',
      blank=True,
      max_length=1 + len(CAPTUREINFOTYPE_CAPTURINGDEVICETYPE_CHOICES['choices']) / 4,
      choices=CAPTUREINFOTYPE_CAPTURINGDEVICETYPE_CHOICES['choices'],
      )

    capturingDeviceTypeDetails = XmlCharField(
      verbose_name='Capturing device type details',
      help_text='Provides further information on the capturing device',
      blank=True, max_length=400, )

    capturingDetails = XmlCharField(
      verbose_name='Capturing details',
      help_text='Provides further information on the capturing method an' \
      'd procedure',
      blank=True, max_length=400, )

    capturingEnvironment = models.CharField(
      verbose_name='Capturing environment',
      help_text='Type of capturing environment',
      blank=True,
      max_length=30,
      choices=sorted(CAPTUREINFOTYPE_CAPTURINGENVIRONMENT_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sensorTechnology = MultiTextField(max_length=200, widget=MultiFieldWidget(widget_id=10, max_length=200),
      verbose_name='Sensor technology',
      help_text='Specifies either the type of image sensor or the sensin' \
      'g method used in the camera or the image-capture device',
      blank=True, validators=[validate_matches_xml_char_production], )

    sceneIllumination = models.CharField(
      verbose_name='Scene illumination',
      help_text='Information on the illumination of the scene',
      blank=True,
      max_length=30,
      choices=sorted(CAPTUREINFOTYPE_SCENEILLUMINATION_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    personSourceSetInfo = models.OneToOneField("personSourceSetInfoType_model",
      verbose_name='Person source set',
      help_text='Groups information on the persons (speakers, video part' \
      'icipants, etc.) in the audio and video parts of the resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

PERSONSOURCESETINFOTYPE_AGEOFPERSONS_CHOICES = _make_choices_from_list([
  u'child', u'teenager', u'adult', u'elderly',
])

PERSONSOURCESETINFOTYPE_SEXOFPERSONS_CHOICES = _make_choices_from_list([
  u'male', u'female', u'mixed', u'unknown',
])

PERSONSOURCESETINFOTYPE_ORIGINOFPERSONS_CHOICES = _make_choices_from_list([
  u'native', u'nonNative', u'mixed', u'unknown',
])

PERSONSOURCESETINFOTYPE_HEARINGIMPAIRMENTOFPERSONS_CHOICES = _make_choices_from_list([
  u'yes', u'no', u'mixed',
])

PERSONSOURCESETINFOTYPE_SPEAKINGIMPAIRMENTOFPERSONS_CHOICES = _make_choices_from_list([
  u'yes', u'no', u'mixed',
])

PERSONSOURCESETINFOTYPE_SPEECHINFLUENCES_CHOICES = _make_choices_from_list([
  u'alcohol', u'sleepDeprivation', u'hyperbaric', u'medication', u'other',
])

# pylint: disable-msg=C0103
class personSourceSetInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Person source set"


    __schema_name__ = 'personSourceSetInfoType'
    __schema_fields__ = (
      ( u'numberOfPersons', u'numberOfPersons', OPTIONAL ),
      ( u'ageOfPersons', u'ageOfPersons', OPTIONAL ),
      ( u'ageRangeStart', u'ageRangeStart', OPTIONAL ),
      ( u'ageRangeEnd', u'ageRangeEnd', OPTIONAL ),
      ( u'sexOfPersons', u'sexOfPersons', OPTIONAL ),
      ( u'originOfPersons', u'originOfPersons', OPTIONAL ),
      ( u'dialectAccentOfPersons', u'dialectAccentOfPersons', OPTIONAL ),
      ( u'geographicDistributionOfPersons', u'geographicDistributionOfPersons', OPTIONAL ),
      ( u'hearingImpairmentOfPersons', u'hearingImpairmentOfPersons', OPTIONAL ),
      ( u'speakingImpairmentOfPersons', u'speakingImpairmentOfPersons', OPTIONAL ),
      ( u'numberOfTrainedSpeakers', u'numberOfTrainedSpeakers', OPTIONAL ),
      ( u'speechInfluences', u'speechInfluences', OPTIONAL ),
      ( u'participantInfo', u'participantinfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'participantInfo': "participantInfoType_model",
    }

    numberOfPersons = models.BigIntegerField(
      verbose_name='Number of persons',
      help_text='The number of the persons participating in the audio or' \
      ' video part of the resource',
      blank=True, null=True, )

    ageOfPersons = MultiSelectField(
      verbose_name='Age of persons',
      help_text='The age range of the group of participants; repeat the ' \
      'element if needed',
      blank=True,
      max_length=1 + len(PERSONSOURCESETINFOTYPE_AGEOFPERSONS_CHOICES['choices']) / 4,
      choices=PERSONSOURCESETINFOTYPE_AGEOFPERSONS_CHOICES['choices'],
      )

    ageRangeStart = models.BigIntegerField(
      verbose_name='Age range start',
      help_text='Start of age range of the group of participants',
      blank=True, null=True, )

    ageRangeEnd = models.BigIntegerField(
      verbose_name='Age range end',
      help_text='End of age range of the group of participants',
      blank=True, null=True, )

    sexOfPersons = models.CharField(
      verbose_name='Sex of persons',
      help_text='The gender of the group of participants',
      blank=True,
      max_length=30,
      choices=sorted(PERSONSOURCESETINFOTYPE_SEXOFPERSONS_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    originOfPersons = models.CharField(
      verbose_name='Origin of persons',
      help_text='The language origin of the group of participants',
      blank=True,
      max_length=30,
      choices=sorted(PERSONSOURCESETINFOTYPE_ORIGINOFPERSONS_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    dialectAccentOfPersons = MultiTextField(max_length=500, widget=MultiFieldWidget(widget_id=11, max_length=500),
      verbose_name='Dialect accent of persons',
      help_text='Provides information on the dialect of the group of par' \
      'ticipants',
      blank=True, validators=[validate_matches_xml_char_production], )

    geographicDistributionOfPersons = XmlCharField(
      verbose_name='Geographic distribution of persons',
      help_text='Gives information on the geographic distribution of the' \
      ' participants',
      blank=True, max_length=200, )

    hearingImpairmentOfPersons = models.CharField(
      verbose_name='Hearing impairment of persons',
      help_text='Whether the group of participants contains persons with' \
      ' hearing impairments',
      blank=True,
      max_length=30,
      choices=sorted(PERSONSOURCESETINFOTYPE_HEARINGIMPAIRMENTOFPERSONS_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    speakingImpairmentOfPersons = models.CharField(
      verbose_name='Speaking impairment of persons',
      help_text='Whether the group of participants contains persons with' \
      'with speakingimpairments',
      blank=True,
      max_length=30,
      choices=sorted(PERSONSOURCESETINFOTYPE_SPEAKINGIMPAIRMENTOFPERSONS_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    numberOfTrainedSpeakers = models.BigIntegerField(
      verbose_name='Number of trained speakers',
      help_text='The number of participants that have been trained for t' \
      'he specific task',
      blank=True, null=True, )

    speechInfluences = MultiSelectField(
      verbose_name='Speech influences',
      help_text='Specifies the factors influencing speech',
      blank=True,
      max_length=1 + len(PERSONSOURCESETINFOTYPE_SPEECHINFLUENCES_CHOICES['choices']) / 4,
      choices=PERSONSOURCESETINFOTYPE_SPEECHINFLUENCES_CHOICES['choices'],
      )

    # OneToMany field: participantInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

SETTINGINFOTYPE_NATURALITY_CHOICES = _make_choices_from_list([
  u'natural', u'planned', u'semiPlanned', u'readSpeech', u'spontaneous',
  u'elicited',u'assisted', u'prompted', u'other',
])

SETTINGINFOTYPE_CONVERSATIONALTYPE_CHOICES = _make_choices_from_list([
  u'monologue', u'dialogue', u'multilogue',
])

SETTINGINFOTYPE_SCENARIOTYPE_CHOICES = _make_choices_from_list([
  u'frogStory', u'mapTask', u'onlineEducationalGame', u'pearStory',
  u'rolePlay',u'wordGame', u'wizardOfOz', u'other',
])

SETTINGINFOTYPE_AUDIENCE_CHOICES = _make_choices_from_list([
  u'no', u'few', u'some', u'largePublic',
])

SETTINGINFOTYPE_INTERACTIVITY_CHOICES = _make_choices_from_list([
  u'interactive', u'nonInteractive', u'semiInteractive', u'overlapping',
  u'other',
])

# pylint: disable-msg=C0103
class settingInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Setting"


    __schema_name__ = 'settingInfoType'
    __schema_fields__ = (
      ( u'naturality', u'naturality', OPTIONAL ),
      ( u'conversationalType', u'conversationalType', OPTIONAL ),
      ( u'scenarioType', u'scenarioType', OPTIONAL ),
      ( u'audience', u'audience', OPTIONAL ),
      ( u'interactivity', u'interactivity', OPTIONAL ),
      ( u'interaction', u'interaction', OPTIONAL ),
    )

    naturality = models.CharField(
      verbose_name='Naturality',
      help_text='Specifies the level of naturality for multimodal/multim' \
      'edia resources',
      blank=True,
      max_length=30,
      choices=sorted(SETTINGINFOTYPE_NATURALITY_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    conversationalType = MultiSelectField(
      verbose_name='Conversational type',
      help_text='Specifies the conversational type of the resource',
      blank=True,
      max_length=1 + len(SETTINGINFOTYPE_CONVERSATIONALTYPE_CHOICES['choices']) / 4,
      choices=SETTINGINFOTYPE_CONVERSATIONALTYPE_CHOICES['choices'],
      )

    scenarioType = MultiSelectField(
      verbose_name='Scenario type',
      help_text='Indicates the task defined for the conversation or the ' \
      'interaction of participants',
      blank=True,
      max_length=1 + len(SETTINGINFOTYPE_SCENARIOTYPE_CHOICES['choices']) / 4,
      choices=SETTINGINFOTYPE_SCENARIOTYPE_CHOICES['choices'],
      )

    audience = models.CharField(
      verbose_name='Audience',
      help_text='Indication of the intended audience size',
      blank=True,
      max_length=30,
      choices=sorted(SETTINGINFOTYPE_AUDIENCE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    interactivity = models.CharField(
      verbose_name='Interactivity',
      help_text='Indicates the level of conversational interaction betwe' \
      'en speakers (for audio component) or participants (for video comp' \
      'onent)',
      blank=True,
      max_length=30,
      choices=sorted(SETTINGINFOTYPE_INTERACTIVITY_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    interaction = XmlCharField(
      verbose_name='Interaction',
      help_text='Specifies the parts that interact in an audio or video ' \
      'component',
      blank=True, max_length=1000, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['naturality', 'conversationalType', 'scenarioType', 'audience', 'interactivity', ]
        formatstring = u'{} {} {} {} {}'
        return self.unicode_(formatstring, formatargs)

RUNNINGENVIRONMENTINFOTYPE_REQUIREDHARDWARE_CHOICES = _make_choices_from_list([
  u'graphicCard', u'microphone', u'ocrSystem', u'specialHardwareEquipment',
  u'none',u'other',
])

# pylint: disable-msg=C0103
class runningEnvironmentInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Running environment"


    __schema_name__ = 'runningEnvironmentInfoType'
    __schema_fields__ = (
      ( u'requiredSoftware', u'requiredSoftware', OPTIONAL ),
      ( u'requiredHardware', u'requiredHardware', RECOMMENDED ),
      ( u'requiredLRs', u'requiredLRs', OPTIONAL ),
      ( u'runningEnvironmentDetails', u'runningEnvironmentDetails', OPTIONAL ),
    )
    __schema_classes__ = {
      u'requiredLRs': "targetResourceInfoType_model",
      u'requiredSoftware': "targetResourceInfoType_model",
    }

    requiredSoftware = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Required software',
      help_text='Additional software required for running a tool and/or ' \
      'computational grammar',
      blank=True, null=True, related_name="requiredSoftware_%(class)s_related", )

    requiredHardware = MultiSelectField(
      verbose_name='Required hardware',
      help_text='Hardware required for running a tool and/or computation' \
      'al grammar',
      blank=True,
      max_length=1 + len(RUNNINGENVIRONMENTINFOTYPE_REQUIREDHARDWARE_CHOICES['choices']) / 4,
      choices=RUNNINGENVIRONMENTINFOTYPE_REQUIREDHARDWARE_CHOICES['choices'],
      )

    requiredLRs = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Required language resources',
      help_text='If for running a tool and/or computational grammar, spe' \
      'cific LRs (e.g. a grammar, a list of words etc.) are required',
      blank=True, null=True, related_name="requiredLRs_%(class)s_related", )

    runningEnvironmentDetails = XmlCharField(
      verbose_name='Running environment details',
      help_text='Provides further information on the running environment' \
      '',
      blank=True, max_length=200, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

RECORDINGINFOTYPE_RECORDINGDEVICETYPE_CHOICES = _make_choices_from_list([
  u'hardDisk', u'dv', u'tapeVHS', u'flash', u'DAT', u'soundBlasterCard',
  u'other',
])

RECORDINGINFOTYPE_RECORDINGENVIRONMENT_CHOICES = _make_choices_from_list([
  u'office', u'inCar', u'studio', u'conferenceRoom', u'lectureRoom',
  u'industrial',u'transport', u'openPublicPlace', u'closedPublicPlace',
  u'anechoicChamber',u'other',
])

RECORDINGINFOTYPE_SOURCECHANNEL_CHOICES = _make_choices_from_list([
  u'internet', u'radio', u'tv', u'telephone', u'laryngograph', u'airflow',
  u'EMA',u'webCam', u'camcorder', u'other',
])

RECORDINGINFOTYPE_SOURCECHANNELTYPE_CHOICES = _make_choices_from_list([
  u'ISDN', u'GSM', u'3G', u'CDMA', u'DVB-T', u'DVB-S', u'DVB-C', u'VOIP',
  u'other',
])

# pylint: disable-msg=C0103
class recordingInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Recording"


    __schema_name__ = 'recordingInfoType'
    __schema_fields__ = (
      ( u'recordingDeviceType', u'recordingDeviceType', OPTIONAL ),
      ( u'recordingDeviceTypeDetails', u'recordingDeviceTypeDetails', OPTIONAL ),
      ( u'recordingPlatformSoftware', u'recordingPlatformSoftware', OPTIONAL ),
      ( u'recordingEnvironment', u'recordingEnvironment', OPTIONAL ),
      ( u'sourceChannel', u'sourceChannel', OPTIONAL ),
      ( u'sourceChannelType', u'sourceChannelType', OPTIONAL ),
      ( u'sourceChannelName', u'sourceChannelName', OPTIONAL ),
      ( u'sourceChannelDetails', u'sourceChannelDetails', OPTIONAL ),
      ( 'recorder/personInfo', 'recorder', OPTIONAL ),
      ( 'recorder/organizationInfo', 'recorder', OPTIONAL ),
    )
    __schema_classes__ = {
      u'organizationInfo': "organizationInfoType_model",
      u'personInfo': "personInfoType_model",
    }

    recordingDeviceType = MultiSelectField(
      verbose_name='Recording device type',
      help_text='The nature of the recording platform hardware and the s' \
      'torage medium',
      blank=True,
      max_length=1 + len(RECORDINGINFOTYPE_RECORDINGDEVICETYPE_CHOICES['choices']) / 4,
      choices=RECORDINGINFOTYPE_RECORDINGDEVICETYPE_CHOICES['choices'],
      )

    recordingDeviceTypeDetails = XmlCharField(
      verbose_name='Recording device type details',
      help_text='Free text description of the recoding device',
      blank=True, max_length=500, )

    recordingPlatformSoftware = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=12, max_length=100),
      verbose_name='Recording platform software',
      help_text='The software used for the recording platform',
      blank=True, validators=[validate_matches_xml_char_production], )

    recordingEnvironment = MultiSelectField(
      verbose_name='Recording environment',
      help_text='Where the recording took place',
      blank=True,
      max_length=1 + len(RECORDINGINFOTYPE_RECORDINGENVIRONMENT_CHOICES['choices']) / 4,
      choices=RECORDINGINFOTYPE_RECORDINGENVIRONMENT_CHOICES['choices'],
      )

    sourceChannel = MultiSelectField(
      verbose_name='Source channel',
      help_text='Information on the source channel',
      blank=True,
      max_length=1 + len(RECORDINGINFOTYPE_SOURCECHANNEL_CHOICES['choices']) / 4,
      choices=RECORDINGINFOTYPE_SOURCECHANNEL_CHOICES['choices'],
      )

    sourceChannelType = MultiSelectField(
      verbose_name='Source channel type',
      help_text='Type of the source channel',
      blank=True,
      max_length=1 + len(RECORDINGINFOTYPE_SOURCECHANNELTYPE_CHOICES['choices']) / 4,
      choices=RECORDINGINFOTYPE_SOURCECHANNELTYPE_CHOICES['choices'],
      )

    sourceChannelName = MultiTextField(max_length=30, widget=MultiFieldWidget(widget_id=13, max_length=30),
      verbose_name='Source channel name',
      help_text='The name of the specific source recorded',
      blank=True, validators=[validate_matches_xml_char_production], )

    sourceChannelDetails = XmlCharField(
      verbose_name='Source channel details',
      help_text='The details of the channel equipment used (brand, type ' \
      'etc.)',
      blank=True, max_length=200, )

    recorder = models.ManyToManyField("actorInfoType_model",
      verbose_name='Recorder',
      help_text='Information on the recorder(s) of the audio or video pa' \
      'rt of the resource',
      blank=True, null=True, related_name="recorder_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

RESOLUTIONINFOTYPE_RESOLUTIONSTANDARD_CHOICES = _make_choices_from_list([
  u'VGA', u'HD.720', u'HD.1080',
])

# pylint: disable-msg=C0103
class resolutionInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Resolution"


    __schema_name__ = 'resolutionInfoType'
    __schema_fields__ = (
      ( u'sizeWidth', u'sizeWidth', OPTIONAL ),
      ( u'sizeHeight', u'sizeHeight', OPTIONAL ),
      ( u'resolutionStandard', u'resolutionStandard', OPTIONAL ),
    )

    sizeWidth = models.IntegerField(
      verbose_name='Size width',
      help_text='The frame width in pixels',
      blank=True, null=True, )

    sizeHeight = models.IntegerField(
      verbose_name='Size height',
      help_text='The frame height in pixels',
      blank=True, null=True, )

    resolutionStandard = models.CharField(
      verbose_name='Resolution standard',
      help_text='The standard to which the resolution conforms',
      blank=True,
      max_length=50,
      choices=sorted(RESOLUTIONINFOTYPE_RESOLUTIONSTANDARD_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['sizeWidth', 'sizeHeight', 'resolutionStandard', ]
        formatstring = u'{} {} {}'
        return self.unicode_(formatstring, formatargs)

COMPRESSIONINFOTYPE_COMPRESSIONNAME_CHOICES = _make_choices_from_list([
  u'mpg', u'avi', u'mov', u'flac', u'shorten', u'mp3', u'oggVorbis',
  u'atrac',u'aac', u'mpeg', u'realAudio', u'other',
])

# pylint: disable-msg=C0103
class compressionInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Compression"


    __schema_name__ = 'compressionInfoType'
    __schema_fields__ = (
      ( u'compression', u'compression', REQUIRED ),
      ( u'compressionName', u'compressionName', OPTIONAL ),
      ( u'compressionLoss', u'compressionLoss', OPTIONAL ),
    )

    compression = MetaBooleanField(
      verbose_name='Compression',
      help_text='Whether the audio, video or image is compressed or not',
      )

    compressionName = MultiSelectField(
      verbose_name='Compression name',
      help_text='The name of the compression applied',
      blank=True,
      max_length=1 + len(COMPRESSIONINFOTYPE_COMPRESSIONNAME_CHOICES['choices']) / 4,
      choices=COMPRESSIONINFOTYPE_COMPRESSIONNAME_CHOICES['choices'],
      )

    compressionLoss = MetaBooleanField(
      verbose_name='Compression loss',
      help_text='Whether there is loss due to compression',
      blank=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LINKTOOTHERMEDIAINFOTYPE_OTHERMEDIA_CHOICES = _make_choices_from_list([
  u'text', u'textNumerical', u'video', u'audio', u'image',
])

# pylint: disable-msg=C0103
class linkToOtherMediaInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Link to other media"
        verbose_name_plural = "Links to other media"


    __schema_name__ = 'linkToOtherMediaInfoType'
    __schema_fields__ = (
      ( u'otherMedia', u'otherMedia', REQUIRED ),
      ( u'mediaTypeDetails', u'mediaTypeDetails', OPTIONAL ),
      ( u'synchronizedWithText', u'synchronizedWithText', OPTIONAL ),
      ( u'synchronizedWithAudio', u'synchronizedWithAudio', OPTIONAL ),
      ( u'synchronizedWithVideo', u'synchronizedWithVideo', OPTIONAL ),
      ( u'synchronizedWithImage', u'synchronizedWithImage', OPTIONAL ),
      ( u'synchronizedWithTextNumerical', u'synchronizedWithTextNumerical', OPTIONAL ),
    )

    otherMedia = models.CharField(
      verbose_name='Other media',
      help_text='Specifies the media types that are linked to the media ' \
      'type described within the same resource',

      max_length=30,
      choices=sorted(LINKTOOTHERMEDIAINFOTYPE_OTHERMEDIA_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    mediaTypeDetails = XmlCharField(
      verbose_name='Media type details',
      help_text='Provides further information on the way the media types' \
      ' are linked and/or synchronized with each other within the same r' \
      'esource',
      blank=True, max_length=500, )

    synchronizedWithText = MetaBooleanField(
      verbose_name='Synchronized with text',
      help_text='Whether video, text and textNumerical media type is syn' \
      'chronized with text within the same resource',
      blank=True, )

    synchronizedWithAudio = MetaBooleanField(
      verbose_name='Synchronized with audio',
      help_text='Whether text, video or textNumerical media type is sync' \
      'hronized with audio within the same resource',
      blank=True, )

    synchronizedWithVideo = MetaBooleanField(
      verbose_name='Synchronized with video',
      help_text='Whether text or textNumerical media type is synchronize' \
      'd with video within the same resource',
      blank=True, )

    synchronizedWithImage = MetaBooleanField(
      verbose_name='Synchronized with image',
      help_text='Whether text or textNumerical media type is synchronize' \
      'd with image within the same resource',
      blank=True, )

    synchronizedWithTextNumerical = MetaBooleanField(
      verbose_name='Synchronized with text numerical',
      help_text='Whether video or audio media type is synchronized with ' \
      'the textNumerical (representation of sensorimotor measurements) w' \
      'ithin the same resource',
      blank=True, )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_corpustextnumericalinfotype_model = models.ForeignKey("corpusTextNumericalInfoType_model",  blank=True, null=True)

    back_to_languagedescriptiontextinfotype_model = models.ForeignKey("languageDescriptionTextInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionvideoinfotype_model = models.ForeignKey("languageDescriptionVideoInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionimageinfotype_model = models.ForeignKey("languageDescriptionImageInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class documentListType_model(SchemaModel):

    class Meta:
        verbose_name = "Document list"


    __schema_name__ = 'documentListType'
    __schema_fields__ = (
      ( u'documentInfo', u'documentInfo', REQUIRED ),
    )
    __schema_classes__ = {
      u'documentInfo': "documentInfoType_model",
    }

    documentInfo = models.ManyToManyField("documentInfoType_model",
      verbose_name='Document',
      help_text='Groups information on a document in a structured format' \
      '; it can be used both for published or unpublished documents; dep' \
      'ending on the role of the document (e.g. usage report, validation' \
      ' report, annotation manual etc.), it can be found at various plac' \
      'es of the metadata',
      related_name="documentInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class communicationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Communication"


    __schema_name__ = 'communicationInfoType'
    __schema_fields__ = (
      ( u'email', u'email', REQUIRED ),
      ( u'url', u'url', OPTIONAL ),
      ( u'address', u'address', OPTIONAL ),
      ( u'zipCode', u'zipCode', OPTIONAL ),
      ( u'city', u'city', OPTIONAL ),
      ( u'region', u'region', OPTIONAL ),
      ( u'country', u'country', OPTIONAL ),
      ( u'telephoneNumber', u'telephoneNumber', OPTIONAL ),
      ( u'faxNumber', u'faxNumber', OPTIONAL ),
    )

    email = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=14, max_length=100),
      verbose_name='Email', validators=[EMAILADDRESS_VALIDATOR],
      help_text='The email address of a person or an organization',
      )

    url = MultiTextField(max_length=150, widget=MultiFieldWidget(widget_id=15, max_length=150),
      verbose_name='URL (Landing page)', validators=[HTTPURI_VALIDATOR],
      help_text='A URL used as homepage of an entity (e.g. of a person, ' \
      'organization, resource etc.); it provides general information (fo' \
      'r instance in the case of a resource, it may present a descriptio' \
      'n of the resource, its creators and possibly include links to the' \
      ' URL where it can be accessed from)',
      blank=True, )

    address = XmlCharField(
      verbose_name='Address',
      help_text='The street and the number of the postal address of a pe' \
      'rson or organization',
      blank=True, max_length=200, )

    zipCode = XmlCharField(
      verbose_name='Zip code',
      help_text='The zip code of the postal address of a person or organ' \
      'ization',
      blank=True, max_length=30, )

    city = XmlCharField(
      verbose_name='City',
      help_text='The name of the city, town or village as mentioned in t' \
      'he postal address of a person or organization',
      blank=True, max_length=50, )

    region = XmlCharField(
      verbose_name='Region',
      help_text='The name of the region, county or department as mention' \
      'ed in the postal address of a person or organization',
      blank=True, max_length=100, )

    country = XmlCharField(
      verbose_name='Country',
      help_text='The name of the country mentioned in the postal address' \
      ' of a person or organization as defined in the list of values of ' \
      'ISO 3166',
      blank=True, max_length=100,
      choices =_make_choices_from_list(sorted(iana.get_all_regions()))['choices'])

    countryId = XmlCharField(
      verbose_name='Country identifier',
      help_text='The identifier of the country mentioned in the postal '\
                'address of a person or organization as defined in the '\
                'list of values of ISO 3166',
      max_length=100, editable=False,)

    telephoneNumber = MultiTextField(max_length=30, widget=MultiFieldWidget(widget_id=16, max_length=30),
      verbose_name='Telephone number',
      help_text='The telephone number of a person or an organization; re' \
      'commended format: +_international code_city code_number',
      blank=True, validators=[validate_matches_xml_char_production], )

    faxNumber = MultiTextField(max_length=30, widget=MultiFieldWidget(widget_id=17, max_length=30),
      verbose_name='Fax number',
      help_text='The fax number of a person or an organization; recommen' \
      'ded format: +_international code_city code_number',
      blank=True, validators=[validate_matches_xml_char_production], )

    def save(self, *args, **kwargs):
        if self.country:
            self.countryId = iana.get_region_subtag(self.country)

        # # Call save() method from super class with all arguments.
        super(communicationInfoType_model, self).save(*args, **kwargs)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['email', 'telephoneNumber', ]
        formatstring = u'{} {}'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class personListType_model(SchemaModel):

    class Meta:
        verbose_name = "Person list"


    __schema_name__ = 'personListType'
    __schema_fields__ = (
      ( u'personInfo', u'personInfo', REQUIRED ),
    )
    __schema_classes__ = {
      u'personInfo': "personInfoType_model",
    }

    personInfo = models.ManyToManyField("personInfoType_model",
      verbose_name='Person',
      help_text='Groups information relevant to persons related to the r' \
      'esource; to be used mainly for contact persons, resource creators' \
      ', validators, annotators etc. for whom personal data can be provi' \
      'ded',
      related_name="personInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class organizationListType_model(SchemaModel):

    class Meta:
        verbose_name = "Organization list"


    __schema_name__ = 'organizationListType'
    __schema_fields__ = (
      ( u'organizationInfo', u'organizationInfo', REQUIRED ),
    )
    __schema_classes__ = {
      u'organizationInfo': "organizationInfoType_model",
    }

    organizationInfo = models.ManyToManyField("organizationInfoType_model",
      verbose_name='Organization',
      help_text='Groups information on organizations related to the reso' \
      'urce',
      related_name="organizationInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class actorInfoType_model(SubclassableModel):

    __schema_name__ = 'SUBCLASSABLE'

    class Meta:
        verbose_name = "Actor"


# pylint: disable-msg=C0103
class organizationInfoType_model(actorInfoType_model):

    class Meta:
        verbose_name = "Organization"


    __schema_name__ = 'organizationInfoType'
    __schema_fields__ = (
      ( u'organizationName', u'organizationName', REQUIRED ),
      ( u'organizationShortName', u'organizationShortName', OPTIONAL ),
      ( u'departmentName', u'departmentName', OPTIONAL ),
      ( u'communicationInfo', u'communicationInfo', REQUIRED ),
    )
    __schema_classes__ = {
      u'communicationInfo': "communicationInfoType_model",
    }

    organizationName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Organization name',
      max_val_length=100,
      help_text='The full name of an organization',
      )

    organizationShortName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Organization short name',
      max_val_length=100,
      help_text='The short name (abbreviation, acronym etc.) used for an' \
      ' organization',
      blank=True)

    departmentName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Department name',
      help_text='The name of the department or unit (e.g. specific unive' \
      'rsity faculty/department, department/unit of a research organizat' \
      'ion or private company etc.)',
      blank=True)

    communicationInfo = models.OneToOneField("communicationInfoType_model",
      verbose_name='Communication',
      help_text='Groups information on communication details of a person' \
      ' or an organization',
      )


    source_url = models.URLField(verify_exists=False,
      default=DJANGO_URL,
      help_text="(Read-only) base URL for the server where the master copy of " \
      "the associated entity instance is located.")

    copy_status = models.CharField(default=MASTER, max_length=1, choices=COPY_CHOICES,
        help_text="Generalized copy status flag for this entity instance.")

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['organizationName', 'departmentName', ]
        formatstring = u'{} \u2013 department: {}'
        return self.unicode_(formatstring, formatargs)

PERSONINFOTYPE_SEX_CHOICES = _make_choices_from_list([
  u'male', u'female', u'unknown',
])

# pylint: disable-msg=C0103
class personInfoType_model(actorInfoType_model):

    class Meta:
        verbose_name = "Person"


    __schema_name__ = 'personInfoType'
    __schema_fields__ = (
      ( u'surname', u'surname', REQUIRED ),
      ( u'givenName', u'givenName', RECOMMENDED ),
      ( u'sex', u'sex', OPTIONAL ),
      ( u'communicationInfo', u'communicationInfo', REQUIRED ),
      ( u'position', u'position', OPTIONAL ),
      ( u'affiliation', u'affiliation', OPTIONAL ),
    )
    __schema_classes__ = {
      u'affiliation': "organizationInfoType_model",
      u'communicationInfo': "communicationInfoType_model",
    }

    surname = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Surname',
      max_val_length=100,
      help_text='The surname (family name) of a person related to the re' \
      'source',
      )

    givenName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Given name',
      max_val_length=100,
      help_text='The given name (first name) of a person related to the ' \
      'resource; initials can also be used',
      blank=True)

    sex = models.CharField(
      verbose_name='Sex',
      help_text='The gender of a person related to or participating in t' \
      'he resource',
      blank=True,
      max_length=30,
      choices=sorted(PERSONINFOTYPE_SEX_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    communicationInfo = models.OneToOneField("communicationInfoType_model",
      verbose_name='Communication',
      help_text='Groups information on communication details of a person' \
      ' or an organization',
      )

    position = XmlCharField(
      verbose_name='Position',
      help_text='The position or the title of a person if affiliated to ' \
      'an organization',
      blank=True, max_length=100, )

    affiliation = models.ManyToManyField("organizationInfoType_model",
      verbose_name='Affiliation',
      help_text='Groups information on organization to whomtheperson is ' \
      'affiliated',
      blank=True, null=True, related_name="affiliation_%(class)s_related", )


    source_url = models.URLField(verify_exists=False,
      default=DJANGO_URL,
      help_text="(Read-only) base URL for the server where the master copy of " \
      "the associated entity instance is located.")

    copy_status = models.CharField(default=MASTER, max_length=1, choices=COPY_CHOICES,
        help_text="Generalized copy status flag for this entity instance.")

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['surname', 'givenName', 'communicationInfo/email', 'affiliation', ]
        formatstring = u'{} {} {} {}'
        return self.unicode_(formatstring, formatargs)

DISTRIBUTIONINFOTYPE_AVAILABILITY_CHOICES = _make_choices_from_list([
  u'available', u'availableThroughOtherDistributor', u'underNegotiation',
])

# pylint: disable-msg=C0103
class distributionInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Distribution"


    __schema_name__ = 'distributionInfoType'
    __schema_fields__ = (
      ( u'availability', u'availability', REQUIRED ),
      ( u'licenceInfo', u'licenceinfotype_model_set', REQUIRED ),
      ( 'iprHolder/personInfo', 'iprHolder', OPTIONAL ),
      ( 'iprHolder/organizationInfo', 'iprHolder', OPTIONAL ),
      ( u'availabilityEndDate', u'availabilityEndDate', OPTIONAL ),
      ( u'availabilityStartDate', u'availabilityStartDate', OPTIONAL ),
    )
    __schema_classes__ = {
      u'licenceInfo': "licenceInfoType_model",
      u'organizationInfo': "organizationInfoType_model",
      u'personInfo': "personInfoType_model",
    }

    availability = models.CharField(
      verbose_name='Availability',
      help_text='Specifies the availability status of the resource; rest' \
      'rictionsOfUse can be further used to indicate the specific terms ' \
      'of availability',

      max_length=40,
      choices=sorted(DISTRIBUTIONINFOTYPE_AVAILABILITY_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    # OneToMany field: licenceInfo

    iprHolder = models.ManyToManyField("actorInfoType_model",
      verbose_name='IPR holder',
      help_text='Groups information on a person or an organization who h' \
      'olds the full Intellectual Property Rights (Copyright, trademark ' \
      'etc) that subsist in the resource. The IPR holder could be differ' \
      'ent from the creator that may have assigned the rights to the IPR' \
      ' holder (e.g. an author as a creator assigns her rights to the pu' \
      'blisher who is the IPR holder) and the distributor that holds a s' \
      'pecific licence (i.e. a permission) to distribute the work within' \
      ' the META-SHARE network.',
      blank=True, null=True, related_name="iprHolder_%(class)s_related", )

    availabilityEndDate = models.DateField(
      verbose_name='Availability end date',
      help_text='Specifies the end date of availability of a resource - ' \
      'only for cases where a resource is available for a restricted tim' \
      'e period.',
      blank=True, null=True, )

    availabilityStartDate = models.DateField(
      verbose_name='Availability start date',
      help_text='Specifies the start date of availability of a resource ' \
      '- only for cases where a resource is available for a restricted t' \
      'ime period.',
      blank=True, null=True, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['availability', 'licenceInfo', ]
        formatstring = u'{}, licenses: {}'
        return self.unicode_(formatstring, formatargs)

MEMBERSHIPINFOTYPE_MEMBERSHIPINSTITUTION_CHOICES = _make_choices_from_list([
  u'ELRA', u'LDC', u'TST-CENTRALE', u'other',
])

# pylint: disable-msg=C0103
class membershipInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Membership"


    __schema_name__ = 'membershipInfoType'
    __schema_fields__ = (
      ( u'member', u'member', REQUIRED ),
      ( u'membershipInstitution', u'membershipInstitution', REQUIRED ),
    )

    member = MetaBooleanField(
      verbose_name='Member',
      help_text='Whether the user is a member or not',
      )

    membershipInstitution = MultiSelectField(
      verbose_name='Membership institution',
      help_text='This lists the different institutions releasing the res' \
      'ources and establishing membership conditions',

      max_length=1 + len(MEMBERSHIPINFOTYPE_MEMBERSHIPINSTITUTION_CHOICES['choices']) / 4,
      choices=MEMBERSHIPINFOTYPE_MEMBERSHIPINSTITUTION_CHOICES['choices'],
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['member', 'membershipInstitution', ]
        formatstring = u'member:{} {}'
        return self.unicode_(formatstring, formatargs)

LICENCEINFOTYPE_LICENCE_CHOICES = _make_choices_from_list([
  u'CC-BY', u'CC-BY-NC', u'CC-BY-NC-ND', u'CC-BY-NC-SA', u'CC-BY-ND',
  u'CC-BY-SA',u'CC-ZERO', u'PDDL', u'ODC-BY', u'ODbL', u'MS-NoReD',
  u'MS-NoReD-FF',u'MS-NoReD-ND', u'MS-NoReD-ND-FF', u'MS-NC-NoReD',
  u'MS-NC-NoReD-FF',u'MS-NC-NoReD-ND', u'MS-NC-NoReD-ND-FF',
  u'ELRA_END_USER',u'ELRA_EVALUATION', u'ELRA_VAR', u'CLARIN_PUB',
  u'CLARIN_ACA',u'CLARIN_ACA-NC', u'CLARIN_RES', u'AGPL',
  u'ApacheLicence_2.0',u'BSD_4-clause', u'BSD_3-clause', u'FreeBSD',
  u'GFDL',u'GPL', u'LGPL', u'Princeton_Wordnet', u'proprietary',
  u'underNegotiation',u'nonStandardLicenceTerms',
])

LICENCEINFOTYPE_RESTRICTIONSOFUSE_CHOICES = _make_choices_from_list([
  u'attribution', u'nonCommercialUse', u'commercialUse', u'shareAlike',
  u'noDerivatives',u'noRedistribution', u'evaluationUse', u'research',
  u'education',u'informLicensor', u'redeposit', u'compensate',
  u'languageEngineeringResearch', u'requestPlan', u'spatialConstraint',
  u'userIdentified', u'personalDataIncluded',u'sensitiveDataIncluded', u'other',
])

LICENCEINFOTYPE_DISTRIBUTIONACCESSMEDIUM_CHOICES = _make_choices_from_list([
  u'webExecutable', u'paperCopy', u'hardDisk', u'bluRay', u'DVD-R',
  u'CD-ROM',u'downloadable', u'accessibleThroughInterface', u'other',
])

LICENCEINFOTYPE_USERNATURE_CHOICES = _make_choices_from_list([
  u'academic', u'commercial',
])

# pylint: disable-msg=C0103
class licenceInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Licence"


    __schema_name__ = 'licenceInfoType'
    __schema_fields__ = (
      ( u'licence', u'licence', REQUIRED ),
      ( u'nonStandardLicenceName', u'nonStandardLicenceName', OPTIONAL ),
      ( u'nonStandardLicenceTermsURL', u'nonStandardLicenceTermsURL', OPTIONAL ),
      ( u'nonStandaradLicenceTermsText', u'nonStandaradLicenceTermsText', OPTIONAL ),
      ( u'restrictionsOfUse', u'restrictionsOfUse', OPTIONAL ),
      ( u'distributionAccessMedium', u'distributionAccessMedium', RECOMMENDED ),
      ( u'downloadLocation', u'downloadLocation', OPTIONAL ),
      ( u'executionLocation', u'executionLocation', OPTIONAL ),
      ( u'attributionText', u'attributionText', OPTIONAL ),
      ( u'fee', u'fee', OPTIONAL ),
      ( 'licensor/personInfo', 'licensor', RECOMMENDED ),
      ( 'licensor/organizationInfo', 'licensor', RECOMMENDED ),
      ( 'distributionRightsHolder/personInfo', 'distributionRightsHolder', RECOMMENDED ),
      ( 'distributionRightsHolder/organizationInfo', 'distributionRightsHolder', RECOMMENDED ),
      ( u'userNature', u'userNature', OPTIONAL ),
      ( u'membershipInfo', u'membershipInfo', OPTIONAL ),
    )
    __schema_classes__ = {
      u'membershipInfo': "membershipInfoType_model",
      u'organizationInfo': "organizationInfoType_model",
      u'personInfo': "personInfoType_model",
    }

    licence = MultiSelectField(
      verbose_name='Licence',
      help_text='The licence of use for the resource; if possible, pleas' \
      'e use one of the recommended standard licences',

      max_length=1 + len(LICENCEINFOTYPE_LICENCE_CHOICES['choices']) / 4,
      choices=LICENCEINFOTYPE_LICENCE_CHOICES['choices'],
      )

    nonStandardLicenceName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Name (for non-standard licences)',
      max_val_length=100,
      help_text='The name with which a licence is known; to be used for ' \
      'licences not included in the pre-defined list of recommended lice' \
      'nces',
      blank=True)

    nonStandardLicenceTermsURL = XmlCharField(
      verbose_name='URL for non-standard licences / terms of use / terms of service', validators=[HTTPURI_VALIDATOR],
      help_text='Used to provide a hyperlink to a url containing the tex' \
      't of a licence not included in the predefined list or describing ' \
      'the terms of use for a language resource or terms of service for ' \
      'web services',
      blank=True, max_length=1000, )

    nonStandaradLicenceTermsText = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Text (for non-standard licences / terms of use / terms of service)',
      max_val_length=1000,
      help_text='Used for inputting the text of licences (that are not i' \
      'ncluded in the pre-defined list) and terms of use or terms of ser' \
      'vice (for web services)',
      blank=True)

    restrictionsOfUse = MultiSelectField(
      verbose_name='Conditions of use',
      help_text='Specifies the conditions and terms of use imposed by th' \
      'e licence',
      blank=True,
      max_length=1 + len(LICENCEINFOTYPE_RESTRICTIONSOFUSE_CHOICES['choices']) / 4,
      choices=LICENCEINFOTYPE_RESTRICTIONSOFUSE_CHOICES['choices'],
      )

    distributionAccessMedium = MultiSelectField(
      verbose_name='Distribution / Access medium',
      help_text='Specifies the medium (channel) used for delivery or pro' \
      'viding access to the resource',
      blank=True,
      max_length=1 + len(LICENCEINFOTYPE_DISTRIBUTIONACCESSMEDIUM_CHOICES['choices']) / 4,
      choices=LICENCEINFOTYPE_DISTRIBUTIONACCESSMEDIUM_CHOICES['choices'],
      )

    downloadLocation = MultiTextField(max_length=150, widget=MultiFieldWidget(widget_id=18, max_length=150),
      verbose_name='Download location', validators=[HTTPURI_VALIDATOR],
      help_text='Any url where the resource can be downloaded from; plea' \
      'se, use if the resource is "downloadable" and you have not upload' \
      'ed the resource in the repository',
      blank=True, )

    executionLocation = MultiTextField(max_length=150, widget=MultiFieldWidget(widget_id=19, max_length=150),
      verbose_name='Execution location', validators=[HTTPURI_VALIDATOR],
      help_text=' Any url where the service providing access to a resour' \
      'ce is being executed; please use for resources that are "accessib' \
      'leThroughInterface" or "webExecutable" ',
      blank=True, )

    attributionText = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Attribution text',
      max_val_length=1000,
      help_text=' The text that must be quoted for attribution purposes ' \
      'when using a resource - for cases where a resource is provided wi' \
      'th a restriction on attribution; you can use a standard text such' \
      ' as "Resource A by Resource Creator/Owner B used under licence C ' \
      'as accessed at D" ',
      blank=True)

    fee = XmlCharField(
      verbose_name='Fee',
      help_text='Specifies the costs that are required to access the res' \
      'ource, a fragment of the resource or to use a tool or service',
      blank=True, max_length=100, )

    licensor = models.ManyToManyField("actorInfoType_model",
      verbose_name='Licensor',
      help_text='Groups information on the person who is legally eligibl' \
      'e to licence and actually licenses the resource. The licensor cou' \
      'ld be different from the creator, the distributor or the IP right' \
      'sholder. The licensor has the necessary rights or licences to lic' \
      'ense the work and is the party that actually licenses the resourc' \
      'e that enters the META-SHARE network. She will have obtained the ' \
      'necessary rights or licences from the IPR holder and she may have' \
      ' a distribution agreement with a distributor that disseminates th' \
      'e work under a set of conditions defined in the specific licence ' \
      'and collects revenue on the licensor\'s behalf. The attribution o' \
      'f the creator, separately from the attribution of the licensor, m' \
      'ay be part of the licence under which the resource is distributed' \
      ' (as e.g. is the case with Creative Commons Licences)',
      blank=True, null=True, related_name="licensor_%(class)s_related", )

    distributionRightsHolder = models.ManyToManyField("actorInfoType_model",
      verbose_name='Distribution rights holder',
      help_text='Groups information on a person or an organization that ' \
      'holds the distribution rights. The range and scope of distributio' \
      'n rights is defined in the distribution agreement. The distributo' \
      'r in most cases only has a limited licence to distribute the work' \
      ' and collect royalties on behalf of the licensor or the IPR holde' \
      'r and cannot give to any recipient of the work permissions that e' \
      'xceed the scope of the distribution agreement (e.g. to allow uses' \
      ' of the work that are not defined in the distribution agreement)',
      blank=True, null=True, related_name="distributionRightsHolder_%(class)s_related", )

    userNature = MultiSelectField(
      verbose_name='User nature',
      help_text='The conditions imposed by the nature of the user (for i' \
      'nstance, a research use may have different implications depending' \
      ' on this)',
      blank=True,
      max_length=1 + len(LICENCEINFOTYPE_USERNATURE_CHOICES['choices']) / 4,
      choices=LICENCEINFOTYPE_USERNATURE_CHOICES['choices'],
      )

    membershipInfo = models.ManyToManyField("membershipInfoType_model",
      verbose_name='Membership', blank=True, null=True, related_name="membershipInfo_%(class)s_related", )

    back_to_distributioninfotype_model = models.ForeignKey("distributionInfoType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['licence', ]
        formatstring = u'{}'
        return self.unicode_(formatstring, formatargs)

CHARACTERENCODINGINFOTYPE_CHARACTERENCODING_CHOICES = _make_choices_from_list([
  u'US-ASCII', u'windows-1250', u'windows-1251', u'windows-1252',
  u'windows-1253',u'windows-1254', u'windows-1257', u'ISO-8859-1',
  u'ISO-8859-2',u'ISO-8859-4', u'ISO-8859-5', u'ISO-8859-7', u'ISO-8859-9',
  u'ISO-8859-13',u'ISO-8859-15', u'KOI8-R', u'UTF-8', u'UTF-16',
  u'UTF-16BE',u'UTF-16LE', u'windows-1255', u'windows-1256',
  u'windows-1258',u'ISO-8859-3', u'ISO-8859-6', u'ISO-8859-8',
  u'windows-31j',u'EUC-JP', u'x-EUC-JP-LINUX', u'Shift_JIS', u'ISO-2022-JP',
  u'x-mswin-936',u'GB18030', u'x-EUC-CN', u'GBK', u'ISCII91',
  u'x-windows-949',u'EUC-KR', u'ISO-2022-KR', u'x-windows-950',
  u'x-MS950-HKSCS',u'x-EUC-TW', u'Big5', u'Big5-HKSCS', u'TIS-620',
  u'Big5_Solaris',u'Cp037', u'Cp273', u'Cp277', u'Cp278', u'Cp280',
  u'Cp284',u'Cp285', u'Cp297', u'Cp420', u'Cp424', u'Cp437', u'Cp500',
  u'Cp737',u'Cp775', u'Cp838', u'Cp850', u'Cp852', u'Cp855', u'Cp856',
  u'Cp857',u'Cp858', u'Cp860', u'Cp861', u'Cp862', u'Cp863', u'Cp864',
  u'Cp865',u'Cp866', u'Cp868', u'Cp869', u'Cp870', u'Cp871', u'Cp874',
  u'Cp875',u'Cp918', u'Cp921', u'Cp922', u'Cp930', u'Cp933', u'Cp935',
  u'Cp937',u'Cp939', u'Cp942', u'Cp942C', u'Cp943', u'Cp943C', u'Cp948',
  u'Cp949',u'Cp949C', u'Cp950', u'Cp964', u'Cp970', u'Cp1006', u'Cp1025',
  u'Cp1026',u'Cp1046', u'Cp1047', u'Cp1097', u'Cp1098', u'Cp1112',
  u'Cp1122',u'Cp1123', u'Cp1124', u'Cp1140', u'Cp1141', u'Cp1142',
  u'Cp1143',u'Cp1144', u'Cp1145', u'Cp1146', u'Cp1147', u'Cp1148',
  u'Cp1149',u'Cp1381', u'Cp1383', u'Cp33722', u'ISO2022_CN_CNS',
  u'ISO2022_CN_GB',u'JISAutoDetect', u'MS874', u'MacArabic',
  u'MacCentralEurope',u'MacCroatian', u'MacCyrillic', u'MacDingbat',
  u'MacGreek',u'MacHebrew', u'MacIceland', u'MacRoman', u'MacRomania',
  u'MacSymbol',u'MacThai', u'MacTurkish', u'MacUkraine',
])

# pylint: disable-msg=C0103
class characterEncodingInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Character encoding"


    __schema_name__ = 'characterEncodingInfoType'
    __schema_fields__ = (
      ( u'characterEncoding', u'characterEncoding', REQUIRED ),
      ( u'sizePerCharacterEncoding', u'sizePerCharacterEncoding', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerCharacterEncoding': "sizeInfoType_model",
    }

    characterEncoding = models.CharField(
      verbose_name='Character encoding',
      help_text='The name of the character encoding used in the resource' \
      ' or accepted by the tool/service',

      max_length=100,
      choices=sorted(CHARACTERENCODINGINFOTYPE_CHARACTERENCODING_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerCharacterEncoding = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per character encoding',
      help_text='Provides information on the size of the resource parts ' \
      'with different character encoding',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    back_to_languagedescriptiontextinfotype_model = models.ForeignKey("languageDescriptionTextInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcetextinfotype_model = models.ForeignKey("lexicalConceptualResourceTextInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class timeCoverageInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Time coverage"


    __schema_name__ = 'timeCoverageInfoType'
    __schema_fields__ = (
      ( u'timeCoverage', u'timeCoverage', REQUIRED ),
      ( u'sizePerTimeCoverage', u'sizePerTimeCoverage', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerTimeCoverage': "sizeInfoType_model",
    }

    timeCoverage = XmlCharField(
      verbose_name='Time coverage',
      help_text='The time period that the content of a resource is about' \
      '',
      max_length=100, )

    sizePerTimeCoverage = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per time coverage',
      help_text='Provides information on size per time period represente' \
      'd in the resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    back_to_languagedescriptiontextinfotype_model = models.ForeignKey("languageDescriptionTextInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionvideoinfotype_model = models.ForeignKey("languageDescriptionVideoInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionimageinfotype_model = models.ForeignKey("languageDescriptionImageInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceaudioinfotype_model = models.ForeignKey("lexicalConceptualResourceAudioInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcetextinfotype_model = models.ForeignKey("lexicalConceptualResourceTextInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcevideoinfotype_model = models.ForeignKey("lexicalConceptualResourceVideoInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceimageinfotype_model = models.ForeignKey("lexicalConceptualResourceImageInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class geographicCoverageInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Geographic coverage"


    __schema_name__ = 'geographicCoverageInfoType'
    __schema_fields__ = (
      ( u'geographicCoverage', u'geographicCoverage', REQUIRED ),
      ( u'sizePerGeographicCoverage', u'sizePerGeographicCoverage', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerGeographicCoverage': "sizeInfoType_model",
    }

    geographicCoverage = XmlCharField(
      verbose_name='Geographic coverage',
      help_text='The geographic region that the content of a resource is' \
      ' about; for countries, recommended use of ISO-3166',
      max_length=100, )

    sizePerGeographicCoverage = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per geographic coverage',
      help_text='Provides information on size per geographically distinc' \
      't section of the resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    back_to_languagedescriptiontextinfotype_model = models.ForeignKey("languageDescriptionTextInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionvideoinfotype_model = models.ForeignKey("languageDescriptionVideoInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionimageinfotype_model = models.ForeignKey("languageDescriptionImageInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceaudioinfotype_model = models.ForeignKey("lexicalConceptualResourceAudioInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcetextinfotype_model = models.ForeignKey("lexicalConceptualResourceTextInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcevideoinfotype_model = models.ForeignKey("lexicalConceptualResourceVideoInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceimageinfotype_model = models.ForeignKey("lexicalConceptualResourceImageInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LINGUALITYINFOTYPE_LINGUALITYTYPE_CHOICES = _make_choices_from_list([
  u'monolingual', u'bilingual', u'multilingual',
])

LINGUALITYINFOTYPE_MULTILINGUALITYTYPE_CHOICES = _make_choices_from_list([
  u'parallel', u'comparable', u'multilingualSingleText', u'other',
])

# pylint: disable-msg=C0103
class lingualityInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Linguality"
        verbose_name_plural = "Lingualities"


    __schema_name__ = 'lingualityInfoType'
    __schema_fields__ = (
      ( u'lingualityType', u'lingualityType', REQUIRED ),
      ( u'multilingualityType', u'multilingualityType', OPTIONAL ),
      ( u'multilingualityTypeDetails', u'multilingualityTypeDetails', OPTIONAL ),
    )

    lingualityType = models.CharField(
      verbose_name='Linguality type',
      help_text='Indicates whether the resource includes one, two or mor' \
      'e languages',

      max_length=20,
      choices=sorted(LINGUALITYINFOTYPE_LINGUALITYTYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    multilingualityType = models.CharField(
      verbose_name='Multilinguality type',
      help_text='Indicates whether the corpus is parallel, comparable or' \
      ' mixed',
      blank=True,
      max_length=30,
      choices=sorted(LINGUALITYINFOTYPE_MULTILINGUALITYTYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    multilingualityTypeDetails = XmlCharField(
      verbose_name='Multilinguality type details',
      help_text='Provides further information on multilinguality of a re' \
      'source in free text',
      blank=True, max_length=512, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['lingualityType', ]
        formatstring = u'{}'
        return self.unicode_(formatstring, formatargs)

LANGUAGEVARIETYINFOTYPE_LANGUAGEVARIETYTYPE_CHOICES = _make_choices_from_list([
  u'dialect', u'jargon', u'other',
])

# pylint: disable-msg=C0103
class languageVarietyInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Language variety"
        verbose_name_plural = "Language varieties"


    __schema_name__ = 'languageVarietyInfoType'
    __schema_fields__ = (
      ( u'languageVarietyType', u'languageVarietyType', REQUIRED ),
      ( u'languageVarietyName', u'languageVarietyName', REQUIRED ),
      ( u'sizePerLanguageVariety', u'sizePerLanguageVariety', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerLanguageVariety': "sizeInfoType_model",
    }

    languageVarietyType = models.CharField(
      verbose_name='Language variety type',
      help_text='Specifies the type of the language variety that occurs ' \
      'in the resource or is supported by a tool/service',

      max_length=20,
      choices=sorted(LANGUAGEVARIETYINFOTYPE_LANGUAGEVARIETYTYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    languageVarietyName = XmlCharField(
      verbose_name='Language variety name',
      help_text='The name of the language variety that occurs in the res' \
      'ource or is supported by a tool/service',
      max_length=100, )

    sizePerLanguageVariety = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per language variety',
      help_text='Provides information on the size per language variety c' \
      'omponent',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['languageVarietyName', 'languageVarietyType', ]
        formatstring = u'{} ({})'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class languageInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Language"


    __schema_name__ = 'languageInfoType'
    __schema_fields__ = (
      ( u'languageId', u'languageId', REQUIRED ),
      ( u'languageName', u'languageName', REQUIRED ),
      ( u'languageScript', u'languageScript', OPTIONAL ),
      ( u'region', u'region', OPTIONAL ),
      ( u'variant', u'variant', OPTIONAL ),
      ( u'sizePerLanguage', u'sizePerLanguage', OPTIONAL ),
      ( u'languageVarietyInfo', u'languageVarietyInfo', OPTIONAL ),
    )
    __schema_classes__ = {
      u'languageVarietyInfo': "languageVarietyInfoType_model",
      u'sizePerLanguage': "sizeInfoType_model",
    }

    languageId = XmlCharField(
      verbose_name='Language identifier',
      help_text='The identifier of the language that is included in the ' \
      'resource or supported by the tool/service, according to the IETF ' \
      'BCP47 guidelines',
      max_length=100, editable=False,)

    languageName = models.CharField(
      verbose_name='Language name',
      help_text='A human understandable name of the language that is use' \
      'd in the resource or supported by the tool/service, as specified ' \
      'in the BCP47 guidelines (https://tools.ietf.org/html/bcp47); the ' \
      'guidelines includes (a) language subtag according to ISO 639-1 an' \
      'd for languages not covered by this, the ISO 639-3; (b) the scrip' \
      't tag according to ISO 15924; (c) the region tag according to ISO' \
      ' 3166-1; (d) the variant subtag',
      max_length=100,
      choices=languagename_optgroup_choices(),
    )

    languageScript = XmlCharField(
      verbose_name='Language script',
      help_text='Specifies the writing system used to represent the lang' \
      'uage in form of a four letter code as it is defined in ISO-15924',
      blank=True, max_length=100,
      choices = _make_choices_from_list(sorted(iana.get_all_scripts()))['choices'])

    region = XmlCharField(
      verbose_name='Region',
      help_text='Name of the region where the language of the resource i' \
      's spoken (e.g. for English as spoken in the US or the UK etc.)',
      blank=True, max_length=100,
      choices =_make_choices_from_list(sorted(iana.get_all_regions()))['choices'])

    variant = MultiTextField(max_length=500, widget=MultiChoiceWidget(widget_id=65, choices = _make_choices_from_list(sorted(iana.get_all_variants()))['choices']),
      verbose_name='Variants',
      help_text='Name of the variant of the language of the resource is ' \
      'spoken (according to IETF BCP47)',
      blank=True)

    sizePerLanguage = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per language',
      help_text='Provides information on the size per language component' \
      '',
      blank=True, null=True, on_delete=models.SET_NULL, )

    languageVarietyInfo = models.ManyToManyField("languageVarietyInfoType_model",
      verbose_name='Language variety',
      help_text='Groups information on language varieties occurred in th' \
      'e resource (e.g. dialects)',
      blank=True, null=True, related_name="languageVarietyInfo_%(class)s_related", )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    back_to_languagedescriptiontextinfotype_model = models.ForeignKey("languageDescriptionTextInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionvideoinfotype_model = models.ForeignKey("languageDescriptionVideoInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionimageinfotype_model = models.ForeignKey("languageDescriptionImageInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceaudioinfotype_model = models.ForeignKey("lexicalConceptualResourceAudioInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcetextinfotype_model = models.ForeignKey("lexicalConceptualResourceTextInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcevideoinfotype_model = models.ForeignKey("lexicalConceptualResourceVideoInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceimageinfotype_model = models.ForeignKey("lexicalConceptualResourceImageInfoType_model",  blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.languageName:
            if not self.languageScript:
                self.languageScript = \
                    iana.get_suppressed_script_description(self.languageName)
            self.languageId = \
                iana.make_id(self.languageName, self.languageScript, self.region, self.variant)

    #     # # Call save() method from super class with all arguments.
        super(languageInfoType_model, self).save(*args, **kwargs)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['languageName', 'languageId', 'languageVarietyInfo', ]
        formatstring = u'{} ({}) {}'
        return self.unicode_(formatstring, formatargs)

PROJECTINFOTYPE_FUNDINGTYPE_CHOICES = _make_choices_from_list([
  u'other', u'ownFunds', u'nationalFunds', u'euFunds',
])

# pylint: disable-msg=C0103
class projectInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Project"


    __schema_name__ = 'projectInfoType'
    __schema_fields__ = (
      ( u'projectName', u'projectName', REQUIRED ),
      ( u'projectShortName', u'projectShortName', OPTIONAL ),
      ( u'projectID', u'projectID', OPTIONAL ),
      ( u'url', u'url', OPTIONAL ),
      ( u'fundingType', u'fundingType', REQUIRED ),
      ( u'funder', u'funder', RECOMMENDED ),
      ( u'fundingCountry', u'fundingCountry', RECOMMENDED ),
      ( u'projectStartDate', u'projectStartDate', OPTIONAL ),
      ( u'projectEndDate', u'projectEndDate', OPTIONAL ),
    )

    projectName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Project name',
      max_val_length=500,
      help_text='The full name of a project related to the resource',
      )

    projectShortName = DictField(validators=[validate_lang_code_keys, validate_dict_values],
      default_retriever=best_lang_value_retriever,
      verbose_name='Project short name',
      max_val_length=500,
      help_text='A short name or abbreviation of a project related to th' \
      'e resource',
      blank=True)

    projectID = XmlCharField(
      verbose_name='Project identifier',
      help_text='An unambiguous referent to a project related to the res' \
      'ource',
      blank=True, max_length=100, )

    url = MultiTextField(max_length=150, widget=MultiFieldWidget(widget_id=20, max_length=150),
      verbose_name='URL (Landing page)', validators=[HTTPURI_VALIDATOR],
      help_text='A URL used as homepage of an entity (e.g. of a person, ' \
      'organization, resource etc.); it provides general information (fo' \
      'r instance in the case of a resource, it may present a descriptio' \
      'n of the resource, its creators and possibly include links to the' \
      ' URL where it can be accessed from)',
      blank=True, )

    fundingType = MultiSelectField(
      verbose_name='Funding type',
      help_text='Specifies the type of funding of the project',

      max_length=1 + len(PROJECTINFOTYPE_FUNDINGTYPE_CHOICES['choices']) / 4,
      choices=PROJECTINFOTYPE_FUNDINGTYPE_CHOICES['choices'],
      )

    funder = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=21, max_length=100),
      verbose_name='Funder',
      help_text='The full name of the funder of the project',
      blank=True, validators=[validate_matches_xml_char_production], )

    fundingCountry =  MultiTextField(max_length=100, widget=MultiChoiceWidget(widget_id=22,\
      choices = _make_choices_from_list(sorted(iana.get_all_regions()))['choices']),
      verbose_name='Funding country',
      help_text='The name of the funding country, in case of national fu' \
      'nding as mentioned in ISO3166',
      blank=True, validators=[validate_matches_xml_char_production], )


    fundingCountryId = XmlCharField(
      verbose_name='Funding country identifier',
      help_text='The identifier of the funding country, '\
                'in case of national funding as mentioned in '\
                'ISO3166',
      max_length=100, editable=False,)

    projectStartDate = models.DateField(
      verbose_name='Project start date',
      help_text='The starting date of a project related to the resource',
      blank=True, null=True, )

    projectEndDate = models.DateField(
      verbose_name='Project end date',
      help_text='The end date of a project related to the resources',
      blank=True, null=True, )


    source_url = models.URLField(verify_exists=False,
      default=DJANGO_URL,
      help_text="(Read-only) base URL for the server where the master copy of " \
      "the associated entity instance is located.")

    copy_status = models.CharField(default=MASTER, max_length=1, choices=COPY_CHOICES,
        help_text="Generalized copy status flag for this entity instance.")


    def save(self, *args, **kwargs):
        if self.fundingCountry:
            self.fundingCountryId = iana.get_region_subtag(self.fundingCountry)
        # # Call save() method from super class with all arguments.
        super(projectInfoType_model, self).save(*args, **kwargs)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['projectName', 'projectShortName', ]
        formatstring = u'{} ({})'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class usageInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Usage"


    __schema_name__ = 'usageInfoType'
    __schema_fields__ = (
      ( u'accessTool', u'accessTool', OPTIONAL ),
      ( u'resourceAssociatedWith', u'resourceAssociatedWith', OPTIONAL ),
      ( u'foreseenUseInfo', u'foreseenuseinfotype_model_set', RECOMMENDED ),
      ( u'actualUseInfo', u'actualuseinfotype_model_set', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'accessTool': "targetResourceInfoType_model",
      u'actualUseInfo': "actualUseInfoType_model",
      u'foreseenUseInfo': "foreseenUseInfoType_model",
      u'resourceAssociatedWith': "targetResourceInfoType_model",
    }

    accessTool = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Access tool',
      help_text='The name or the identifier or the url of the tool used ' \
      'to access a resource (e.g. a corpus workbench)',
      blank=True, null=True, related_name="accessTool_%(class)s_related", )

    resourceAssociatedWith = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Resource associated with',
      help_text='Refers to another resource that the resource described ' \
      'uses for its operation',
      blank=True, null=True, related_name="resourceAssociatedWith_%(class)s_related", )

    # OneToMany field: foreseenUseInfo

    # OneToMany field: actualUseInfo

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['foreseenUseInfo', 'actualUseInfo', ]
        formatstring = u'foreseen uses: {} / actual uses: {}'
        return self.unicode_(formatstring, formatargs)

FORESEENUSEINFOTYPE_FORESEENUSE_CHOICES = _make_choices_from_list([
  u'humanUse', u'nlpApplications',
])

FORESEENUSEINFOTYPE_USENLPSPECIFIC_CHOICES = _make_choices_from_list([
  u'alignment', u'annotation', u'avatarSynthesis',
  u'bilingualLexiconInduction',u'contradictionDetection',
  u'coreferenceResolution',u'dependencyParsing',
  u'derivationalMorphologicalAnalysis',u'discourseAnalysis',
  u'documentClassification',u'emotionGeneration', u'emotionRecognition',
  u'entityMentionRecognition',u'eventExtraction', u'expressionRecognition',
  u'faceRecognition',u'faceVerification', u'humanoidAgentSynthesis',
  u'informationExtraction',u'informationRetrieval',
  u'intra-documentCoreferenceResolution',u'knowledgeDiscovery',
  u'knowledgeRepresentation',u'languageIdentification',
  u'languageModelling',u'languageModelsTraining', u'lemmatization',
  u'lexiconAccess',u'lexiconAcquisitionFromCorpora', u'lexiconEnhancement',
  u'lexiconExtractionFromLexica',u'lexiconFormatConversion',
  u'lexiconVisualization',u'linguisticResearch', u'lipTrackingAnalysis',
  u'machineTranslation',u'morphologicalAnalysis',
  u'morphosyntacticAnnotation-bPosTagging',
  u'morphosyntacticAnnotation-posTagging',u'multimediaDevelopment',
  u'multimediaDocumentProcessing',u'namedEntityRecognition',
  u'naturalLanguageGeneration',u'naturalLanguageUnderstanding',
  u'opinionMining',u'other', u'personIdentification', u'personRecognition',
  u'persuasiveExpressionMining',u'phraseAlignment', u'qualitativeAnalysis',
  u'questionAnswering', u'readingAndWritingAidApplications',u'semanticRoleLabelling',
  u'semanticWeb',u'sentenceAlignment', u'sentenceSplitting',
  u'sentimentAnalysis',u'shallowParsing', u'signLanguageGeneration',
  u'signLanguageRecognition',u'speakerIdentification',
  u'speakerVerification',u'speechAnalysis', u'speechAssistedVideoControl',
  u'speechLipsCorrelationAnalysis',u'speechRecognition', u'speechSynthesis',
  u'speechToSpeechTranslation',u'speechUnderstanding',
  u'speechVerification',u'spellChecking', u'spokenDialogueSystems',
  u'summarization',u'talkingHeadSynthesis',
  u'temporalExpressionRecognition',u'terminologyExtraction',
  u'textCategorisation',u'textGeneration', u'textMining',
  u'textToSpeechSynthesis',u'textualEntailment', u'tokenization',
  u'tokenizationAndSentenceSplitting',u'topicDetection_Tracking',
  u'userAuthentication',u'visualSceneUnderstanding', u'voiceControl',
  u'wordAlignment',u'wordSenseDisambiguation',
])

# pylint: disable-msg=C0103
class foreseenUseInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Foreseen use"


    __schema_name__ = 'foreseenUseInfoType'
    __schema_fields__ = (
      ( u'foreseenUse', u'foreseenUse', REQUIRED ),
      ( u'useNLPSpecific', u'useNLPSpecific', RECOMMENDED ),
    )

    foreseenUse = models.CharField(
      verbose_name='Foreseen use',
      help_text='Classification of the intended use of the resource',

      max_length=30,
      choices=sorted(FORESEENUSEINFOTYPE_FORESEENUSE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    useNLPSpecific = MultiSelectField(
      verbose_name='Use specific to NLP',
      help_text='Specifies the NLP application for which the resource is' \
      'created or the application in which it has actually been used',
      blank=True,
      max_length=1 + len(FORESEENUSEINFOTYPE_USENLPSPECIFIC_CHOICES['choices']) / 4,
      choices=FORESEENUSEINFOTYPE_USENLPSPECIFIC_CHOICES['choices'],
      )

    back_to_usageinfotype_model = models.ForeignKey("usageInfoType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['foreseenUse', 'useNLPSpecific', ]
        formatstring = u'{}, NLP specific: {}'
        return self.unicode_(formatstring, formatargs)

ACTUALUSEINFOTYPE_ACTUALUSE_CHOICES = _make_choices_from_list([
  u'humanUse', u'nlpApplications',
])

ACTUALUSEINFOTYPE_USENLPSPECIFIC_CHOICES = _make_choices_from_list([
  u'alignment', u'annotation', u'avatarSynthesis',
  u'bilingualLexiconInduction',u'contradictionDetection',
  u'coreferenceResolution',u'dependencyParsing',
  u'derivationalMorphologicalAnalysis',u'discourseAnalysis',
  u'documentClassification',u'emotionGeneration', u'emotionRecognition',
  u'entityMentionRecognition',u'eventExtraction', u'expressionRecognition',
  u'faceRecognition',u'faceVerification', u'humanoidAgentSynthesis',
  u'informationExtraction',u'informationRetrieval',
  u'intra-documentCoreferenceResolution',u'knowledgeDiscovery',
  u'knowledgeRepresentation',u'languageIdentification',
  u'languageModelling',u'languageModelsTraining', u'lemmatization',
  u'lexiconAccess',u'lexiconAcquisitionFromCorpora', u'lexiconEnhancement',
  u'lexiconExtractionFromLexica',u'lexiconFormatConversion',
  u'lexiconVisualization',u'linguisticResearch', u'lipTrackingAnalysis',
  u'machineTranslation',u'morphologicalAnalysis',
  u'morphosyntacticAnnotation-bPosTagging',
  u'morphosyntacticAnnotation-posTagging',u'multimediaDevelopment',
  u'multimediaDocumentProcessing',u'namedEntityRecognition',
  u'naturalLanguageGeneration',u'naturalLanguageUnderstanding',
  u'opinionMining',u'other', u'personIdentification', u'personRecognition',
  u'persuasiveExpressionMining',u'phraseAlignment', u'qualitativeAnalysis',
  u'questionAnswering',u'questionAnswering',
  u'readingAndWritingAidApplications',u'semanticRoleLabelling',
  u'semanticWeb',u'sentenceAlignment', u'sentenceSplitting',
  u'sentimentAnalysis',u'shallowParsing', u'signLanguageGeneration',
  u'signLanguageRecognition',u'speakerIdentification',
  u'speakerVerification',u'speechAnalysis', u'speechAssistedVideoControl',
  u'speechLipsCorrelationAnalysis',u'speechRecognition', u'speechSynthesis',
  u'speechToSpeechTranslation',u'speechUnderstanding',
  u'speechVerification',u'spellChecking', u'spokenDialogueSystems',
  u'summarization',u'talkingHeadSynthesis',
  u'temporalExpressionRecognition',u'terminologyExtraction',
  u'textCategorisation',u'textGeneration', u'textMining',
  u'textToSpeechSynthesis',u'textualEntailment', u'tokenization',
  u'tokenizationAndSentenceSplitting',u'topicDetection_Tracking',
  u'userAuthentication',u'visualSceneUnderstanding', u'voiceControl',
  u'wordAlignment',u'wordSenseDisambiguation',
])

# pylint: disable-msg=C0103
class actualUseInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Actual use"


    __schema_name__ = 'actualUseInfoType'
    __schema_fields__ = (
      ( u'actualUse', u'actualUse', REQUIRED ),
      ( u'useNLPSpecific', u'useNLPSpecific', RECOMMENDED ),
      ( 'usageReport/documentUnstructured', 'usageReport', OPTIONAL ),
      ( 'usageReport/documentInfo', 'usageReport', OPTIONAL ),
      ( u'derivedResource', u'derivedResource', OPTIONAL ),
      ( u'usageProject', u'usageProject', OPTIONAL ),
      ( u'actualUseDetails', u'actualUseDetails', OPTIONAL ),
    )
    __schema_classes__ = {
      u'derivedResource': "targetResourceInfoType_model",
      u'documentInfo': "documentInfoType_model",
      u'documentUnstructured': "documentUnstructuredString_model",
      u'usageProject': "projectInfoType_model",
    }

    actualUse = models.CharField(
      verbose_name='Actual use',
      help_text='Classification of the actual use of the resource',

      max_length=30,
      choices=sorted(ACTUALUSEINFOTYPE_ACTUALUSE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    useNLPSpecific = MultiSelectField(
      verbose_name='Use specific to NLP',
      help_text='Specifies the NLP application for which the resource is' \
      'created or the application in which it has actually been used.',
      blank=True,
      max_length=1 + len(ACTUALUSEINFOTYPE_USENLPSPECIFIC_CHOICES['choices']) / 4,
      choices=ACTUALUSEINFOTYPE_USENLPSPECIFIC_CHOICES['choices'],
      )

    usageReport = models.ManyToManyField("documentationInfoType_model",
      verbose_name='Usage report',
      help_text='Reports on the research papers documenting the usage of' \
      ' a resource, either in a structured form or in free text',
      blank=True, null=True, related_name="usageReport_%(class)s_related", )

    derivedResource = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Derived resource',
      help_text='The name, the identifier or the url of the outcome or p' \
      'roduct of the resource.',
      blank=True, null=True, related_name="derivedResource_%(class)s_related", )

    usageProject = models.ManyToManyField("projectInfoType_model",
      verbose_name='Usage project',
      help_text='Groups information on the project in which the resource' \
      ' has been used',
      blank=True, null=True, related_name="usageProject_%(class)s_related", )

    actualUseDetails = XmlCharField(
      verbose_name='Actual use details',
      help_text='Reports on the usage of the resource in free text',
      blank=True, max_length=250, )

    back_to_usageinfotype_model = models.ForeignKey("usageInfoType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['actualUse', 'useNLPSpecific', ]
        formatstring = u'{}, NLP specific: {}'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class projectListType_model(SchemaModel):

    class Meta:
        verbose_name = "Project list"


    __schema_name__ = 'projectListType'
    __schema_fields__ = (
      ( u'projectInfo', u'projectInfo', REQUIRED ),
    )
    __schema_classes__ = {
      u'projectInfo': "projectInfoType_model",
    }

    projectInfo = models.ManyToManyField("projectInfoType_model",
      verbose_name='Project',
      help_text='Groups information on a project related to the resource' \
      '(e.g. a project the resource has been used in; a funded project t' \
      'hat led to the resource creation etc.)',
      related_name="projectInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class corpusAudioInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Corpus audio"


    __schema_name__ = 'corpusAudioInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageinfotype_model_set', REQUIRED ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'audioSizeInfo', u'audioSizeInfo', REQUIRED ),
      ( u'audioContentInfo', u'audioContentInfo', RECOMMENDED ),
      ( u'settingInfo', u'settingInfo', RECOMMENDED ),
      ( u'audioFormatInfo', u'audioformatinfotype_model_set', RECOMMENDED ),
      ( u'annotationInfo', u'annotationinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', RECOMMENDED ),
      ( u'audioClassificationInfo', u'audioclassificationinfotype_model_set', RECOMMENDED ),
      ( u'recordingInfo', u'recordingInfo', RECOMMENDED ),
      ( u'captureInfo', u'captureInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', OPTIONAL ),
      ( u'linkToOtherMediaInfo', u'linktoothermediainfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'annotationInfo': "annotationInfoType_model",
      u'audioClassificationInfo': "audioClassificationInfoType_model",
      u'audioContentInfo': "audioContentInfoType_model",
      u'audioFormatInfo': "audioFormatInfoType_model",
      u'audioSizeInfo': "audioSizeInfoType_model",
      u'captureInfo': "captureInfoType_model",
      u'creationInfo': "creationInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'linkToOtherMediaInfo': "linkToOtherMediaInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'recordingInfo': "recordingInfoType_model",
      u'settingInfo': "settingInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="audio", editable=False, max_length=1000, )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    # OneToMany field: languageInfo

    # OneToMany field: modalityInfo

    audioSizeInfo = models.ManyToManyField("audioSizeInfoType_model",
      verbose_name='Audio size',
      help_text='SizeInfo Element for Audio parts of a resource',
      related_name="audioSizeInfo_%(class)s_related", )

    audioContentInfo = models.OneToOneField("audioContentInfoType_model",
      verbose_name='Audio content',
      help_text='Groups together information on the contents of the audi' \
      'o part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    settingInfo = models.OneToOneField("settingInfoType_model",
      verbose_name='Setting',
      help_text='Groups together information on the setting of the audio' \
      ' and/or video part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: audioFormatInfo

    # OneToMany field: annotationInfo

    # OneToMany field: domainInfo

    # OneToMany field: timeCoverageInfo

    # OneToMany field: geographicCoverageInfo

    # OneToMany field: audioClassificationInfo

    recordingInfo = models.OneToOneField("recordingInfoType_model",
      verbose_name='Recording',
      help_text='Groups together information on the recording of the aud' \
      'io or video part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    captureInfo = models.OneToOneField("captureInfoType_model",
      verbose_name='Capture',
      help_text='Groups together information on the capture of the audio' \
      ' or video part of a corpus',
      blank=True, null=True, on_delete=models.SET_NULL, )

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: linkToOtherMediaInfo

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['lingualityInfo', 'languageInfo', ]
        formatstring = u'audio ({} {})'
        return self.unicode_(formatstring, formatargs)

AUDIOCONTENTINFOTYPE_SPEECHITEMS_CHOICES = _make_choices_from_list([
  u'isolatedWords', u'isolatedDigits', u'naturalNumbers', u'properNouns',
  u'applicationWords',u'phoneticallyRichSentences',
  u'phoneticallyRichWords',u'phoneticallyBalancedSentences',
  u'moneyAmounts',u'creditCardNumbers', u'telephoneNumbers',
  u'yesNoQuestions',u'vcvSequences', u'freeSpeech', u'other',
])

AUDIOCONTENTINFOTYPE_NONSPEECHITEMS_CHOICES = _make_choices_from_list([
  u'notes', u'tempo', u'sounds', u'noise', u'music', u'commercial',
  u'other',
])

AUDIOCONTENTINFOTYPE_NOISELEVEL_CHOICES = _make_choices_from_list([
  u'low', u'medium', u'high',
])

# pylint: disable-msg=C0103
class audioContentInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Audio content"


    __schema_name__ = 'audioContentInfoType'
    __schema_fields__ = (
      ( u'speechItems', u'speechItems', OPTIONAL ),
      ( u'nonSpeechItems', u'nonSpeechItems', OPTIONAL ),
      ( u'textualDescription', u'textualDescription', OPTIONAL ),
      ( u'noiseLevel', u'noiseLevel', OPTIONAL ),
    )

    speechItems = MultiSelectField(
      verbose_name='Speech items',
      help_text='Specifies the distinct elements that are pronounced and' \
      ' annotated as such',
      blank=True,
      max_length=1 + len(AUDIOCONTENTINFOTYPE_SPEECHITEMS_CHOICES['choices']) / 4,
      choices=AUDIOCONTENTINFOTYPE_SPEECHITEMS_CHOICES['choices'],
      )

    nonSpeechItems = MultiSelectField(
      verbose_name='Non-speech items',
      help_text='Specifies the distinct elements that maybe included in ' \
      'the audio corpus',
      blank=True,
      max_length=1 + len(AUDIOCONTENTINFOTYPE_NONSPEECHITEMS_CHOICES['choices']) / 4,
      choices=AUDIOCONTENTINFOTYPE_NONSPEECHITEMS_CHOICES['choices'],
      )

    textualDescription = XmlCharField(
      verbose_name='Textual description',
      help_text='The legend of the soundtrack',
      blank=True, max_length=500, )

    noiseLevel = models.CharField(
      verbose_name='Noise level',
      help_text='Specifies the level of background noise',
      blank=True,
      max_length=30,
      choices=sorted(AUDIOCONTENTINFOTYPE_NOISELEVEL_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class audioSizeInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Audio size"


    __schema_name__ = 'audioSizeInfoType'
    __schema_fields__ = (
      ( u'sizeInfo', u'sizeinfotype_model_set', REQUIRED ),
      ( u'durationOfEffectiveSpeechInfo', u'durationofeffectivespeechinfotype_model_set', OPTIONAL ),
      ( u'durationOfAudioInfo', u'durationofaudioinfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'durationOfAudioInfo': "durationOfAudioInfoType_model",
      u'durationOfEffectiveSpeechInfo': "durationOfEffectiveSpeechInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
    }

    # OneToMany field: sizeInfo

    # OneToMany field: durationOfEffectiveSpeechInfo

    # OneToMany field: durationOfAudioInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

DURATIONOFEFFECTIVESPEECHINFOTYPE_DURATIONUNIT_CHOICES = _make_choices_from_list([
  u'hours', u'minutes', u'seconds',
])

# pylint: disable-msg=C0103
class durationOfEffectiveSpeechInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Duration of effective speech"


    __schema_name__ = 'durationOfEffectiveSpeechInfoType'
    __schema_fields__ = (
      ( u'size', u'size', REQUIRED ),
      ( u'durationUnit', u'durationUnit', REQUIRED ),
    )

    size = XmlCharField(
      verbose_name='Size',
      help_text='Specifies the size of the resource with regard to the d' \
      'urationUnit measurement in form of a number',
      max_length=1000, )

    durationUnit = models.CharField(
      verbose_name='Duration unit',
      help_text='Specification of the unit of size that is used when pro' \
      'viding information on the size of a resource',

      max_length=30,
      choices=sorted(DURATIONOFEFFECTIVESPEECHINFOTYPE_DURATIONUNIT_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    back_to_audiosizeinfotype_model = models.ForeignKey("audioSizeInfoType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['size', 'durationUnit', ]
        formatstring = u'{} {}'
        return self.unicode_(formatstring, formatargs)

DURATIONOFAUDIOINFOTYPE_DURATIONUNIT_CHOICES = _make_choices_from_list([
  u'hours', u'minutes', u'seconds',
])

# pylint: disable-msg=C0103
class durationOfAudioInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Duration of audio"


    __schema_name__ = 'durationOfAudioInfoType'
    __schema_fields__ = (
      ( u'size', u'size', REQUIRED ),
      ( u'durationUnit', u'durationUnit', REQUIRED ),
    )

    size = XmlCharField(
      verbose_name='Size',
      help_text='Specifies the size of the resource with regard to the d' \
      'urationUnit measurement in form of a number',
      max_length=1000, )

    durationUnit = models.CharField(
      verbose_name='Duration unit',
      help_text='Specification of the unit of duration (e.g. minutes, ho' \
      'urs etc.)',

      max_length=30,
      choices=sorted(DURATIONOFAUDIOINFOTYPE_DURATIONUNIT_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    back_to_audiosizeinfotype_model = models.ForeignKey("audioSizeInfoType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['size', 'durationUnit', ]
        formatstring = u'{} {}'
        return self.unicode_(formatstring, formatargs)

AUDIOFORMATINFOTYPE_MIMETYPE_CHOICES = _make_choices_from_list([
  u'text/plain', u'application/vnd.xmi+xml', u'application/xml',
  u'application/x-tmx+xml',u'application/x-xces+xml',
  u'application/tei+xml',u'application/rdf+xml', u'application/xhtml+xml',
  u'application/emma+xml',u'application/pls+xml',
  u'application/voicexml+xml',u'text/sgml', u'text/html',
  u'application/x-tex',u'application/rtf', u'application/x-latex',
  u'text/csv',u'text/tab-separated-values', u'application/pdf',
  u'application/x-msaccess',u'audio/mp4', u'audio/mpeg', u'audio/x-wav',
  u'image/bmp',u'image/gif', u'image/jpeg', u'image/png', u'image/svg+xml',
  u'image/tiff',u'video/jpeg', u'video/mp4', u'video/mpeg', u'video/x-flv',
  u'video/x-msvideo',u'video/x-ms-wmv', u'application/msword',
  u'application/vnd.ms-excel',u'audio/mpeg3', u'text/turtle', u'other',
])

AUDIOFORMATINFOTYPE_SIGNALENCODING_CHOICES = _make_choices_from_list([
  u'aLaw', u'linearPCM', u'\u03bc-law', u'ADPCM', u'other',
])

AUDIOFORMATINFOTYPE_QUANTIZATION_CHOICES = _make_choices_from_int_list([
8, 16, 24, 32, 64,
])

AUDIOFORMATINFOTYPE_BYTEORDER_CHOICES = _make_choices_from_list([
  u'littleEndian', u'bigEndian',
])

AUDIOFORMATINFOTYPE_SIGNCONVENTION_CHOICES = _make_choices_from_list([
  u'signedInteger', u'unsignedInteger', u'floatingPoint',
])

AUDIOFORMATINFOTYPE_AUDIOQUALITYMEASURESINCLUDED_CHOICES = _make_choices_from_list([
  u'SNR', u'crossTalk', u'clippingRate', u'backgroundNoise', u'other',
])

AUDIOFORMATINFOTYPE_NUMBEROFTRACKS_CHOICES = _make_choices_from_int_list([
1, 2, 4, 8,
])

AUDIOFORMATINFOTYPE_RECORDINGQUALITY_CHOICES = _make_choices_from_list([
  u'veryLow', u'low', u'medium', u'high', u'veryHigh',
])

# pylint: disable-msg=C0103
class audioFormatInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Audio format"


    __schema_name__ = 'audioFormatInfoType'
    __schema_fields__ = (
      ( u'mimeType', u'mimeType', REQUIRED ),
      ( u'signalEncoding', u'signalEncoding', RECOMMENDED ),
      ( u'samplingRate', u'samplingRate', RECOMMENDED ),
      ( u'quantization', u'quantization', OPTIONAL ),
      ( u'byteOrder', u'byteOrder', OPTIONAL ),
      ( u'signConvention', u'signConvention', OPTIONAL ),
      ( u'compressionInfo', u'compressionInfo', OPTIONAL ),
      ( u'audioQualityMeasuresIncluded', u'audioQualityMeasuresIncluded', OPTIONAL ),
      ( u'numberOfTracks', u'numberOfTracks', OPTIONAL ),
      ( u'recordingQuality', u'recordingQuality', OPTIONAL ),
      ( u'sizePerAudioFormat', u'sizePerAudioFormat', OPTIONAL ),
    )
    __schema_classes__ = {
      u'compressionInfo': "compressionInfoType_model",
      u'sizePerAudioFormat': "sizeInfoType_model",
    }

    mimeType = models.CharField(
      verbose_name='Mime type',
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts, in conformance with the values of the IANA (Internet ' \
      'Assigned Numbers Authority); you can select one of the pre-define' \
      'd values or add a value, PREFERABLY FROM THE IANA MEDIA MIMETYPE ' \
      'RECOMMENDED VALUES (http://www.iana.org/assignments/media-types/m' \
      'edia-types.xhtml)',

      max_length=50,
      choices=sorted(AUDIOFORMATINFOTYPE_MIMETYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    signalEncoding = MultiSelectField(
      verbose_name='Signal encoding',
      help_text='Specifies the encoding the audio type uses',
      blank=True,
      max_length=1 + len(AUDIOFORMATINFOTYPE_SIGNALENCODING_CHOICES['choices']) / 4,
      choices=AUDIOFORMATINFOTYPE_SIGNALENCODING_CHOICES['choices'],
      )

    samplingRate = models.BigIntegerField(
      verbose_name='Sampling rate',
      help_text='Specifies the format of files contained in the resource' \
      ' in Hertz',
      blank=True, null=True, )

    quantization = models.IntegerField(
      verbose_name='Quantization',
      help_text='The number of bits for each audio sample',

      max_length=AUDIOFORMATINFOTYPE_QUANTIZATION_CHOICES['max_length'],
      choices=AUDIOFORMATINFOTYPE_QUANTIZATION_CHOICES['choices'],
      blank=True, null=True, )

    byteOrder = models.CharField(
      verbose_name='Byte order',
      help_text='The byte order of 2 or more bytes sample',
      blank=True,
      max_length=30,
      choices=sorted(AUDIOFORMATINFOTYPE_BYTEORDER_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    signConvention = models.CharField(
      verbose_name='Sign convention',
      help_text='Binary representation of numbers',
      blank=True,
      max_length=30,
      choices=sorted(AUDIOFORMATINFOTYPE_SIGNCONVENTION_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    compressionInfo = models.OneToOneField("compressionInfoType_model",
      verbose_name='Compression',
      help_text='Groups together information on the compression status a' \
      'nd method of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    audioQualityMeasuresIncluded = models.CharField(
      verbose_name='Audio quality measures included',
      help_text='Specifies the audio quality measures',
      blank=True,
      max_length=30,
      choices=sorted(AUDIOFORMATINFOTYPE_AUDIOQUALITYMEASURESINCLUDED_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    numberOfTracks = models.IntegerField(
      verbose_name='Number of tracks',
      help_text='Specifies the number of audio channels',

      max_length=AUDIOFORMATINFOTYPE_NUMBEROFTRACKS_CHOICES['max_length'],
      choices=AUDIOFORMATINFOTYPE_NUMBEROFTRACKS_CHOICES['choices'],
      blank=True, null=True, )

    recordingQuality = models.CharField(
      verbose_name='Recording quality',
      help_text='Indication of the audio or video recording quality',
      blank=True,
      max_length=30,
      choices=sorted(AUDIOFORMATINFOTYPE_RECORDINGQUALITY_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerAudioFormat = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per audio format',
      help_text='Used to give info on size of parts of a resource that d' \
      'iffer as to the format',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceaudioinfotype_model = models.ForeignKey("lexicalConceptualResourceAudioInfoType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['mimeType', 'signalEncoding', ]
        formatstring = u'{} {}'
        return self.unicode_(formatstring, formatargs)

AUDIOCLASSIFICATIONINFOTYPE_AUDIOGENRE_CHOICES = _make_choices_from_list([
  u'speech', u'humanNonSpeech', u'noise', u'animalVocalizations', u'song',
  u'instrumentalMusic',u'other',
])

AUDIOCLASSIFICATIONINFOTYPE_SPEECHGENRE_CHOICES = _make_choices_from_list([
  u'broadcastNews', u'meeting', u'lecture', u'emotionalExpressive',
  u'airTrafficControl',u'conversation', u'roundtable', u'interview',
  u'debate',u'call-in', u'questionAnswer', u'presentation', u'narrative',
  u'other',
])

AUDIOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'DK-5', u'EUROVOC',
  u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other',
])

# pylint: disable-msg=C0103
class audioClassificationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Audio classification"


    __schema_name__ = 'audioClassificationInfoType'
    __schema_fields__ = (
      ( u'audioGenre', u'audioGenre', REQUIRED ),
      ( u'speechGenre', u'speechGenre', RECOMMENDED ),
      ( u'subject_topic', u'subject_topic', OPTIONAL ),
      ( u'register', u'register', OPTIONAL ),
      ( u'conformanceToClassificationScheme', u'conformanceToClassificationScheme', OPTIONAL ),
      ( u'sizePerAudioClassification', u'sizePerAudioClassification', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerAudioClassification': "sizeInfoType_model",
    }

    audioGenre = models.CharField(
      verbose_name='Audio genre',
      help_text='A first indication of type of sounds recorded',

      max_length=30,
      choices=sorted(AUDIOCLASSIFICATIONINFOTYPE_AUDIOGENRE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    speechGenre = models.CharField(
      verbose_name='Speech genre',
      help_text='The conventionalized discourse of the content of the re' \
      'source, based on extra-linguistic and internal linguistic criteri' \
      'a; the values here are intended only for speech',
      blank=True,
      max_length=30,
      choices=sorted(AUDIOCLASSIFICATIONINFOTYPE_SPEECHGENRE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    subject_topic = XmlCharField(
      verbose_name='Subject / Topic',
      help_text='For corpora that have already been using subject classi' \
      'fication',
      blank=True, max_length=500, )

    register = XmlCharField(
      verbose_name='Register',
      help_text='For corpora that have already been using register class' \
      'ification',
      blank=True, max_length=1000, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme',
      help_text='Specifies the external classification schemes',
      blank=True,
      max_length=100,
      choices=sorted(AUDIOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerAudioClassification = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per audio classification',
      help_text='The size of the audio subparts of the resource in terms' \
      ' of classification criteria',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class corpusTextInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Corpus text"


    __schema_name__ = 'corpusTextInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageinfotype_model_set', REQUIRED ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', REQUIRED ),
      ( u'textFormatInfo', u'textformatinfotype_model_set', RECOMMENDED ),
      ( u'characterEncodingInfo', u'characterencodinginfotype_model_set', RECOMMENDED ),
      ( u'annotationInfo', u'annotationinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', RECOMMENDED ),
      ( u'textClassificationInfo', u'textclassificationinfotype_model_set', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linktoothermediainfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'annotationInfo': "annotationInfoType_model",
      u'characterEncodingInfo': "characterEncodingInfoType_model",
      u'creationInfo': "creationInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'linkToOtherMediaInfo': "linkToOtherMediaInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'textClassificationInfo': "textClassificationInfoType_model",
      u'textFormatInfo': "textFormatInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="text", editable=False, max_length=1000, )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    # OneToMany field: languageInfo

    # OneToMany field: modalityInfo

    # OneToMany field: sizeInfo

    # OneToMany field: textFormatInfo

    # OneToMany field: characterEncodingInfo

    # OneToMany field: annotationInfo

    # OneToMany field: domainInfo

    # OneToMany field: textClassificationInfo

    # OneToMany field: timeCoverageInfo

    # OneToMany field: geographicCoverageInfo

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: linkToOtherMediaInfo

    back_to_corpusmediatypetype_model = models.ForeignKey("corpusMediaTypeType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['lingualityInfo', 'languageInfo', ]
        formatstring = u'text ({} {})'
        return self.unicode_(formatstring, formatargs)

TEXTFORMATINFOTYPE_MIMETYPE_CHOICES = _make_choices_from_list([
  u'text/plain', u'application/vnd.xmi+xml', u'application/xml',
  u'application/x-tmx+xml',u'application/x-xces+xml',
  u'application/tei+xml',u'application/rdf+xml', u'application/xhtml+xml',
  u'application/emma+xml',u'application/pls+xml',
  u'application/voicexml+xml',u'text/sgml', u'text/html',
  u'application/x-tex',u'application/rtf', u'application/x-latex',
  u'text/csv',u'text/tab-separated-values', u'application/pdf',
  u'application/x-msaccess',u'audio/mp4', u'audio/mpeg', u'audio/x-wav',
  u'image/bmp',u'image/gif', u'image/jpeg', u'image/png', u'image/svg+xml',
  u'image/tiff',u'video/jpeg', u'video/mp4', u'video/mpeg', u'video/x-flv',
  u'video/x-msvideo',u'video/x-ms-wmv', u'application/msword',
  u'application/vnd.ms-excel',u'audio/mpeg3', u'text/turtle', u'other',
])

# pylint: disable-msg=C0103
class textFormatInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Text format"


    __schema_name__ = 'textFormatInfoType'
    __schema_fields__ = (
      ( u'mimeType', u'mimeType', REQUIRED ),
      ( u'sizePerTextFormat', u'sizePerTextFormat', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerTextFormat': "sizeInfoType_model",
    }

    mimeType = models.CharField(
      verbose_name='Mime type',
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts, in conformance with the values of the IANA (Internet ' \
      'Assigned Numbers Authority); you can select one of the pre-define' \
      'd values or add a value, PREFERABLY FROM THE IANA MEDIA MIMETYPE ' \
      'RECOMMENDED VALUES (http://www.iana.org/assignments/media-types/m' \
      'edia-types.xhtml)',

      max_length=50,
      choices=sorted(TEXTFORMATINFOTYPE_MIMETYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerTextFormat = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per text format',
      help_text='Provides information on the size of the resource parts ' \
      'with different format',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    back_to_languagedescriptiontextinfotype_model = models.ForeignKey("languageDescriptionTextInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcetextinfotype_model = models.ForeignKey("lexicalConceptualResourceTextInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

TEXTCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'DK-5', u'EUROVOC',
  u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other',
])

# pylint: disable-msg=C0103
class textClassificationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Text classification"


    __schema_name__ = 'textClassificationInfoType'
    __schema_fields__ = (
      ( u'textGenre', u'textGenre', OPTIONAL ),
      ( u'textType', u'textType', OPTIONAL ),
      ( u'register', u'register', OPTIONAL ),
      ( u'subject_topic', u'subject_topic', OPTIONAL ),
      ( u'conformanceToClassificationScheme', u'conformanceToClassificationScheme', OPTIONAL ),
      ( u'sizePerTextClassification', u'sizePerTextClassification', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerTextClassification': "sizeInfoType_model",
    }

    textGenre = XmlCharField(
      verbose_name='Text genre',
      help_text='Genre: The conventionalized discourse or text types of ' \
      'the content of the resource, based on extra-linguistic and intern' \
      'al linguistic criteria',
      blank=True, max_length=50, )

    textType = XmlCharField(
      verbose_name='Text type',
      help_text='Specifies the type of the text according to a text type' \
      ' classification',
      blank=True, max_length=50, )

    register = XmlCharField(
      verbose_name='Register',
      help_text='For corpora that have already been using register class' \
      'ification',
      blank=True, max_length=1000, )

    subject_topic = XmlCharField(
      verbose_name='Subject / Topic',
      help_text='For corpora that have already been using subject classi' \
      'fication',
      blank=True, max_length=500, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme',
      help_text='Specifies the external classification schemes',
      blank=True,
      max_length=100,
      choices=sorted(TEXTCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerTextClassification = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per text classification',
      help_text='Provides information on size of resource parts with dif' \
      'ferent text classification',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpustextinfotype_model = models.ForeignKey("corpusTextInfoType_model",  blank=True, null=True)

    back_to_corpustextngraminfotype_model = models.ForeignKey("corpusTextNgramInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class corpusVideoInfoType_model(SchemaModel):
    """
    Groups together information on the video component of a corpus
    """

    class Meta:
        verbose_name = "Corpus video"


    __schema_name__ = 'corpusVideoInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageinfotype_model_set', OPTIONAL ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', REQUIRED ),
      ( u'videoContentInfo', u'videoContentInfo', RECOMMENDED ),
      ( u'settingInfo', u'settingInfo', RECOMMENDED ),
      ( u'videoFormatInfo', u'videoformatinfotype_model_set', RECOMMENDED ),
      ( u'annotationInfo', u'annotationinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', RECOMMENDED ),
      ( u'videoClassificationInfo', u'videoclassificationinfotype_model_set', RECOMMENDED ),
      ( u'recordingInfo', u'recordingInfo', RECOMMENDED ),
      ( u'captureInfo', u'captureInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linktoothermediainfotype_model_set', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'annotationInfo': "annotationInfoType_model",
      u'captureInfo': "captureInfoType_model",
      u'creationInfo': "creationInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'linkToOtherMediaInfo': "linkToOtherMediaInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'recordingInfo': "recordingInfoType_model",
      u'settingInfo': "settingInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
      u'videoClassificationInfo': "videoClassificationInfoType_model",
      u'videoContentInfo': "videoContentInfoType_model",
      u'videoFormatInfo': "videoFormatInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="video", editable=False, max_length=1000, )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: languageInfo

    # OneToMany field: modalityInfo

    # OneToMany field: sizeInfo

    videoContentInfo = models.OneToOneField("videoContentInfoType_model",
      verbose_name='Video content',
      help_text='Groups together information on the contents of the vide' \
      'o part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    settingInfo = models.OneToOneField("settingInfoType_model",
      verbose_name='Setting',
      help_text='Groups together information on the setting of the audio' \
      ' and/or video part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: videoFormatInfo

    # OneToMany field: annotationInfo

    # OneToMany field: domainInfo

    # OneToMany field: timeCoverageInfo

    # OneToMany field: geographicCoverageInfo

    # OneToMany field: videoClassificationInfo

    recordingInfo = models.OneToOneField("recordingInfoType_model",
      verbose_name='Recording',
      help_text='Groups together information on the recording of the aud' \
      'io or video part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    captureInfo = models.OneToOneField("captureInfoType_model",
      verbose_name='Capture',
      help_text='Groups together information on the capture of the audio' \
      ' or video part of a corpus',
      blank=True, null=True, on_delete=models.SET_NULL, )

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: linkToOtherMediaInfo

    back_to_corpusmediatypetype_model = models.ForeignKey("corpusMediaTypeType_model",  blank=True, null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['lingualityInfo', 'languageInfo', ]
        formatstring = u'video ({} {})'
        return self.unicode_(formatstring, formatargs)

VIDEOCONTENTINFOTYPE_TEXTINCLUDEDINVIDEO_CHOICES = _make_choices_from_list([
  u'captions', u'subtitles', u'none',
])

# pylint: disable-msg=C0103
class videoContentInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Video content"


    __schema_name__ = 'videoContentInfoType'
    __schema_fields__ = (
      ( u'typeOfVideoContent', u'typeOfVideoContent', REQUIRED ),
      ( u'textIncludedInVideo', u'textIncludedInVideo', OPTIONAL ),
      ( u'dynamicElementInfo', u'dynamicElementInfo', OPTIONAL ),
    )
    __schema_classes__ = {
      u'dynamicElementInfo': "dynamicElementInfoType_model",
    }

    typeOfVideoContent = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=23, max_length=1000),
      verbose_name='Type of content',
      help_text='Main type of object or people represented in the video',
      validators=[validate_matches_xml_char_production], )

    textIncludedInVideo = MultiSelectField(
      verbose_name='Text included in video',
      help_text='Indicates if text is present in or in conjunction with ' \
      'the video',
      blank=True,
      max_length=1 + len(VIDEOCONTENTINFOTYPE_TEXTINCLUDEDINVIDEO_CHOICES['choices']) / 4,
      choices=VIDEOCONTENTINFOTYPE_TEXTINCLUDEDINVIDEO_CHOICES['choices'],
      )

    dynamicElementInfo = models.OneToOneField("dynamicElementInfoType_model",
      verbose_name='Dynamic element',
      help_text='Groups information on the dynamic elements that are rep' \
      'resented in the video part of the resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

VIDEOFORMATINFOTYPE_MIMETYPE_CHOICES = _make_choices_from_list([
  u'text/plain', u'application/vnd.xmi+xml', u'application/xml',
  u'application/x-tmx+xml',u'application/x-xces+xml',
  u'application/tei+xml',u'application/rdf+xml', u'application/xhtml+xml',
  u'application/emma+xml',u'application/pls+xml',
  u'application/voicexml+xml',u'text/sgml', u'text/html',
  u'application/x-tex',u'application/rtf', u'application/x-latex',
  u'text/csv',u'text/tab-separated-values', u'application/pdf',
  u'application/x-msaccess',u'audio/mp4', u'audio/mpeg', u'audio/x-wav',
  u'image/bmp',u'image/gif', u'image/jpeg', u'image/png', u'image/svg+xml',
  u'image/tiff',u'video/jpeg', u'video/mp4', u'video/mpeg', u'video/x-flv',
  u'video/x-msvideo',u'video/x-ms-wmv', u'application/msword',
  u'application/vnd.ms-excel',u'audio/mpeg3', u'text/turtle', u'other',
])

VIDEOFORMATINFOTYPE_COLOURSPACE_CHOICES = _make_choices_from_list([
  u'RGB', u'CMYK', u'4:2:2', u'YUV',
])

VIDEOFORMATINFOTYPE_VISUALMODELLING_CHOICES = _make_choices_from_list([
  u'2D', u'3D',
])

# pylint: disable-msg=C0103
class videoFormatInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Video format"


    __schema_name__ = 'videoFormatInfoType'
    __schema_fields__ = (
      ( u'mimeType', u'mimeType', REQUIRED ),
      ( u'colourSpace', u'colourSpace', RECOMMENDED ),
      ( u'colourDepth', u'colourDepth', OPTIONAL ),
      ( u'frameRate', u'frameRate', OPTIONAL ),
      ( u'resolutionInfo', u'resolutionInfo', RECOMMENDED ),
      ( u'visualModelling', u'visualModelling', OPTIONAL ),
      ( u'fidelity', u'fidelity', OPTIONAL ),
      ( u'compressionInfo', u'compressionInfo', OPTIONAL ),
      ( u'sizePerVideoFormat', u'sizePerVideoFormat', OPTIONAL ),
    )
    __schema_classes__ = {
      u'compressionInfo': "compressionInfoType_model",
      u'resolutionInfo': "resolutionInfoType_model",
      u'sizePerVideoFormat': "sizeInfoType_model",
    }

    mimeType = models.CharField(
      verbose_name='Mime type',
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts, in conformance with the values of the IANA (Internet ' \
      'Assigned Numbers Authority); you can select one of the pre-define' \
      'd values or add a value, PREFERABLY FROM THE IANA MEDIA MIMETYPE ' \
      'RECOMMENDED VALUES (http://www.iana.org/assignments/media-types/m' \
      'edia-types.xhtml)',

      max_length=50,
      choices=sorted(VIDEOFORMATINFOTYPE_MIMETYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    colourSpace = MultiSelectField(
      verbose_name='Colour space',
      help_text='Defines the colour space for the image and video',
      blank=True,
      max_length=1 + len(VIDEOFORMATINFOTYPE_COLOURSPACE_CHOICES['choices']) / 4,
      choices=VIDEOFORMATINFOTYPE_COLOURSPACE_CHOICES['choices'],
      )

    colourDepth = models.IntegerField(
      verbose_name='Colour depth',
      help_text='The number of bits used to represent the colour of a si' \
      'ngle pixel',
      blank=True, null=True, )

    frameRate = models.IntegerField(
      verbose_name='Frame rate',
      help_text='The number of frames per second',
      blank=True, null=True, )

    resolutionInfo = models.ManyToManyField("resolutionInfoType_model",
      verbose_name='Resolution',
      help_text='Groups together information on the image resolution',
      blank=True, null=True, related_name="resolutionInfo_%(class)s_related", )

    visualModelling = models.CharField(
      verbose_name='Visual modelling',
      help_text='The dimensional form applied on video or image corpus',
      blank=True,
      max_length=30,
      choices=sorted(VIDEOFORMATINFOTYPE_VISUALMODELLING_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    fidelity = MetaBooleanField(
      verbose_name='Fidelity',
      help_text='Defines whether blur is present in the moving sequences' \
      '',
      blank=True, )

    compressionInfo = models.OneToOneField("compressionInfoType_model",
      verbose_name='Compression',
      help_text='Groups together information on the compression status a' \
      'nd method of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    sizePerVideoFormat = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per video format',
      help_text='Used to give info on size of parts of a resource that d' \
      'iffer as to the format',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionvideoinfotype_model = models.ForeignKey("languageDescriptionVideoInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourcevideoinfotype_model = models.ForeignKey("lexicalConceptualResourceVideoInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

VIDEOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'DK-5', u'EUROVOC',
  u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other',
])

# pylint: disable-msg=C0103
class videoClassificationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Video classification"


    __schema_name__ = 'videoClassificationInfoType'
    __schema_fields__ = (
      ( u'videoGenre', u'videoGenre', RECOMMENDED ),
      ( u'subject_topic', u'subject_topic', OPTIONAL ),
      ( u'conformanceToClassificationScheme', u'conformanceToClassificationScheme', OPTIONAL ),
      ( u'sizePerVideoClassification', u'sizePerVideoClassification', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerVideoClassification': "sizeInfoType_model",
    }

    videoGenre = XmlCharField(
      verbose_name='Video genre',
      help_text='A first indication of type of video recorded',
      blank=True, max_length=1000, )

    subject_topic = XmlCharField(
      verbose_name='Subject / Topic',
      help_text='For corpora that have already been using subject classi' \
      'fication',
      blank=True, max_length=500, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme',
      help_text='Specifies the external classification schemes',
      blank=True,
      max_length=100,
      choices=sorted(VIDEOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerVideoClassification = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per video classification',
      help_text='Used to give info on size of parts with different video' \
      ' classification',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class corpusImageInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Corpus image"


    __schema_name__ = 'corpusImageInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageinfotype_model_set', OPTIONAL ),
      ( u'sizeInfo', u'sizeinfotype_model_set', REQUIRED ),
      ( u'imageContentInfo', u'imageContentInfo', RECOMMENDED ),
      ( u'imageFormatInfo', u'imageformatinfotype_model_set', RECOMMENDED ),
      ( u'annotationInfo', u'annotationinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', OPTIONAL ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', OPTIONAL ),
      ( u'imageClassificationInfo', u'imageclassificationinfotype_model_set', OPTIONAL ),
      ( u'captureInfo', u'captureInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', OPTIONAL ),
      ( u'linkToOtherMediaInfo', u'linktoothermediainfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'annotationInfo': "annotationInfoType_model",
      u'captureInfo': "captureInfoType_model",
      u'creationInfo': "creationInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'imageClassificationInfo': "imageClassificationInfoType_model",
      u'imageContentInfo': "imageContentInfoType_model",
      u'imageFormatInfo': "imageFormatInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'linkToOtherMediaInfo': "linkToOtherMediaInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="image", editable=False, max_length=1000, )

    # OneToMany field: modalityInfo

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: languageInfo

    # OneToMany field: sizeInfo

    imageContentInfo = models.OneToOneField("imageContentInfoType_model",
      verbose_name='Image content',
      help_text='Groups together information on the contents of the imag' \
      'e part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: imageFormatInfo

    # OneToMany field: annotationInfo

    # OneToMany field: domainInfo

    # OneToMany field: timeCoverageInfo

    # OneToMany field: geographicCoverageInfo

    # OneToMany field: imageClassificationInfo

    captureInfo = models.OneToOneField("captureInfoType_model",
      verbose_name='Capture',
      help_text='Groups together information on the capture of the audio' \
      ' or video part of a corpus',
      blank=True, null=True, on_delete=models.SET_NULL, )

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: linkToOtherMediaInfo

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['sizeInfo', ]
        formatstring = u'image ({})'
        return self.unicode_(formatstring, formatargs)

IMAGECONTENTINFOTYPE_TEXTINCLUDEDINIMAGE_CHOICES = _make_choices_from_list([
  u'captions', u'subtitles', u'captureTime', u'none',
])

# pylint: disable-msg=C0103
class imageContentInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Image content"


    __schema_name__ = 'imageContentInfoType'
    __schema_fields__ = (
      ( u'typeOfImageContent', u'typeOfImageContent', REQUIRED ),
      ( u'textIncludedInImage', u'textIncludedInImage', OPTIONAL ),
      ( u'staticElementInfo', u'staticElementInfo', OPTIONAL ),
    )
    __schema_classes__ = {
      u'staticElementInfo': "staticElementInfoType_model",
    }

    typeOfImageContent = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=24, max_length=1000),
      verbose_name='Type of image content',
      help_text='The main types of object or people represented in the i' \
      'mage corpus',
      validators=[validate_matches_xml_char_production], )

    textIncludedInImage = MultiSelectField(
      verbose_name='Text included in image',
      help_text='Provides information on the type of text that may be on' \
      ' the image',
      blank=True,
      max_length=1 + len(IMAGECONTENTINFOTYPE_TEXTINCLUDEDINIMAGE_CHOICES['choices']) / 4,
      choices=IMAGECONTENTINFOTYPE_TEXTINCLUDEDINIMAGE_CHOICES['choices'],
      )

    staticElementInfo = models.OneToOneField("staticElementInfoType_model",
      verbose_name='Static element',
      help_text='Groups information on the static element visible on the' \
      ' images',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

IMAGEFORMATINFOTYPE_MIMETYPE_CHOICES = _make_choices_from_list([
  u'text/plain', u'application/vnd.xmi+xml', u'application/xml',
  u'application/x-tmx+xml',u'application/x-xces+xml',
  u'application/tei+xml',u'application/rdf+xml', u'application/xhtml+xml',
  u'application/emma+xml',u'application/pls+xml',
  u'application/voicexml+xml',u'text/sgml', u'text/html',
  u'application/x-tex',u'application/rtf', u'application/x-latex',
  u'text/csv',u'text/tab-separated-values', u'application/pdf',
  u'application/x-msaccess',u'audio/mp4', u'audio/mpeg', u'audio/x-wav',
  u'image/bmp',u'image/gif', u'image/jpeg', u'image/png', u'image/svg+xml',
  u'image/tiff',u'video/jpeg', u'video/mp4', u'video/mpeg', u'video/x-flv',
  u'video/x-msvideo',u'video/x-ms-wmv', u'application/msword',
  u'application/vnd.ms-excel',u'audio/mpeg3', u'text/turtle', u'other',
])

IMAGEFORMATINFOTYPE_COLOURSPACE_CHOICES = _make_choices_from_list([
  u'RGB', u'CMYK', u'4:2:2', u'YUV',
])

IMAGEFORMATINFOTYPE_VISUALMODELLING_CHOICES = _make_choices_from_list([
  u'2D', u'3D',
])

IMAGEFORMATINFOTYPE_RASTERORVECTORGRAPHICS_CHOICES = _make_choices_from_list([
  u'raster', u'vector',
])

IMAGEFORMATINFOTYPE_QUALITY_CHOICES = _make_choices_from_list([
  u'veryLow', u'low', u'medium', u'high', u'veryHigh',
])

# pylint: disable-msg=C0103
class imageFormatInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Image format"


    __schema_name__ = 'imageFormatInfoType'
    __schema_fields__ = (
      ( u'mimeType', u'mimeType', REQUIRED ),
      ( u'colourSpace', u'colourSpace', RECOMMENDED ),
      ( u'colourDepth', u'colourDepth', OPTIONAL ),
      ( u'compressionInfo', u'compressionInfo', OPTIONAL ),
      ( u'resolutionInfo', u'resolutionInfo', OPTIONAL ),
      ( u'visualModelling', u'visualModelling', OPTIONAL ),
      ( u'rasterOrVectorGraphics', u'rasterOrVectorGraphics', OPTIONAL ),
      ( u'quality', u'quality', OPTIONAL ),
      ( u'sizePerImageFormat', u'sizePerImageFormat', OPTIONAL ),
    )
    __schema_classes__ = {
      u'compressionInfo': "compressionInfoType_model",
      u'resolutionInfo': "resolutionInfoType_model",
      u'sizePerImageFormat': "sizeInfoType_model",
    }

    mimeType = models.CharField(
      verbose_name='Mime type',
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts, in conformance with the values of the IANA (Internet ' \
      'Assigned Numbers Authority); you can select one of the pre-define' \
      'd values or add a value, PREFERABLY FROM THE IANA MEDIA MIMETYPE ' \
      'RECOMMENDED VALUES (http://www.iana.org/assignments/media-types/m' \
      'edia-types.xhtml)',

      max_length=50,
      choices=sorted(IMAGEFORMATINFOTYPE_MIMETYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    colourSpace = MultiSelectField(
      verbose_name='Colour space',
      help_text='Defines the colour space for the image and video',
      blank=True,
      max_length=1 + len(IMAGEFORMATINFOTYPE_COLOURSPACE_CHOICES['choices']) / 4,
      choices=IMAGEFORMATINFOTYPE_COLOURSPACE_CHOICES['choices'],
      )

    colourDepth = models.IntegerField(
      verbose_name='Colour depth',
      help_text='The number of bits used to represent the colour of a si' \
      'ngle pixel',
      blank=True, null=True, )

    compressionInfo = models.OneToOneField("compressionInfoType_model",
      verbose_name='Compression',
      help_text='Groups together information on the compression status a' \
      'nd method of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    resolutionInfo = models.ManyToManyField("resolutionInfoType_model",
      verbose_name='Resolution',
      help_text='Groups together information on the image resolution',
      blank=True, null=True, related_name="resolutionInfo_%(class)s_related", )

    visualModelling = models.CharField(
      verbose_name='Visual modelling',
      help_text='The dimensional form applied on video or image corpus',
      blank=True,
      max_length=30,
      choices=sorted(IMAGEFORMATINFOTYPE_VISUALMODELLING_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    rasterOrVectorGraphics = models.CharField(
      verbose_name='Raster or vector graphics',
      help_text='Indicates if the image is stored as raster or vector gr' \
      'aphics',
      blank=True,
      max_length=30,
      choices=sorted(IMAGEFORMATINFOTYPE_RASTERORVECTORGRAPHICS_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    quality = models.CharField(
      verbose_name='Quality',
      help_text='Specifies the quality level of image resource',
      blank=True,
      max_length=30,
      choices=sorted(IMAGEFORMATINFOTYPE_QUALITY_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerImageFormat = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per image format',
      help_text='Used to give info on size of parts of a resource that d' \
      'iffer as to the format',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    back_to_languagedescriptionimageinfotype_model = models.ForeignKey("languageDescriptionImageInfoType_model",  blank=True, null=True)

    back_to_lexicalconceptualresourceimageinfotype_model = models.ForeignKey("lexicalConceptualResourceImageInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

IMAGECLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'DK-5', u'EUROVOC',
  u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other',
])

# pylint: disable-msg=C0103
class imageClassificationInfoType_model(SchemaModel):
    """
    Groups information on the classification of the image corpus
    """

    class Meta:
        verbose_name = "Image classification"


    __schema_name__ = 'imageClassificationInfoType'
    __schema_fields__ = (
      ( u'imageGenre', u'imageGenre', OPTIONAL ),
      ( u'subject_topic', u'subject_topic', OPTIONAL ),
      ( u'conformanceToClassificationScheme', u'conformanceToClassificationScheme', OPTIONAL ),
      ( u'sizePerImageClassification', u'sizePerImageClassification', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerImageClassification': "sizeInfoType_model",
    }

    imageGenre = XmlCharField(
      verbose_name='Image genre',
      help_text='A first indication of the genre of images',
      blank=True, max_length=1000, )

    subject_topic = XmlCharField(
      verbose_name='Subject / Topic',
      help_text='For corpora that have already been using subject classi' \
      'fication',
      blank=True, max_length=500, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme',
      help_text='Specifies the external classification schemes',
      blank=True,
      max_length=100,
      choices=sorted(IMAGECLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerImageClassification = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per image classification',
      help_text='Provides information on size of parts with different im' \
      'age classification',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class corpusTextNumericalInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Corpus numerical text component"


    __schema_name__ = 'corpusTextNumericalInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', RECOMMENDED ),
      ( u'textNumericalContentInfo', u'textNumericalContentInfo', RECOMMENDED ),
      ( u'textNumericalFormatInfo', u'textnumericalformatinfotype_model_set', RECOMMENDED ),
      ( u'recordingInfo', u'recordingInfo', RECOMMENDED ),
      ( u'captureInfo', u'captureInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'annotationInfo', u'annotationinfotype_model_set', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linktoothermediainfotype_model_set', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'annotationInfo': "annotationInfoType_model",
      u'captureInfo': "captureInfoType_model",
      u'creationInfo': "creationInfoType_model",
      u'linkToOtherMediaInfo': "linkToOtherMediaInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'recordingInfo': "recordingInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'textNumericalContentInfo': "textNumericalContentInfoType_model",
      u'textNumericalFormatInfo': "textNumericalFormatInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="textNumerical", editable=False, max_length=1000, )

    # OneToMany field: modalityInfo

    # OneToMany field: sizeInfo

    textNumericalContentInfo = models.OneToOneField("textNumericalContentInfoType_model",
      verbose_name='Text numerical content',
      help_text='Groups information on the content of the textNumerical ' \
      'part of the resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: textNumericalFormatInfo

    recordingInfo = models.OneToOneField("recordingInfoType_model",
      verbose_name='Recording',
      help_text='Groups together information on the recording of the aud' \
      'io or video part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    captureInfo = models.OneToOneField("captureInfoType_model",
      verbose_name='Capture',
      help_text='Groups together information on the capture of the audio' \
      ' or video part of a corpus',
      blank=True, null=True, on_delete=models.SET_NULL, )

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: annotationInfo

    # OneToMany field: linkToOtherMediaInfo

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['modalityInfo', 'sizeInfo', ]
        formatstring = u'textNumerical ({} {})'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class textNumericalContentInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Text numerical content"


    __schema_name__ = 'textNumericalContentInfoType'
    __schema_fields__ = (
      ( u'typeOfTextNumericalContent', u'typeOfTextNumericalContent', REQUIRED ),
    )

    typeOfTextNumericalContent = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=25, max_length=1000),
      verbose_name='Type of text numerical content',
      help_text='Specifies the content that is represented in the textNu' \
      'merical part of the resource',
      validators=[validate_matches_xml_char_production], )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

TEXTNUMERICALFORMATINFOTYPE_MIMETYPE_CHOICES = _make_choices_from_list([
  u'text/plain', u'application/vnd.xmi+xml', u'application/xml',
  u'application/x-tmx+xml',u'application/x-xces+xml',
  u'application/tei+xml',u'application/rdf+xml', u'application/xhtml+xml',
  u'application/emma+xml',u'application/pls+xml',
  u'application/voicexml+xml',u'text/sgml', u'text/html',
  u'application/x-tex',u'application/rtf', u'application/x-latex',
  u'text/csv',u'text/tab-separated-values', u'application/pdf',
  u'application/x-msaccess',u'audio/mp4', u'audio/mpeg', u'audio/x-wav',
  u'image/bmp',u'image/gif', u'image/jpeg', u'image/png', u'image/svg+xml',
  u'image/tiff',u'video/jpeg', u'video/mp4', u'video/mpeg', u'video/x-flv',
  u'video/x-msvideo',u'video/x-ms-wmv', u'application/msword',
  u'application/vnd.ms-excel',u'audio/mpeg3', u'text/turtle', u'other',
])

# pylint: disable-msg=C0103
class textNumericalFormatInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Text numerical format"


    __schema_name__ = 'textNumericalFormatInfoType'
    __schema_fields__ = (
      ( u'mimeType', u'mimeType', REQUIRED ),
      ( u'sizePerTextNumericalFormat', u'sizePerTextNumericalFormat', OPTIONAL ),
    )
    __schema_classes__ = {
      u'sizePerTextNumericalFormat': "sizeInfoType_model",
    }

    mimeType = models.CharField(
      verbose_name='Mime type',
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts, in conformance with the values of the IANA (Internet ' \
      'Assigned Numbers Authority); you can select one of the pre-define' \
      'd values or add a value, PREFERABLY FROM THE IANA MEDIA MIMETYPE ' \
      'RECOMMENDED VALUES (http://www.iana.org/assignments/media-types/m' \
      'edia-types.xhtml)',

      max_length=50,
      choices=sorted(TEXTNUMERICALFORMATINFOTYPE_MIMETYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    sizePerTextNumericalFormat = models.OneToOneField("sizeInfoType_model",
      verbose_name='Size per text numerical format',
      help_text='Gives information on the size of textNumerical resource' \
      ' parts with different format',
      blank=True, null=True, on_delete=models.SET_NULL, )

    back_to_corpustextnumericalinfotype_model = models.ForeignKey("corpusTextNumericalInfoType_model",  blank=True, null=True)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class corpusTextNgramInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Corpus n-gram text component"


    __schema_name__ = 'corpusTextNgramInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'ngramInfo', u'ngramInfo', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageinfotype_model_set', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', REQUIRED ),
      ( u'textFormatInfo', u'textformatinfotype_model_set', RECOMMENDED ),
      ( u'characterEncodingInfo', u'characterencodinginfotype_model_set', RECOMMENDED ),
      ( u'annotationInfo', u'annotationinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', RECOMMENDED ),
      ( u'textClassificationInfo', u'textclassificationinfotype_model_set', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'annotationInfo': "annotationInfoType_model",
      u'characterEncodingInfo': "characterEncodingInfoType_model",
      u'creationInfo': "creationInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'ngramInfo': "ngramInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'textClassificationInfo': "textClassificationInfoType_model",
      u'textFormatInfo': "textFormatInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="textNgram", editable=False, max_length=1000, )

    ngramInfo = models.OneToOneField("ngramInfoType_model",
      verbose_name='N-gram',
      help_text='Groups information specific to n-gram resources (e.g. r' \
      'ange of n-grams, base item etc.)',
      )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    # OneToMany field: languageInfo

    modalityInfo = models.OneToOneField("modalityInfoType_model",
      verbose_name='Modality',
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: sizeInfo

    # OneToMany field: textFormatInfo

    # OneToMany field: characterEncodingInfo

    # OneToMany field: annotationInfo

    # OneToMany field: domainInfo

    # OneToMany field: textClassificationInfo

    # OneToMany field: timeCoverageInfo

    # OneToMany field: geographicCoverageInfo

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['lingualityInfo', 'languageInfo', ]
        formatstring = u'textNgram ({} {})'
        return self.unicode_(formatstring, formatargs)

NGRAMINFOTYPE_BASEITEM_CHOICES = _make_choices_from_list([
  u'word', u'syllable', u'letter', u'phoneme', u'other',
])

# pylint: disable-msg=C0103
class ngramInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Ngram"


    __schema_name__ = 'ngramInfoType'
    __schema_fields__ = (
      ( u'baseItem', u'baseItem', REQUIRED ),
      ( u'order', u'order', REQUIRED ),
      ( u'perplexity', u'perplexity', RECOMMENDED ),
      ( u'isFactored', u'isFactored', RECOMMENDED ),
      ( u'factors', u'factors', RECOMMENDED ),
      ( u'smoothing', u'smoothing', RECOMMENDED ),
      ( u'interpolated', u'interpolated', OPTIONAL ),
    )

    baseItem = MultiSelectField(
      verbose_name='Base item',
      help_text='Type of item that is represented in the n-gram resource' \
      '',

      max_length=1 + len(NGRAMINFOTYPE_BASEITEM_CHOICES['choices']) / 4,
      choices=NGRAMINFOTYPE_BASEITEM_CHOICES['choices'],
      )

    order = models.IntegerField(
      verbose_name='Order',
      help_text='The maximum number of items in the sequence',
      )

    perplexity = models.FloatField(
      verbose_name='Perplexity',
      help_text='Derived from running on test set taken from the same co' \
      'rpus',
      blank=True, null=True, )

    isFactored = MetaBooleanField(
      verbose_name='Is factored',
      help_text='Specifies whether the model is factored or not',
      blank=True, )

    factors = MultiTextField(max_length=150, widget=MultiFieldWidget(widget_id=26, max_length=150),
      verbose_name='Factors',
      help_text='The list of factors that have been used for the n-gram ' \
      'model',
      blank=True, validators=[validate_matches_xml_char_production], )

    smoothing = XmlCharField(
      verbose_name='Smoothing',
      help_text='The technique used for giving unseen items some probabi' \
      'lity',
      blank=True, max_length=1000, )

    interpolated = MetaBooleanField(
      verbose_name='Interpolated',
      help_text='Interpolated language models are constructed by 2 or mo' \
      're corpora. Each corpus is represented in the model according to ' \
      'a predefined weight.',
      blank=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

RELATEDLEXICONINFOTYPE_RELATEDLEXICONTYPE_CHOICES = _make_choices_from_list([
  u'included', u'attached', u'compatible', u'none',
])

RELATEDLEXICONINFOTYPE_COMPATIBLELEXICONTYPE_CHOICES = _make_choices_from_list([
  u'wordnet', u'wordlist', u'morphologicalLexicon', u'other',
])

# pylint: disable-msg=C0103
class relatedLexiconInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Related lexicon"


    __schema_name__ = 'relatedLexiconInfoType'
    __schema_fields__ = (
      ( u'relatedLexiconType', u'relatedLexiconType', REQUIRED ),
      ( u'attachedLexiconPosition', u'attachedLexiconPosition', OPTIONAL ),
      ( u'compatibleLexiconType', u'compatibleLexiconType', OPTIONAL ),
    )

    relatedLexiconType = models.CharField(
      verbose_name='Related lexicon type',
      help_text='Indicates the position of the lexica that must or can b' \
      'e used with the grammar',

      max_length=30,
      choices=sorted(RELATEDLEXICONINFOTYPE_RELATEDLEXICONTYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    attachedLexiconPosition = XmlCharField(
      verbose_name='Attached lexicon position',
      help_text='Indicates the position of the lexicon, if attached to t' \
      'he grammar',
      blank=True, max_length=500, )

    compatibleLexiconType = MultiSelectField(
      verbose_name='Compatible lexicon type',
      help_text='Type of (external) lexicon that can be used with the gr' \
      'ammar',
      blank=True,
      max_length=1 + len(RELATEDLEXICONINFOTYPE_COMPATIBLELEXICONTYPE_CHOICES['choices']) / 4,
      choices=RELATEDLEXICONINFOTYPE_COMPATIBLELEXICONTYPE_CHOICES['choices'],
      )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LANGUAGEDESCRIPTIONENCODINGINFOTYPE_ENCODINGLEVEL_CHOICES = _make_choices_from_list([
  u'phonetics', u'phonology', u'semantics', u'morphology', u'syntax',
  u'pragmatics',u'other',
])

LANGUAGEDESCRIPTIONENCODINGINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES = _make_choices_from_list([
  u'BML', u'CES', u'EAGLES', u'EML', u'EMMA', u'GMX', u'GrAF', u'HamNoSys',
  u'InkML',u'ILSP_NLP', u'ISO12620', u'ISO16642', u'ISO1987', u'ISO26162',
  u'ISO30042',u'ISO704', u'LAF', u'LMF', u'MAF', u'MLIF', u'MOSES',
  u'MULTEXT',u'MUMIN', u'multimodalInteractionFramework', u'OAXAL', u'OWL',
  u'PANACEA',u'pennTreeBank', u'pragueTreebank', u'RDF', u'SemAF',
  u'SemAF_DA',u'SemAF_NE', u'SemAF_SRL', u'SemAF_DS', u'SKOS', u'SRX',
  u'SynAF',u'TBX', u'TMX', u'TEI', u'TEI_P3', u'TEI_P4', u'TEI_P5',
  u'TimeML',u'XCES', u'XLIFF', u'WordNet', u'other',
])

LANGUAGEDESCRIPTIONENCODINGINFOTYPE_TASK_CHOICES = _make_choices_from_list([
  u'anaphoraResolution', u'chunking', u'parsing', u'npRecognition',
  u'titlesParsing',u'definitionsParsing', u'analysis', u'generation',
  u'other',
])

LANGUAGEDESCRIPTIONENCODINGINFOTYPE_GRAMMATICALPHENOMENACOVERAGE_CHOICES = _make_choices_from_list([
  u'clauseStructure', u'ppAttachment', u'npStructure', u'coordination',
  u'anaphora',u'other',
])

# pylint: disable-msg=C0103
class languageDescriptionEncodingInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Language description encoding"


    __schema_name__ = 'languageDescriptionEncodingInfoType'
    __schema_fields__ = (
      ( u'encodingLevel', u'encodingLevel', REQUIRED ),
      ( u'conformanceToStandardsBestPractices', u'conformanceToStandardsBestPractices', RECOMMENDED ),
      ( u'theoreticModel', u'theoreticModel', RECOMMENDED ),
      ( u'formalism', u'formalism', OPTIONAL ),
      ( u'task', u'task', RECOMMENDED ),
      ( u'grammaticalPhenomenaCoverage', u'grammaticalPhenomenaCoverage', RECOMMENDED ),
      ( u'weightedGrammar', u'weightedGrammar', OPTIONAL ),
    )

    encodingLevel = MultiSelectField(
      verbose_name='Encoding level',
      help_text='Information on the contents of the lexicalConceptualRes' \
      'ource as regards the linguistic level of analysis',

      max_length=1 + len(LANGUAGEDESCRIPTIONENCODINGINFOTYPE_ENCODINGLEVEL_CHOICES['choices']) / 4,
      choices=LANGUAGEDESCRIPTIONENCODINGINFOTYPE_ENCODINGLEVEL_CHOICES['choices'],
      )

    conformanceToStandardsBestPractices = MultiSelectField(
      verbose_name='Conformance to standards / best practices',
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True,
      max_length=1 + len(LANGUAGEDESCRIPTIONENCODINGINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices']) / 4,
      choices=LANGUAGEDESCRIPTIONENCODINGINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices'],
      )

    theoreticModel = MultiTextField(max_length=500, widget=MultiFieldWidget(widget_id=27, max_length=500),
      verbose_name='Theoretic model',
      help_text='Name of the theoretic model applied for the creation or' \
      ' enrichment of the resource, and/or a reference (URL or bibliogra' \
      'phic reference) to informative material about the theoretic model' \
      ' used',
      blank=True, validators=[validate_matches_xml_char_production], )

    formalism = XmlCharField(
      verbose_name='Formalism',
      help_text='Reference (name, bibliographic reference or link to url' \
      ') for the formalism used for the creation/enrichment of the resou' \
      'rce (grammar or tool/service)',
      blank=True, max_length=1000, )

    task = MultiSelectField(
      verbose_name='Task',
      help_text='An indication of the task performed by the grammar',
      blank=True,
      max_length=1 + len(LANGUAGEDESCRIPTIONENCODINGINFOTYPE_TASK_CHOICES['choices']) / 4,
      choices=LANGUAGEDESCRIPTIONENCODINGINFOTYPE_TASK_CHOICES['choices'],
      )

    grammaticalPhenomenaCoverage = MultiSelectField(
      verbose_name='Grammatical phenomena coverage',
      help_text='An indication of the grammatical phenomena covered by t' \
      'he grammar',
      blank=True,
      max_length=1 + len(LANGUAGEDESCRIPTIONENCODINGINFOTYPE_GRAMMATICALPHENOMENACOVERAGE_CHOICES['choices']) / 4,
      choices=LANGUAGEDESCRIPTIONENCODINGINFOTYPE_GRAMMATICALPHENOMENACOVERAGE_CHOICES['choices'],
      )

    weightedGrammar = MetaBooleanField(
      verbose_name='Weighted grammar',
      help_text='Indicates whether the grammar contains numerical weight' \
      's (incl. probabilities)',
      blank=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class languageDescriptionOperationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Language description operation"


    __schema_name__ = 'languageDescriptionOperationInfoType'
    __schema_fields__ = (
      ( u'runningEnvironmentInfo', u'runningEnvironmentInfo', RECOMMENDED ),
      ( u'relatedLexiconInfo', u'relatedLexiconInfo', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'relatedLexiconInfo': "relatedLexiconInfoType_model",
      u'runningEnvironmentInfo': "runningEnvironmentInfoType_model",
    }

    runningEnvironmentInfo = models.OneToOneField("runningEnvironmentInfoType_model",
      verbose_name='Running environment',
      help_text='Groups together information on the running environment ' \
      'of a tool or a language description',
      blank=True, null=True, on_delete=models.SET_NULL, )

    relatedLexiconInfo = models.OneToOneField("relatedLexiconInfoType_model",
      verbose_name='Related lexicon',
      help_text='Groups together information on requirements for lexica ' \
      'set by the LanguageDescriptions',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class languageDescriptionPerformanceInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Language description performance"


    __schema_name__ = 'languageDescriptionPerformanceInfoType'
    __schema_fields__ = (
      ( u'robustness', u'robustness', RECOMMENDED ),
      ( u'shallowness', u'shallowness', RECOMMENDED ),
      ( u'output', u'output', RECOMMENDED ),
    )

    robustness = XmlCharField(
      verbose_name='Robustness',
      help_text='Free text statement on the robustness of the grammar (h' \
      'ow well the grammar can cope with misspelt/unknown etc. input, i.' \
      'e. whether it can produce even partial interpretations of the inp' \
      'ut)',
      blank=True, max_length=500, )

    shallowness = XmlCharField(
      verbose_name='Shallowness',
      help_text='Free text statement on the shallowness of the grammar (' \
      'how deep the syntactic analysis performed by the grammar can be)',
      blank=True, max_length=200, )

    output = XmlCharField(
      verbose_name='Output',
      help_text='Indicates whether the output of the operation of the gr' \
      'ammar is a statement of grammaticality (grammatical/ungrammatical' \
      ') or structures (interpretation of the input)',
      blank=True, max_length=500, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class languageDescriptionTextInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Language description text"


    __schema_name__ = 'languageDescriptionTextInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linktoothermediainfotype_model_set', OPTIONAL ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageinfotype_model_set', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', RECOMMENDED ),
      ( u'textFormatInfo', u'textformatinfotype_model_set', RECOMMENDED ),
      ( u'characterEncodingInfo', u'characterencodinginfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'characterEncodingInfo': "characterEncodingInfoType_model",
      u'creationInfo': "creationInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'linkToOtherMediaInfo': "linkToOtherMediaInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'textFormatInfo': "textFormatInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="text", editable=False, max_length=1000, )

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: linkToOtherMediaInfo

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    # OneToMany field: languageInfo

    modalityInfo = models.OneToOneField("modalityInfoType_model",
      verbose_name='Modality',
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: sizeInfo

    # OneToMany field: textFormatInfo

    # OneToMany field: characterEncodingInfo

    # OneToMany field: domainInfo

    # OneToMany field: timeCoverageInfo

    # OneToMany field: geographicCoverageInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class languageDescriptionVideoInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Language description video"


    __schema_name__ = 'languageDescriptionVideoInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linktoothermediainfotype_model_set', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageinfotype_model_set', OPTIONAL ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', RECOMMENDED ),
      ( u'videoContentInfo', u'videoContentInfo', RECOMMENDED ),
      ( u'videoFormatInfo', u'videoformatinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'creationInfo': "creationInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'linkToOtherMediaInfo': "linkToOtherMediaInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
      u'videoContentInfo': "videoContentInfoType_model",
      u'videoFormatInfo': "videoFormatInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="video", editable=False, max_length=1000, )

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: linkToOtherMediaInfo

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: languageInfo

    # OneToMany field: modalityInfo

    # OneToMany field: sizeInfo

    videoContentInfo = models.OneToOneField("videoContentInfoType_model",
      verbose_name='Video content',
      help_text='Groups together information on the contents of the vide' \
      'o part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: videoFormatInfo

    # OneToMany field: domainInfo

    # OneToMany field: geographicCoverageInfo

    # OneToMany field: timeCoverageInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class languageDescriptionImageInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Language description image"


    __schema_name__ = 'languageDescriptionImageInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageinfotype_model_set', OPTIONAL ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linktoothermediainfotype_model_set', REQUIRED ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', RECOMMENDED ),
      ( u'imageContentInfo', u'imageContentInfo', RECOMMENDED ),
      ( u'imageFormatInfo', u'imageformatinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', OPTIONAL ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'creationInfo': "creationInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'imageContentInfo': "imageContentInfoType_model",
      u'imageFormatInfo': "imageFormatInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'linkToOtherMediaInfo': "linkToOtherMediaInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="image", editable=False, max_length=1000, )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: languageInfo

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: linkToOtherMediaInfo

    # OneToMany field: modalityInfo

    # OneToMany field: sizeInfo

    imageContentInfo = models.OneToOneField("imageContentInfoType_model",
      verbose_name='Image content',
      help_text='Groups together information on the contents of the imag' \
      'e part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: imageFormatInfo

    # OneToMany field: domainInfo

    # OneToMany field: geographicCoverageInfo

    # OneToMany field: timeCoverageInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_ENCODINGLEVEL_CHOICES = _make_choices_from_list([
  u'phonetics', u'phonology', u'semantics', u'morphology', u'syntax',
  u'pragmatics',u'other',
])

LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_LINGUISTICINFORMATION_CHOICES = _make_choices_from_list([
  u'accentuation', u'lemma', u'lemma-MultiWordUnits', u'lemma-Variants',
  u'lemma-Abbreviations',u'lemma-Compounds', u'lemma-CliticForms',
  u'partOfSpeech',u'morpho-Case', u'morpho-Gender', u'morpho-Number',
  u'morpho-Degree',u'morpho-IrregularForms', u'morpho-Mood',
  u'morpho-Tense',u'morpho-Person', u'morpho-Aspect', u'morpho-Voice',
  u'morpho-Auxiliary',u'morpho-Inflection', u'morpho-Reflexivity',
  u'syntax-SubcatFrame',u'semantics-Traits', u'semantics-SemanticClass',
  u'semantics-CrossReferences',u'semantics-Relations',
  u'semantics-Relations-Hyponyms',u'semantics-Relations-Hyperonyms',
  u'semantics-Relations-Synonyms',u'semantics-Relations-Antonyms',
  u'semantics-Relations-Troponyms',u'semantics-Relations-Meronyms',
  u'usage-Frequency',u'usage-Register', u'usage-Collocations',
  u'usage-Examples',u'usage-Notes', u'definition/gloss',
  u'translationEquivalent',u'phonetics-Transcription', u'semantics-Domain',
  u'semantics-EventType',u'semantics-SemanticRoles',
  u'statisticalProperties',u'morpho-Derivation',
  u'semantics-QualiaStructure',u'syntacticoSemanticLinks', u'other',
])

LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES = _make_choices_from_list([
  u'BML', u'CES', u'EAGLES', u'EML', u'EMMA', u'GMX', u'GrAF', u'HamNoSys',
  u'InkML',u'ILSP_NLP', u'ISO12620', u'ISO16642', u'ISO1987', u'ISO26162',
  u'ISO30042',u'ISO704', u'LAF', u'LMF', u'MAF', u'MLIF', u'MOSES',
  u'MULTEXT',u'MUMIN', u'multimodalInteractionFramework', u'OAXAL', u'OWL',
  u'PANACEA',u'pennTreeBank', u'pragueTreebank', u'RDF', u'SemAF',
  u'SemAF_DA',u'SemAF_NE', u'SemAF_SRL', u'SemAF_DS', u'SKOS', u'SRX',
  u'SynAF',u'TBX', u'TMX', u'TEI', u'TEI_P3', u'TEI_P4', u'TEI_P5',
  u'TimeML',u'XCES', u'XLIFF', u'WordNet', u'other',
])

LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATION_CHOICES = _make_choices_from_list([
  u'images', u'videos', u'soundRecordings', u'other',
])

LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATIONUNIT_CHOICES = _make_choices_from_list([
  u'word', u'lemma', u'semantics', u'example', u'syntax', u'lexicalUnit',
  u'other',
])

# pylint: disable-msg=C0103
class lexicalConceptualResourceEncodingInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Lexical conceptual resource encoding"


    __schema_name__ = 'lexicalConceptualResourceEncodingInfoType'
    __schema_fields__ = (
      ( u'encodingLevel', u'encodingLevel', REQUIRED ),
      ( u'linguisticInformation', u'linguisticInformation', RECOMMENDED ),
      ( u'conformanceToStandardsBestPractices', u'conformanceToStandardsBestPractices', RECOMMENDED ),
      ( u'theoreticModel', u'theoreticModel', OPTIONAL ),
      ( u'externalRef', u'externalRef', OPTIONAL ),
      ( u'extratextualInformation', u'extratextualInformation', OPTIONAL ),
      ( u'extraTextualInformationUnit', u'extraTextualInformationUnit', OPTIONAL ),
    )

    encodingLevel = MultiSelectField(
      verbose_name='Encoding level',
      help_text='Information on the contents of the lexicalConceptualRes' \
      'ource as regards the linguistic level of analysis',

      max_length=1 + len(LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_ENCODINGLEVEL_CHOICES['choices']) / 4,
      choices=LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_ENCODINGLEVEL_CHOICES['choices'],
      )

    linguisticInformation = MultiSelectField(
      verbose_name='Linguistic information',
      help_text='A more detailed account of the linguistic information c' \
      'ontained in the lexicalConceptualResource',
      blank=True,
      max_length=1 + len(LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_LINGUISTICINFORMATION_CHOICES['choices']) / 4,
      choices=LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_LINGUISTICINFORMATION_CHOICES['choices'],
      )

    conformanceToStandardsBestPractices = MultiSelectField(
      verbose_name='Conformance to standards / best practices',
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True,
      max_length=1 + len(LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices']) / 4,
      choices=LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices'],
      )

    theoreticModel = MultiTextField(max_length=500, widget=MultiFieldWidget(widget_id=28, max_length=500),
      verbose_name='Theoretic model',
      help_text='Name of the theoretic model applied for the creation or' \
      ' enrichment of the resource, and/or a reference (URL or bibliogra' \
      'phic reference) to informative material about the theoretic model' \
      ' used',
      blank=True, validators=[validate_matches_xml_char_production], )

    externalRef = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=29, max_length=100),
      verbose_name='External reference',
      help_text='Another resource to which the lexicalConceptualResource' \
      ' is linked (e.g. link to a wordnet or ontology)',
      blank=True, validators=[validate_matches_xml_char_production], )

    extratextualInformation = MultiSelectField(
      verbose_name='Extratextual information',
      help_text='An indication of the extratextual information contained' \
      ' in the lexicalConceptualResouce; can be used as an alternative t' \
      'o audio, image, videos etc. for cases where these are not conside' \
      'red an important part of the lcr',
      blank=True,
      max_length=1 + len(LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATION_CHOICES['choices']) / 4,
      choices=LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATION_CHOICES['choices'],
      )

    extraTextualInformationUnit = MultiSelectField(
      verbose_name='Extratextual information unit',
      help_text='The unit of the extratextual information contained in t' \
      'he lexical conceptual resource',
      blank=True,
      max_length=1 + len(LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATIONUNIT_CHOICES['choices']) / 4,
      choices=LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATIONUNIT_CHOICES['choices'],
      )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class lexicalConceptualResourceAudioInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Lexical conceptual resource audio"


    __schema_name__ = 'lexicalConceptualResourceAudioInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageinfotype_model_set', OPTIONAL ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', RECOMMENDED ),
      ( u'audioContentInfo', u'audioContentInfo', RECOMMENDED ),
      ( u'audioFormatInfo', u'audioformatinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', OPTIONAL ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'audioContentInfo': "audioContentInfoType_model",
      u'audioFormatInfo': "audioFormatInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="audio", editable=False, max_length=1000, )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: languageInfo

    # OneToMany field: modalityInfo

    # OneToMany field: sizeInfo

    audioContentInfo = models.OneToOneField("audioContentInfoType_model",
      verbose_name='Audio content',
      help_text='Groups together information on the contents of the audi' \
      'o part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: audioFormatInfo

    # OneToMany field: domainInfo

    # OneToMany field: geographicCoverageInfo

    # OneToMany field: timeCoverageInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class lexicalConceptualResourceTextInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Lexical conceptual resource text"


    __schema_name__ = 'lexicalConceptualResourceTextInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageinfotype_model_set', REQUIRED ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', REQUIRED ),
      ( u'textFormatInfo', u'textformatinfotype_model_set', RECOMMENDED ),
      ( u'characterEncodingInfo', u'characterencodinginfotype_model_set', OPTIONAL ),
      ( u'domainInfo', u'domaininfotype_model_set', OPTIONAL ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'characterEncodingInfo': "characterEncodingInfoType_model",
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'textFormatInfo': "textFormatInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="text", editable=False, max_length=1000, )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    # OneToMany field: languageInfo

    # OneToMany field: modalityInfo

    # OneToMany field: sizeInfo

    # OneToMany field: textFormatInfo

    # OneToMany field: characterEncodingInfo

    # OneToMany field: domainInfo

    # OneToMany field: timeCoverageInfo

    # OneToMany field: geographicCoverageInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class lexicalConceptualResourceVideoInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Lexical conceptual resource video"


    __schema_name__ = 'lexicalConceptualResourceVideoInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageinfotype_model_set', OPTIONAL ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'sizeInfo', u'sizeinfotype_model_set', RECOMMENDED ),
      ( u'videoContentInfo', u'videoContentInfo', REQUIRED ),
      ( u'videoFormatInfo', u'videoformatinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', OPTIONAL ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
      u'videoContentInfo': "videoContentInfoType_model",
      u'videoFormatInfo': "videoFormatInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="video", editable=False, max_length=1000, )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: languageInfo

    # OneToMany field: modalityInfo

    # OneToMany field: sizeInfo

    videoContentInfo = models.OneToOneField("videoContentInfoType_model",
      verbose_name='Video content',
      help_text='Groups together information on the contents of the vide' \
      'o part of a resource',
      )

    # OneToMany field: videoFormatInfo

    # OneToMany field: domainInfo

    # OneToMany field: geographicCoverageInfo

    # OneToMany field: timeCoverageInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class lexicalConceptualResourceImageInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Lexical conceptual resource image"


    __schema_name__ = 'lexicalConceptualResourceImageInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'modalityInfo', u'modalityinfotype_model_set', RECOMMENDED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageinfotype_model_set', OPTIONAL ),
      ( u'sizeInfo', u'sizeinfotype_model_set', RECOMMENDED ),
      ( u'imageContentInfo', u'imageContentInfo', RECOMMENDED ),
      ( u'imageFormatInfo', u'imageformatinfotype_model_set', RECOMMENDED ),
      ( u'domainInfo', u'domaininfotype_model_set', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographiccoverageinfotype_model_set', OPTIONAL ),
      ( u'timeCoverageInfo', u'timecoverageinfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'domainInfo': "domainInfoType_model",
      u'geographicCoverageInfo': "geographicCoverageInfoType_model",
      u'imageContentInfo': "imageContentInfoType_model",
      u'imageFormatInfo': "imageFormatInfoType_model",
      u'languageInfo': "languageInfoType_model",
      u'lingualityInfo': "lingualityInfoType_model",
      u'modalityInfo': "modalityInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
      u'timeCoverageInfo': "timeCoverageInfoType_model",
    }

    mediaType = XmlCharField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      default="image", editable=False, max_length=1000, )

    # OneToMany field: modalityInfo

    lingualityInfo = models.OneToOneField("lingualityInfoType_model",
      verbose_name='Linguality',
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: languageInfo

    # OneToMany field: sizeInfo

    imageContentInfo = models.OneToOneField("imageContentInfoType_model",
      verbose_name='Image content',
      help_text='Groups together information on the contents of the imag' \
      'e part of a resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: imageFormatInfo

    # OneToMany field: domainInfo

    # OneToMany field: geographicCoverageInfo

    # OneToMany field: timeCoverageInfo

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

INPUTINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical',
])

INPUTINFOTYPE_RESOURCETYPE_CHOICES = _make_choices_from_list([
  u'corpus', u'lexicalConceptualResource', u'languageDescription',
])

INPUTINFOTYPE_MODALITYTYPE_CHOICES = _make_choices_from_list([
  u'bodyGesture', u'facialExpression', u'voice', u'combinationOfModalities',
  u'signLanguage',u'spokenLanguage', u'writtenLanguage', u'other',
])

INPUTINFOTYPE_MIMETYPE_CHOICES = _make_choices_from_list([
  u'text/plain', u'application/vnd.xmi+xml', u'application/xml',
  u'application/x-tmx+xml',u'application/x-xces+xml',
  u'application/tei+xml',u'application/rdf+xml', u'application/xhtml+xml',
  u'application/emma+xml',u'application/pls+xml',
  u'application/voicexml+xml',u'text/sgml', u'text/html',
  u'application/x-tex',u'application/rtf', u'application/x-latex',
  u'text/csv',u'text/tab-separated-values', u'application/pdf',
  u'application/x-msaccess',u'audio/mp4', u'audio/mpeg', u'audio/x-wav',
  u'image/bmp',u'image/gif', u'image/jpeg', u'image/png', u'image/svg+xml',
  u'image/tiff',u'video/jpeg', u'video/mp4', u'video/mpeg', u'video/x-flv',
  u'video/x-msvideo',u'video/x-ms-wmv', u'application/msword',
  u'application/vnd.ms-excel',u'audio/mpeg3', u'text/turtle', u'other',
])

INPUTINFOTYPE_CHARACTERENCODING_CHOICES = _make_choices_from_list([
  u'US-ASCII', u'windows-1250', u'windows-1251', u'windows-1252',
  u'windows-1253',u'windows-1254', u'windows-1257', u'ISO-8859-1',
  u'ISO-8859-2',u'ISO-8859-4', u'ISO-8859-5', u'ISO-8859-7', u'ISO-8859-9',
  u'ISO-8859-13',u'ISO-8859-15', u'KOI8-R', u'UTF-8', u'UTF-16',
  u'UTF-16BE',u'UTF-16LE', u'windows-1255', u'windows-1256',
  u'windows-1258',u'ISO-8859-3', u'ISO-8859-6', u'ISO-8859-8',
  u'windows-31j',u'EUC-JP', u'x-EUC-JP-LINUX', u'Shift_JIS', u'ISO-2022-JP',
  u'x-mswin-936',u'GB18030', u'x-EUC-CN', u'GBK', u'ISCII91',
  u'x-windows-949',u'EUC-KR', u'ISO-2022-KR', u'x-windows-950',
  u'x-MS950-HKSCS',u'x-EUC-TW', u'Big5', u'Big5-HKSCS', u'TIS-620',
  u'Big5_Solaris',u'Cp037', u'Cp273', u'Cp277', u'Cp278', u'Cp280',
  u'Cp284',u'Cp285', u'Cp297', u'Cp420', u'Cp424', u'Cp437', u'Cp500',
  u'Cp737',u'Cp775', u'Cp838', u'Cp850', u'Cp852', u'Cp855', u'Cp856',
  u'Cp857',u'Cp858', u'Cp860', u'Cp861', u'Cp862', u'Cp863', u'Cp864',
  u'Cp865',u'Cp866', u'Cp868', u'Cp869', u'Cp870', u'Cp871', u'Cp874',
  u'Cp875',u'Cp918', u'Cp921', u'Cp922', u'Cp930', u'Cp933', u'Cp935',
  u'Cp937',u'Cp939', u'Cp942', u'Cp942C', u'Cp943', u'Cp943C', u'Cp948',
  u'Cp949',u'Cp949C', u'Cp950', u'Cp964', u'Cp970', u'Cp1006', u'Cp1025',
  u'Cp1026',u'Cp1046', u'Cp1047', u'Cp1097', u'Cp1098', u'Cp1112',
  u'Cp1122',u'Cp1123', u'Cp1124', u'Cp1140', u'Cp1141', u'Cp1142',
  u'Cp1143',u'Cp1144', u'Cp1145', u'Cp1146', u'Cp1147', u'Cp1148',
  u'Cp1149',u'Cp1381', u'Cp1383', u'Cp33722', u'ISO2022_CN_CNS',
  u'ISO2022_CN_GB',u'JISAutoDetect', u'MS874', u'MacArabic',
  u'MacCentralEurope',u'MacCroatian', u'MacCyrillic', u'MacDingbat',
  u'MacGreek',u'MacHebrew', u'MacIceland', u'MacRoman', u'MacRomania',
  u'MacSymbol',u'MacThai', u'MacTurkish', u'MacUkraine',
])

INPUTINFOTYPE_ANNOTATIONTYPE_CHOICES = _make_choices_from_list([
  u'alignment', u'discourseAnnotation',
  u'discourseAnnotation-audienceReactions',
  u'discourseAnnotation-coreference',u'discourseAnnotation-dialogueActs',
  u'discourseAnnotation-discourseRelations',u'lemmatization',
  u'morphosyntacticAnnotation-bPosTagging',
  u'morphosyntacticAnnotation-posTagging',u'segmentation',
  u'semanticAnnotation',u'semanticAnnotation-certaintyLevel',
  u'semanticAnnotation-emotions',u'semanticAnnotation-entityMentions',
  u'semanticAnnotation-events',u'semanticAnnotation-namedEntities',
  u'semanticAnnotation-polarity',
  u'semanticAnnotation-questionTopicalTarget',
  u'semanticAnnotation-semanticClasses',
  u'semanticAnnotation-semanticRelations',
  u'semanticAnnotation-semanticRoles',u'semanticAnnotation-speechActs',
  u'semanticAnnotation-temporalExpressions',
  u'semanticAnnotation-textualEntailment',u'semanticAnnotation-wordSenses',
  u'speechAnnotation',u'speechAnnotation-orthographicTranscription',
  u'speechAnnotation-paralanguageAnnotation',
  u'speechAnnotation-phoneticTranscription',
  u'speechAnnotation-prosodicAnnotation',u'speechAnnotation-soundEvents',
  u'speechAnnotation-soundToTextAlignment',
  u'speechAnnotation-speakerIdentification',
  u'speechAnnotation-speakerTurns',u'stemming', u'structuralAnnotation',
  u'syntacticAnnotation-subcategorizationFrames',
  u'syntacticAnnotation-dependencyTrees',
  u'syntacticAnnotation-constituencyTrees',
  u'syntacticosemanticAnnotation-links',u'translation', u'transliteration',
  u'modalityAnnotation-bodyMovements',
  u'modalityAnnotation-facialExpressions',
  u'modalityAnnotation-gazeEyeMovements',
  u'modalityAnnotation-handArmGestures',
  u'modalityAnnotation-handManipulationOfObjects',
  u'modalityAnnotation-headMovements',u'modalityAnnotation-lipMovements',
  u'other',
])

INPUTINFOTYPE_SEGMENTATIONLEVEL_CHOICES = _make_choices_from_list([
  u'paragraph', u'sentence', u'clause', u'word', u'wordGroup', u'utterance',
  u'topic',u'signal', u'phoneme', u'syllable', u'phrase', u'diphone',
  u'prosodicBoundaries',u'frame', u'scene', u'shot', u'token', u'other',
])

INPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES = _make_choices_from_list([
  u'BML', u'CES', u'EAGLES', u'EML', u'EMMA', u'GMX', u'GrAF', u'HamNoSys',
  u'InkML',u'ILSP_NLP', u'ISO12620', u'ISO16642', u'ISO1987', u'ISO26162',
  u'ISO30042',u'ISO704', u'LAF', u'LMF', u'MAF', u'MLIF', u'MOSES',
  u'MULTEXT',u'MUMIN', u'multimodalInteractionFramework', u'OAXAL', u'OWL',
  u'PANACEA',u'pennTreeBank', u'pragueTreebank', u'RDF', u'SemAF',
  u'SemAF_DA',u'SemAF_NE', u'SemAF_SRL', u'SemAF_DS', u'SKOS', u'SRX',
  u'SynAF',u'TBX', u'TMX', u'TEI', u'TEI_P3', u'TEI_P4', u'TEI_P5',
  u'TimeML',u'XCES', u'XLIFF', u'WordNet', u'other',
])

# pylint: disable-msg=C0103
class inputInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Input"


    __schema_name__ = 'inputInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'resourceType', u'resourceType', RECOMMENDED ),
      ( u'modalityType', u'modalityType', RECOMMENDED ),
      ( u'languageName', u'languageName', OPTIONAL ),
      ( u'languageId', u'languageId', OPTIONAL ),
      ( u'languageVarietyName', u'languageVarietyName', OPTIONAL ),
      ( u'mimeType', u'mimeType', RECOMMENDED ),
      ( u'characterEncoding', u'characterEncoding', OPTIONAL ),
      ( u'domain', u'domain', OPTIONAL ),
      ( u'annotationType', u'annotationType', OPTIONAL ),
      ( u'annotationFormat', u'annotationFormat', OPTIONAL ),
      ( u'tagset', u'tagset', OPTIONAL ),
      ( u'segmentationLevel', u'segmentationLevel', OPTIONAL ),
      ( u'conformanceToStandardsBestPractices', u'conformanceToStandardsBestPractices', OPTIONAL ),
    )

    mediaType = MultiSelectField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',

      max_length=1 + len(INPUTINFOTYPE_MEDIATYPE_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    resourceType = MultiSelectField(
      verbose_name='Resource type',
      help_text='The type of the resource that a tool or service takes a' \
      's input or produces as output',
      blank=True,
      max_length=1 + len(INPUTINFOTYPE_RESOURCETYPE_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_RESOURCETYPE_CHOICES['choices'],
      )

    modalityType = MultiSelectField(
      verbose_name='Modality type',
      help_text='Specifies the type of the modality represented in the r' \
      'esource or processed by a tool/service',
      blank=True,
      max_length=1 + len(INPUTINFOTYPE_MODALITYTYPE_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_MODALITYTYPE_CHOICES['choices'],
      )

    languageName = MultiTextField(max_length=500, widget=MultiChoiceWidget(widget_id=30, choices = languagename_optgroup_choices()),
    verbose_name='Language name',
    help_text='A human understandable name of the language that is use' \
      'd in the resource or supported by the tool/service, as specified ' \
      'in the BCP47 guidelines (https://tools.ietf.org/html/bcp47); the ' \
      'guidelines includes (a) language subtag according to ISO 639-1 an' \
      'd for languages not covered by this, the ISO 639-3; (b) the scrip' \
      't tag according to ISO 15924; (c) the region tag according to ISO' \
      ' 3166-1; (d) the variant subtag',
    blank=True, validators=[validate_matches_xml_char_production], )

    languageId = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=31, max_length=100),
        verbose_name='Language identifier',
        help_text='The identifier of the language that is included in the ' \
      'resource or supported by the tool/service according to the IETF B' \
      'CP47 standard',
        blank=True, validators=[validate_matches_xml_char_production], editable=False)

    languageVarietyName = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=32, max_length=100),
      verbose_name='Language variety name',
      help_text='The name of the language variety that occurs in the res' \
      'ource or is supported by a tool/service',
      blank=True, validators=[validate_matches_xml_char_production], )

    mimeType = MultiSelectField(
      verbose_name='Mime type',
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts, in conformance with the values of the IANA (Internet ' \
      'Assigned Numbers Authority); you can select one of the pre-define' \
      'd values or add a value, PREFERABLY FROM THE IANA MEDIA MIMETYPE ' \
      'RECOMMENDED VALUES (http://www.iana.org/assignments/media-types/m' \
      'edia-types.xhtml)',
      blank=True,
      max_length=1 + len(INPUTINFOTYPE_MIMETYPE_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_MIMETYPE_CHOICES['choices'],
      )

    characterEncoding = MultiSelectField(
      verbose_name='Character encoding',
      help_text='The name of the character encoding used in the resource' \
      ' or accepted by the tool/service',
      blank=True,
      max_length=1 + len(INPUTINFOTYPE_CHARACTERENCODING_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_CHARACTERENCODING_CHOICES['choices'],
      )

    domain = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=33, max_length=100),
      verbose_name='Domain',
      help_text='Specifies the application domain of the resource or the' \
      ' tool/service',
      blank=True, validators=[validate_matches_xml_char_production], )

    annotationType = MultiSelectField(
      verbose_name='Annotation type',
      help_text='Specifies the annotation level of the resource or the a' \
      'nnotation type a tool/ service requires or produces as an output',
      blank=True,
      max_length=1 + len(INPUTINFOTYPE_ANNOTATIONTYPE_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_ANNOTATIONTYPE_CHOICES['choices'],
      )

    annotationFormat = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=34, max_length=100),
      verbose_name='Annotation format',
      help_text='Specifies the format that is used in the annotation pro' \
      'cess since often the mime type will not be sufficient for machine' \
      ' processing',
      blank=True, validators=[validate_matches_xml_char_production], )

    tagset = MultiTextField(max_length=500, widget=MultiFieldWidget(widget_id=35, max_length=500),
      verbose_name='Tagset',
      help_text='A name or a url reference to the tagset used in the ann' \
      'otation of the resource or used by the tool/service',
      blank=True, validators=[validate_matches_xml_char_production], )

    segmentationLevel = MultiSelectField(
      verbose_name='Segmentation level',
      help_text='Specifies the segmentation unit in terms of which the r' \
      'esource has been segmented or the level of segmentation a tool/se' \
      'rvice requires/outputs',
      blank=True,
      max_length=1 + len(INPUTINFOTYPE_SEGMENTATIONLEVEL_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_SEGMENTATIONLEVEL_CHOICES['choices'],
      )

    conformanceToStandardsBestPractices = MultiSelectField(
      verbose_name='Conformance to standards / best practices',
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True,
      max_length=1 + len(INPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices'],
      )

    def save(self, *args, **kwargs):
        if self.languageName:
            self.languageId = iana.get_language_subtag(self.languageName)
        super(inputInfoType_model, self).save(*args, **kwargs)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

OUTPUTINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical',
])

OUTPUTINFOTYPE_RESOURCETYPE_CHOICES = _make_choices_from_list([
  u'corpus', u'lexicalConceptualResource', u'languageDescription',
])

OUTPUTINFOTYPE_MODALITYTYPE_CHOICES = _make_choices_from_list([
  u'bodyGesture', u'facialExpression', u'voice', u'combinationOfModalities',
  u'signLanguage',u'spokenLanguage', u'writtenLanguage', u'other',
])

OUTPUTINFOTYPE_MIMETYPE_CHOICES = _make_choices_from_list([
  u'text/plain', u'application/vnd.xmi+xml', u'application/xml',
  u'application/x-tmx+xml',u'application/x-xces+xml',
  u'application/tei+xml',u'application/rdf+xml', u'application/xhtml+xml',
  u'application/emma+xml',u'application/pls+xml',
  u'application/voicexml+xml',u'text/sgml', u'text/html',
  u'application/x-tex',u'application/rtf', u'application/x-latex',
  u'text/csv',u'text/tab-separated-values', u'application/pdf',
  u'application/x-msaccess',u'audio/mp4', u'audio/mpeg', u'audio/x-wav',
  u'image/bmp',u'image/gif', u'image/jpeg', u'image/png', u'image/svg+xml',
  u'image/tiff',u'video/jpeg', u'video/mp4', u'video/mpeg', u'video/x-flv',
  u'video/x-msvideo',u'video/x-ms-wmv', u'application/msword',
  u'application/vnd.ms-excel',u'audio/mpeg3', u'text/turtle', u'other',
])

OUTPUTINFOTYPE_CHARACTERENCODING_CHOICES = _make_choices_from_list([
  u'US-ASCII', u'windows-1250', u'windows-1251', u'windows-1252',
  u'windows-1253',u'windows-1254', u'windows-1257', u'ISO-8859-1',
  u'ISO-8859-2',u'ISO-8859-4', u'ISO-8859-5', u'ISO-8859-7', u'ISO-8859-9',
  u'ISO-8859-13',u'ISO-8859-15', u'KOI8-R', u'UTF-8', u'UTF-16',
  u'UTF-16BE',u'UTF-16LE', u'windows-1255', u'windows-1256',
  u'windows-1258',u'ISO-8859-3', u'ISO-8859-6', u'ISO-8859-8',
  u'windows-31j',u'EUC-JP', u'x-EUC-JP-LINUX', u'Shift_JIS', u'ISO-2022-JP',
  u'x-mswin-936',u'GB18030', u'x-EUC-CN', u'GBK', u'ISCII91',
  u'x-windows-949',u'EUC-KR', u'ISO-2022-KR', u'x-windows-950',
  u'x-MS950-HKSCS',u'x-EUC-TW', u'Big5', u'Big5-HKSCS', u'TIS-620',
  u'Big5_Solaris',u'Cp037', u'Cp273', u'Cp277', u'Cp278', u'Cp280',
  u'Cp284',u'Cp285', u'Cp297', u'Cp420', u'Cp424', u'Cp437', u'Cp500',
  u'Cp737',u'Cp775', u'Cp838', u'Cp850', u'Cp852', u'Cp855', u'Cp856',
  u'Cp857',u'Cp858', u'Cp860', u'Cp861', u'Cp862', u'Cp863', u'Cp864',
  u'Cp865',u'Cp866', u'Cp868', u'Cp869', u'Cp870', u'Cp871', u'Cp874',
  u'Cp875',u'Cp918', u'Cp921', u'Cp922', u'Cp930', u'Cp933', u'Cp935',
  u'Cp937',u'Cp939', u'Cp942', u'Cp942C', u'Cp943', u'Cp943C', u'Cp948',
  u'Cp949',u'Cp949C', u'Cp950', u'Cp964', u'Cp970', u'Cp1006', u'Cp1025',
  u'Cp1026',u'Cp1046', u'Cp1047', u'Cp1097', u'Cp1098', u'Cp1112',
  u'Cp1122',u'Cp1123', u'Cp1124', u'Cp1140', u'Cp1141', u'Cp1142',
  u'Cp1143',u'Cp1144', u'Cp1145', u'Cp1146', u'Cp1147', u'Cp1148',
  u'Cp1149',u'Cp1381', u'Cp1383', u'Cp33722', u'ISO2022_CN_CNS',
  u'ISO2022_CN_GB',u'JISAutoDetect', u'MS874', u'MacArabic',
  u'MacCentralEurope',u'MacCroatian', u'MacCyrillic', u'MacDingbat',
  u'MacGreek',u'MacHebrew', u'MacIceland', u'MacRoman', u'MacRomania',
  u'MacSymbol',u'MacThai', u'MacTurkish', u'MacUkraine',
])

OUTPUTINFOTYPE_ANNOTATIONTYPE_CHOICES = _make_choices_from_list([
  u'alignment', u'discourseAnnotation',
  u'discourseAnnotation-audienceReactions',
  u'discourseAnnotation-coreference',u'discourseAnnotation-dialogueActs',
  u'discourseAnnotation-discourseRelations',u'lemmatization',
  u'morphosyntacticAnnotation-bPosTagging',
  u'morphosyntacticAnnotation-posTagging',u'segmentation',
  u'semanticAnnotation',u'semanticAnnotation-certaintyLevel',
  u'semanticAnnotation-emotions',u'semanticAnnotation-entityMentions',
  u'semanticAnnotation-events',u'semanticAnnotation-namedEntities',
  u'semanticAnnotation-polarity',
  u'semanticAnnotation-questionTopicalTarget',
  u'semanticAnnotation-semanticClasses',
  u'semanticAnnotation-semanticRelations',
  u'semanticAnnotation-semanticRoles',u'semanticAnnotation-speechActs',
  u'semanticAnnotation-temporalExpressions',
  u'semanticAnnotation-textualEntailment',u'semanticAnnotation-wordSenses',
  u'speechAnnotation',u'speechAnnotation-orthographicTranscription',
  u'speechAnnotation-paralanguageAnnotation',
  u'speechAnnotation-phoneticTranscription',
  u'speechAnnotation-prosodicAnnotation',u'speechAnnotation-soundEvents',
  u'speechAnnotation-soundToTextAlignment',
  u'speechAnnotation-speakerIdentification',
  u'speechAnnotation-speakerTurns',u'stemming', u'structuralAnnotation',
  u'syntacticAnnotation-subcategorizationFrames',
  u'syntacticAnnotation-dependencyTrees',
  u'syntacticAnnotation-constituencyTrees',
  u'syntacticosemanticAnnotation-links',u'translation', u'transliteration',
  u'modalityAnnotation-bodyMovements',
  u'modalityAnnotation-facialExpressions',
  u'modalityAnnotation-gazeEyeMovements',
  u'modalityAnnotation-handArmGestures',
  u'modalityAnnotation-handManipulationOfObjects',
  u'modalityAnnotation-headMovements',u'modalityAnnotation-lipMovements',
  u'other',
])

OUTPUTINFOTYPE_SEGMENTATIONLEVEL_CHOICES = _make_choices_from_list([
  u'paragraph', u'sentence', u'clause', u'word', u'wordGroup', u'utterance',
  u'topic',u'signal', u'phoneme', u'syllable', u'phrase', u'diphone',
  u'prosodicBoundaries',u'frame', u'scene', u'shot', u'token', u'other',
])

OUTPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES = _make_choices_from_list([
  u'BML', u'CES', u'EAGLES', u'EML', u'EMMA', u'GMX', u'GrAF', u'HamNoSys',
  u'InkML',u'ILSP_NLP', u'ISO12620', u'ISO16642', u'ISO1987', u'ISO26162',
  u'ISO30042',u'ISO704', u'LAF', u'LMF', u'MAF', u'MLIF', u'MOSES',
  u'MULTEXT',u'MUMIN', u'multimodalInteractionFramework', u'OAXAL', u'OWL',
  u'PANACEA',u'pennTreeBank', u'pragueTreebank', u'RDF', u'SemAF',
  u'SemAF_DA',u'SemAF_NE', u'SemAF_SRL', u'SemAF_DS', u'SKOS', u'SRX',
  u'SynAF',u'TBX', u'TMX', u'TEI', u'TEI_P3', u'TEI_P4', u'TEI_P5',
  u'TimeML',u'XCES', u'XLIFF', u'WordNet', u'other',
])

# pylint: disable-msg=C0103
class outputInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Output"


    __schema_name__ = 'outputInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'resourceType', u'resourceType', RECOMMENDED ),
      ( u'modalityType', u'modalityType', RECOMMENDED ),
      ( u'languageName', u'languageName', OPTIONAL ),
      ( u'languageId', u'languageId', OPTIONAL ),
      ( u'languageVarietyName', u'languageVarietyName', OPTIONAL ),
      ( u'mimeType', u'mimeType', RECOMMENDED ),
      ( u'characterEncoding', u'characterEncoding', OPTIONAL ),
      ( u'annotationType', u'annotationType', OPTIONAL ),
      ( u'annotationFormat', u'annotationFormat', OPTIONAL ),
      ( u'tagset', u'tagset', OPTIONAL ),
      ( u'segmentationLevel', u'segmentationLevel', OPTIONAL ),
      ( u'conformanceToStandardsBestPractices', u'conformanceToStandardsBestPractices', OPTIONAL ),
    )

    mediaType = MultiSelectField(
      verbose_name='Media type',
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',

      max_length=1 + len(OUTPUTINFOTYPE_MEDIATYPE_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    resourceType = MultiSelectField(
      verbose_name='Resource type',
      help_text='The type of the resource that a tool or service takes a' \
      's input or produces as output',
      blank=True,
      max_length=1 + len(OUTPUTINFOTYPE_RESOURCETYPE_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_RESOURCETYPE_CHOICES['choices'],
      )

    modalityType = MultiSelectField(
      verbose_name='Modality type',
      help_text='Specifies the type of the modality represented in the r' \
      'esource or processed by a tool/service',
      blank=True,
      max_length=1 + len(OUTPUTINFOTYPE_MODALITYTYPE_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_MODALITYTYPE_CHOICES['choices'],
      )

    languageName = MultiTextField(max_length=500, widget=MultiChoiceWidget(widget_id=36, choices = languagename_optgroup_choices()),
      verbose_name='Language name',
      help_text='A human understandable name of the language that is use' \
      'd in the resource or supported by the tool/service, as specified ' \
      'in the BCP47 guidelines (https://tools.ietf.org/html/bcp47); the ' \
      'guidelines includes (a) language subtag according to ISO 639-1 an' \
      'd for languages not covered by this, the ISO 639-3; (b) the scrip' \
      't tag according to ISO 15924; (c) the region tag according to ISO' \
      ' 3166-1; (d) the variant subtag',
      blank=True, validators=[validate_matches_xml_char_production], )

    languageId = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=37, max_length=100),
      verbose_name='Language identifier',
      help_text='The identifier of the language that is included in the ' \
      'resource or supported by the tool/service according to the IETF B' \
      'CP47 standard',
      blank=True, validators=[validate_matches_xml_char_production], editable=False)

    languageVarietyName = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=38, max_length=100),
      verbose_name='Language variety name',
      help_text='The name of the language variety that occurs in the res' \
      'ource or is supported by a tool/service',
      blank=True, validators=[validate_matches_xml_char_production], )

    mimeType = MultiSelectField(
      verbose_name='Mime type',
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts, in conformance with the values of the IANA (Internet ' \
      'Assigned Numbers Authority); you can select one of the pre-define' \
      'd values or add a value, PREFERABLY FROM THE IANA MEDIA MIMETYPE ' \
      'RECOMMENDED VALUES (http://www.iana.org/assignments/media-types/m' \
      'edia-types.xhtml)',
      blank=True,
      max_length=1 + len(OUTPUTINFOTYPE_MIMETYPE_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_MIMETYPE_CHOICES['choices'],
      )

    characterEncoding = MultiSelectField(
      verbose_name='Character encoding',
      help_text='The name of the character encoding used in the resource' \
      ' or accepted by the tool/service',
      blank=True,
      max_length=1 + len(OUTPUTINFOTYPE_CHARACTERENCODING_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_CHARACTERENCODING_CHOICES['choices'],
      )

    annotationType = MultiSelectField(
      verbose_name='Annotation type',
      help_text='Specifies the annotation level of the resource or the a' \
      'nnotation type a tool/ service requires or produces as an output',
      blank=True,
      max_length=1 + len(OUTPUTINFOTYPE_ANNOTATIONTYPE_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_ANNOTATIONTYPE_CHOICES['choices'],
      )

    annotationFormat = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=39, max_length=100),
      verbose_name='Annotation format',
      help_text='Specifies the format that is used in the annotation pro' \
      'cess since often the mime type will not be sufficient for machine' \
      ' processing',
      blank=True, validators=[validate_matches_xml_char_production], )

    tagset = MultiTextField(max_length=500, widget=MultiFieldWidget(widget_id=40, max_length=500),
      verbose_name='Tagset',
      help_text='A name or a url reference to the tagset used in the ann' \
      'otation of the resource or used by the tool/service',
      blank=True, validators=[validate_matches_xml_char_production], )

    segmentationLevel = MultiSelectField(
      verbose_name='Segmentation level',
      help_text='Specifies the segmentation unit in terms of which the r' \
      'esource has been segmented or the level of segmentation a tool/se' \
      'rvice requires/outputs',
      blank=True,
      max_length=1 + len(OUTPUTINFOTYPE_SEGMENTATIONLEVEL_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_SEGMENTATIONLEVEL_CHOICES['choices'],
      )

    conformanceToStandardsBestPractices = MultiSelectField(
      verbose_name='Conformance to standards / best practices',
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True,
      max_length=1 + len(OUTPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices'],
      )

    def save(self, *args, **kwargs):
        if self.languageName:
            self.languageId = iana.get_language_subtag(self.languageName)
        super(outputInfoType_model, self).save(*args, **kwargs)

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONLEVEL_CHOICES = _make_choices_from_list([
  u'technological', u'usage', u'impact', u'diagnostic',
])

TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONTYPE_CHOICES = _make_choices_from_list([
  u'glassBox', u'blackBox',
])

TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONCRITERIA_CHOICES = _make_choices_from_list([
  u'extrinsic', u'intrinsic',
])

TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONMEASURE_CHOICES = _make_choices_from_list([
  u'human', u'automatic',
])

# pylint: disable-msg=C0103
class toolServiceEvaluationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Tool service evaluation"


    __schema_name__ = 'toolServiceEvaluationInfoType'
    __schema_fields__ = (
      ( u'evaluated', u'evaluated', REQUIRED ),
      ( u'evaluationLevel', u'evaluationLevel', OPTIONAL ),
      ( u'evaluationType', u'evaluationType', OPTIONAL ),
      ( u'evaluationCriteria', u'evaluationCriteria', OPTIONAL ),
      ( u'evaluationMeasure', u'evaluationMeasure', OPTIONAL ),
      ( 'evaluationReport/documentUnstructured', 'evaluationReport', RECOMMENDED ),
      ( 'evaluationReport/documentInfo', 'evaluationReport', RECOMMENDED ),
      ( u'evaluationTool', u'evaluationTool', RECOMMENDED ),
      ( u'evaluationDetails', u'evaluationDetails', RECOMMENDED ),
      ( 'evaluator/personInfo', 'evaluator', OPTIONAL ),
      ( 'evaluator/organizationInfo', 'evaluator', OPTIONAL ),
    )
    __schema_classes__ = {
      u'documentInfo': "documentInfoType_model",
      u'documentUnstructured': "documentUnstructuredString_model",
      u'evaluationTool': "targetResourceInfoType_model",
      u'organizationInfo': "organizationInfoType_model",
      u'personInfo': "personInfoType_model",
    }

    evaluated = MetaBooleanField(
      verbose_name='Evaluated',
      help_text='Indicates whether the tool or service has been evaluate' \
      'd',
      )

    evaluationLevel = MultiSelectField(
      verbose_name='Evaluation level',
      help_text='Indicates the evaluation level',
      blank=True,
      max_length=1 + len(TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONLEVEL_CHOICES['choices']) / 4,
      choices=TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONLEVEL_CHOICES['choices'],
      )

    evaluationType = MultiSelectField(
      verbose_name='Evaluation type',
      help_text='Indicates the evaluation type',
      blank=True,
      max_length=1 + len(TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONTYPE_CHOICES['choices']) / 4,
      choices=TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONTYPE_CHOICES['choices'],
      )

    evaluationCriteria = MultiSelectField(
      verbose_name='Evaluation criteria',
      help_text='Defines the criteria of the evaluation of a tool',
      blank=True,
      max_length=1 + len(TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONCRITERIA_CHOICES['choices']) / 4,
      choices=TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONCRITERIA_CHOICES['choices'],
      )

    evaluationMeasure = MultiSelectField(
      verbose_name='Evaluation measure',
      help_text='Defines whether the evaluation measure is human or auto' \
      'matic',
      blank=True,
      max_length=1 + len(TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONMEASURE_CHOICES['choices']) / 4,
      choices=TOOLSERVICEEVALUATIONINFOTYPE_EVALUATIONMEASURE_CHOICES['choices'],
      )

    evaluationReport = models.ManyToManyField("documentationInfoType_model",
      verbose_name='Evaluation report',
      help_text='A bibliographical record of or link to a report describ' \
      'ing the evaluation process, tool, method etc. of the tool or serv' \
      'ice',
      blank=True, null=True, related_name="evaluationReport_%(class)s_related", )

    evaluationTool = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Evaluation tool',
      help_text='The name or id or url of the tool used for the evaluati' \
      'on of the tool or service',
      blank=True, null=True, related_name="evaluationTool_%(class)s_related", )

    evaluationDetails = XmlCharField(
      verbose_name='Evaluation details',
      help_text='Provides further information on the evaluation process ' \
      'of a tool or service',
      blank=True, max_length=500, )

    evaluator = models.ManyToManyField("actorInfoType_model",
      verbose_name='Evaluator',
      help_text='Groups information on person or organization that evalu' \
      'ated the tool or service',
      blank=True, null=True, related_name="evaluator_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

TOOLSERVICEOPERATIONINFOTYPE_OPERATINGSYSTEM_CHOICES = _make_choices_from_list([
  u'os-independent', u'windows', u'linux', u'unix', u'mac-OS',
  u'googleChromeOS',u'iOS', u'android', u'other', u'',
])

# pylint: disable-msg=C0103
class toolServiceOperationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Tool service operation"


    __schema_name__ = 'toolServiceOperationInfoType'
    __schema_fields__ = (
      ( u'operatingSystem', u'operatingSystem', OPTIONAL ),
      ( u'runningEnvironmentInfo', u'runningEnvironmentInfo', RECOMMENDED ),
      ( u'runningTime', u'runningTime', OPTIONAL ),
    )
    __schema_classes__ = {
      u'runningEnvironmentInfo': "runningEnvironmentInfoType_model",
    }

    operatingSystem = MultiSelectField(
      verbose_name='Operating system',
      help_text='The operating system on which the tool will be running',
      blank=True,
      max_length=1 + len(TOOLSERVICEOPERATIONINFOTYPE_OPERATINGSYSTEM_CHOICES['choices']) / 4,
      choices=TOOLSERVICEOPERATIONINFOTYPE_OPERATINGSYSTEM_CHOICES['choices'],
      )

    runningEnvironmentInfo = models.OneToOneField("runningEnvironmentInfoType_model",
      verbose_name='Running environment',
      help_text='Groups together information on the running environment ' \
      'of a tool or a language description',
      blank=True, null=True, on_delete=models.SET_NULL, )

    runningTime = XmlCharField(
      verbose_name='Running time',
      help_text='Gives information on the running time of a tool or serv' \
      'ice',
      blank=True, max_length=100, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class toolServiceCreationInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Tool service creation"


    __schema_name__ = 'toolServiceCreationInfoType'
    __schema_fields__ = (
      ( u'implementationLanguage', u'implementationLanguage', RECOMMENDED ),
      ( u'formalism', u'formalism', OPTIONAL ),
      ( u'originalSource', u'originalSource', OPTIONAL ),
      ( u'creationDetails', u'creationDetails', OPTIONAL ),
    )
    __schema_classes__ = {
      u'originalSource': "targetResourceInfoType_model",
    }

    implementationLanguage = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=41, max_length=100),
      verbose_name='Implementation language',
      help_text='The programming languages needed for allowing user cont' \
      'ributions, or for running the tools, in case no executables are a' \
      'vailable',
      blank=True, validators=[validate_matches_xml_char_production], )

    formalism = MultiTextField(max_length=100, widget=MultiFieldWidget(widget_id=42, max_length=100),
      verbose_name='Formalism',
      help_text='Reference (name, bibliographic reference or link to url' \
      ') for the formalism used for the creation/enrichment of the resou' \
      'rce (grammar or tool/service)',
      blank=True, validators=[validate_matches_xml_char_production], )

    originalSource = models.ManyToManyField("targetResourceInfoType_model",
      verbose_name='Original source',
      help_text='The name, the identifier or the url of thethe original ' \
      'resources that were at the base of the creation process of the re' \
      'source',
      blank=True, null=True, related_name="originalSource_%(class)s_related", )

    creationDetails = XmlCharField(
      verbose_name='Creation details',
      help_text='Provides additional information on the creation of a to' \
      'ol or service',
      blank=True, max_length=500, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class resourceComponentTypeType_model(SubclassableModel):

    __schema_name__ = 'SUBCLASSABLE'

    class Meta:
        verbose_name = "Resource component"


LEXICALCONCEPTUALRESOURCEINFOTYPE_LEXICALCONCEPTUALRESOURCETYPE_CHOICES = _make_choices_from_list([
  u'wordList', u'computationalLexicon', u'ontology', u'wordnet',
  u'thesaurus',u'framenet', u'terminologicalResource',
  u'machineReadableDictionary',u'lexicon', u'other',
])

# pylint: disable-msg=C0103
class lexicalConceptualResourceInfoType_model(resourceComponentTypeType_model):

    class Meta:
        verbose_name = "Lexical conceptual resource"


    __schema_name__ = 'lexicalConceptualResourceInfoType'
    __schema_fields__ = (
      ( u'resourceType', u'resourceType', REQUIRED ),
      ( u'lexicalConceptualResourceType', u'lexicalConceptualResourceType', REQUIRED ),
      ( u'lexicalConceptualResourceEncodingInfo', u'lexicalConceptualResourceEncodingInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', OPTIONAL ),
      ( u'lexicalConceptualResourceMediaType', u'lexicalConceptualResourceMediaType', REQUIRED ),
    )
    __schema_classes__ = {
      u'creationInfo': "creationInfoType_model",
      u'lexicalConceptualResourceEncodingInfo': "lexicalConceptualResourceEncodingInfoType_model",
      u'lexicalConceptualResourceMediaType': "lexicalConceptualResourceMediaTypeType_model",
    }

    resourceType = XmlCharField(
      verbose_name='Resource type',
      help_text='Specifies the type of the resource being described',
      default="lexicalConceptualResource", editable=False, max_length=1000, )

    lexicalConceptualResourceType = models.CharField(
      verbose_name='Lexical conceptual resource type',
      help_text='Specifies the subtype of lexicalConceptualResource',

      max_length=LEXICALCONCEPTUALRESOURCEINFOTYPE_LEXICALCONCEPTUALRESOURCETYPE_CHOICES['max_length'],
      choices=LEXICALCONCEPTUALRESOURCEINFOTYPE_LEXICALCONCEPTUALRESOURCETYPE_CHOICES['choices'],
      )

    lexicalConceptualResourceEncodingInfo = models.OneToOneField("lexicalConceptualResourceEncodingInfoType_model",
      verbose_name='Lexical / Conceptual resource encoding',
      help_text='Groups all information regarding the contents of lexica' \
      'l/conceptual resources',
      blank=True, null=True, on_delete=models.SET_NULL, )

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    lexicalConceptualResourceMediaType = models.OneToOneField("lexicalConceptualResourceMediaTypeType_model",
      verbose_name='Media type component of lexical / conceptual resource',
      help_text='Restriction of mediaType for lexicalConceptualResources' \
      '',
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['lexicalConceptualResourceType', ]
        formatstring = u'lexicalConceptualResource ({})'
        return self.unicode_(formatstring, formatargs)

LANGUAGEDESCRIPTIONINFOTYPE_LANGUAGEDESCRIPTIONTYPE_CHOICES = _make_choices_from_list([
  u'grammar', u'other',
])

# pylint: disable-msg=C0103
class languageDescriptionInfoType_model(resourceComponentTypeType_model):

    class Meta:
        verbose_name = "Language description"


    __schema_name__ = 'languageDescriptionInfoType'
    __schema_fields__ = (
      ( u'resourceType', u'resourceType', REQUIRED ),
      ( u'languageDescriptionType', u'languageDescriptionType', REQUIRED ),
      ( u'languageDescriptionEncodingInfo', u'languageDescriptionEncodingInfo', RECOMMENDED ),
      ( u'languageDescriptionOperationInfo', u'languageDescriptionOperationInfo', OPTIONAL ),
      ( u'languageDescriptionPerformanceInfo', u'languageDescriptionPerformanceInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'languageDescriptionMediaType', u'languageDescriptionMediaType', REQUIRED ),
    )
    __schema_classes__ = {
      u'creationInfo': "creationInfoType_model",
      u'languageDescriptionEncodingInfo': "languageDescriptionEncodingInfoType_model",
      u'languageDescriptionMediaType': "languageDescriptionMediaTypeType_model",
      u'languageDescriptionOperationInfo': "languageDescriptionOperationInfoType_model",
      u'languageDescriptionPerformanceInfo': "languageDescriptionPerformanceInfoType_model",
    }

    resourceType = XmlCharField(
      verbose_name='Resource type',
      help_text='Specifies the type of the resource being described',
      default="languageDescription", editable=False, max_length=30, )

    languageDescriptionType = models.CharField(
      verbose_name='Language description type',
      help_text='The type of the language description',

      max_length=30,
      choices=sorted(LANGUAGEDESCRIPTIONINFOTYPE_LANGUAGEDESCRIPTIONTYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    languageDescriptionEncodingInfo = models.OneToOneField("languageDescriptionEncodingInfoType_model",
      verbose_name='Language description encoding',
      help_text='Groups together information on the contents of the Lang' \
      'uageDescriptions',
      blank=True, null=True, on_delete=models.SET_NULL, )

    languageDescriptionOperationInfo = models.OneToOneField("languageDescriptionOperationInfoType_model",
      verbose_name='Language description operation',
      help_text='Groups together information on the operation requiremen' \
      'ts of the Language Descriptions',
      blank=True, null=True, on_delete=models.SET_NULL, )

    languageDescriptionPerformanceInfo = models.OneToOneField("languageDescriptionPerformanceInfoType_model",
      verbose_name='Language description performance',
      help_text='Groups together information on the performance of the L' \
      'anguage Descriptions',
      blank=True, null=True, on_delete=models.SET_NULL, )

    creationInfo = models.OneToOneField("creationInfoType_model",
      verbose_name='Creation',
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    languageDescriptionMediaType = models.OneToOneField("languageDescriptionMediaTypeType_model",
      verbose_name='Media type component of language description',
      help_text='Groups information on the media type-specific component' \
      's for language descriptions',
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['languageDescriptionType', ]
        formatstring = u'languageDescription ({})'
        return self.unicode_(formatstring, formatargs)

TOOLSERVICEINFOTYPE_TOOLSERVICETYPE_CHOICES = _make_choices_from_list([
  u'tool', u'service', u'platform', u'suiteOfTools', u'infrastructure',
  u'architecture',u'nlpDevelopmentEnvironment', u'other',
])

TOOLSERVICEINFOTYPE_TOOLSERVICESUBTYPE_CHOICES = _make_choices_from_list([
  u'alignment', u'annotation', u'avatarSynthesis',
  u'bilingualLexiconInduction',u'contradictionDetection',
  u'coreferenceResolution',u'dependencyParsing',
  u'derivationalMorphologicalAnalysis',u'discourseAnalysis',
  u'documentClassification',u'emotionGeneration', u'emotionRecognition',
  u'entityMentionRecognition',u'eventExtraction', u'expressionRecognition',
  u'faceRecognition',u'faceVerification', u'humanoidAgentSynthesis',
  u'informationExtraction',u'informationRetrieval',
  u'intra-documentCoreferenceResolution',u'knowledgeDiscovery',
  u'knowledgeRepresentation',u'languageIdentification',
  u'languageModelling',u'languageModelsTraining', u'lemmatization',
  u'lexiconAccess',u'lexiconAcquisitionFromCorpora', u'lexiconEnhancement',
  u'lexiconExtractionFromLexica',u'lexiconFormatConversion',
  u'lexiconVisualization',u'linguisticResearch', u'lipTrackingAnalysis',
  u'machineTranslation',u'morphologicalAnalysis',
  u'morphosyntacticAnnotation-bPosTagging',
  u'morphosyntacticAnnotation-posTagging',u'multimediaDevelopment',
  u'multimediaDocumentProcessing',u'namedEntityRecognition',
  u'naturalLanguageGeneration',u'naturalLanguageUnderstanding',
  u'opinionMining',u'other', u'personIdentification', u'personRecognition',
  u'persuasiveExpressionMining',u'phraseAlignment', u'qualitativeAnalysis',
  u'questionAnswering',u'questionAnswering',
  u'readingAndWritingAidApplications',u'semanticRoleLabelling',
  u'semanticWeb',u'sentenceAlignment', u'sentenceSplitting',
  u'sentimentAnalysis',u'shallowParsing', u'signLanguageGeneration',
  u'signLanguageRecognition',u'speakerIdentification',
  u'speakerVerification',u'speechAnalysis', u'speechAssistedVideoControl',
  u'speechLipsCorrelationAnalysis',u'speechRecognition', u'speechSynthesis',
  u'speechToSpeechTranslation',u'speechUnderstanding',
  u'speechVerification',u'spellChecking', u'spokenDialogueSystems',
  u'summarization',u'talkingHeadSynthesis',
  u'temporalExpressionRecognition',u'terminologyExtraction',
  u'textCategorisation',u'textGeneration', u'textMining',
  u'textToSpeechSynthesis',u'textualEntailment', u'tokenization',
  u'tokenizationAndSentenceSplitting',u'topicDetection_Tracking',
  u'userAuthentication',u'visualSceneUnderstanding', u'voiceControl',
  u'wordAlignment',u'wordSenseDisambiguation',
])

# pylint: disable-msg=C0103
class toolServiceInfoType_model(resourceComponentTypeType_model):

    class Meta:
        verbose_name = "Tool service"


    __schema_name__ = 'toolServiceInfoType'
    __schema_fields__ = (
      ( u'resourceType', u'resourceType', REQUIRED ),
      ( u'toolServiceType', u'toolServiceType', REQUIRED ),
      ( u'toolServiceSubtype', u'toolServiceSubtype', OPTIONAL ),
      ( u'languageDependent', u'languageDependent', REQUIRED ),
      ( u'inputInfo', u'inputInfo', RECOMMENDED ),
      ( u'outputInfo', u'outputInfo', RECOMMENDED ),
      ( u'toolServiceOperationInfo', u'toolServiceOperationInfo', RECOMMENDED ),
      ( u'toolServiceEvaluationInfo', u'toolServiceEvaluationInfo', RECOMMENDED ),
      ( u'toolServiceCreationInfo', u'toolServiceCreationInfo', OPTIONAL ),
    )
    __schema_classes__ = {
      u'inputInfo': "inputInfoType_model",
      u'outputInfo': "outputInfoType_model",
      u'toolServiceCreationInfo': "toolServiceCreationInfoType_model",
      u'toolServiceEvaluationInfo': "toolServiceEvaluationInfoType_model",
      u'toolServiceOperationInfo': "toolServiceOperationInfoType_model",
    }

    resourceType = XmlCharField(
      verbose_name='Resource type',
      help_text='The type of the resource that a tool or service takes a' \
      's input or produces as output',
      default="toolService", editable=False, max_length=1000, )

    toolServiceType = models.CharField(
      verbose_name='Tool / Service type',
      help_text='Specifies the type of the tool or service',

      max_length=100,
      choices=sorted(TOOLSERVICEINFOTYPE_TOOLSERVICETYPE_CHOICES['choices'],
                     key=lambda choice: choice[1].lower()),
      )

    toolServiceSubtype = MultiSelectField(
      verbose_name='Subtype of tool / service',
      help_text='Specifies the subtype of tool or service',
      blank=True,
      max_length=1 + len(TOOLSERVICEINFOTYPE_TOOLSERVICESUBTYPE_CHOICES['choices']) / 4,
      choices=TOOLSERVICEINFOTYPE_TOOLSERVICESUBTYPE_CHOICES['choices'],
      )

    languageDependent = MetaBooleanField(
      verbose_name='Language dependent',
      help_text='Indicates whether the operation of the tool or service ' \
      'is language dependent or not',
      )

    inputInfo = models.OneToOneField("inputInfoType_model",
      verbose_name='Input',
      help_text='Groups together information on the requirements set on ' \
      'the input resource of a tool or service',
      blank=True, null=True, on_delete=models.SET_NULL, )

    outputInfo = models.OneToOneField("outputInfoType_model",
      verbose_name='Output',
      help_text='Groups together information on the requirements set on ' \
      'the output of a tool or service',
      blank=True, null=True, on_delete=models.SET_NULL, )

    toolServiceOperationInfo = models.OneToOneField("toolServiceOperationInfoType_model",
      verbose_name='Tool / Service operation',
      help_text='Groups together information on the operation of a tool ' \
      'or service',
      blank=True, null=True, on_delete=models.SET_NULL, )

    toolServiceEvaluationInfo = models.OneToOneField("toolServiceEvaluationInfoType_model",
      verbose_name='Tool / Service evaluation',
      help_text='Groups together information on the evaluation status of' \
      ' a tool or service',
      blank=True, null=True, on_delete=models.SET_NULL, )

    toolServiceCreationInfo = models.OneToOneField("toolServiceCreationInfoType_model",
      verbose_name='Tool / Service creation',
      help_text='Groups together information on the creation of a tool o' \
      'r service',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['toolServiceType', ]
        formatstring = u'toolService ({})'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class corpusInfoType_model(resourceComponentTypeType_model):

    class Meta:
        verbose_name = "Corpus"
        verbose_name_plural = "Corpora"


    __schema_name__ = 'corpusInfoType'
    __schema_fields__ = (
      ( u'resourceType', u'resourceType', REQUIRED ),
      ( u'corpusMediaType', u'corpusMediaType', REQUIRED ),
    )
    __schema_classes__ = {
      u'corpusMediaType': "corpusMediaTypeType_model",
    }

    resourceType = XmlCharField(
      verbose_name='Resource type',
      help_text='Specifies the type of the resource being described',
      default="corpus", editable=False, max_length=1000, )

    corpusMediaType = models.OneToOneField("corpusMediaTypeType_model",
      verbose_name='Media type component of corpus',
      help_text='Used to specify the media type specific to corpora and ' \
      'group together the relevant information',
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['corpusMediaType/corpusTextInfo', 'corpusMediaType/corpusAudioInfo', 'corpusMediaType/corpusVideoInfo', 'corpusMediaType/corpusImageInfo', 'corpusMediaType/corpusTextNumericalInfo', 'corpusMediaType/corpusTextNgramInfo', ]
        formatstring = u'corpus ({} {} {} {} {} {})'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class corpusMediaTypeType_model(SchemaModel):

    class Meta:
        verbose_name = "Media type component of corpus"


    __schema_name__ = 'corpusMediaTypeType'
    __schema_fields__ = (
      ( u'corpusTextInfo', u'corpustextinfotype_model_set', RECOMMENDED ),
      ( u'corpusAudioInfo', u'corpusAudioInfo', RECOMMENDED ),
      ( u'corpusVideoInfo', u'corpusvideoinfotype_model_set', RECOMMENDED ),
      ( u'corpusImageInfo', u'corpusImageInfo', RECOMMENDED ),
      ( u'corpusTextNumericalInfo', u'corpusTextNumericalInfo', RECOMMENDED ),
      ( u'corpusTextNgramInfo', u'corpusTextNgramInfo', RECOMMENDED ),
    )
    __schema_classes__ = {
      u'corpusAudioInfo': "corpusAudioInfoType_model",
      u'corpusImageInfo': "corpusImageInfoType_model",
      u'corpusTextInfo': "corpusTextInfoType_model",
      u'corpusTextNgramInfo': "corpusTextNgramInfoType_model",
      u'corpusTextNumericalInfo': "corpusTextNumericalInfoType_model",
      u'corpusVideoInfo': "corpusVideoInfoType_model",
    }

    # OneToMany field: corpusTextInfo

    corpusAudioInfo = models.OneToOneField("corpusAudioInfoType_model",
      verbose_name='Corpus audio component',
      help_text='Groups together information on the audio module of a co' \
      'rpus',
      blank=True, null=True, on_delete=models.SET_NULL, )

    # OneToMany field: corpusVideoInfo

    corpusImageInfo = models.OneToOneField("corpusImageInfoType_model",
      verbose_name='Corpus image component',
      help_text='Groups together information on the image component of a' \
      ' resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    corpusTextNumericalInfo = models.OneToOneField("corpusTextNumericalInfoType_model",
      verbose_name='Corpus numerical text component',
      help_text='Groups together information on the textNumerical compon' \
      'ent of a corpus. It is used basically for the textual representat' \
      'ion of measurements and observations linked to sensorimotor recor' \
      'dings',
      blank=True, null=True, on_delete=models.SET_NULL, )

    corpusTextNgramInfo = models.OneToOneField("corpusTextNgramInfoType_model",
      verbose_name='Corpus n-gram text component',
      help_text='Groups together information required for n-gram resourc' \
      'es; information can be provided both as regards features drawn fr' \
      'om the source corpus (e.g. language coverage, size, format, domai' \
      'ns etc.) and features pertaining to the n-gram output itself (e.g' \
      '. range of n-grams, type of item included, etc.)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

DYNAMICELEMENTINFOTYPE_BODYPARTS_CHOICES = _make_choices_from_list([
  u'arms', u'face', u'feet', u'hands', u'head', u'legs', u'mouth',
  u'wholeBody',u'none',
])

# pylint: disable-msg=C0103
class dynamicElementInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Dynamic element"


    __schema_name__ = 'dynamicElementInfoType'
    __schema_fields__ = (
      ( u'typeOfElement', u'typeOfElement', OPTIONAL ),
      ( u'bodyParts', u'bodyParts', OPTIONAL ),
      ( u'distractors', u'distractors', OPTIONAL ),
      ( u'interactiveMedia', u'interactiveMedia', OPTIONAL ),
      ( u'faceViews', u'faceViews', OPTIONAL ),
      ( u'faceExpressions', u'faceExpressions', OPTIONAL ),
      ( u'bodyMovement', u'bodyMovement', OPTIONAL ),
      ( u'gestures', u'gestures', OPTIONAL ),
      ( u'handArmMovement', u'handArmMovement', OPTIONAL ),
      ( u'handManipulation', u'handManipulation', OPTIONAL ),
      ( u'headMovement', u'headMovement', OPTIONAL ),
      ( u'eyeMovement', u'eyeMovement', OPTIONAL ),
      ( u'posesPerSubject', u'posesPerSubject', OPTIONAL ),
    )

    typeOfElement = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=43, max_length=1000),
      verbose_name='Type of element',
      help_text='The type of objects or people that represented in the v' \
      'ideo or image part of the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    bodyParts = MultiSelectField(
      verbose_name='Body parts',
      help_text='The body parts visible in the video or image part of th' \
      'e resource',
      blank=True,
      max_length=1 + len(DYNAMICELEMENTINFOTYPE_BODYPARTS_CHOICES['choices']) / 4,
      choices=DYNAMICELEMENTINFOTYPE_BODYPARTS_CHOICES['choices'],
      )

    distractors = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=44, max_length=1000),
      verbose_name='Distractors',
      help_text='Any distractors visible in the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    interactiveMedia = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=45, max_length=1000),
      verbose_name='Interactive media',
      help_text='Any interactive media visible in the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    faceViews = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=46, max_length=1000),
      verbose_name='Face views',
      help_text='Indicates the view of the face(s) that appear in the vi' \
      'deo or on the image part of the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    faceExpressions = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=47, max_length=1000),
      verbose_name='Face expressions',
      help_text='Indicates the facial expressions visible in the resourc' \
      'e',
      blank=True, validators=[validate_matches_xml_char_production], )

    bodyMovement = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=48, max_length=1000),
      verbose_name='Body movement',
      help_text='Indicates the body parts that move in the video part of' \
      ' the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    gestures = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=49, max_length=1000),
      verbose_name='Gestures',
      help_text='Indicates the type of gestures visible in the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    handArmMovement = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=50, max_length=1000),
      verbose_name='Hand / Arm movement',
      help_text='Indicates the movement of hands and/or arms visible in ' \
      'the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    handManipulation = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=51, max_length=1000),
      verbose_name='Hand manipulation',
      help_text='Gives information on the manipulation of objects by han' \
      'd',
      blank=True, validators=[validate_matches_xml_char_production], )

    headMovement = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=52, max_length=1000),
      verbose_name='Head movement',
      help_text='Indicates the movements of the head visible in the reso' \
      'urce',
      blank=True, validators=[validate_matches_xml_char_production], )

    eyeMovement = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=53, max_length=1000),
      verbose_name='Eye movement',
      help_text='Indicates the movement of the eyes visible in the resou' \
      'rce',
      blank=True, validators=[validate_matches_xml_char_production], )

    posesPerSubject = models.IntegerField(
      verbose_name='Poses per subject',
      help_text='The number of poses per subject that participates in th' \
      'e video part of the resource',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

STATICELEMENTINFOTYPE_BODYPARTS_CHOICES = _make_choices_from_list([
  u'arms', u'face', u'feet', u'hands', u'head', u'legs', u'mouth',
  u'wholeBody',u'none',
])

# pylint: disable-msg=C0103
class staticElementInfoType_model(SchemaModel):

    class Meta:
        verbose_name = "Static element"


    __schema_name__ = 'staticElementInfoType'
    __schema_fields__ = (
      ( u'typeOfElement', u'typeOfElement', OPTIONAL ),
      ( u'bodyParts', u'bodyParts', OPTIONAL ),
      ( u'faceViews', u'faceViews', RECOMMENDED ),
      ( u'faceExpressions', u'faceExpressions', RECOMMENDED ),
      ( u'artifactParts', u'artifactParts', OPTIONAL ),
      ( u'landscapeParts', u'landscapeParts', OPTIONAL ),
      ( u'personDescription', u'personDescription', OPTIONAL ),
      ( u'thingDescription', u'thingDescription', OPTIONAL ),
      ( u'organizationDescription', u'organizationDescription', OPTIONAL ),
      ( u'eventDescription', u'eventDescription', OPTIONAL ),
    )

    typeOfElement = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=54, max_length=1000),
      verbose_name='Type of element',
      help_text='The type of objects or people that represented in the v' \
      'ideo or image part of the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    bodyParts = MultiSelectField(
      verbose_name='Body parts',
      help_text='The body parts visible in the video or image part of th' \
      'e resource',
      blank=True,
      max_length=1 + len(STATICELEMENTINFOTYPE_BODYPARTS_CHOICES['choices']) / 4,
      choices=STATICELEMENTINFOTYPE_BODYPARTS_CHOICES['choices'],
      )

    faceViews = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=55, max_length=1000),
      verbose_name='Face views',
      help_text='Indicates the view of the face(s) that appear in the vi' \
      'deo or on the image part of the resource',
      blank=True, validators=[validate_matches_xml_char_production], )

    faceExpressions = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=56, max_length=1000),
      verbose_name='Face expressions',
      help_text='Indicates the facial expressions visible in the resourc' \
      'e',
      blank=True, validators=[validate_matches_xml_char_production], )

    artifactParts = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=57, max_length=1000),
      verbose_name='Artifact parts',
      help_text='Indicates the parts of the artifacts represented in the' \
      ' image corpus',
      blank=True, validators=[validate_matches_xml_char_production], )

    landscapeParts = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=58, max_length=1000),
      verbose_name='Landscape parts',
      help_text='landscape parts represented in the image corpus',
      blank=True, validators=[validate_matches_xml_char_production], )

    personDescription = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=59, max_length=1000),
      verbose_name='Description of person',
      help_text='Provides descriptive features for the persons represent' \
      'ed in the image corpus',
      blank=True, validators=[validate_matches_xml_char_production], )

    thingDescription = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=60, max_length=1000),
      verbose_name='Description of thing',
      help_text='Provides description of the things represented in the i' \
      'mage corpus',
      blank=True, validators=[validate_matches_xml_char_production], )

    organizationDescription = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=61, max_length=1000),
      verbose_name='Description of organization',
      help_text='Provides description of the organizations that may appe' \
      'ar in the image corpus',
      blank=True, validators=[validate_matches_xml_char_production], )

    eventDescription = MultiTextField(max_length=1000, widget=MultiFieldWidget(widget_id=62, max_length=1000),
      verbose_name='Description of event',
      help_text='Provides description of any events represented in the i' \
      'mage corpus',
      blank=True, validators=[validate_matches_xml_char_production], )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class languageDescriptionMediaTypeType_model(SchemaModel):

    class Meta:
        verbose_name = "Language description media"


    __schema_name__ = 'languageDescriptionMediaTypeType'
    __schema_fields__ = (
      ( u'languageDescriptionTextInfo', u'languageDescriptionTextInfo', RECOMMENDED ),
      ( u'languageDescriptionVideoInfo', u'languageDescriptionVideoInfo', OPTIONAL ),
      ( u'languageDescriptionImageInfo', u'languageDescriptionImageInfo', OPTIONAL ),
    )
    __schema_classes__ = {
      u'languageDescriptionImageInfo': "languageDescriptionImageInfoType_model",
      u'languageDescriptionTextInfo': "languageDescriptionTextInfoType_model",
      u'languageDescriptionVideoInfo': "languageDescriptionVideoInfoType_model",
    }

    languageDescriptionTextInfo = models.OneToOneField("languageDescriptionTextInfoType_model",
      verbose_name='Language description text component',
      help_text='Groups together all information relevant to the text mo' \
      'dule of a language description (e.g. format, languages, size etc.' \
      '); it is obligatory for all language descriptions',
      blank=True, null=True, on_delete=models.SET_NULL, )

    languageDescriptionVideoInfo = models.OneToOneField("languageDescriptionVideoInfoType_model",
      verbose_name='Language description video component',
      help_text='Groups together all information relevant to the video p' \
      'arts of a language description (e.g. format, languages, size etc.' \
      '), if there are any (e.g. for sign language grammars)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    languageDescriptionImageInfo = models.OneToOneField("languageDescriptionImageInfoType_model",
      verbose_name='Language description image component',
      help_text='Groups together all information relevant to the image m' \
      'odule of a language description (e.g. format, languages, size etc' \
      '.), if there are any (e.g. for sign language grammars)',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class lexicalConceptualResourceMediaTypeType_model(SchemaModel):

    class Meta:
        verbose_name = "Lexical conceptual resource media"


    __schema_name__ = 'lexicalConceptualResourceMediaTypeType'
    __schema_fields__ = (
      ( u'lexicalConceptualResourceTextInfo', u'lexicalConceptualResourceTextInfo', RECOMMENDED ),
      ( u'lexicalConceptualResourceAudioInfo', u'lexicalConceptualResourceAudioInfo', OPTIONAL ),
      ( u'lexicalConceptualResourceVideoInfo', u'lexicalConceptualResourceVideoInfo', OPTIONAL ),
      ( u'lexicalConceptualResourceImageInfo', u'lexicalConceptualResourceImageInfo', OPTIONAL ),
    )
    __schema_classes__ = {
      u'lexicalConceptualResourceAudioInfo': "lexicalConceptualResourceAudioInfoType_model",
      u'lexicalConceptualResourceImageInfo': "lexicalConceptualResourceImageInfoType_model",
      u'lexicalConceptualResourceTextInfo': "lexicalConceptualResourceTextInfoType_model",
      u'lexicalConceptualResourceVideoInfo': "lexicalConceptualResourceVideoInfoType_model",
    }

    lexicalConceptualResourceTextInfo = models.OneToOneField("lexicalConceptualResourceTextInfoType_model",
      verbose_name='Lexical / Conceptual resource text component',
      help_text='Groups information on the textual part of the lexical/c' \
      'onceptual resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    lexicalConceptualResourceAudioInfo = models.OneToOneField("lexicalConceptualResourceAudioInfoType_model",
      verbose_name='Lexical / Conceptual resource audio component',
      help_text='Groups information on the audio part of the lexical/con' \
      'ceptual resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    lexicalConceptualResourceVideoInfo = models.OneToOneField("lexicalConceptualResourceVideoInfoType_model",
      verbose_name='Lexical / Conceptual resource video component',
      help_text='Groups information on the video part of the lexical con' \
      'ceptual resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    lexicalConceptualResourceImageInfo = models.OneToOneField("lexicalConceptualResourceImageInfoType_model",
      verbose_name='Lexical / Conceptual resource image component',
      help_text='Groups information on the image part of the lexical/con' \
      'ceptual resource',
      blank=True, null=True, on_delete=models.SET_NULL, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class documentUnstructuredString_model(InvisibleStringModel, documentationInfoType_model):
    def save(self, *args, **kwargs):
        """
        Prevents id collisions for documentationInfoType_model sub classes.
        """
        # pylint: disable-msg=E0203
        if not self.id:
            # pylint: disable-msg=W0201
            self.id = _compute_documentationInfoType_key()
        super(documentUnstructuredString_model, self).save(*args, **kwargs)
