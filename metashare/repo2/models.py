# pylint: disable-msg=C0302
import logging
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from xml.etree.ElementTree import tostring

# pylint: disable-msg=W0611
from metashare.repo2.supermodel import SchemaModel, SubclassableModel, \
  _make_choices_from_list, InvisibleStringModel, pretty_xml, \
  REQUIRED, OPTIONAL, RECOMMENDED
from metashare.repo2.editor.widgets import MultiFieldWidget
from metashare.repo2.fields import MultiTextField, MetaBooleanField, \
  MultiSelectField

from metashare.storage.models import StorageObject

from metashare.settings import DJANGO_BASE, LOG_LEVEL, LOG_HANDLER

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repo2.models')
LOGGER.addHandler(LOG_HANDLER)

EMAILADDRESS_VALIDATOR = RegexValidator(r'[^@]+@[^\.]+\..+',
  'Not a valid emailAddress value.', ValidationError)

HTTPURI_VALIDATOR = RegexValidator(r'(https?://.*|ftp://.*|www*)',
  'Not a valid httpURI value.', ValidationError)


# pylint: disable-msg=C0103
class resourceInfoType_model(SchemaModel):
    """
    Groups together all information required for the description of
    language resources
    """

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
      help_text='Groups information on the person(s) that is responsible' \
      ' for giving information for the resource',
      related_name="contactPerson_%(class)s_related", )

    metadataInfo = models.OneToOneField("metadataInfoType_model", 
      verbose_name='Metadata', 
      help_text='Groups information on the metadata record itself',
      )

    versionInfo = models.OneToOneField("versionInfoType_model", 
      verbose_name='Version', 
      help_text='Groups information on a specific version or release of ' \
      'the resource',
      blank=True, null=True, )

    # OneToMany field: validationInfo

    usageInfo = models.OneToOneField("usageInfoType_model", 
      verbose_name='Usage', 
      help_text='Groups information on usage of the resource (both inten' \
      'ded and actual use)',
      blank=True, null=True, )

    resourceDocumentationInfo = models.OneToOneField("resourceDocumentationInfoType_model", 
      verbose_name='Resource documentation', 
      help_text='Groups together information on any document describing ' \
      'the resource',
      blank=True, null=True, )

    resourceCreationInfo = models.OneToOneField("resourceCreationInfoType_model", 
      verbose_name='Resource creation', 
      help_text='Groups information on the creation procedure of a resou' \
      'rce',
      blank=True, null=True, )

    # OneToMany field: relationInfo

    resourceComponentType = models.OneToOneField("resourceComponentTypeType_model", 
      verbose_name='Resource component', 
      help_text='Used for distinguishing between resource types',
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['identificationInfo/resourceName', ]
        formatstring = u'{}'
        return self.unicode_(formatstring, formatargs)


    owners = models.ManyToManyField(User, blank=True, null=True)

    storage_object = models.ForeignKey(StorageObject, blank=True, null=True,
      unique=True)

    def save(self, *args, **kwargs):
        """
        Overrides the predefined save() method to ensure that a corresponding
        StorageObject instance is existing, creating it if missing.  Also, we
        check that the storage object instance is a local master copy.
        """
        # Serialize current object information into XML String.
        try:
            _metadata = pretty_xml(tostring(self.export_to_elementtree()))

        except ValueError:
            _metadata = '<NOT_READY_YET/>'

        # If we have not yet created a StorageObject for this resource, do so.
        if not self.storage_object:
            self.storage_object = StorageObject.objects.create(
              metadata=_metadata)

        # Otherwise, just update the metadata attribute of the StorageObject.
        else:
            # Check that the storage object instance is a local master copy.
            if not self.storage_object.master_copy:
                LOGGER.warning('Trying to modify non master copy {0}, ' \
                  'aborting!'.format(self.storage_object))
                return

            self.storage_object.metadata = _metadata
            self.storage_object.save()

        LOGGER.debug(u"\nMETADATA: {0}\n".format(
          self.storage_object.metadata))

        # Call save() method from super class with all arguments.
        super(resourceInfoType_model, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return '/{0}repo2/browse/{1}/'.format(DJANGO_BASE, self.id)

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
  u'5-grams',u'rules', u'other', 
])

# pylint: disable-msg=C0103
class sizeInfoType_model(SchemaModel):
    """
    Groups information on the size of the resource or of resource parts
    """

    class Meta:
        verbose_name = "Size"

    __schema_name__ = 'sizeInfoType'
    __schema_fields__ = (
      ( u'size', u'size', REQUIRED ),
      ( u'sizeUnit', u'sizeUnit', REQUIRED ),
    )

    size = models.CharField(
      verbose_name='Size', 
      help_text='Specifies the size of the resource with regard to the S' \
      'izeUnit measurement in form of a number',
      max_length=100, )

    sizeUnit = models.CharField(
      verbose_name='Size unit', 
      help_text='Specifies the unit that is used when providing informat' \
      'ion on the size of the resource or of resource parts',
      
      max_length=30,
      choices=SIZEINFOTYPE_SIZEUNIT_CHOICES['choices'],
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['size', 'sizeUnit', ]
        formatstring = u'{} {}'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class identificationInfoType_model(SchemaModel):
    """
    Groups together information needed to identify the resource
    """

    class Meta:
        verbose_name = "Identification"

    __schema_name__ = 'identificationInfoType'
    __schema_fields__ = (
      ( u'resourceName', u'resourceName', REQUIRED ),
      ( u'description', u'description', REQUIRED ),
      ( u'resourceShortName', u'resourceShortName', OPTIONAL ),
      ( u'url', u'url', RECOMMENDED ),
      ( u'metaShareId', u'metaShareId', REQUIRED ),
      ( u'identifier', u'identifier', OPTIONAL ),
    )

    resourceName = MultiTextField(widget = MultiFieldWidget(widget_id=0), 
      verbose_name='Resource name', 
      help_text='The full name by which the resource is known',
      )

    description = MultiTextField(widget = MultiFieldWidget(widget_id=1), 
      verbose_name='Description', 
      help_text='Provides the description of the resource in prose',
      )

    resourceShortName = MultiTextField(widget = MultiFieldWidget(widget_id=2), 
      verbose_name='Resource short name', 
      help_text='The short form (abbreviation, acronym etc.) used to ide' \
      'ntify the resource',
      blank=True)

    url = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=3), 
      verbose_name='Url', validators=[HTTPURI_VALIDATOR], 
      help_text='A URL used as homepage of an entity (e.g. of a person, ' \
      'organization, resource etc.) and/or where an entity (e.g.LR, docu' \
      'ment etc.) is located',
      blank=True, )

    metaShareId = models.CharField(
      verbose_name='Meta share id', 
      help_text='An unambiguous referent to the resource within META-SHA' \
      'RE',
      max_length=100, )

    identifier = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=4), 
      verbose_name='Identifier', 
      help_text='A reference to the resource like a pid or an internal i' \
      'dentifier used by the resource provider; the attribute "type" is ' \
      'obligatorily used for further specification',
      blank=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class versionInfoType_model(SchemaModel):
    """
    Groups information on a specific version or release of the resource
    """

    class Meta:
        verbose_name = "Version"

    __schema_name__ = 'versionInfoType'
    __schema_fields__ = (
      ( u'version', u'version', REQUIRED ),
      ( u'revision', u'revision', OPTIONAL ),
      ( u'lastDateUpdated', u'lastDateUpdated', OPTIONAL ),
      ( u'updateFrequency', u'updateFrequency', OPTIONAL ),
    )

    version = models.CharField(
      verbose_name='Version', 
      help_text='Any string, usually a number, that identifies the versi' \
      'on of a resource',
      max_length=100, )

    revision = models.CharField(
      verbose_name='Revision', 
      help_text='Provides an account of the revisions in free text or a ' \
      'link to a document with revisions',
      blank=True, max_length=500, )

    lastDateUpdated = models.DateField(
      verbose_name='Last date updated', 
      help_text='Date of the last update of the version of the resource',
      blank=True, null=True, )

    updateFrequency = models.CharField(
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
    """
    Groups information on validation of a resource; it can be repeated
    to allow for different validations (e.g. formal validation of
    the whole resource; content validation of one part of the
    resource etc.).
    """

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
      verbose_name='Validation', 
      help_text='Specifies the type of the validation that have been per' \
      'formed',
      blank=True, 
      max_length=20,
      choices=VALIDATIONINFOTYPE_VALIDATIONTYPE_CHOICES['choices'],
      )

    validationMode = models.CharField(
      verbose_name='Validation mode', 
      help_text='Specifies the validation methodology applied',
      blank=True, 
      max_length=20,
      choices=VALIDATIONINFOTYPE_VALIDATIONMODE_CHOICES['choices'],
      )

    validationModeDetails = models.CharField(
      verbose_name='Validation mode details', 
      help_text='Textual field for additional information on validation',
      blank=True, max_length=500, )

    validationExtent = models.CharField(
      verbose_name='Validation extent', 
      help_text='The resource coverage in terms of validated data',
      blank=True, 
      max_length=20,
      choices=VALIDATIONINFOTYPE_VALIDATIONEXTENT_CHOICES['choices'],
      )

    validationExtentDetails = models.CharField(
      verbose_name='Validation extent details', 
      help_text='Provides information on size or other details of partia' \
      'lly validated data; to be used if only part of the resource has b' \
      'een validated and as an alternative to SizeInfo if the validated ' \
      'part cannot be counted otherwise',
      blank=True, max_length=500, )

    sizePerValidation = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per validation', 
      help_text='Specifies the size of the validated part of a resource',
      blank=True, null=True, )

    validationReport = models.OneToOneField("documentationInfoType_model", 
      verbose_name='Validation report', 
      help_text='A short account of the validation details or a link to ' \
      'the validation report',
      blank=True, null=True, )

    validationTool = models.OneToOneField("targetResourceInfoType_model", 
      verbose_name='Validation tool', 
      help_text='The name, the identifier or the url of the tool used fo' \
      'r the validation of the resource',
      blank=True, null=True, )

    validator = models.ManyToManyField("actorInfoType_model", 
      verbose_name='Validator', 
      help_text='Groups information on the person(s) or the organization' \
      '(s) that validated the resource',
      blank=True, null=True, related_name="validator_%(class)s_related", )

    back_to_resourceinfotype_model = models.ForeignKey("resourceInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class resourceCreationInfoType_model(SchemaModel):
    """
    Groups information on the creation procedure of a resource
    """

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
    """
    Groups together information on the resource creation (e.g. for
    corpora, selection of texts/audio files/ video files etc. and
    structural encoding thereof; for lexica, construction of lemma
    list etc.)
    """

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
      choices=CREATIONINFOTYPE_CREATIONMODE_CHOICES['choices'],
      )

    creationModeDetails = models.CharField(
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

# pylint: disable-msg=C0103
class metadataInfoType_model(SchemaModel):
    """
    Groups information on the metadata record itself
    """

    class Meta:
        verbose_name = "Metadata"

    __schema_name__ = 'metadataInfoType'
    __schema_fields__ = (
      ( u'metadataCreationDate', u'metadataCreationDate', REQUIRED ),
      ( u'metadataCreator', u'metadataCreator', OPTIONAL ),
      ( u'source', u'source', OPTIONAL ),
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
      help_text='The date of creation of this metadata description',
      )

    metadataCreator = models.ManyToManyField("personInfoType_model", 
      verbose_name='Metadata creator', 
      help_text='Groups information on the person that created the metad' \
      'ata in META-SHARE editor; to be automatically assigned',
      blank=True, null=True, related_name="metadataCreator_%(class)s_related", )

    source = models.CharField(
      verbose_name='Source', 
      help_text='Refers to the catalogue or repository from which the me' \
      'tadata has been originated',
      blank=True, max_length=500, )

    originalMetadataSchema = models.CharField(
      verbose_name='Original metadata schema', 
      help_text='Refers to the metadata schema originally used for the d' \
      'escription of the resource',
      blank=True, max_length=500, )

    originalMetadataLink = models.CharField(
      verbose_name='Original metadata link', validators=[HTTPURI_VALIDATOR], 
      help_text='A link to the metadata of the original source',
      blank=True, max_length=1000, )

    metadataLanguageName = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=5), 
      verbose_name='Metadata language name', 
      help_text='The name of the language in which the metadata descript' \
      'ion is written according to IETF BCP47',
      blank=True, )

    metadataLanguageId = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=6), 
      verbose_name='Metadata language id', 
      help_text='The identifier of the language in which the metadata de' \
      'scription is written according to IETF BCP47',
      blank=True, )

    metadataLastDateUpdated = models.DateField(
      verbose_name='Metadata last date updated', 
      help_text='The date of the last updating of the metadata record',
      blank=True, null=True, )

    revision = models.CharField(
      verbose_name='Revision', 
      help_text='Provides an account of the revisions in free text or a ' \
      'link to a document with revisions',
      blank=True, max_length=500, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class documentationInfoType_model(SubclassableModel):
    """
    Groups information on the documentation of the resource pointing to
    either structured and unstructured presentation of the relevant
    documents
    """

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
    """
    Groups information on all the documents resporting onvarious aspects
    of the resource (creation, usage etc.), published or
    unpublished; it is used in various places of the metadata schema
    depending on its role (e.g. usage report, validation report,
    annotation manual etc.)
    """

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
      ( u'url', u'url', OPTIONAL ),
      ( u'ISSN', u'ISSN', OPTIONAL ),
      ( u'ISBN', u'ISBN', OPTIONAL ),
      ( u'keywords', u'keywords', OPTIONAL ),
      ( u'documentLanguageName', u'documentLanguageName', OPTIONAL ),
      ( u'documentLanguageId', u'documentLanguageId', OPTIONAL ),
    )

    documentType = models.CharField(
      verbose_name='Document', 
      help_text='Specifies the type of the document provided with or rel' \
      'ated to the resource',
      
      max_length=30,
      choices=DOCUMENTINFOTYPE_DOCUMENTTYPE_CHOICES['choices'],
      )

    title = MultiTextField(widget = MultiFieldWidget(widget_id=7), 
      verbose_name='Title', 
      help_text='The title of the document reporting on the resource',
      )

    author = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=8), 
      verbose_name='Author', 
      help_text='The name(s) of the author(s), in the format described i' \
      'n the document',
      blank=True, )

    editor = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=9), 
      verbose_name='Editor', 
      help_text='The name of the editor as mentioned in the document',
      blank=True, )

    year = models.DateField(
      verbose_name='Year', 
      help_text='The year of publication or, for an unpublished work, th' \
      'e year it was written',
      blank=True, null=True, )

    publisher = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=10), 
      verbose_name='Publisher', 
      help_text='The name of the publisher',
      blank=True, )

    bookTitle = models.CharField(
      verbose_name='Book title', 
      help_text='The title of a book, part of which is being cited',
      blank=True, max_length=200, )

    journal = models.CharField(
      verbose_name='Journal', 
      help_text='A journal name. Abbreviations could also be provided',
      blank=True, max_length=200, )

    volume = models.CharField(
      verbose_name='Volume', 
      help_text='Specifies the volume of a journal or multivolume book',
      blank=True, max_length=1000, )

    series = models.CharField(
      verbose_name='Series', 
      help_text='The name of a series or set of books. When citing an en' \
      'tire book, the title field gives its title and an optional series' \
      ' field gives the name of a series or multi-volume set in which th' \
      'e book is published',
      blank=True, max_length=200, )

    pages = models.CharField(
      verbose_name='Pages', 
      help_text='One or more page numbers or range of page numbers',
      blank=True, max_length=100, )

    edition = models.CharField(
      verbose_name='Edition', 
      help_text='The edition of a book',
      blank=True, max_length=100, )

    conference = models.CharField(
      verbose_name='Conference', 
      help_text='The name of the conference in which the document has be' \
      'en presented',
      blank=True, max_length=300, )

    doi = models.CharField(
      verbose_name='Doi', 
      help_text='A digital object identifier assigned to the document',
      blank=True, max_length=100, )

    url = models.CharField(
      verbose_name='Url', validators=[HTTPURI_VALIDATOR], 
      help_text='A URL used as homepage of an entity (e.g. of a person, ' \
      'organization, resource etc.) and/or where an entity (e.g.LR, docu' \
      'ment etc.) is located',
      blank=True, max_length=1000, )

    ISSN = models.CharField(
      verbose_name='Issn', 
      help_text='The International Standard Serial Number used to identi' \
      'fy a journal',
      blank=True, max_length=100, )

    ISBN = models.CharField(
      verbose_name='Isbn', 
      help_text='The International Standard Book Number',
      blank=True, max_length=100, )

    keywords = MultiTextField(max_length=250, widget = MultiFieldWidget(widget_id=11), 
      verbose_name='Keywords', 
      help_text='The keyword(s) for indexing and classification of the d' \
      'ocument',
      blank=True, )

    documentLanguageName = models.CharField(
      verbose_name='Document language name', 
      help_text='The name of the language the document is written in, as' \
      ' mentioned in IETF BCP47',
      blank=True, max_length=150, )

    documentLanguageId = models.CharField(
      verbose_name='Document language id', 
      help_text='The id of the language the document is written in, as m' \
      'entioned in IETF BCP47',
      blank=True, max_length=20, )

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
    """
    Groups together information on any document describing the resource
    """

    class Meta:
        verbose_name = "Resource documentation"

    __schema_name__ = 'resourceDocumentationInfoType'
    __schema_fields__ = (
      ( 'documentation/documentUnstructured', 'documentation', RECOMMENDED ),
      ( 'documentation/documentInfo', 'documentation', RECOMMENDED ),
      ( u'samplesLocation', u'samplesLocation', RECOMMENDED ),
      ( u'toolDocumentationType', u'toolDocumentationType', OPTIONAL ),
    )
    __schema_classes__ = {
      u'documentInfo': "documentInfoType_model",
      u'documentUnstructured': "documentUnstructuredString_model",
    }

    documentation = models.ManyToManyField("documentationInfoType_model", 
      verbose_name='Documentation', 
      help_text='Refers to papers, manuals, reports etc. describing the ' \
      'resource',
      blank=True, null=True, related_name="documentation_%(class)s_related", )

    samplesLocation = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=12), 
      verbose_name='Samples location', validators=[HTTPURI_VALIDATOR], 
      help_text='A url with samples of the resource or, in the case of t' \
      'ools, of samples of the output',
      blank=True, )

    toolDocumentationType = MultiSelectField(
      verbose_name='Tool documentation', 
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
  u'DDC_classification',u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other', 
])

# pylint: disable-msg=C0103
class domainInfoType_model(SchemaModel):
    """
    Groups together information on domains represented in the resource;
    can be repeated for parts of the resource with distinct domain
    """

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

    domain = models.CharField(
      verbose_name='Domain', 
      help_text='Specifies the application domain of the resource or the' \
      ' tool/service',
      max_length=100, )

    sizePerDomain = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per domain', 
      help_text='Specifies the size of resource parts per domain',
      blank=True, null=True, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme', 
      help_text='Specifies the external classification schemes',
      blank=True, 
      max_length=DOMAININFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['max_length'],
      choices=DOMAININFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
      )

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
  u'speechAnnotation-speakerTurns',u'speechAnnotation', u'stemming',
  u'structuralAnnotation',u'syntacticAnnotation-shallowParsing',
  u'syntacticAnnotation-subcategorizationFrames',
  u'syntacticAnnotation-treebanks',u'syntacticosemanticAnnotation-links',
  u'translation',u'transliteration', u'discourseAnnotation-dialogueActs',
  u'modalityAnnotation-bodyMovements',
  u'modalityAnnotation-facialExpressions',
  u'modalityAnnotation-gazeEyeMovements',
  u'modalityAnnotation-handArmGestures',
  u'modalityAnnotation-handManipulationOfObjects',
  u'modalityAnnotation-headMovements',u'modalityAnnotation-lipMovements',
  u'semanticAnnotation-emotions',u'other', 
])

ANNOTATIONINFOTYPE_ANNOTATEDELEMENTS_CHOICES = _make_choices_from_list([
  u'speakerNoise', u'backgroundNoise', u'mispronunciations', u'truncation',
  u'discourseMarkers',u'other', 
])

ANNOTATIONINFOTYPE_SEGMENTATIONLEVEL_CHOICES = _make_choices_from_list([
  u'paragraph', u'sentence', u'clause', u'word', u'wordGroup', u'utterance',
  u'topic',u'signal', u'phoneme', u'syllable', u'phrase', u'diphone',
  u'prosodicBoundaries',u'frame', u'scene', u'shot', u'other', 
])

ANNOTATIONINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES = _make_choices_from_list([
  u'CES', u'EML', u'EMMA', u'GMX', u'HamNoSys', u'InkML', u'ISO12620',
  u'ISO16642',u'ISO1987', u'ISO26162', u'ISO30042', u'ISO704', u'LMF',
  u'MAF',u'MLIF', u'MULTEXT', u'multimodalInteractionFramework', u'OAXAL',
  u'OWL',u'pennTreeBank', u'pragueTreebank', u'RDF', u'SemAF', u'SemAF_DA',
  u'SemAF_NE',u'SemAF_SRL', u'SemAF_DS', u'SKOS', u'SRX', u'SynAF', u'TBX',
  u'TMX',u'TEI', u'TEI_P3', u'TEI_P4', u'TEI_P5', u'TimeML', u'XCES',
  u'XLIFF',u'MUMIN', u'BLM', u'other', 
])

ANNOTATIONINFOTYPE_ANNOTATIONMODE_CHOICES = _make_choices_from_list([
  u'automatic', u'manual', u'mixed', u'interactive', 
])

# pylint: disable-msg=C0103
class annotationInfoType_model(SchemaModel):
    """
    Groups information on the annotated part(s) of a resource
    """

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
      verbose_name='Annotation', 
      help_text='Specifies the annotation level of the resource or the a' \
      'nnotation type a tool/ service requires or produces as an output',
      
      max_length=ANNOTATIONINFOTYPE_ANNOTATIONTYPE_CHOICES['max_length'],
      choices=ANNOTATIONINFOTYPE_ANNOTATIONTYPE_CHOICES['choices'],
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

    annotationFormat = models.CharField(
      verbose_name='Annotation format', 
      help_text='Specifies the format that is used in the annotation pro' \
      'cess since often the mime type will not be sufficient for machine' \
      ' processing',
      blank=True, max_length=1000, )

    tagset = models.CharField(
      verbose_name='Tagset', 
      help_text='A name or a url reference to the tagset used in the ann' \
      'otation of the resource or used by the tool/service',
      blank=True, max_length=1000, )

    tagsetLanguageId = models.CharField(
      verbose_name='Tagset language id', 
      help_text='The identifier of the tagset language as expressed in t' \
      'he values of IETF BP47',
      blank=True, max_length=20, )

    tagsetLanguageName = models.CharField(
      verbose_name='Tagset language name', 
      help_text='The name of the tagset language expressed in the values' \
      ' of IETF BP47',
      blank=True, max_length=100, )

    conformanceToStandardsBestPractices = MultiSelectField(
      verbose_name='Conformance to standards best practices', 
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True, 
      max_length=1 + len(ANNOTATIONINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices']) / 4,
      choices=ANNOTATIONINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices'],
      )

    theoreticModel = models.CharField(
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
      choices=ANNOTATIONINFOTYPE_ANNOTATIONMODE_CHOICES['choices'],
      )

    annotationModeDetails = models.CharField(
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
      blank=True, null=True, )

    interannotatorAgreement = models.CharField(
      verbose_name='Interannotator agreement', 
      help_text='Provides information on the interannotator agreement an' \
      'd the methods/metrics applied',
      blank=True, max_length=1000, )

    intraannotatorAgreement = models.CharField(
      verbose_name='Intraannotator agreement', 
      help_text='Provides information on the intra-annotator agreement a' \
      'nd the methods/metrics applied',
      blank=True, max_length=1000, )

    annotator = models.ManyToManyField("actorInfoType_model", 
      verbose_name='Annotator', 
      help_text='Groups information on the annotators of the specific an' \
      'notation type',
      blank=True, null=True, related_name="annotator_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class targetResourceInfoType_model(SchemaModel):
    """
    Groups information on the resource related to the one being
    described; can be an identifier, a resource name or a URL
    """

    class Meta:
        verbose_name = "Target resource"

    __schema_name__ = 'targetResourceInfoType'
    __schema_fields__ = (
      ( u'targetResourceNameURI', u'targetResourceNameURI', REQUIRED ),
    )

    targetResourceNameURI = models.CharField(
      verbose_name='Target resource name uri', 
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
    """
    Groups information on the relations of the resource being described
    with other resources
    """

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

    relationType = models.CharField(
      verbose_name='Relation', 
      help_text='Specifies the type of relation not covered by the ones ' \
      'proposed by META-SHARE',
      max_length=100, )

    relatedResource = models.OneToOneField("targetResourceInfoType_model", 
      verbose_name='Related resource', 
      help_text='The full name, the identifier or the url of the related' \
      ' resource',
      )

    back_to_resourceinfotype_model = models.ForeignKey("resourceInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

MODALITYINFOTYPE_MODALITYTYPE_CHOICES = _make_choices_from_list([
  u'bodyGesture', u'facialExpression', u'voice', u'combinationOfModalities',
  u'signLanguage',u'spokenLanguage', u'writtenLanguage', u'other', 
])

# pylint: disable-msg=C0103
class modalityInfoType_model(SchemaModel):
    """
    Groups information on the modalities represented in the resource
    """

    class Meta:
        verbose_name = "Modality"

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
      verbose_name='Modality', 
      help_text='Specifies the type of the modality represented in the r' \
      'esource or processed by a tool/service',
      
      max_length=1 + len(MODALITYINFOTYPE_MODALITYTYPE_CHOICES['choices']) / 4,
      choices=MODALITYINFOTYPE_MODALITYTYPE_CHOICES['choices'],
      )

    modalityTypeDetails = models.CharField(
      verbose_name='Modality details', 
      help_text='Provides further information on modalities',
      blank=True, max_length=500, )

    sizePerModality = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per modality', 
      help_text='Provides information on the size per modality component' \
      '',
      blank=True, null=True, )

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
    """
    Groups information on the person(s) participating in the audio,
    video, sensorimotor (textNumerical) part of the resource
    """

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

    alias = MultiTextField(widget = MultiFieldWidget(widget_id=13), 
      verbose_name='Alias', 
      help_text='The name of the person used instead of the real one',
      blank=True)

    ageGroup = models.CharField(
      verbose_name='Age group', 
      help_text='The age group to which the participant belongs',
      blank=True, 
      max_length=30,
      choices=PARTICIPANTINFOTYPE_AGEGROUP_CHOICES['choices'],
      )

    age = models.CharField(
      verbose_name='Age', 
      help_text='The age of the participant',
      blank=True, max_length=50, )

    sex = models.CharField(
      verbose_name='Sex', 
      help_text='The gender of a person related to or participating in t' \
      'he resource',
      blank=True, 
      max_length=30,
      choices=PARTICIPANTINFOTYPE_SEX_CHOICES['choices'],
      )

    origin = models.CharField(
      verbose_name='Origin', 
      help_text='The language origin of the participant',
      blank=True, 
      max_length=30,
      choices=PARTICIPANTINFOTYPE_ORIGIN_CHOICES['choices'],
      )

    placeOfLiving = models.CharField(
      verbose_name='Place of living', 
      help_text='The participant\'s place of living',
      blank=True, max_length=100, )

    placeOfBirth = models.CharField(
      verbose_name='Place of birth', 
      help_text='The place in which the participant has been born',
      blank=True, max_length=100, )

    placeOfChildhood = models.CharField(
      verbose_name='Place of childhood', 
      help_text='The place in which the participant lived as a child',
      blank=True, max_length=100, )

    dialectAccent = MultiTextField(widget = MultiFieldWidget(widget_id=14), 
      verbose_name='Dialect accent', 
      help_text='Provides information on the dialect of the participant',
      blank=True)

    speakingImpairment = models.CharField(
      verbose_name='Speaking impairment', 
      help_text='Provides information on any speaking impairment the par' \
      'ticipant may have',
      blank=True, max_length=200, )

    hearingImpairment = models.CharField(
      verbose_name='Hearing impairment', 
      help_text='Provides information on any hearing impairment the part' \
      'icipant may have',
      blank=True, max_length=200, )

    smokingHabits = models.CharField(
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
      choices=PARTICIPANTINFOTYPE_VOCALTRACTCONDITIONS_CHOICES['choices'],
      )

    profession = models.CharField(
      verbose_name='Profession', 
      help_text='Provides information on the participant\'s profession',
      blank=True, max_length=100, )

    height = models.IntegerField(
      verbose_name='Height', 
      help_text='Provides information on the height of the participant i' \
      'n cm',
      blank=True, null=True, )

    weight = models.IntegerField(
      verbose_name='Weight', 
      help_text='Provides information on the weight of the participant',
      blank=True, null=True, )

    trainedSpeaker = MetaBooleanField(
      verbose_name='Trained speaker', 
      help_text='Provides information on whether the participant is trai' \
      'ned in a specific task',
      blank=True, )

    placeOfSecondEducation = models.CharField(
      verbose_name='Place of second education', 
      help_text='Specifies the place of the secondary education of the p' \
      'articipant',
      blank=True, max_length=100, )

    educationLevel = models.CharField(
      verbose_name='Education level', 
      help_text='Provides information on the education level of the part' \
      'icipant',
      blank=True, max_length=100, )

    back_to_personsourcesetinfotype_model = models.ForeignKey("personSourceSetInfoType_model", )

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
    """
    Groups together information on the capture of the audio or video
    part of a corpus
    """

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
      verbose_name='Capturing device', 
      help_text='The transducers through which the data is captured',
      blank=True, 
      max_length=1 + len(CAPTUREINFOTYPE_CAPTURINGDEVICETYPE_CHOICES['choices']) / 4,
      choices=CAPTUREINFOTYPE_CAPTURINGDEVICETYPE_CHOICES['choices'],
      )

    capturingDeviceTypeDetails = models.CharField(
      verbose_name='Capturing device details', 
      help_text='Provides further information on the capturing device',
      blank=True, max_length=400, )

    capturingDetails = models.CharField(
      verbose_name='Capturing details', 
      help_text='Provides further information on the capturing method an' \
      'd procedure',
      blank=True, max_length=400, )

    capturingEnvironment = models.CharField(
      verbose_name='Capturing environment', 
      help_text='Type of capturing environment',
      blank=True, 
      max_length=30,
      choices=CAPTUREINFOTYPE_CAPTURINGENVIRONMENT_CHOICES['choices'],
      )

    sensorTechnology = MultiTextField(max_length=200, widget = MultiFieldWidget(widget_id=15), 
      verbose_name='Sensor technology', 
      help_text='Specifies either the type of image sensor or the sensin' \
      'g method used in the camera or the image-capture device',
      blank=True, )

    sceneIllumination = models.CharField(
      verbose_name='Scene illumination', 
      help_text='Information on the illumination of the scene',
      blank=True, 
      max_length=30,
      choices=CAPTUREINFOTYPE_SCENEILLUMINATION_CHOICES['choices'],
      )

    personSourceSetInfo = models.OneToOneField("personSourceSetInfoType_model", 
      verbose_name='Person source set', 
      help_text='Groups information on the persons (speakers, video part' \
      'icipants, etc.) in the audio andvideoparts of the resource',
      blank=True, null=True, )

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
    """
    Groups information on the persons (speakers, video participants,
    etc.) in the audio andvideoparts of the resource
    """

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

    numberOfPersons = models.IntegerField(
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

    ageRangeStart = models.IntegerField(
      verbose_name='Age range start', 
      help_text='Start of age range of the group of participants',
      blank=True, null=True, )

    ageRangeEnd = models.IntegerField(
      verbose_name='Age range end', 
      help_text='End of age range of the group of participants',
      blank=True, null=True, )

    sexOfPersons = models.CharField(
      verbose_name='Sex of persons', 
      help_text='The gender of the group of participants',
      blank=True, 
      max_length=30,
      choices=PERSONSOURCESETINFOTYPE_SEXOFPERSONS_CHOICES['choices'],
      )

    originOfPersons = models.CharField(
      verbose_name='Origin of persons', 
      help_text='The language origin of the group of participants',
      blank=True, 
      max_length=30,
      choices=PERSONSOURCESETINFOTYPE_ORIGINOFPERSONS_CHOICES['choices'],
      )

    dialectAccentOfPersons = MultiTextField(max_length=500, widget = MultiFieldWidget(widget_id=16), 
      verbose_name='Dialect accent of persons', 
      help_text='Provides information on the dialect of the group of par' \
      'ticipants',
      blank=True, )

    geographicDistributionOfPersons = models.CharField(
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
      choices=PERSONSOURCESETINFOTYPE_HEARINGIMPAIRMENTOFPERSONS_CHOICES['choices'],
      )

    speakingImpairmentOfPersons = models.CharField(
      verbose_name='Speaking impairment of persons', 
      help_text='Whether the group of participants contains persons with' \
      'with speakingimpairments',
      blank=True, 
      max_length=30,
      choices=PERSONSOURCESETINFOTYPE_SPEAKINGIMPAIRMENTOFPERSONS_CHOICES['choices'],
      )

    numberOfTrainedSpeakers = models.IntegerField(
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
  u'frogStory', u'pearStory', u'mapTask', u'onlineEducationalGame',
  u'pearStory',u'rolePlay', u'wordGame', u'wizardOfOz', u'other', 
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
    """
    Groups together information on the setting of the audio and/or video
    part of a resource
    """

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
      choices=SETTINGINFOTYPE_NATURALITY_CHOICES['choices'],
      )

    conversationalType = models.CharField(
      verbose_name='Conversational', 
      help_text='Specifies the conversational type of the resource',
      blank=True, 
      max_length=30,
      choices=SETTINGINFOTYPE_CONVERSATIONALTYPE_CHOICES['choices'],
      )

    scenarioType = models.CharField(
      verbose_name='Scenario', 
      help_text='Indicates the task defined for the conversation or the ' \
      'interaction of participants',
      blank=True, 
      max_length=30,
      choices=SETTINGINFOTYPE_SCENARIOTYPE_CHOICES['choices'],
      )

    audience = models.CharField(
      verbose_name='Audience', 
      help_text='Indication of the intended audience size',
      blank=True, 
      max_length=30,
      choices=SETTINGINFOTYPE_AUDIENCE_CHOICES['choices'],
      )

    interactivity = models.CharField(
      verbose_name='Interactivity', 
      help_text='Indicates the level of conversational interaction betwe' \
      'en speakers (for audio component) or participants (for video comp' \
      'onent)',
      blank=True, 
      max_length=30,
      choices=SETTINGINFOTYPE_INTERACTIVITY_CHOICES['choices'],
      )

    interaction = models.CharField(
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
    """
    Groups together information on the running environment of a tool or
    a language description
    """

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
      verbose_name='Required lrs', 
      help_text='If for running a tool and/or computational grammar, spe' \
      'cific LRs (e.g. a grammar, a list of words etc.) are required',
      blank=True, null=True, related_name="requiredLRs_%(class)s_related", )

    runningEnvironmentDetails = models.CharField(
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
    """
    Groups together information on the recording of the audio or video
    part of a resource
    """

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
      verbose_name='Recording device', 
      help_text='The nature of the recording platform hardware and the s' \
      'torage medium',
      blank=True, 
      max_length=1 + len(RECORDINGINFOTYPE_RECORDINGDEVICETYPE_CHOICES['choices']) / 4,
      choices=RECORDINGINFOTYPE_RECORDINGDEVICETYPE_CHOICES['choices'],
      )

    recordingDeviceTypeDetails = models.CharField(
      verbose_name='Recording device details', 
      help_text='Free text description of the recoding device',
      blank=True, max_length=500, )

    recordingPlatformSoftware = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=17), 
      verbose_name='Recording platform software', 
      help_text='The software used for the recording platform',
      blank=True, )

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
      verbose_name='Source channel', 
      help_text='Type of the source channel',
      blank=True, 
      max_length=1 + len(RECORDINGINFOTYPE_SOURCECHANNELTYPE_CHOICES['choices']) / 4,
      choices=RECORDINGINFOTYPE_SOURCECHANNELTYPE_CHOICES['choices'],
      )

    sourceChannelName = MultiTextField(max_length=30, widget = MultiFieldWidget(widget_id=18), 
      verbose_name='Source channel name', 
      help_text='The name of the specific source recorded',
      blank=True, )

    sourceChannelDetails = models.CharField(
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
    """
    Groups together information on the image resolution
    """

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
      choices=RESOLUTIONINFOTYPE_RESOLUTIONSTANDARD_CHOICES['choices'],
      )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

COMPRESSIONINFOTYPE_COMPRESSIONNAME_CHOICES = _make_choices_from_list([
  u'mpg', u'avi', u'mov', u'flac', u'shorten', u'mp3', u'oggVorbis',
  u'atrac',u'aac', u'mpeg', u'realAudio', u'other', 
])

# pylint: disable-msg=C0103
class compressionInfoType_model(SchemaModel):
    """
    Groups together information on the compression status and method of
    a resource
    """

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
    """
    Groups information on the way different media of the resource
    interact with or link to each other. To be used for multimodal
    resources or for resources representing sensorimotor data
    """

    class Meta:
        verbose_name = "Link to other media"

    __schema_name__ = 'linkToOtherMediaInfoType'
    __schema_fields__ = (
      ( u'otherMedia', u'otherMedia', REQUIRED ),
      ( u'mediaTypeDetails', u'mediaTypeDetails', OPTIONAL ),
      ( u'synchronizedWithText', u'synchronizedWithText', OPTIONAL ),
      ( u'synchronizedWithAudio', u'synchronizedWithAudio', OPTIONAL ),
      ( u'synchronizedWithVideo', u'synchronizedWithVideo', OPTIONAL ),
      ( u'sycnhronizedWithImage', u'sycnhronizedWithImage', OPTIONAL ),
      ( u'synchronizedWithTextNumerical', u'synchronizedWithTextNumerical', OPTIONAL ),
    )

    otherMedia = models.CharField(
      verbose_name='Other media', 
      help_text='Specifies the media types that are linked to the media ' \
      'type described within the same resource',
      
      max_length=30,
      choices=LINKTOOTHERMEDIAINFOTYPE_OTHERMEDIA_CHOICES['choices'],
      )

    mediaTypeDetails = models.CharField(
      verbose_name='Media details', 
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

    sycnhronizedWithImage = MetaBooleanField(
      verbose_name='Sycnhronized with image', 
      help_text='Whether text or textNumerical media type is synchronize' \
      'd with image within the same resource',
      blank=True, )

    synchronizedWithTextNumerical = MetaBooleanField(
      verbose_name='Synchronized with text numerical', 
      help_text='Whether video or audio media type is synchronized with ' \
      'the textNumerical (representation of sensorimotor measurements) w' \
      'ithin the same resource',
      blank=True, )

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
      verbose_name='Document', related_name="documentInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class communicationInfoType_model(SchemaModel):
    """
    Groups information on communication details of a person or an
    organization
    """

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

    email = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=19), 
      verbose_name='Email', validators=[EMAILADDRESS_VALIDATOR], 
      help_text='The email address of a person or an organization',
      )

    url = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=20), 
      verbose_name='Url', validators=[HTTPURI_VALIDATOR], 
      help_text='A URL used as homepage of an entity (e.g. of a person, ' \
      'organization, resource etc.) and/or where an entity (e.g.LR, docu' \
      'ment etc.) is located',
      blank=True, )

    address = models.CharField(
      verbose_name='Address', 
      help_text='The street and the number of the postal address of a pe' \
      'rson or organization',
      blank=True, max_length=200, )

    zipCode = models.CharField(
      verbose_name='Zip code', 
      help_text='The zip code of the postal address of a person or organ' \
      'ization',
      blank=True, max_length=30, )

    city = models.CharField(
      verbose_name='City', 
      help_text='The name of the city, town or village as mentioned in t' \
      'he postal address of a person or organization',
      blank=True, max_length=50, )

    region = models.CharField(
      verbose_name='Region', 
      help_text='The name of the region, county or department as mention' \
      'ed in the postal address of a person or organization',
      blank=True, max_length=100, )

    country = models.CharField(
      verbose_name='Country', 
      help_text='The name of the country mentioned in the postal address' \
      ' of a person or organization as defined in the list of values of ' \
      'ISO 3166',
      blank=True, max_length=100, )

    telephoneNumber = MultiTextField(max_length=30, widget = MultiFieldWidget(widget_id=21), 
      verbose_name='Telephone number', 
      help_text='The telephone number of a person or an organization; re' \
      'commended format: +_international code_city code_number',
      blank=True, )

    faxNumber = MultiTextField(max_length=30, widget = MultiFieldWidget(widget_id=22), 
      verbose_name='Fax number', 
      help_text='The fax number of a person or an organization; recommen' \
      'ded format: +_international code_city code_number',
      blank=True, )

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
      verbose_name='Person', related_name="personInfo_%(class)s_related", )

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
      verbose_name='Organization', related_name="organizationInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class actorInfoType_model(SubclassableModel):
    """
    Used to bring persons and organizations (in whatever role they may
    have with regard to the resource, e.g., resource creator, IPR
    holder, etc.)
    """

    __schema_name__ = 'SUBCLASSABLE'

    class Meta:
        verbose_name = "Actor"


# pylint: disable-msg=C0103
class organizationInfoType_model(actorInfoType_model):
    """
    Groups information on organizations related to the resource
    """

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

    organizationName = MultiTextField(widget = MultiFieldWidget(widget_id=23), 
      verbose_name='Organization name', 
      help_text='The full name of an organization',
      )

    organizationShortName = MultiTextField(widget = MultiFieldWidget(widget_id=24), 
      verbose_name='Organization short name', 
      help_text='The short name (abbreviation, acronym etc.) used for an' \
      ' organization',
      blank=True)

    departmentName = MultiTextField(widget = MultiFieldWidget(widget_id=25), 
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

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['organizationName', ]
        formatstring = u'{}'
        return self.unicode_(formatstring, formatargs)

PERSONINFOTYPE_SEX_CHOICES = _make_choices_from_list([
  u'male', u'female', u'unknown', 
])

# pylint: disable-msg=C0103
class personInfoType_model(actorInfoType_model):
    """
    Groups information relevant to personsrelated to the resource; to be
    used mainly for contact persons, resource creators, validators,
    annotators etc. for whom personal data can be provided
    """

    class Meta:
        verbose_name = "Person"

    __schema_name__ = 'personInfoType'
    __schema_fields__ = (
      ( u'surname', u'surname', REQUIRED ),
      ( u'givenName', u'givenName', RECOMMENDED ),
      ( u'sex', u'sex', RECOMMENDED ),
      ( u'communicationInfo', u'communicationInfo', REQUIRED ),
      ( u'position', u'position', OPTIONAL ),
      ( u'affiliation', u'affiliation', OPTIONAL ),
    )
    __schema_classes__ = {
      u'affiliation': "organizationInfoType_model",
      u'communicationInfo': "communicationInfoType_model",
    }

    surname = MultiTextField(widget = MultiFieldWidget(widget_id=26), 
      verbose_name='Surname', 
      help_text='The surname (family name) of a person related to the re' \
      'source',
      )

    givenName = MultiTextField(widget = MultiFieldWidget(widget_id=27), 
      verbose_name='Given name', 
      help_text='The given name (first name) of a person related to the ' \
      'resource; initials can also be used',
      blank=True)

    sex = models.CharField(
      verbose_name='Sex', 
      help_text='The gender of a person related to or participating in t' \
      'he resource',
      blank=True, 
      max_length=30,
      choices=PERSONINFOTYPE_SEX_CHOICES['choices'],
      )

    communicationInfo = models.OneToOneField("communicationInfoType_model", 
      verbose_name='Communication', 
      help_text='Groups information on communication details of a person' \
      ' or an organization',
      )

    position = models.CharField(
      verbose_name='Position', 
      help_text='The position or the title of a person if affiliated to ' \
      'an organization',
      blank=True, max_length=100, )

    affiliation = models.ManyToManyField("organizationInfoType_model", 
      verbose_name='Affiliation', 
      help_text='Groups information on organization to whomtheperson is ' \
      'affiliated',
      blank=True, null=True, related_name="affiliation_%(class)s_related", )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['givenName', 'surname', 'communicationInfo/email', 'affiliation', ]
        formatstring = u'{} {} {} {}'
        return self.unicode_(formatstring, formatargs)

DISTRIBUTIONINFOTYPE_AVAILABILITY_CHOICES = _make_choices_from_list([
  u'available-unrestrictedUse', u'available-restrictedUse',
  u'notAvailableThroughMetaShare',u'underNegotiation', 
])

# pylint: disable-msg=C0103
class distributionInfoType_model(SchemaModel):
    """
    Groups information on the distribution of the resource
    """

    class Meta:
        verbose_name = "Distribution"

    __schema_name__ = 'distributionInfoType'
    __schema_fields__ = (
      ( u'availability', u'availability', REQUIRED ),
      ( u'licenceInfo', u'licenceinfotype_model_set', OPTIONAL ),
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
      choices=DISTRIBUTIONINFOTYPE_AVAILABILITY_CHOICES['choices'],
      )

    # OneToMany field: licenceInfo

    iprHolder = models.ManyToManyField("actorInfoType_model", 
      verbose_name='Ipr holder', 
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
      help_text='Specifies the end date of availability of a resource',
      blank=True, null=True, )

    availabilityStartDate = models.DateField(
      verbose_name='Availability start date', 
      help_text='Specifies the start date of availability of a resource',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

MEMBERSHIPINFOTYPE_MEMBERSHIPINSTITUTION_CHOICES = _make_choices_from_list([
  u'ELRA', u'LDC', u'TST-CENTRALE', u'other', 
])

# pylint: disable-msg=C0103
class membershipInfoType_model(SchemaModel):
    """
    The conditions imposed by the user being member of some
    association/institution (e.g., ELRA, LDC) distributing the
    resource. This indicates the availability conditions (and
    prices) for users who are members or not.
    """

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
  u'AGPL', u'LGPL', u'CC_BY-NC-ND', u'CC_BY-NC-SA', u'CC_BY-NC',
  u'CC_BY-ND',u'CC_BY-SA', u'CC_BY', u'MSCommons_BY', u'MSCommons_BY-NC',
  u'MSCommons_BY-NC-ND',u'MSCommons_BY-NC-SA', u'MSCommons_BY-ND',
  u'MSCommons_BY-SA',u'MSCommons_COM-NR-FF', u'MSCommons_COM-NR',
  u'MSCommons_COM-NR-ND-FF',u'MSCommons_COM-NR-ND',
  u'MSCommons_NoCOM-NC-NR-ND-FF',u'MSCommons_NoCOM-NC-NR-ND',
  u'MSCommons_NoCOM-NC-NR-FF',u'MSCommons_NoCOM-NC-NR', u'ELRA_EVALUATION',
  u'ELRA_VAR',u'ELRA_END_USER', u'ELRA_LIMITED', u'proprietary', u'CC',
  u'CLARIN_PUB',u'CLARIN_ACA-NC', u'CC_BY-SA_3.0', u'LGPLv3', u'CLARIN_ACA',
  u'CLARIN_RES',u'Princeton_Wordnet', u'GPL', u'GeneralLicenceGrant',
  u'GFDL',u'CC_BY-NC-SA_3.0', u'ApacheLicence_V2.0', u'BSD-style',
  u'underNegotiation',u'other', 
])

LICENCEINFOTYPE_RESTRICTIONSOFUSE_CHOICES = _make_choices_from_list([
  u'informLicensor', u'redeposit', u'onlyMSmembers',
  u'academic-nonCommercialUse',u'evaluationUse', u'commercialUse',
  u'attribution',u'shareAlike', u'noDerivatives', u'noRedistribution',
  u'other',
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
    """
    Groups information on licences for the resource; can be repeated to
    allow for different modes of access and restrictions of use
    (e.g. free for academic use, on-a-fee basis for commercial use,
    download of a sample for free use etc.)
    """

    class Meta:
        verbose_name = "Licence"

    __schema_name__ = 'licenceInfoType'
    __schema_fields__ = (
      ( u'licence', u'licence', REQUIRED ),
      ( u'restrictionsOfUse', u'restrictionsOfUse', OPTIONAL ),
      ( u'distributionAccessMedium', u'distributionAccessMedium', RECOMMENDED ),
      ( u'downloadLocation', u'downloadLocation', OPTIONAL ),
      ( u'executionLocation', u'executionLocation', OPTIONAL ),
      ( u'price', u'price', OPTIONAL ),
      ( u'attributionText', u'attributionText', OPTIONAL ),
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
      help_text='The licence of use for the resource',
      
      max_length=1 + len(LICENCEINFOTYPE_LICENCE_CHOICES['choices']) / 4,
      choices=LICENCEINFOTYPE_LICENCE_CHOICES['choices'],
      )

    restrictionsOfUse = MultiSelectField(
      verbose_name='Restrictions of use', 
      help_text='Specifies the restrictions imposed by the type of the l' \
      'icence',
      blank=True, 
      max_length=1 + len(LICENCEINFOTYPE_RESTRICTIONSOFUSE_CHOICES['choices']) / 4,
      choices=LICENCEINFOTYPE_RESTRICTIONSOFUSE_CHOICES['choices'],
      )

    distributionAccessMedium = MultiSelectField(
      verbose_name='Distribution access medium', 
      help_text='Specifies the medium (channel) used for delivery or pro' \
      'viding access to the resource',
      blank=True, 
      max_length=1 + len(LICENCEINFOTYPE_DISTRIBUTIONACCESSMEDIUM_CHOICES['choices']) / 4,
      choices=LICENCEINFOTYPE_DISTRIBUTIONACCESSMEDIUM_CHOICES['choices'],
      )

    downloadLocation = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=28), 
      verbose_name='Download location', validators=[HTTPURI_VALIDATOR], 
      help_text='Any url where the resource can be downloaded from',
      blank=True, )

    executionLocation = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=29), 
      verbose_name='Execution location', validators=[HTTPURI_VALIDATOR], 
      help_text='Any url where the service providing access to a resourc' \
      'e is being executed',
      blank=True, )

    price = models.CharField(
      verbose_name='Price', 
      help_text='Specifies the costs that are required to access the res' \
      'ource, a fragment of the resource or to use atool or service',
      blank=True, max_length=100, )

    attributionText = MultiTextField(widget = MultiFieldWidget(widget_id=30), 
      verbose_name='Attribution text', 
      help_text='The text that must be quoted for attribution purposes w' \
      'hen using a resource',
      blank=True)

    licensor = models.ManyToManyField("actorInfoType_model", 
      verbose_name='Licensor', 
      help_text='Groups information on person who is legally eligible to' \
      ' licence and actually licenses the resource. The licensor could b' \
      'e different from the creator, the distributor or the IP rightshol' \
      'der. The licensor has the necessary rights or licences to license' \
      ' the work and is the party that actually licenses the resource th' \
      'at enters the META-SHARE network. She will have obtained the nece' \
      'ssary rights or licences from the IPR holder and she may have a d' \
      'istribution agreement with a distributor that disseminates the wo' \
      'rk under a set of conditions defined in the specific licence and ' \
      'collects revenue on the licensor\'s behalf. The attribution of th' \
      'e creator, separately from the attribution of the licensor, may b' \
      'e part of the licence under which the resource is distributed (as' \
      ' e.g. is the case with Creative Commons Licences)',
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
      verbose_name='Membership', 
      help_text='The conditions imposed by the user being member of some' \
      ' association/institution (e.g., ELRA, LDC) distributing the resou' \
      'rce. This indicates the availability conditions (and prices) for ' \
      'users who are members or not',
      blank=True, null=True, related_name="membershipInfo_%(class)s_related", )

    back_to_distributioninfotype_model = models.ForeignKey("distributionInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

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
    """
    Groups together information on character encoding of the resource
    """

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
      
      max_length=CHARACTERENCODINGINFOTYPE_CHARACTERENCODING_CHOICES['max_length'],
      choices=CHARACTERENCODINGINFOTYPE_CHARACTERENCODING_CHOICES['choices'],
      )

    sizePerCharacterEncoding = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per character encoding', 
      help_text='Provides information on thesize of the resource parts w' \
      'ith different character encoding',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class timeCoverageInfoType_model(SchemaModel):
    """
    Groups together information on time classification of the resource
    """

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

    timeCoverage = models.CharField(
      verbose_name='Time coverage', 
      help_text='The time period that the content of a resource is about' \
      '',
      max_length=100, )

    sizePerTimeCoverage = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per time coverage', 
      help_text='Provides information on size per time period represente' \
      'd in the resource',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class geographicCoverageInfoType_model(SchemaModel):
    """
    Groups information on geographic classification of the resource
    """

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

    geographicCoverage = models.CharField(
      verbose_name='Geographic coverage', 
      help_text='The geographic region that the content of a resource is' \
      ' about; for countries, recommended use of ISO-3166',
      max_length=100, )

    sizePerGeographicCoverage = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per geographic coverage', 
      help_text='Provides information on size per geographically distinc' \
      't section of the resource',
      blank=True, null=True, )

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
    """
    Groups information on the number of languages of the resource part
    and of the way they are combined to each other
    """

    class Meta:
        verbose_name = "Linguality"

    __schema_name__ = 'lingualityInfoType'
    __schema_fields__ = (
      ( u'lingualityType', u'lingualityType', REQUIRED ),
      ( u'multilingualityType', u'multilingualityType', OPTIONAL ),
      ( u'multilingualityTypeDetails', u'multilingualityTypeDetails', OPTIONAL ),
    )

    lingualityType = models.CharField(
      verbose_name='Linguality', 
      help_text='Indicates whether the resource includes one, two or mor' \
      'e languages',
      
      max_length=20,
      choices=LINGUALITYINFOTYPE_LINGUALITYTYPE_CHOICES['choices'],
      )

    multilingualityType = models.CharField(
      verbose_name='Multilinguality', 
      help_text='Indicates whether the corpus is parallel, comparable or' \
      ' mixed',
      blank=True, 
      max_length=30,
      choices=LINGUALITYINFOTYPE_MULTILINGUALITYTYPE_CHOICES['choices'],
      )

    multilingualityTypeDetails = models.CharField(
      verbose_name='Multilinguality details', 
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
    """
    Groups information on language varieties occurred in the resource
    (e.g. dialects)
    """

    class Meta:
        verbose_name = "Language variety"

    __schema_name__ = 'languageVarietyInfoType'
    __schema_fields__ = (
      ( u'languageVarietyType', u'languageVarietyType', REQUIRED ),
      ( u'languageVarietyName', u'languageVarietyName', REQUIRED ),
      ( u'sizePerLanguageVariety', u'sizePerLanguageVariety', REQUIRED ),
    )
    __schema_classes__ = {
      u'sizePerLanguageVariety': "sizeInfoType_model",
    }

    languageVarietyType = models.CharField(
      verbose_name='Language variety', 
      help_text='Specifies the type of the language variety that occurs ' \
      'in the resource or is supported by a tool/service',
      
      max_length=20,
      choices=LANGUAGEVARIETYINFOTYPE_LANGUAGEVARIETYTYPE_CHOICES['choices'],
      )

    languageVarietyName = models.CharField(
      verbose_name='Language variety name', 
      help_text='The name of the language variety that occurs in the res' \
      'ource or is supported by a tool/service',
      max_length=1000, )

    sizePerLanguageVariety = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per language variety', 
      help_text='Provides information on the size per language variety c' \
      'omponent',
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['languageVarietyName', 'languageVarietyType', ]
        formatstring = u'{} ({})'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class languageInfoType_model(SchemaModel):
    """
    Groups information on the languages represented in the resource
    """

    class Meta:
        verbose_name = "Language"

    __schema_name__ = 'languageInfoType'
    __schema_fields__ = (
      ( u'languageId', u'languageId', REQUIRED ),
      ( u'languageName', u'languageName', REQUIRED ),
      ( u'languageScript', u'languageScript', OPTIONAL ),
      ( u'sizePerLanguage', u'sizePerLanguage', OPTIONAL ),
      ( u'languageVarietyInfo', u'languageVarietyInfo', OPTIONAL ),
    )
    __schema_classes__ = {
      u'languageVarietyInfo': "languageVarietyInfoType_model",
      u'sizePerLanguage': "sizeInfoType_model",
    }

    languageId = models.CharField(
      verbose_name='Language id', 
      help_text='The identifier of the language that is included in the ' \
      'resource or supported by the tool/service according to the IETF B' \
      'CP47 standard',
      max_length=1000, )

    languageName = models.CharField(
      verbose_name='Language name', 
      help_text='A human understandable name of the language that is use' \
      'd in the resource or supported by the tool/service according to t' \
      'he IETF BCP47 standard',
      max_length=1000, )

    languageScript = models.CharField(
      verbose_name='Language script', 
      help_text='Specifies the writing system used to represent the lang' \
      'uage in form of a four letter code as it is defined in ISO-15924',
      blank=True, max_length=100, )

    sizePerLanguage = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per language', 
      help_text='Provides information on the size per language component' \
      '',
      blank=True, null=True, )

    languageVarietyInfo = models.ManyToManyField("languageVarietyInfoType_model", 
      verbose_name='Language variety', 
      help_text='Groups information on language varieties occurred in th' \
      'e resource (e.g. dialects)',
      blank=True, null=True, related_name="languageVarietyInfo_%(class)s_related", )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['languageName', 'languageVarietyInfo', ]
        formatstring = u'{} {}'
        return self.unicode_(formatstring, formatargs)

PROJECTINFOTYPE_FUNDINGTYPE_CHOICES = _make_choices_from_list([
  u'other', u'ownFunds', u'nationalFunds', u'euFunds', 
])

# pylint: disable-msg=C0103
class projectInfoType_model(SchemaModel):
    """
    Groups information on a project related to the resource(e.g. a
    project the resource has been used in; a funded project that led
    to the resource creation etc.)
    """

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

    projectName = MultiTextField(widget = MultiFieldWidget(widget_id=31), 
      verbose_name='Project name', 
      help_text='The full name of a project related to the resource',
      )

    projectShortName = MultiTextField(widget = MultiFieldWidget(widget_id=32), 
      verbose_name='Project short name', 
      help_text='A short name or abbreviation of a project related to th' \
      'e resource',
      blank=True)

    projectID = models.CharField(
      verbose_name='Project id', 
      help_text='An unambiguous referent to a project related to the res' \
      'ource',
      blank=True, max_length=100, )

    url = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=33), 
      verbose_name='Url', validators=[HTTPURI_VALIDATOR], 
      help_text='A URL used as homepage of an entity (e.g. of a person, ' \
      'organization, resource etc.) and/or where an entity (e.g.LR, docu' \
      'ment etc.) is located',
      blank=True, )

    fundingType = MultiSelectField(
      verbose_name='Funding', 
      help_text='Specifies the type of funding of the project',
      
      max_length=1 + len(PROJECTINFOTYPE_FUNDINGTYPE_CHOICES['choices']) / 4,
      choices=PROJECTINFOTYPE_FUNDINGTYPE_CHOICES['choices'],
      )

    funder = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=34), 
      verbose_name='Funder', 
      help_text='The full name of the funder of the project',
      blank=True, )

    fundingCountry = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=35), 
      verbose_name='Funding country', 
      help_text='The name of the funding country, in case of national fu' \
      'nding as mentioned in ISO3166',
      blank=True, )

    projectStartDate = models.DateField(
      verbose_name='Project start date', 
      help_text='The starting date of a project related to the resource',
      blank=True, null=True, )

    projectEndDate = models.DateField(
      verbose_name='Project end date', 
      help_text='The end date of a project related to the resources',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class usageInfoType_model(SchemaModel):
    """
    Groups information on usage of the resource (both intended and
    actual use)
    """

    class Meta:
        verbose_name = "Usage"

    __schema_name__ = 'usageInfoType'
    __schema_fields__ = (
      ( u'accessTool', u'accessTool', OPTIONAL ),
      ( u'resourceAssociatedWith', u'resourceAssociatedWith', OPTIONAL ),
      ( u'foreseenUseInfo', u'foreseenuseinfotype_model_set', RECOMMENDED ),
      ( u'actualUseInfo', u'actualUseInfo', RECOMMENDED ),
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

    actualUseInfo = models.ManyToManyField("actualUseInfoType_model", 
      verbose_name='Actual use', blank=True, null=True, related_name="actualUseInfo_%(class)s_related", )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['foreseenUseInfo', 'actualUseInfo', ]
        formatstring = u'foreseen: {} / actual: {}'
        return self.unicode_(formatstring, formatargs)

FORESEENUSEINFOTYPE_FORESEENUSE_CHOICES = _make_choices_from_list([
  u'humanUse', u'nlpApplications', 
])

FORESEENUSEINFOTYPE_USENLPSPECIFIC_CHOICES = _make_choices_from_list([
  u'parsing', u'contradictionDetection', u'opinionMining',
  u'wordSenseDisambiguation',u'voiceControl', u'topicDetection_Tracking',
  u'textualEntailment',u'textMining', u'textCategorisation',
  u'terminologyExtraction',u'summarisation', u'spellChecking',
  u'speechUnderstanding',u'speechToSpeechTranslation', u'speechSynthesis',
  u'speechRecognition',u'signLanguageRecognition',
  u'signLanguageGeneration',u'semanticWeb', u'questionAnswering',
  u'informationExtraction',u'posTagging', u'personIdentification',
  u'naturalLanguageUnderstanding',u'naturalLanguageGeneration',
  u'namedEntityRecognition',u'multimediaDocumentProcessing',
  u'morphosyntacticTagging',u'morphologicalAnalysis', u'linguisticResearch',
  u'lexiconEnhancement',u'lemmatization', u'languageModelsTraining',
  u'languageModelling',u'languageIdentification',
  u'knowledgeRepresentation',u'knowledgeDiscovery', u'emotionRecognition',
  u'emotionGeneration',u'documentClassification',
  u'derivationalMorphologicalAnalysis',u'coreferenceResolution',
  u'bilingualLexiconInduction',u'annotation', u'webServices',
  u'eventExtraction',u'semanticRoleLabelling',
  u'readingAndWritingAidApplications',u'temporalExpressionRecognition',
  u'intra-documentCoreferenceResolution',u'visualSceneUnderstanding',
  u'entityMentionRecognition',u'sentimentAnalysis', u'machineTranslation',
  u'persuasiveExpressionMining',u'qualitativeAnalysis',
  u'texToSpeechSynthesis',u'personRecognition', u'textGeneration',
  u'avatarSynthesis',u'discourseAnalysis', u'expressionRecognition',
  u'faceRecognition',u'faceVerification', u'humanoidAgentSynthesis',
  u'informationRetrieval',u'lexiconAccess',
  u'lexiconAcquisitionFromCorpora',u'lexiconExtractionFromLexica',
  u'lexiconFormatConversion',u'lexiconMerging', u'lexiconVisualization',
  u'lipTrackingAnalysis',u'multimediaDevelopment', u'speakerIdentification',
  u'speakerVerification',u'speechLipsCorrelationAnalysis',
  u'speechAnalysis',u'speechAssistedVideoControl', u'speechVerification',
  u'spokenDialogueSystems',u'talkingHeadSynthesis', u'userAuthentication',
  u'other',
])

# pylint: disable-msg=C0103
class foreseenUseInfoType_model(SchemaModel):
    """
    Groups information on the use for which the resource is created
    """

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
      choices=FORESEENUSEINFOTYPE_FORESEENUSE_CHOICES['choices'],
      )

    useNLPSpecific = MultiSelectField(
      verbose_name='Use nlpspecific', 
      help_text='Specifies the NLP application for which the resource is' \
      'created or the application in which it has actually been used.',
      blank=True, 
      max_length=1 + len(FORESEENUSEINFOTYPE_USENLPSPECIFIC_CHOICES['choices']) / 4,
      choices=FORESEENUSEINFOTYPE_USENLPSPECIFIC_CHOICES['choices'],
      )

    back_to_usageinfotype_model = models.ForeignKey("usageInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

ACTUALUSEINFOTYPE_ACTUALUSE_CHOICES = _make_choices_from_list([
  u'humanUse', u'nlpApplications', 
])

ACTUALUSEINFOTYPE_USENLPSPECIFIC_CHOICES = _make_choices_from_list([
  u'parsing', u'contradictionDetection', u'opinionMining',
  u'wordSenseDisambiguation',u'voiceControl', u'topicDetection_Tracking',
  u'textualEntailment',u'textMining', u'textCategorisation',
  u'terminologyExtraction',u'summarisation', u'spellChecking',
  u'speechUnderstanding',u'speechToSpeechTranslation', u'speechSynthesis',
  u'speechRecognition',u'signLanguageRecognition',
  u'signLanguageGeneration',u'semanticWeb', u'questionAnswering',
  u'informationExtraction',u'posTagging', u'personIdentification',
  u'naturalLanguageUnderstanding',u'naturalLanguageGeneration',
  u'namedEntityRecognition',u'multimediaDocumentProcessing',
  u'morphosyntacticTagging',u'morphologicalAnalysis', u'linguisticResearch',
  u'lexiconEnhancement',u'lemmatization', u'languageModelsTraining',
  u'languageModelling',u'languageIdentification',
  u'knowledgeRepresentation',u'knowledgeDiscovery', u'emotionRecognition',
  u'emotionGeneration',u'documentClassification',
  u'derivationalMorphologicalAnalysis',u'coreferenceResolution',
  u'bilingualLexiconInduction',u'annotation', u'webServices',
  u'eventExtraction',u'semanticRoleLabelling',
  u'readingAndWritingAidApplications',u'temporalExpressionRecognition',
  u'intra-documentCoreferenceResolution',u'visualSceneUnderstanding',
  u'entityMentionRecognition',u'sentimentAnalysis', u'machineTranslation',
  u'persuasiveExpressionMining',u'qualitativeAnalysis',
  u'texToSpeechSynthesis',u'personRecognition', u'textGeneration',
  u'avatarSynthesis',u'discourseAnalysis', u'expressionRecognition',
  u'faceRecognition',u'faceVerification', u'humanoidAgentSynthesis',
  u'informationRetrieval',u'lexiconAccess',
  u'lexiconAcquisitionFromCorpora',u'lexiconExtractionFromLexica',
  u'lexiconFormatConversion',u'lexiconMerging', u'lexiconVisualization',
  u'lipTrackingAnalysis',u'multimediaDevelopment', u'speakerIdentification',
  u'speakerVerification',u'speechLipsCorrelationAnalysis',
  u'speechAnalysis',u'speechAssistedVideoControl', u'speechVerification',
  u'spokenDialogueSystems',u'talkingHeadSynthesis', u'userAuthentication',
  u'other',
])

# pylint: disable-msg=C0103
class actualUseInfoType_model(SchemaModel):
    """
    Groups information on how the resource has already been used
    """

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
      choices=ACTUALUSEINFOTYPE_ACTUALUSE_CHOICES['choices'],
      )

    useNLPSpecific = MultiSelectField(
      verbose_name='Use nlpspecific', 
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

    actualUseDetails = models.CharField(
      verbose_name='Actual use details', 
      help_text='Reports on the usage of the resource in free text',
      blank=True, max_length=250, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['actualUse', 'useNLPSpecific', ]
        formatstring = u'{} {}'
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
      verbose_name='Project', related_name="projectInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

CORPUSAUDIOINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class corpusAudioInfoType_model(SchemaModel):
    """
    Groups together information on the audio module of a corpus
    """

    class Meta:
        verbose_name = "Corpus audio"

    __schema_name__ = 'corpusAudioInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageInfo', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'audioSizeInfo', u'audiosizeinfotype_model_set', REQUIRED ),
      ( u'audioContentInfo', u'audioContentInfo', RECOMMENDED ),
      ( u'settingInfo', u'settingInfo', RECOMMENDED ),
      ( u'audioFormatInfo', u'audioFormatInfo', RECOMMENDED ),
      ( u'annotationInfo', u'annotationInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', RECOMMENDED ),
      ( u'audioClassificationInfo', u'audioClassificationInfo', RECOMMENDED ),
      ( u'recordingInfo', u'recordingInfo', RECOMMENDED ),
      ( u'captureInfo', u'captureInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', OPTIONAL ),
      ( u'linkToOtherMediaInfo', u'linkToOtherMediaInfo', OPTIONAL ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=30,
      choices=CORPUSAUDIOINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    # OneToMany field: audioSizeInfo

    audioContentInfo = models.OneToOneField("audioContentInfoType_model", 
      verbose_name='Audio content', 
      help_text='Groups together information on the contents of the audi' \
      'o part of a resource',
      blank=True, null=True, )

    settingInfo = models.OneToOneField("settingInfoType_model", 
      verbose_name='Setting', 
      help_text='Groups together information on the setting of the audio' \
      ' and/or video part of a resource',
      blank=True, null=True, )

    audioFormatInfo = models.ManyToManyField("audioFormatInfoType_model", 
      verbose_name='Audio format', 
      help_text='Groups together information on the format of the audio ' \
      'part of a resource',
      blank=True, null=True, related_name="audioFormatInfo_%(class)s_related", )

    annotationInfo = models.ManyToManyField("annotationInfoType_model", 
      verbose_name='Annotation', 
      help_text='Groups information on the annotated part(s) of a resour' \
      'ce',
      blank=True, null=True, related_name="annotationInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    audioClassificationInfo = models.ManyToManyField("audioClassificationInfoType_model", 
      verbose_name='Audio classification', 
      help_text='Groups together information on audio type/genre of the ' \
      'resource',
      blank=True, null=True, related_name="audioClassificationInfo_%(class)s_related", )

    recordingInfo = models.OneToOneField("recordingInfoType_model", 
      verbose_name='Recording', 
      help_text='Groups together information on the recording of the aud' \
      'io or video part of a resource',
      blank=True, null=True, )

    captureInfo = models.OneToOneField("captureInfoType_model", 
      verbose_name='Capture', 
      help_text='Groups together information on the capture of the audio' \
      ' or video part of a corpus',
      blank=True, null=True, )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    linkToOtherMediaInfo = models.ManyToManyField("linkToOtherMediaInfoType_model", 
      verbose_name='Link to other media', 
      help_text='Groups information on the way different media of the re' \
      'source interact with or link to each other. To be used for multim' \
      'odal resources or for resources representing sensorimotor data',
      blank=True, null=True, related_name="linkToOtherMediaInfo_%(class)s_related", )

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
  u'notes', u'tempo', u'sounds', u'noise', u'music', u'commercial ',
  u'other',
])

AUDIOCONTENTINFOTYPE_NOISELEVEL_CHOICES = _make_choices_from_list([
  u'low', u'medium', u'high', 
])

# pylint: disable-msg=C0103
class audioContentInfoType_model(SchemaModel):
    """
    Groups together information on the contents of the audio part of a
    resource
    """

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
      verbose_name='Non speech items', 
      help_text='Specifies the distinct elements that maybe included in ' \
      'the audio corpus',
      blank=True, 
      max_length=1 + len(AUDIOCONTENTINFOTYPE_NONSPEECHITEMS_CHOICES['choices']) / 4,
      choices=AUDIOCONTENTINFOTYPE_NONSPEECHITEMS_CHOICES['choices'],
      )

    textualDescription = models.CharField(
      verbose_name='Textual description', 
      help_text='The legend of the soundtrack',
      blank=True, max_length=500, )

    noiseLevel = models.CharField(
      verbose_name='Noise level', 
      help_text='Specifies the level of background noise',
      blank=True, 
      max_length=30,
      choices=AUDIOCONTENTINFOTYPE_NOISELEVEL_CHOICES['choices'],
      )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class audioSizeInfoType_model(SchemaModel):
    """
    SizeInfo Element for Audio parts of a resource
    """

    class Meta:
        verbose_name = "Audio size"

    __schema_name__ = 'audioSizeInfoType'
    __schema_fields__ = (
      ( u'sizeInfo', u'sizeInfo', REQUIRED ),
      ( u'durationOfEffectiveSpeechInfo', u'durationofeffectivespeechinfotype_model_set', OPTIONAL ),
      ( u'durationOfAudioInfo', u'durationofaudioinfotype_model_set', OPTIONAL ),
    )
    __schema_classes__ = {
      u'durationOfAudioInfo': "durationOfAudioInfoType_model",
      u'durationOfEffectiveSpeechInfo': "durationOfEffectiveSpeechInfoType_model",
      u'sizeInfo': "sizeInfoType_model",
    }

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      related_name="sizeInfo_%(class)s_related", )

    # OneToMany field: durationOfEffectiveSpeechInfo

    # OneToMany field: durationOfAudioInfo

    back_to_corpusaudioinfotype_model = models.ForeignKey("corpusAudioInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

DURATIONOFEFFECTIVESPEECHINFOTYPE_DURATIONUNIT_CHOICES = _make_choices_from_list([
  u'hours', u'minutes', u'seconds', 
])

# pylint: disable-msg=C0103
class durationOfEffectiveSpeechInfoType_model(SchemaModel):
    """
    Groups together information on the duration of effective speech
    """

    class Meta:
        verbose_name = "Duration of effective speech"

    __schema_name__ = 'durationOfEffectiveSpeechInfoType'
    __schema_fields__ = (
      ( u'size', u'size', REQUIRED ),
      ( u'durationUnit', u'durationUnit', REQUIRED ),
    )

    size = models.IntegerField(
      verbose_name='Size', 
      help_text='Specifies the size of the resource with regard to the S' \
      'izeUnit measurement in form of a number',
      )

    durationUnit = models.CharField(
      verbose_name='Duration unit', 
      help_text='Specification of the unit of size that is used when pro' \
      'viding information on the size of a resource',
      
      max_length=DURATIONOFEFFECTIVESPEECHINFOTYPE_DURATIONUNIT_CHOICES['max_length'],
      choices=DURATIONOFEFFECTIVESPEECHINFOTYPE_DURATIONUNIT_CHOICES['choices'],
      )

    back_to_audiosizeinfotype_model = models.ForeignKey("audioSizeInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

DURATIONOFAUDIOINFOTYPE_DURATIONUNIT_CHOICES = _make_choices_from_list([
  u'hours', u'minutes', u'seconds', 
])

# pylint: disable-msg=C0103
class durationOfAudioInfoType_model(SchemaModel):
    """
    Groups together information on the size of audio parts; for
    silences, music etc.
    """

    class Meta:
        verbose_name = "Duration of audio"

    __schema_name__ = 'durationOfAudioInfoType'
    __schema_fields__ = (
      ( u'size', u'size', REQUIRED ),
      ( u'durationUnit', u'durationUnit', REQUIRED ),
    )

    size = models.IntegerField(
      verbose_name='Size', 
      help_text='Specifies the size of the resource with regard to the S' \
      'izeUnit measurement in form of a number',
      )

    durationUnit = models.CharField(
      verbose_name='Duration unit', 
      help_text='Specification of the unit of size that is used when pro' \
      'viding information on the size of a resource',
      
      max_length=30,
      choices=DURATIONOFAUDIOINFOTYPE_DURATIONUNIT_CHOICES['choices'],
      )

    back_to_audiosizeinfotype_model = models.ForeignKey("audioSizeInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

AUDIOFORMATINFOTYPE_SIGNALENCODING_CHOICES = _make_choices_from_list([
  u'aLaw', u'linearPCM', u'\xb5-law', u'ADPCM', u'other', 
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

AUDIOFORMATINFOTYPE_RECORDINGQUALITY_CHOICES = _make_choices_from_list([
  u'veryLow', u'low', u'medium', u'high', u'veryHigh', 
])

# pylint: disable-msg=C0103
class audioFormatInfoType_model(SchemaModel):
    """
    Groups together information on the format of the audio part of a
    resource
    """

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
      verbose_name='Mime', 
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts; value to be taken from a subset of the official mime ' \
      'types of the Internet Assigned Numbers Authority (http://www.iana' \
      '.org/)',
      max_length=1000, )

    signalEncoding = MultiSelectField(
      verbose_name='Signal encoding', 
      help_text='Specifies the encoding the audio type uses',
      blank=True, 
      max_length=1 + len(AUDIOFORMATINFOTYPE_SIGNALENCODING_CHOICES['choices']) / 4,
      choices=AUDIOFORMATINFOTYPE_SIGNALENCODING_CHOICES['choices'],
      )

    samplingRate = models.IntegerField(
      verbose_name='Sampling rate', 
      help_text='Specifies the format of files contained in the resource' \
      ' in Hertz',
      blank=True, null=True, )

    quantization = models.IntegerField(
      verbose_name='Quantization', 
      help_text='The number of bits for each audio sample',
      blank=True, null=True, )

    byteOrder = models.CharField(
      verbose_name='Byte order', 
      help_text='The byte order of 2 or more bytes sample',
      blank=True, 
      max_length=30,
      choices=AUDIOFORMATINFOTYPE_BYTEORDER_CHOICES['choices'],
      )

    signConvention = models.CharField(
      verbose_name='Sign convention', 
      help_text='Binary representation of numbers',
      blank=True, 
      max_length=30,
      choices=AUDIOFORMATINFOTYPE_SIGNCONVENTION_CHOICES['choices'],
      )

    compressionInfo = models.OneToOneField("compressionInfoType_model", 
      verbose_name='Compression', 
      help_text='Groups together information on the compression status a' \
      'nd method of a resource',
      blank=True, null=True, )

    audioQualityMeasuresIncluded = models.CharField(
      verbose_name='Audio quality measures included', 
      help_text='Specifies the audio quality measures',
      blank=True, 
      max_length=30,
      choices=AUDIOFORMATINFOTYPE_AUDIOQUALITYMEASURESINCLUDED_CHOICES['choices'],
      )

    numberOfTracks = models.IntegerField(
      verbose_name='Number of tracks', 
      help_text='Specifies the number of audio channels',
      blank=True, null=True, )

    recordingQuality = models.CharField(
      verbose_name='Recording quality', 
      help_text='Indication of the audio or video recording quality',
      blank=True, 
      max_length=30,
      choices=AUDIOFORMATINFOTYPE_RECORDINGQUALITY_CHOICES['choices'],
      )

    sizePerAudioFormat = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per audio format', 
      help_text='Used to give info on size of parts of a resource that d' \
      'iffer as to the format',
      blank=True, null=True, )

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
])

AUDIOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other', 
])

# pylint: disable-msg=C0103
class audioClassificationInfoType_model(SchemaModel):
    """
    Groups together information on audio type/genre of the resource
    """

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
      choices=AUDIOCLASSIFICATIONINFOTYPE_AUDIOGENRE_CHOICES['choices'],
      )

    speechGenre = models.CharField(
      verbose_name='Speech genre', 
      help_text='The conventionalized discourse of the content of the re' \
      'source, based on extra-linguistic and internal linguistic criteri' \
      'a; the values here are intended only for speech',
      blank=True, 
      max_length=30,
      choices=AUDIOCLASSIFICATIONINFOTYPE_SPEECHGENRE_CHOICES['choices'],
      )

    subject_topic = models.CharField(
      verbose_name='Subject_topic', 
      help_text='For corpora that have already been using subject classi' \
      'fication',
      blank=True, max_length=500, )

    register = models.CharField(
      verbose_name='Register', 
      help_text='For corpora that have already been using register class' \
      'ification',
      blank=True, max_length=500, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme', 
      help_text='Specifies the external classification schemes',
      blank=True, 
      max_length=AUDIOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['max_length'],
      choices=AUDIOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
      )

    sizePerAudioClassification = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per audio classification', 
      help_text='The size of the audio subparts of the resource in terms' \
      ' of classification criteria',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

CORPUSTEXTINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class corpusTextInfoType_model(SchemaModel):
    """
    Groups together information on the text component of a resource
    """

    class Meta:
        verbose_name = "Corpus text"

    __schema_name__ = 'corpusTextInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageInfo', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', REQUIRED ),
      ( u'textFormatInfo', u'textFormatInfo', RECOMMENDED ),
      ( u'characterEncodingInfo', u'characterEncodingInfo', RECOMMENDED ),
      ( u'annotationInfo', u'annotationInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', RECOMMENDED ),
      ( u'textClassificationInfo', u'textClassificationInfo', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linkToOtherMediaInfo', OPTIONAL ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=30,
      choices=CORPUSTEXTINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      related_name="sizeInfo_%(class)s_related", )

    textFormatInfo = models.ManyToManyField("textFormatInfoType_model", 
      verbose_name='Text format', 
      help_text='Groups information on the text format(s) of a resource',
      blank=True, null=True, related_name="textFormatInfo_%(class)s_related", )

    characterEncodingInfo = models.ManyToManyField("characterEncodingInfoType_model", 
      verbose_name='Character encoding', 
      help_text='Groups together information on character encoding of th' \
      'e resource',
      blank=True, null=True, related_name="characterEncodingInfo_%(class)s_related", )

    annotationInfo = models.ManyToManyField("annotationInfoType_model", 
      verbose_name='Annotation', 
      help_text='Groups information on the annotated part(s) of a resour' \
      'ce',
      blank=True, null=True, related_name="annotationInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    textClassificationInfo = models.ManyToManyField("textClassificationInfoType_model", 
      verbose_name='Text classification', 
      help_text='Groups together information on text type/genre of the r' \
      'esource',
      blank=True, null=True, related_name="textClassificationInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    linkToOtherMediaInfo = models.ManyToManyField("linkToOtherMediaInfoType_model", 
      verbose_name='Link to other media', 
      help_text='Groups information on the way different media of the re' \
      'source interact with or link to each other. To be used for multim' \
      'odal resources or for resources representing sensorimotor data',
      blank=True, null=True, related_name="linkToOtherMediaInfo_%(class)s_related", )

    back_to_corpusmediatypetype_model = models.ForeignKey("corpusMediaTypeType_model",  null=True)

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['lingualityInfo', 'languageInfo', ]
        formatstring = u'text ({} {})'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class textFormatInfoType_model(SchemaModel):
    """
    Groups information on the text format(s) of a resource
    """

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
      verbose_name='Mime', 
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts; value to be taken from a subset of the official mime ' \
      'types of the Internet Assigned Numbers Authority (http://www.iana' \
      '.org/)',
      max_length=50, )

    sizePerTextFormat = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per text format', 
      help_text='Provides information on the size of the resource parts ' \
      'with different format',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

TEXTCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other', 
])

# pylint: disable-msg=C0103
class textClassificationInfoType_model(SchemaModel):
    """
    Groups together information on text type/genre of the resource
    """

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

    textGenre = models.CharField(
      verbose_name='Text genre', 
      help_text='Genre: The conventionalized discourse or text types of ' \
      'the content of the resource, based on extra-linguistic and intern' \
      'al linguistic criteria',
      blank=True, max_length=50, )

    textType = models.CharField(
      verbose_name='Text', 
      help_text='Specifies the type of the text according to a text type' \
      ' classification',
      blank=True, max_length=50, )

    register = models.CharField(
      verbose_name='Register', 
      help_text='For corpora that have already been using register class' \
      'ification',
      blank=True, max_length=500, )

    subject_topic = models.CharField(
      verbose_name='Subject_topic', 
      help_text='For corpora that have already been using subject classi' \
      'fication',
      blank=True, max_length=500, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme', 
      help_text='Specifies the external classification schemes',
      blank=True, 
      max_length=TEXTCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['max_length'],
      choices=TEXTCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
      )

    sizePerTextClassification = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per text classification', 
      help_text='Provides information on size of resource parts with dif' \
      'ferent text classification',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

CORPUSVIDEOINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

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
      ( u'languageInfo', u'languageInfo', OPTIONAL ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', REQUIRED ),
      ( u'videoContentInfo', u'videoContentInfo', RECOMMENDED ),
      ( u'settingInfo', u'settingInfo', RECOMMENDED ),
      ( u'videoFormatInfo', u'videoFormatInfo', RECOMMENDED ),
      ( u'annotationInfo', u'annotationInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', RECOMMENDED ),
      ( u'videoClassificationInfo', u'videoclassificationinfotype_model_set', RECOMMENDED ),
      ( u'recordingInfo', u'recordingInfo', RECOMMENDED ),
      ( u'captureInfo', u'captureInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linkToOtherMediaInfo', RECOMMENDED ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=30,
      choices=CORPUSVIDEOINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      blank=True, null=True, related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.OneToOneField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      related_name="sizeInfo_%(class)s_related", )

    videoContentInfo = models.OneToOneField("videoContentInfoType_model", 
      verbose_name='Video content', 
      help_text='Groups together information on the contents of the vide' \
      'o part of a resource',
      blank=True, null=True, )

    settingInfo = models.OneToOneField("settingInfoType_model", 
      verbose_name='Setting', 
      help_text='Groups together information on the setting of the audio' \
      ' and/or video part of a resource',
      blank=True, null=True, )

    videoFormatInfo = models.ManyToManyField("videoFormatInfoType_model", 
      verbose_name='Video format', 
      help_text='Groups information on the format(s) of a resource; repe' \
      'ated if parts of the resource are in different formats',
      blank=True, null=True, related_name="videoFormatInfo_%(class)s_related", )

    annotationInfo = models.ManyToManyField("annotationInfoType_model", 
      verbose_name='Annotation', 
      help_text='Groups information on the annotated part(s) of a resour' \
      'ce',
      blank=True, null=True, related_name="annotationInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    # OneToMany field: videoClassificationInfo

    recordingInfo = models.OneToOneField("recordingInfoType_model", 
      verbose_name='Recording', 
      help_text='Groups together information on the recording of the aud' \
      'io or video part of a resource',
      blank=True, null=True, )

    captureInfo = models.OneToOneField("captureInfoType_model", 
      verbose_name='Capture', 
      help_text='Groups together information on the capture of the audio' \
      ' or video part of a corpus',
      blank=True, null=True, )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    linkToOtherMediaInfo = models.ManyToManyField("linkToOtherMediaInfoType_model", 
      verbose_name='Link to other media', 
      help_text='Groups information on the way different media of the re' \
      'source interact with or link to each other. To be used for multim' \
      'odal resources or for resources representing sensorimotor data',
      blank=True, null=True, related_name="linkToOtherMediaInfo_%(class)s_related", )

    back_to_corpusmediatypetype_model = models.ForeignKey("corpusMediaTypeType_model",  null=True)

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
    """
    Groups together information on the contents of the video part of a
    resource
    """

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

    typeOfVideoContent = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=36), 
      verbose_name='Type of video content', 
      help_text='Main type of object or people represented in the video',
      )

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
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

VIDEOFORMATINFOTYPE_COLOURSPACE_CHOICES = _make_choices_from_list([
  u'RGB', u'CMYK', u'4:2:2', u'YUV', 
])

VIDEOFORMATINFOTYPE_VISUALMODELLING_CHOICES = _make_choices_from_list([
  u'2D', u'3D', 
])

# pylint: disable-msg=C0103
class videoFormatInfoType_model(SchemaModel):
    """
    Groups information on the format(s) of a resource; repeated if parts
    of the resource are in different formats
    """

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
      verbose_name='Mime', 
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts; value to be taken from a subset of the official mime ' \
      'types of the Internet Assigned Numbers Authority (http://www.iana' \
      '.org/)',
      max_length=1000, )

    colourSpace = MultiSelectField(
      verbose_name='Colour space', 
      help_text='Defines the colour space for the video',
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
      max_length=VIDEOFORMATINFOTYPE_VISUALMODELLING_CHOICES['max_length'],
      choices=VIDEOFORMATINFOTYPE_VISUALMODELLING_CHOICES['choices'],
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
      blank=True, null=True, )

    sizePerVideoFormat = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per video format', 
      help_text='Used to give info on size of parts of a resource that d' \
      'iffer as to the format',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

VIDEOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'libraryOfCongress_domainClassification',
  u'libraryofCongressSubjectHeadings_classification',u'MeSH_classification',
  u'NLK_classification',u'PAROLE_topicClassification',
  u'PAROLE_genreClassification',u'UDC_classification', u'other', 
])

# pylint: disable-msg=C0103
class videoClassificationInfoType_model(SchemaModel):
    """
    Groups together information on video genre of the resource
    """

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

    videoGenre = models.CharField(
      verbose_name='Video genre', 
      help_text='A first indication of type of video recorded',
      blank=True, max_length=1000, )

    subject_topic = models.CharField(
      verbose_name='Subject_topic', 
      help_text='For corpora that have already been using subject classi' \
      'fication',
      blank=True, max_length=1000, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme', 
      help_text='Specifies the external classification schemes',
      blank=True, 
      max_length=VIDEOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['max_length'],
      choices=VIDEOCLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
      )

    sizePerVideoClassification = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per video classification', 
      help_text='Used to give info on size of parts with different video' \
      ' classification',
      blank=True, null=True, )

    back_to_corpusvideoinfotype_model = models.ForeignKey("corpusVideoInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

CORPUSIMAGEINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class corpusImageInfoType_model(SchemaModel):
    """
    Groups together information on the image component of a resource
    """

    class Meta:
        verbose_name = "Corpus image"

    __schema_name__ = 'corpusImageInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageInfo', OPTIONAL ),
      ( u'sizeInfo', u'sizeInfo', REQUIRED ),
      ( u'imageContentInfo', u'imageContentInfo', RECOMMENDED ),
      ( u'imageFormatInfo', u'imageFormatInfo', RECOMMENDED ),
      ( u'annotationInfo', u'annotationInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', OPTIONAL ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', OPTIONAL ),
      ( u'imageClassificationInfo', u'imageclassificationinfotype_model_set', OPTIONAL ),
      ( u'captureInfo', u'captureInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', OPTIONAL ),
      ( u'linkToOtherMediaInfo', u'linkToOtherMediaInfo', OPTIONAL ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=30,
      choices=CORPUSIMAGEINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      blank=True, null=True, related_name="languageInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      related_name="sizeInfo_%(class)s_related", )

    imageContentInfo = models.OneToOneField("imageContentInfoType_model", 
      verbose_name='Image content', 
      help_text='Groups together information on the contents of the imag' \
      'e part of a resource',
      blank=True, null=True, )

    imageFormatInfo = models.ManyToManyField("imageFormatInfoType_model", 
      verbose_name='Image format', 
      help_text='Groups information on the format of the image component' \
      ' of the resource',
      blank=True, null=True, related_name="imageFormatInfo_%(class)s_related", )

    annotationInfo = models.ManyToManyField("annotationInfoType_model", 
      verbose_name='Annotation', 
      help_text='Groups information on the annotated part(s) of a resour' \
      'ce',
      blank=True, null=True, related_name="annotationInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    # OneToMany field: imageClassificationInfo

    captureInfo = models.OneToOneField("captureInfoType_model", 
      verbose_name='Capture', 
      help_text='Groups together information on the capture of the audio' \
      ' or video part of a corpus',
      blank=True, null=True, )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    linkToOtherMediaInfo = models.ManyToManyField("linkToOtherMediaInfoType_model", 
      verbose_name='Link to other media', 
      help_text='Groups information on the way different media of the re' \
      'source interact with or link to each other. To be used for multim' \
      'odal resources or for resources representing sensorimotor data',
      blank=True, null=True, related_name="linkToOtherMediaInfo_%(class)s_related", )

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
    """
    Groups together information on the contents of the image part of a
    resource
    """

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

    typeOfImageContent = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=37), 
      verbose_name='Type of image content', 
      help_text='The main types of object or people represented in the i' \
      'mage corpus',
      )

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
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

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
    """
    Groups information on the format of the image component of the
    resource
    """

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
      verbose_name='Mime', 
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts; value to be taken from a subset of the official mime ' \
      'types of the Internet Assigned Numbers Authority (http://www.iana' \
      '.org/)',
      max_length=1000, )

    colourSpace = MultiSelectField(
      verbose_name='Colour space', 
      help_text='Defines the colour space for the video',
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
      choices=IMAGEFORMATINFOTYPE_VISUALMODELLING_CHOICES['choices'],
      )

    rasterOrVectorGraphics = models.CharField(
      verbose_name='Raster or vector graphics', 
      help_text='Indicates if the image is stored as raster or vector gr' \
      'aphics',
      blank=True, 
      max_length=30,
      choices=IMAGEFORMATINFOTYPE_RASTERORVECTORGRAPHICS_CHOICES['choices'],
      )

    quality = models.CharField(
      verbose_name='Quality', 
      help_text='Specifies the quality level of image resource',
      blank=True, 
      max_length=30,
      choices=IMAGEFORMATINFOTYPE_QUALITY_CHOICES['choices'],
      )

    sizePerImageFormat = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per image format', 
      help_text='Used to give info on size of parts of a resource that d' \
      'iffer as to the format',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

IMAGECLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES = _make_choices_from_list([
  u'ANC_domainClassification', u'ANC_genreClassification',
  u'BNC_domainClassification',u'BNC_textTypeClassification',
  u'DDC_classification',u'libraryOfCongress_domainClassification',
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

    imageGenre = models.CharField(
      verbose_name='Image genre', 
      help_text='A first indication of the genre of images',
      blank=True, max_length=1000, )

    subject_topic = models.CharField(
      verbose_name='Subject_topic', 
      help_text='For corpora that have already been using subject classi' \
      'fication',
      blank=True, max_length=1000, )

    conformanceToClassificationScheme = models.CharField(
      verbose_name='Conformance to classification scheme', 
      help_text='Specifies the external classification schemes',
      blank=True, 
      max_length=IMAGECLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['max_length'],
      choices=IMAGECLASSIFICATIONINFOTYPE_CONFORMANCETOCLASSIFICATIONSCHEME_CHOICES['choices'],
      )

    sizePerImageClassification = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per image classification', 
      help_text='Provides information on size of parts with different im' \
      'age classification',
      blank=True, null=True, )

    back_to_corpusimageinfotype_model = models.ForeignKey("corpusImageInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

CORPUSTEXTNUMERICALINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class corpusTextNumericalInfoType_model(SchemaModel):
    """
    Groups together information on the textNumerical component of a
    corpus. It is used basically for the textual representation of
    measurements and observations linked to sensorimotor recordings
    """

    class Meta:
        verbose_name = "Corpus text numerical"

    __schema_name__ = 'corpusTextNumericalInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', RECOMMENDED ),
      ( u'textNumericalContentInfo', u'textNumericalContentInfo', RECOMMENDED ),
      ( u'textNumericalFormatInfo', u'textnumericalformatinfotype_model_set', RECOMMENDED ),
      ( u'recordingInfo', u'recordingInfo', RECOMMENDED ),
      ( u'captureInfo', u'captureInfo', RECOMMENDED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'annotationInfo', u'annotationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linkToOtherMediaInfo', RECOMMENDED ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=30,
      choices=CORPUSTEXTNUMERICALINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      blank=True, null=True, related_name="sizeInfo_%(class)s_related", )

    textNumericalContentInfo = models.OneToOneField("textNumericalContentInfoType_model", 
      verbose_name='Text numerical content', 
      help_text='Groups information on the content of the textNumerical ' \
      'part of the resource',
      blank=True, null=True, )

    # OneToMany field: textNumericalFormatInfo

    recordingInfo = models.OneToOneField("recordingInfoType_model", 
      verbose_name='Recording', 
      help_text='Groups together information on the recording of the aud' \
      'io or video part of a resource',
      blank=True, null=True, )

    captureInfo = models.OneToOneField("captureInfoType_model", 
      verbose_name='Capture', 
      help_text='Groups together information on the capture of the audio' \
      ' or video part of a corpus',
      blank=True, null=True, )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    annotationInfo = models.OneToOneField("annotationInfoType_model", 
      verbose_name='Annotation', 
      help_text='Groups information on the annotated part(s) of a resour' \
      'ce',
      blank=True, null=True, )

    linkToOtherMediaInfo = models.ManyToManyField("linkToOtherMediaInfoType_model", 
      verbose_name='Link to other media', 
      help_text='Groups information on the way different media of the re' \
      'source interact with or link to each other. To be used for multim' \
      'odal resources or for resources representing sensorimotor data',
      blank=True, null=True, related_name="linkToOtherMediaInfo_%(class)s_related", )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['modalityInfo', 'sizeInfo', ]
        formatstring = u'textNumerical ({} {})'
        return self.unicode_(formatstring, formatargs)

# pylint: disable-msg=C0103
class textNumericalContentInfoType_model(SchemaModel):
    """
    Groups information on the content of the textNumerical part of the
    resource
    """

    class Meta:
        verbose_name = "Text numerical content"

    __schema_name__ = 'textNumericalContentInfoType'
    __schema_fields__ = (
      ( u'typeOfTextNumericalContent', u'typeOfTextNumericalContent', REQUIRED ),
    )

    typeOfTextNumericalContent = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=38), 
      verbose_name='Type of text numerical content', 
      help_text='Specifies the content that is represented in the textNu' \
      'merical part of the resource',
      )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class textNumericalFormatInfoType_model(SchemaModel):
    """
    Groups information on the format(s) of the textNumerical part of the
    resource
    """

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
      verbose_name='Mime', 
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts; value to be taken from a subset of the official mime ' \
      'types of the Internet Assigned Numbers Authority (http://www.iana' \
      '.org/)',
      max_length=1000, )

    sizePerTextNumericalFormat = models.OneToOneField("sizeInfoType_model", 
      verbose_name='Size per text numerical format', 
      help_text='Gives information on the size of textNumerical resource' \
      ' parts with different format',
      blank=True, null=True, )

    back_to_corpustextnumericalinfotype_model = models.ForeignKey("corpusTextNumericalInfoType_model", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

CORPUSTEXTNGRAMINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class corpusTextNgramInfoType_model(SchemaModel):
    """
    Groups together information required for n-gram resources;
    information can be provided both as regards features drawn from
    the source corpus (e.g. language coverage, size, format, domains
    etc.) and features pertaining to the n-gram output itself (e.g.
    range of n-grams, type of item included, etc.)
    """

    class Meta:
        verbose_name = "Corpus text ngram"

    __schema_name__ = 'corpusTextNgramInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'ngramInfo', u'ngramInfo', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageInfo', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', REQUIRED ),
      ( u'textFormatInfo', u'textFormatInfo', RECOMMENDED ),
      ( u'characterEncodingInfo', u'characterEncodingInfo', RECOMMENDED ),
      ( u'annotationInfo', u'annotationInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', RECOMMENDED ),
      ( u'textClassificationInfo', u'textClassificationInfo', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', RECOMMENDED ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=30,
      choices=CORPUSTEXTNGRAMINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    ngramInfo = models.OneToOneField("ngramInfoType_model", 
      verbose_name='Ngram', )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.OneToOneField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      related_name="sizeInfo_%(class)s_related", )

    textFormatInfo = models.ManyToManyField("textFormatInfoType_model", 
      verbose_name='Text format', 
      help_text='Groups information on the text format(s) of a resource',
      blank=True, null=True, related_name="textFormatInfo_%(class)s_related", )

    characterEncodingInfo = models.ManyToManyField("characterEncodingInfoType_model", 
      verbose_name='Character encoding', 
      help_text='Groups together information on character encoding of th' \
      'e resource',
      blank=True, null=True, related_name="characterEncodingInfo_%(class)s_related", )

    annotationInfo = models.ManyToManyField("annotationInfoType_model", 
      verbose_name='Annotation', 
      help_text='Groups information on the annotated part(s) of a resour' \
      'ce',
      blank=True, null=True, related_name="annotationInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    textClassificationInfo = models.ManyToManyField("textClassificationInfoType_model", 
      verbose_name='Text classification', 
      help_text='Groups together information on text type/genre of the r' \
      'esource',
      blank=True, null=True, related_name="textClassificationInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

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
    """
    Groups information specific to n-gram resources (e.g. range of
    n-grams, base item etc.)
    """

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

    factors = MultiTextField(max_length=150, widget = MultiFieldWidget(widget_id=39), 
      verbose_name='Factors', 
      help_text='The list of factors that have been used for the n-gram ' \
      'model',
      blank=True, )

    smoothing = models.CharField(
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
    """
    Groups together information on requirements for lexica set by the
    LanguageDescriptions
    """

    class Meta:
        verbose_name = "Related lexicon"

    __schema_name__ = 'relatedLexiconInfoType'
    __schema_fields__ = (
      ( u'relatedLexiconType', u'relatedLexiconType', REQUIRED ),
      ( u'attachedLexiconPosition', u'attachedLexiconPosition', OPTIONAL ),
      ( u'compatibleLexiconType', u'compatibleLexiconType', OPTIONAL ),
    )

    relatedLexiconType = models.CharField(
      verbose_name='Related lexicon', 
      help_text='Indicates the position of the lexica that must or can b' \
      'e used with the grammar',
      
      max_length=30,
      choices=RELATEDLEXICONINFOTYPE_RELATEDLEXICONTYPE_CHOICES['choices'],
      )

    attachedLexiconPosition = models.CharField(
      verbose_name='Attached lexicon position', 
      help_text='Indicates the position of the lexicon, if attached to t' \
      'he grammar',
      blank=True, max_length=500, )

    compatibleLexiconType = MultiSelectField(
      verbose_name='Compatible lexicon', 
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
    """
    Groups together information on the contents of the
    LanguageDescriptions
    """

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
      help_text='Information on the linguistic levels covered by the res' \
      'ource (grammar or lexical/conceptual resource)',
      
      max_length=1 + len(LANGUAGEDESCRIPTIONENCODINGINFOTYPE_ENCODINGLEVEL_CHOICES['choices']) / 4,
      choices=LANGUAGEDESCRIPTIONENCODINGINFOTYPE_ENCODINGLEVEL_CHOICES['choices'],
      )

    conformanceToStandardsBestPractices = MultiTextField(max_length=500, widget = MultiFieldWidget(widget_id=40), 
      verbose_name='Conformance to standards best practices', 
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True, )

    theoreticModel = MultiTextField(max_length=500, widget = MultiFieldWidget(widget_id=41), 
      verbose_name='Theoretic model', 
      help_text='Name of the theoretic model applied for the creation/en' \
      'richment of the resource, and/or reference (URL or bibliographic ' \
      'reference) to informative material about the theoretic model used' \
      '',
      blank=True, )

    formalism = models.CharField(
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
    """
    Groups together information on the operation requirements of the
    Language Descriptions
    """

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
      blank=True, null=True, )

    relatedLexiconInfo = models.OneToOneField("relatedLexiconInfoType_model", 
      verbose_name='Related lexicon', 
      help_text='Groups together information on requirements for lexica ' \
      'set by the LanguageDescriptions',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class languageDescriptionPerformanceInfoType_model(SchemaModel):
    """
    Groups together information on the performance of the Language
    Descriptions
    """

    class Meta:
        verbose_name = "Language description performance"

    __schema_name__ = 'languageDescriptionPerformanceInfoType'
    __schema_fields__ = (
      ( u'robustness', u'robustness', RECOMMENDED ),
      ( u'shallowness', u'shallowness', RECOMMENDED ),
      ( u'output', u'output', RECOMMENDED ),
    )

    robustness = models.CharField(
      verbose_name='Robustness', 
      help_text='Free text statement on the robustness of the grammar (h' \
      'ow well the grammar can cope with misspelt/unknown etc. input, i.' \
      'e. whether it can produce even partial interpretations of the inp' \
      'ut)',
      blank=True, max_length=500, )

    shallowness = models.CharField(
      verbose_name='Shallowness', 
      help_text='Free text statement on the shallowness of the grammar (' \
      'how deep the syntactic analysis performed by the grammar can be)',
      blank=True, max_length=200, )

    output = models.CharField(
      verbose_name='Output', 
      help_text='Indicates whether the output of the operation of the gr' \
      'ammar is a statement of grammaticality (grammatical/ungrammatical' \
      ') or structures (interpretation of the input)',
      blank=True, max_length=500, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LANGUAGEDESCRIPTIONTEXTINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class languageDescriptionTextInfoType_model(SchemaModel):
    """
    Groups together all information relevant to the text module of a
    language description (e.g. format, languages, size etc.); it is
    obligatory for all language descriptions
    """

    class Meta:
        verbose_name = "Language description text"

    __schema_name__ = 'languageDescriptionTextInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linkToOtherMediaInfo', OPTIONAL ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageInfo', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', RECOMMENDED ),
      ( u'textFormatInfo', u'textFormatInfo', RECOMMENDED ),
      ( u'characterEncodingInfo', u'characterEncodingInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', RECOMMENDED ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=LANGUAGEDESCRIPTIONTEXTINFOTYPE_MEDIATYPE_CHOICES['max_length'],
      choices=LANGUAGEDESCRIPTIONTEXTINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    linkToOtherMediaInfo = models.ManyToManyField("linkToOtherMediaInfoType_model", 
      verbose_name='Link to other media', 
      help_text='Groups information on the way different media of the re' \
      'source interact with or link to each other. To be used for multim' \
      'odal resources or for resources representing sensorimotor data',
      blank=True, null=True, related_name="linkToOtherMediaInfo_%(class)s_related", )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.OneToOneField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      blank=True, null=True, related_name="sizeInfo_%(class)s_related", )

    textFormatInfo = models.ManyToManyField("textFormatInfoType_model", 
      verbose_name='Text format', 
      help_text='Groups information on the text format(s) of a resource',
      blank=True, null=True, related_name="textFormatInfo_%(class)s_related", )

    characterEncodingInfo = models.ManyToManyField("characterEncodingInfoType_model", 
      verbose_name='Character encoding', 
      help_text='Groups together information on character encoding of th' \
      'e resource',
      blank=True, null=True, related_name="characterEncodingInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LANGUAGEDESCRIPTIONVIDEOINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class languageDescriptionVideoInfoType_model(SchemaModel):
    """
    Groups together all information relevant to the video parts of a
    language description (e.g. format, languages, size etc.), if
    there are any (e.g. for sign language grammars)
    """

    class Meta:
        verbose_name = "Language description video"

    __schema_name__ = 'languageDescriptionVideoInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linkToOtherMediaInfo', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageInfo', OPTIONAL ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', RECOMMENDED ),
      ( u'videoContentInfo', u'videoContentInfo', RECOMMENDED ),
      ( u'videoFormatInfo', u'videoFormatInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', RECOMMENDED ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', RECOMMENDED ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', RECOMMENDED ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=LANGUAGEDESCRIPTIONVIDEOINFOTYPE_MEDIATYPE_CHOICES['max_length'],
      choices=LANGUAGEDESCRIPTIONVIDEOINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    linkToOtherMediaInfo = models.ManyToManyField("linkToOtherMediaInfoType_model", 
      verbose_name='Link to other media', 
      help_text='Groups information on the way different media of the re' \
      'source interact with or link to each other. To be used for multim' \
      'odal resources or for resources representing sensorimotor data',
      related_name="linkToOtherMediaInfo_%(class)s_related", )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      blank=True, null=True, related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      blank=True, null=True, related_name="sizeInfo_%(class)s_related", )

    videoContentInfo = models.OneToOneField("videoContentInfoType_model", 
      verbose_name='Video content', 
      help_text='Groups together information on the contents of the vide' \
      'o part of a resource',
      blank=True, null=True, )

    videoFormatInfo = models.ManyToManyField("videoFormatInfoType_model", 
      verbose_name='Video format', 
      help_text='Groups information on the format(s) of a resource; repe' \
      'ated if parts of the resource are in different formats',
      blank=True, null=True, related_name="videoFormatInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LANGUAGEDESCRIPTIONIMAGEINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class languageDescriptionImageInfoType_model(SchemaModel):
    """
    Groups together all information relevant to the image module of a
    language description (e.g. format, languages, size etc.), if
    there are any (e.g. for sign language grammars)
    """

    class Meta:
        verbose_name = "Language description image"

    __schema_name__ = 'languageDescriptionImageInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageInfo', OPTIONAL ),
      ( u'creationInfo', u'creationInfo', RECOMMENDED ),
      ( u'linkToOtherMediaInfo', u'linkToOtherMediaInfo', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', RECOMMENDED ),
      ( u'imageContentInfo', u'imageContentInfo', RECOMMENDED ),
      ( u'imageFormatInfo', u'imageFormatInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', OPTIONAL ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', OPTIONAL ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=LANGUAGEDESCRIPTIONIMAGEINFOTYPE_MEDIATYPE_CHOICES['max_length'],
      choices=LANGUAGEDESCRIPTIONIMAGEINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      blank=True, null=True, related_name="languageInfo_%(class)s_related", )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    linkToOtherMediaInfo = models.ManyToManyField("linkToOtherMediaInfoType_model", 
      verbose_name='Link to other media', 
      help_text='Groups information on the way different media of the re' \
      'source interact with or link to each other. To be used for multim' \
      'odal resources or for resources representing sensorimotor data',
      related_name="linkToOtherMediaInfo_%(class)s_related", )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      blank=True, null=True, related_name="sizeInfo_%(class)s_related", )

    imageContentInfo = models.OneToOneField("imageContentInfoType_model", 
      verbose_name='Image content', 
      help_text='Groups together information on the contents of the imag' \
      'e part of a resource',
      blank=True, null=True, )

    imageFormatInfo = models.ManyToManyField("imageFormatInfoType_model", 
      verbose_name='Image format', 
      help_text='Groups information on the format of the image component' \
      ' of the resource',
      blank=True, null=True, related_name="imageFormatInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

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

LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATION_CHOICES = _make_choices_from_list([
  u'images', u'videos', u'soundRecordings', u'other', 
])

LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATIONUNIT_CHOICES = _make_choices_from_list([
  u'word', u'lemma', u'semantics', u'example', u'syntax', u'lexicalUnit',
  u'other',
])

# pylint: disable-msg=C0103
class lexicalConceptualResourceEncodingInfoType_model(SchemaModel):
    """
    Groups all information regarding the contents of lexical/conceptual
    resources
    """

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
      verbose_name='Linguisticrmation', 
      help_text='A more detailed account of the linguistic information c' \
      'ontained in the lexicalConceptualResource',
      blank=True, 
      max_length=1 + len(LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_LINGUISTICINFORMATION_CHOICES['choices']) / 4,
      choices=LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_LINGUISTICINFORMATION_CHOICES['choices'],
      )

    conformanceToStandardsBestPractices = MultiTextField(max_length=500, widget = MultiFieldWidget(widget_id=42), 
      verbose_name='Conformance to standards best practices', 
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True, )

    theoreticModel = MultiTextField(max_length=500, widget = MultiFieldWidget(widget_id=43), 
      verbose_name='Theoretic model', 
      help_text='Name of the theoretic model applied for the creation/en' \
      'richment of the resource, and/or reference (URL or bibliographic ' \
      'reference) to informative material about the theoretic model used' \
      '',
      blank=True, )

    externalRef = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=44), 
      verbose_name='External ref', 
      help_text='Another resource to which the lexicalConceptualResource' \
      ' is linked (e.g. link to a wordnet or ontology)',
      blank=True, )

    extratextualInformation = MultiSelectField(
      verbose_name='Extratextualrmation', 
      help_text='An indication of the extratextual information contained' \
      ' in the lexicalConceptualResouce; can be used as an alternative t' \
      'o audio, image, videos etc. for cases where these are not conside' \
      'red an important part of the lcr',
      blank=True, 
      max_length=1 + len(LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATION_CHOICES['choices']) / 4,
      choices=LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATION_CHOICES['choices'],
      )

    extraTextualInformationUnit = MultiSelectField(
      verbose_name='Extra textualrmation unit', 
      help_text='The unit of the extratextual information contained in t' \
      'he lexical conceptual resource',
      blank=True, 
      max_length=1 + len(LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATIONUNIT_CHOICES['choices']) / 4,
      choices=LEXICALCONCEPTUALRESOURCEENCODINGINFOTYPE_EXTRATEXTUALINFORMATIONUNIT_CHOICES['choices'],
      )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LEXICALCONCEPTUALRESOURCEAUDIOINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class lexicalConceptualResourceAudioInfoType_model(SchemaModel):
    """
    Groups information on the audio part of the lexical/conceptual
    resource
    """

    class Meta:
        verbose_name = "Lexical conceptual resource audio"

    __schema_name__ = 'lexicalConceptualResourceAudioInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageInfo', OPTIONAL ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', RECOMMENDED ),
      ( u'audioContentInfo', u'audioContentInfo', RECOMMENDED ),
      ( u'audioFormatInfo', u'audioFormatInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', OPTIONAL ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', OPTIONAL ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=LEXICALCONCEPTUALRESOURCEAUDIOINFOTYPE_MEDIATYPE_CHOICES['max_length'],
      choices=LEXICALCONCEPTUALRESOURCEAUDIOINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      blank=True, null=True, related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      blank=True, null=True, related_name="sizeInfo_%(class)s_related", )

    audioContentInfo = models.OneToOneField("audioContentInfoType_model", 
      verbose_name='Audio content', 
      help_text='Groups together information on the contents of the audi' \
      'o part of a resource',
      blank=True, null=True, )

    audioFormatInfo = models.ManyToManyField("audioFormatInfoType_model", 
      verbose_name='Audio format', 
      help_text='Groups together information on the format of the audio ' \
      'part of a resource',
      blank=True, null=True, related_name="audioFormatInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LEXICALCONCEPTUALRESOURCETEXTINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class lexicalConceptualResourceTextInfoType_model(SchemaModel):
    """
    Groups information on the textual part of the lexical/conceptual
    resource
    """

    class Meta:
        verbose_name = "Lexical conceptual resource text"

    __schema_name__ = 'lexicalConceptualResourceTextInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', REQUIRED ),
      ( u'languageInfo', u'languageInfo', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', REQUIRED ),
      ( u'textFormatInfo', u'textFormatInfo', RECOMMENDED ),
      ( u'characterEncodingInfo', u'characterEncodingInfo', OPTIONAL ),
      ( u'domainInfo', u'domainInfo', OPTIONAL ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', OPTIONAL ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=LEXICALCONCEPTUALRESOURCETEXTINFOTYPE_MEDIATYPE_CHOICES['max_length'],
      choices=LEXICALCONCEPTUALRESOURCETEXTINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      related_name="sizeInfo_%(class)s_related", )

    textFormatInfo = models.ManyToManyField("textFormatInfoType_model", 
      verbose_name='Text format', 
      help_text='Groups information on the text format(s) of a resource',
      blank=True, null=True, related_name="textFormatInfo_%(class)s_related", )

    characterEncodingInfo = models.ManyToManyField("characterEncodingInfoType_model", 
      verbose_name='Character encoding', 
      help_text='Groups together information on character encoding of th' \
      'e resource',
      blank=True, null=True, related_name="characterEncodingInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LEXICALCONCEPTUALRESOURCEVIDEOINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class lexicalConceptualResourceVideoInfoType_model(SchemaModel):
    """
    Groups information on the video part of the lexical conceptual
    resource
    """

    class Meta:
        verbose_name = "Lexical conceptual resource video"

    __schema_name__ = 'lexicalConceptualResourceVideoInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageInfo', OPTIONAL ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'sizeInfo', u'sizeInfo', RECOMMENDED ),
      ( u'videoContentInfo', u'videoContentInfo', REQUIRED ),
      ( u'videoFormatInfo', u'videoFormatInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', OPTIONAL ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', OPTIONAL ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=LEXICALCONCEPTUALRESOURCEVIDEOINFOTYPE_MEDIATYPE_CHOICES['max_length'],
      choices=LEXICALCONCEPTUALRESOURCEVIDEOINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      blank=True, null=True, related_name="languageInfo_%(class)s_related", )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      blank=True, null=True, related_name="sizeInfo_%(class)s_related", )

    videoContentInfo = models.OneToOneField("videoContentInfoType_model", 
      verbose_name='Video content', 
      help_text='Groups together information on the contents of the vide' \
      'o part of a resource',
      )

    videoFormatInfo = models.ManyToManyField("videoFormatInfoType_model", 
      verbose_name='Video format', 
      help_text='Groups information on the format(s) of a resource; repe' \
      'ated if parts of the resource are in different formats',
      blank=True, null=True, related_name="videoFormatInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

LEXICALCONCEPTUALRESOURCEIMAGEINFOTYPE_MEDIATYPE_CHOICES = _make_choices_from_list([
  u'text', u'audio', u'video', u'image', u'textNumerical', 
])

# pylint: disable-msg=C0103
class lexicalConceptualResourceImageInfoType_model(SchemaModel):
    """
    Groups information on the image part of the lexical/conceptual
    resource
    """

    class Meta:
        verbose_name = "Lexical conceptual resource image"

    __schema_name__ = 'lexicalConceptualResourceImageInfoType'
    __schema_fields__ = (
      ( u'mediaType', u'mediaType', REQUIRED ),
      ( u'modalityInfo', u'modalityInfo', RECOMMENDED ),
      ( u'lingualityInfo', u'lingualityInfo', OPTIONAL ),
      ( u'languageInfo', u'languageInfo', OPTIONAL ),
      ( u'sizeInfo', u'sizeInfo', RECOMMENDED ),
      ( u'imageContentInfo', u'imageContentInfo', RECOMMENDED ),
      ( u'imageFormatInfo', u'imageFormatInfo', RECOMMENDED ),
      ( u'domainInfo', u'domainInfo', OPTIONAL ),
      ( u'geographicCoverageInfo', u'geographicCoverageInfo', OPTIONAL ),
      ( u'timeCoverageInfo', u'timeCoverageInfo', OPTIONAL ),
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

    mediaType = models.CharField(
      verbose_name='Media', 
      help_text='Specifies the media type of the resource and basically ' \
      'corresponds to the physical medium of the content representation.' \
      ' Each media type is described through a distinctive set of featur' \
      'es. A resource may consist of parts attributed to different types' \
      ' of media. A tool/service may take as input/output more than one ' \
      'different media types.',
      
      max_length=LEXICALCONCEPTUALRESOURCEIMAGEINFOTYPE_MEDIATYPE_CHOICES['max_length'],
      choices=LEXICALCONCEPTUALRESOURCEIMAGEINFOTYPE_MEDIATYPE_CHOICES['choices'],
      )

    modalityInfo = models.ManyToManyField("modalityInfoType_model", 
      verbose_name='Modality', 
      help_text='Groups information on the modalities represented in the' \
      ' resource',
      blank=True, null=True, related_name="modalityInfo_%(class)s_related", )

    lingualityInfo = models.OneToOneField("lingualityInfoType_model", 
      verbose_name='Linguality', 
      help_text='Groups information on the number of languages of the re' \
      'source part and of the way they are combined to each other',
      blank=True, null=True, )

    languageInfo = models.ManyToManyField("languageInfoType_model", 
      verbose_name='Language', 
      help_text='Groups information on the languages represented in the ' \
      'resource',
      blank=True, null=True, related_name="languageInfo_%(class)s_related", )

    sizeInfo = models.ManyToManyField("sizeInfoType_model", 
      verbose_name='Size', 
      help_text='Groups information on the size of the resource or of re' \
      'source parts',
      blank=True, null=True, related_name="sizeInfo_%(class)s_related", )

    imageContentInfo = models.OneToOneField("imageContentInfoType_model", 
      verbose_name='Image content', 
      help_text='Groups together information on the contents of the imag' \
      'e part of a resource',
      blank=True, null=True, )

    imageFormatInfo = models.ManyToManyField("imageFormatInfoType_model", 
      verbose_name='Image format', 
      help_text='Groups information on the format of the image component' \
      ' of the resource',
      blank=True, null=True, related_name="imageFormatInfo_%(class)s_related", )

    domainInfo = models.ManyToManyField("domainInfoType_model", 
      verbose_name='Domain', 
      help_text='Groups together information on domains represented in t' \
      'he resource; can be repeated for parts of the resource with disti' \
      'nct domain',
      blank=True, null=True, related_name="domainInfo_%(class)s_related", )

    geographicCoverageInfo = models.ManyToManyField("geographicCoverageInfoType_model", 
      verbose_name='Geographic coverage', 
      help_text='Groups information on geographic classification of the ' \
      'resource',
      blank=True, null=True, related_name="geographicCoverageInfo_%(class)s_related", )

    timeCoverageInfo = models.ManyToManyField("timeCoverageInfoType_model", 
      verbose_name='Time coverage', 
      help_text='Groups together information on time classification of t' \
      'he resource',
      blank=True, null=True, related_name="timeCoverageInfo_%(class)s_related", )

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
  u'speechAnnotation-speakerTurns',u'speechAnnotation', u'stemming',
  u'structuralAnnotation',u'syntacticAnnotation-shallowParsing',
  u'syntacticAnnotation-subcategorizationFrames',
  u'syntacticAnnotation-treebanks',u'syntacticosemanticAnnotation-links',
  u'translation',u'transliteration', u'discourseAnnotation-dialogueActs',
  u'modalityAnnotation-bodyMovements',
  u'modalityAnnotation-facialExpressions',
  u'modalityAnnotation-gazeEyeMovements',
  u'modalityAnnotation-handArmGestures',
  u'modalityAnnotation-handManipulationOfObjects',
  u'modalityAnnotation-headMovements',u'modalityAnnotation-lipMovements',
  u'semanticAnnotation-emotions',u'other', 
])

INPUTINFOTYPE_SEGMENTATIONLEVEL_CHOICES = _make_choices_from_list([
  u'paragraph', u'sentence', u'clause', u'word', u'wordGroup', u'utterance',
  u'topic',u'signal', u'phoneme', u'syllable', u'phrase', u'diphone',
  u'prosodicBoundaries',u'frame', u'scene', u'shot', u'other', 
])

INPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES = _make_choices_from_list([
  u'CES', u'EML', u'EMMA', u'GMX', u'HamNoSys', u'InkML', u'ISO12620',
  u'ISO16642',u'ISO1987', u'ISO26162', u'ISO30042', u'ISO704', u'LMF',
  u'MAF',u'MLIF', u'MULTEXT', u'multimodalInteractionFramework', u'OAXAL',
  u'OWL',u'pennTreeBank', u'pragueTreebank', u'RDF', u'SemAF', u'SemAF_DA',
  u'SemAF_NE',u'SemAF_SRL', u'SemAF_DS', u'SKOS', u'SRX', u'SynAF', u'TBX',
  u'TMX',u'TEI', u'TEI_P3', u'TEI_P4', u'TEI_P5', u'TimeML', u'XCES',
  u'XLIFF',u'MUMIN', u'BLM', u'other', 
])

# pylint: disable-msg=C0103
class inputInfoType_model(SchemaModel):
    """
    Groups together information on the requirements set on the input
    resource of a tool or service
    """

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
      ( u'annotationType', u'annotationType', OPTIONAL ),
      ( u'annotationFormat', u'annotationFormat', OPTIONAL ),
      ( u'tagset', u'tagset', OPTIONAL ),
      ( u'segmentationLevel', u'segmentationLevel', OPTIONAL ),
      ( u'conformanceToStandardsBestPractices', u'conformanceToStandardsBestPractices', OPTIONAL ),
    )

    mediaType = MultiSelectField(
      verbose_name='Media', 
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
      verbose_name='Resource', 
      help_text='The type of the resource that a tool or service takes a' \
      's input or produces as output',
      blank=True, 
      max_length=1 + len(INPUTINFOTYPE_RESOURCETYPE_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_RESOURCETYPE_CHOICES['choices'],
      )

    modalityType = MultiSelectField(
      verbose_name='Modality', 
      help_text='Specifies the type of the modality represented in the r' \
      'esource or processed by a tool/service',
      blank=True, 
      max_length=1 + len(INPUTINFOTYPE_MODALITYTYPE_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_MODALITYTYPE_CHOICES['choices'],
      )

    languageName = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=45), 
      verbose_name='Language name', 
      help_text='A human understandable name of the language that is use' \
      'd in the resource or supported by the tool/service according to t' \
      'he IETF BCP47 standard',
      blank=True, )

    languageId = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=46), 
      verbose_name='Language id', 
      help_text='The identifier of the language that is included in the ' \
      'resource or supported by the tool/service according to the IETF B' \
      'CP47 standard',
      blank=True, )

    languageVarietyName = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=47), 
      verbose_name='Language variety name', 
      help_text='Specifies the type of the language variety that occurs ' \
      'in the resource or is supported by a tool/service',
      blank=True, )

    mimeType = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=48), 
      verbose_name='Mime', 
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts; value to be taken from a subset of the official mime ' \
      'types of the Internet Assigned Numbers Authority (http://www.iana' \
      '.org/)',
      blank=True, )

    characterEncoding = MultiSelectField(
      verbose_name='Character encoding', 
      help_text='The name of the character encoding used in the resource' \
      ' or accepted by the tool/service',
      blank=True, 
      max_length=1 + len(INPUTINFOTYPE_CHARACTERENCODING_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_CHARACTERENCODING_CHOICES['choices'],
      )

    annotationType = MultiSelectField(
      verbose_name='Annotation', 
      help_text='Specifies the annotation level of the resource or the a' \
      'nnotation type a tool/ service requires or produces as an output',
      blank=True, 
      max_length=1 + len(INPUTINFOTYPE_ANNOTATIONTYPE_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_ANNOTATIONTYPE_CHOICES['choices'],
      )

    annotationFormat = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=49), 
      verbose_name='Annotation format', 
      help_text='Specifies the format that is used in the annotation pro' \
      'cess since often the mime type will not be sufficient for machine' \
      ' processing',
      blank=True, )

    tagset = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=50), 
      verbose_name='Tagset', 
      help_text='A name or a url reference to the tagset used in the ann' \
      'otation of the resource or used by the tool/service',
      blank=True, )

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
      verbose_name='Conformance to standards best practices', 
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True, 
      max_length=1 + len(INPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices']) / 4,
      choices=INPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices'],
      )

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
  u'speechAnnotation-speakerTurns',u'speechAnnotation', u'stemming',
  u'structuralAnnotation',u'syntacticAnnotation-shallowParsing',
  u'syntacticAnnotation-subcategorizationFrames',
  u'syntacticAnnotation-treebanks',u'syntacticosemanticAnnotation-links',
  u'translation',u'transliteration', u'discourseAnnotation-dialogueActs',
  u'modalityAnnotation-bodyMovements',
  u'modalityAnnotation-facialExpressions',
  u'modalityAnnotation-gazeEyeMovements',
  u'modalityAnnotation-handArmGestures',
  u'modalityAnnotation-handManipulationOfObjects',
  u'modalityAnnotation-headMovements',u'modalityAnnotation-lipMovements',
  u'semanticAnnotation-emotions',u'other', 
])

OUTPUTINFOTYPE_SEGMENTATIONLEVEL_CHOICES = _make_choices_from_list([
  u'paragraph', u'sentence', u'clause', u'word', u'wordGroup', u'utterance',
  u'topic',u'signal', u'phoneme', u'syllable', u'phrase', u'diphone',
  u'prosodicBoundaries',u'frame', u'scene', u'shot', u'other', 
])

OUTPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES = _make_choices_from_list([
  u'CES', u'EML', u'EMMA', u'GMX', u'HamNoSys', u'InkML', u'ISO12620',
  u'ISO16642',u'ISO1987', u'ISO26162', u'ISO30042', u'ISO704', u'LMF',
  u'MAF',u'MLIF', u'MULTEXT', u'multimodalInteractionFramework', u'OAXAL',
  u'OWL',u'pennTreeBank', u'pragueTreebank', u'RDF', u'SemAF', u'SemAF_DA',
  u'SemAF_NE',u'SemAF_SRL', u'SemAF_DS', u'SKOS', u'SRX', u'SynAF', u'TBX',
  u'TMX',u'TEI', u'TEI_P3', u'TEI_P4', u'TEI_P5', u'TimeML', u'XCES',
  u'XLIFF',u'MUMIN', u'BLM', u'other', 
])

# pylint: disable-msg=C0103
class outputInfoType_model(SchemaModel):
    """
    Groups together information on the requirements set on the output of
    a tool or service
    """

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
      verbose_name='Media', 
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
      verbose_name='Resource', 
      help_text='The type of the resource that a tool or service takes a' \
      's input or produces as output',
      blank=True, 
      max_length=1 + len(OUTPUTINFOTYPE_RESOURCETYPE_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_RESOURCETYPE_CHOICES['choices'],
      )

    modalityType = MultiSelectField(
      verbose_name='Modality', 
      help_text='Specifies the type of the modality represented in the r' \
      'esource or processed by a tool/service',
      blank=True, 
      max_length=1 + len(OUTPUTINFOTYPE_MODALITYTYPE_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_MODALITYTYPE_CHOICES['choices'],
      )

    languageName = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=51), 
      verbose_name='Language name', 
      help_text='A human understandable name of the language that is use' \
      'd in the resource or supported by the tool/service according to t' \
      'he IETF BCP47 standard',
      blank=True, )

    languageId = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=52), 
      verbose_name='Language id', 
      help_text='The identifier of the language that is included in the ' \
      'resource or supported by the tool/service according to the IETF B' \
      'CP47 standard',
      blank=True, )

    languageVarietyName = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=53), 
      verbose_name='Language variety name', 
      help_text='Specifies the type of the language variety that occurs ' \
      'in the resource or is supported by a tool/service',
      blank=True, )

    mimeType = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=54), 
      verbose_name='Mime', 
      help_text='The mime-type of the resource which is a formalized spe' \
      'cifier for the format included or a mime-type that the tool/servi' \
      'ce accepts; value to be taken from a subset of the official mime ' \
      'types of the Internet Assigned Numbers Authority (http://www.iana' \
      '.org/)',
      blank=True, )

    characterEncoding = MultiSelectField(
      verbose_name='Character encoding', 
      help_text='The name of the character encoding used in the resource' \
      ' or accepted by the tool/service',
      blank=True, 
      max_length=1 + len(OUTPUTINFOTYPE_CHARACTERENCODING_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_CHARACTERENCODING_CHOICES['choices'],
      )

    annotationType = MultiSelectField(
      verbose_name='Annotation', 
      help_text='Specifies the annotation level of the resource or the a' \
      'nnotation type a tool/ service requires or produces as an output',
      blank=True, 
      max_length=1 + len(OUTPUTINFOTYPE_ANNOTATIONTYPE_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_ANNOTATIONTYPE_CHOICES['choices'],
      )

    annotationFormat = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=55), 
      verbose_name='Annotation format', 
      help_text='Specifies the format that is used in the annotation pro' \
      'cess since often the mime type will not be sufficient for machine' \
      ' processing',
      blank=True, )

    tagset = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=56), 
      verbose_name='Tagset', 
      help_text='A name or a url reference to the tagset used in the ann' \
      'otation of the resource or used by the tool/service',
      blank=True, )

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
      verbose_name='Conformance to standards best practices', 
      help_text='Specifies the standards or the best practices to which ' \
      'the tagset used for the annotation conforms',
      blank=True, 
      max_length=1 + len(OUTPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices']) / 4,
      choices=OUTPUTINFOTYPE_CONFORMANCETOSTANDARDSBESTPRACTICES_CHOICES['choices'],
      )

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
    """
    Groups together information on the evaluation status of a tool or
    service
    """

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
      verbose_name='Evaluation', 
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

    evaluationDetails = models.CharField(
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
  u'os-independent', u'windows', u'linux', u'unix', u'mac-OS', u'other', 
])

# pylint: disable-msg=C0103
class toolServiceOperationInfoType_model(SchemaModel):
    """
    Groups together information on the operation of a tool or service
    """

    class Meta:
        verbose_name = "Tool service operation"

    __schema_name__ = 'toolServiceOperationInfoType'
    __schema_fields__ = (
      ( u'operatingSystem', u'operatingSystem', REQUIRED ),
      ( u'runningEnvironmentInfo', u'runningEnvironmentInfo', RECOMMENDED ),
      ( u'runningTime', u'runningTime', OPTIONAL ),
    )
    __schema_classes__ = {
      u'runningEnvironmentInfo': "runningEnvironmentInfoType_model",
    }

    operatingSystem = MultiSelectField(
      verbose_name='Operating system', 
      help_text='The operating system on which the tool will be running',
      
      max_length=1 + len(TOOLSERVICEOPERATIONINFOTYPE_OPERATINGSYSTEM_CHOICES['choices']) / 4,
      choices=TOOLSERVICEOPERATIONINFOTYPE_OPERATINGSYSTEM_CHOICES['choices'],
      )

    runningEnvironmentInfo = models.OneToOneField("runningEnvironmentInfoType_model", 
      verbose_name='Running environment', 
      help_text='Groups together information on the running environment ' \
      'of a tool or a language description',
      blank=True, null=True, )

    runningTime = models.CharField(
      verbose_name='Running time', 
      help_text='Gives information on the running time of a tool or serv' \
      'ice',
      blank=True, max_length=100, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class toolServiceCreationInfoType_model(SchemaModel):
    """
    Groups together information on the creation of a tool or service
    """

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

    implementationLanguage = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=57), 
      verbose_name='Implementation language', 
      help_text='The programming languages needed for allowing user cont' \
      'ributions, or for running the tools, in case no executables are a' \
      'vailable',
      blank=True, )

    formalism = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=58), 
      verbose_name='Formalism', 
      help_text='Reference (name, bibliographic reference or link to url' \
      ') for the formalism used for the creation/enrichment of the resou' \
      'rce (grammar or tool/service)',
      blank=True, )

    originalSource = models.ManyToManyField("targetResourceInfoType_model", 
      verbose_name='Original source', 
      help_text='The name, the identifier or the url of thethe original ' \
      'resources that were at the base of the creation process of the re' \
      'source',
      blank=True, null=True, related_name="originalSource_%(class)s_related", )

    creationDetails = models.CharField(
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


LEXICALCONCEPTUALRESOURCEINFOTYPE_RESOURCETYPE_CHOICES = _make_choices_from_list([
  u'lexicalConceptualResource', 
])

LEXICALCONCEPTUALRESOURCEINFOTYPE_LEXICALCONCEPTUALRESOURCETYPE_CHOICES = _make_choices_from_list([
  u'wordList', u'computationalLexicon', u'ontology', u'wordnet',
  u'thesaurus',u'framenet', u'terminologicalResource',
  u'machineReadableDictionary',u'lexicon', u'other', 
])

# pylint: disable-msg=C0103
class lexicalConceptualResourceInfoType_model(resourceComponentTypeType_model):
    """
    Groups together information specific to lexical/conceptual resources
    """

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

    resourceType = models.CharField(
      verbose_name='Resource', 
      help_text='Specifies the type of the resource being described',
      
      max_length=30,
      choices=LEXICALCONCEPTUALRESOURCEINFOTYPE_RESOURCETYPE_CHOICES['choices'],
      )

    lexicalConceptualResourceType = models.CharField(
      verbose_name='Lexical conceptual resource', 
      help_text='Specifies the subtype of lexicalConceptualResource',
      
      max_length=LEXICALCONCEPTUALRESOURCEINFOTYPE_LEXICALCONCEPTUALRESOURCETYPE_CHOICES['max_length'],
      choices=LEXICALCONCEPTUALRESOURCEINFOTYPE_LEXICALCONCEPTUALRESOURCETYPE_CHOICES['choices'],
      )

    lexicalConceptualResourceEncodingInfo = models.OneToOneField("lexicalConceptualResourceEncodingInfoType_model", 
      verbose_name='Lexical conceptual resource encoding', 
      help_text='Groups all information regarding the contents of lexica' \
      'l/conceptual resources',
      blank=True, null=True, )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    lexicalConceptualResourceMediaType = models.OneToOneField("lexicalConceptualResourceMediaTypeType_model", 
      verbose_name='Lexical conceptual resource media', 
      help_text='Restriction of mediaType for lexicalConceptualResources' \
      '',
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['lexicalConceptualResourceType', ]
        formatstring = u'lexicalConceptualResource ({})'
        return self.unicode_(formatstring, formatargs)

LANGUAGEDESCRIPTIONINFOTYPE_RESOURCETYPE_CHOICES = _make_choices_from_list([
  u'languageDescription', 
])

LANGUAGEDESCRIPTIONINFOTYPE_LANGUAGEDESCRIPTIONTYPE_CHOICES = _make_choices_from_list([
  u'grammar', u'other', 
])

# pylint: disable-msg=C0103
class languageDescriptionInfoType_model(resourceComponentTypeType_model):
    """
    Groups together information on language descriptions (grammars)
    """

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

    resourceType = models.CharField(
      verbose_name='Resource', 
      help_text='Specifies the type of the resource being described',
      
      max_length=30,
      choices=LANGUAGEDESCRIPTIONINFOTYPE_RESOURCETYPE_CHOICES['choices'],
      )

    languageDescriptionType = models.CharField(
      verbose_name='Language description', 
      help_text='The type of the language description',
      
      max_length=30,
      choices=LANGUAGEDESCRIPTIONINFOTYPE_LANGUAGEDESCRIPTIONTYPE_CHOICES['choices'],
      )

    languageDescriptionEncodingInfo = models.OneToOneField("languageDescriptionEncodingInfoType_model", 
      verbose_name='Language description encoding', 
      help_text='Groups together information on the contents of the Lang' \
      'uageDescriptions',
      blank=True, null=True, )

    languageDescriptionOperationInfo = models.OneToOneField("languageDescriptionOperationInfoType_model", 
      verbose_name='Language description operation', 
      help_text='Groups together information on the operation requiremen' \
      'ts of the Language Descriptions',
      blank=True, null=True, )

    languageDescriptionPerformanceInfo = models.OneToOneField("languageDescriptionPerformanceInfoType_model", 
      verbose_name='Language description performance', 
      help_text='Groups together information on the performance of the L' \
      'anguage Descriptions',
      blank=True, null=True, )

    creationInfo = models.OneToOneField("creationInfoType_model", 
      verbose_name='Creation', 
      help_text='Groups together information on the resource creation (e' \
      '.g. for corpora, selection of texts/audio files/ video files etc.' \
      ' and structural encoding thereof; for lexica, construction of lem' \
      'ma list etc.)',
      blank=True, null=True, )

    languageDescriptionMediaType = models.OneToOneField("languageDescriptionMediaTypeType_model", 
      verbose_name='Language description media', 
      help_text='Groups information on the media type-specific component' \
      's for language descriptions',
      )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['languageDescriptionType', ]
        formatstring = u'languageDescription ({})'
        return self.unicode_(formatstring, formatargs)

TOOLSERVICEINFOTYPE_RESOURCETYPE_CHOICES = _make_choices_from_list([
  u'toolService', 
])

TOOLSERVICEINFOTYPE_TOOLSERVICETYPE_CHOICES = _make_choices_from_list([
  u'tool', u'service', u'platform', u'suiteOfTools', u'infrastructure',
  u'architecture',u'nlpDevelopmentEnvironment', u'other', 
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

    resourceType = models.CharField(
      verbose_name='Resource', 
      help_text='The type of the resource that a tool or service takes a' \
      's input or produces as output',
      
      max_length=30,
      choices=TOOLSERVICEINFOTYPE_RESOURCETYPE_CHOICES['choices'],
      )

    toolServiceType = models.CharField(
      verbose_name='Tool service', 
      help_text='Specifies the type of the tool or service',
      
      max_length=100,
      choices=TOOLSERVICEINFOTYPE_TOOLSERVICETYPE_CHOICES['choices'],
      )

    toolServiceSubtype = MultiTextField(max_length=100, widget = MultiFieldWidget(widget_id=59), 
      verbose_name='Tool service subtype', 
      help_text='Specifies the subtype of tool or service',
      blank=True, )

    languageDependent = MetaBooleanField(
      verbose_name='Language dependent', 
      help_text='Indicates whether the operation of the tool or service ' \
      'is language dependent or not',
      )

    inputInfo = models.OneToOneField("inputInfoType_model", 
      verbose_name='Input', 
      help_text='Groups together information on the requirements set on ' \
      'the input resource of a tool or service',
      blank=True, null=True, )

    outputInfo = models.OneToOneField("outputInfoType_model", 
      verbose_name='Output', 
      help_text='Groups together information on the requirements set on ' \
      'the output of a tool or service',
      blank=True, null=True, )

    toolServiceOperationInfo = models.OneToOneField("toolServiceOperationInfoType_model", 
      verbose_name='Tool service operation', 
      help_text='Groups together information on the operation of a tool ' \
      'or service',
      blank=True, null=True, )

    toolServiceEvaluationInfo = models.OneToOneField("toolServiceEvaluationInfoType_model", 
      verbose_name='Tool service evaluation', 
      help_text='Groups together information on the evaluation status of' \
      ' a tool or service',
      blank=True, null=True, )

    toolServiceCreationInfo = models.OneToOneField("toolServiceCreationInfoType_model", 
      verbose_name='Tool service creation', 
      help_text='Groups together information on the creation of a tool o' \
      'r service',
      blank=True, null=True, )

    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = ['toolServiceType', ]
        formatstring = u'toolService ({})'
        return self.unicode_(formatstring, formatargs)

CORPUSINFOTYPE_RESOURCETYPE_CHOICES = _make_choices_from_list([
  u'corpus', 
])

# pylint: disable-msg=C0103
class corpusInfoType_model(resourceComponentTypeType_model):
    """
    Groups together information on corpora of all media types
    """

    class Meta:
        verbose_name = "Corpus"

    __schema_name__ = 'corpusInfoType'
    __schema_fields__ = (
      ( u'resourceType', u'resourceType', REQUIRED ),
      ( u'corpusMediaType', u'corpusMediaType', REQUIRED ),
    )
    __schema_classes__ = {
      u'corpusMediaType': "corpusMediaTypeType_model",
    }

    resourceType = models.CharField(
      verbose_name='Resource', 
      help_text='Specifies the type of the resource being described',
      
      max_length=30,
      choices=CORPUSINFOTYPE_RESOURCETYPE_CHOICES['choices'],
      )

    corpusMediaType = models.OneToOneField("corpusMediaTypeType_model", 
      verbose_name='Corpus media', 
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
        verbose_name = "Corpus media"

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
      verbose_name='Corpus audio', 
      help_text='Groups together information on the audio module of a co' \
      'rpus',
      blank=True, null=True, )

    # OneToMany field: corpusVideoInfo

    corpusImageInfo = models.OneToOneField("corpusImageInfoType_model", 
      verbose_name='Corpus image', 
      help_text='Groups together information on the image component of a' \
      ' resource',
      blank=True, null=True, )

    corpusTextNumericalInfo = models.OneToOneField("corpusTextNumericalInfoType_model", 
      verbose_name='Corpus text numerical', 
      help_text='Groups together information on the textNumerical compon' \
      'ent of a corpus. It is used basically for the textual representat' \
      'ion of measurements and observations linked to sensorimotor recor' \
      'dings',
      blank=True, null=True, )

    corpusTextNgramInfo = models.OneToOneField("corpusTextNgramInfoType_model", 
      verbose_name='Corpus text ngram', 
      help_text='Groups together information required for n-gram resourc' \
      'es; information can be provided both as regards features drawn fr' \
      'om the source corpus (e.g. language coverage, size, format, domai' \
      'ns etc.) and features pertaining to the n-gram output itself (e.g' \
      '. range of n-grams, type of item included, etc.)',
      blank=True, null=True, )

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

    typeOfElement = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=60), 
      verbose_name='Type of element', 
      help_text='The type of objects or people that represented in the v' \
      'ideo or image part of the resource',
      blank=True, )

    bodyParts = MultiSelectField(
      verbose_name='Body parts', 
      help_text='The body parts visible in the video or image part of th' \
      'e resource',
      blank=True, 
      max_length=1 + len(DYNAMICELEMENTINFOTYPE_BODYPARTS_CHOICES['choices']) / 4,
      choices=DYNAMICELEMENTINFOTYPE_BODYPARTS_CHOICES['choices'],
      )

    distractors = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=61), 
      verbose_name='Distractors', 
      help_text='Any distractors visible in the resource',
      blank=True, )

    interactiveMedia = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=62), 
      verbose_name='Interactive media', 
      help_text='Any interactive media visible in the resource',
      blank=True, )

    faceViews = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=63), 
      verbose_name='Face views', 
      help_text='Indicates the view of the face(s) that appear in the vi' \
      'deo or on the image part of the resource',
      blank=True, )

    faceExpressions = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=64), 
      verbose_name='Face expressions', 
      help_text='Indicates the facial expressions visible in the resourc' \
      'e',
      blank=True, )

    bodyMovement = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=65), 
      verbose_name='Body movement', 
      help_text='Indicates the body parts that move in the video part of' \
      ' the resource',
      blank=True, )

    gestures = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=66), 
      verbose_name='Gestures', 
      help_text='Indicates the type of gestures visible in the resource',
      blank=True, )

    handArmMovement = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=67), 
      verbose_name='Hand arm movement', 
      help_text='Indicates the movement of hands and/or arms visible in ' \
      'the resource',
      blank=True, )

    handManipulation = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=68), 
      verbose_name='Hand manipulation', 
      help_text='Gives information on the manipulation of objects by han' \
      'd',
      blank=True, )

    headMovement = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=69), 
      verbose_name='Head movement', 
      help_text='Indicates the movements of the head visible in the reso' \
      'urce',
      blank=True, )

    eyeMovement = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=70), 
      verbose_name='Eye movement', 
      help_text='Indicates the movement of the eyes visible in the resou' \
      'rce',
      blank=True, )

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

    typeOfElement = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=71), 
      verbose_name='Type of element', 
      help_text='The type of objects or people that represented in the v' \
      'ideo or image part of the resource',
      blank=True, )

    bodyParts = MultiSelectField(
      verbose_name='Body parts', 
      help_text='The body parts visible in the video or image part of th' \
      'e resource',
      blank=True, 
      max_length=1 + len(STATICELEMENTINFOTYPE_BODYPARTS_CHOICES['choices']) / 4,
      choices=STATICELEMENTINFOTYPE_BODYPARTS_CHOICES['choices'],
      )

    faceViews = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=72), 
      verbose_name='Face views', 
      help_text='Indicates the view of the face(s) that appear in the vi' \
      'deo or on the image part of the resource',
      blank=True, )

    faceExpressions = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=73), 
      verbose_name='Face expressions', 
      help_text='Indicates the facial expressions visible in the resourc' \
      'e',
      blank=True, )

    artifactParts = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=74), 
      verbose_name='Artifact parts', 
      help_text='Indicates the parts of the artifacts represented in the' \
      ' image corpus',
      blank=True, )

    landscapeParts = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=75), 
      verbose_name='Landscape parts', 
      help_text='landscape parts represented in the image corpus',
      blank=True, )

    personDescription = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=76), 
      verbose_name='Person description', 
      help_text='Provides descriptive features for the persons represent' \
      'ed in the image corpus',
      blank=True, )

    thingDescription = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=77), 
      verbose_name='Thing description', 
      help_text='Provides description of the things represented in the i' \
      'mage corpus',
      blank=True, )

    organizationDescription = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=78), 
      verbose_name='Organization description', 
      help_text='Provides description of the organizations that may appe' \
      'ar in the image corpus',
      blank=True, )

    eventDescription = MultiTextField(max_length=1000, widget = MultiFieldWidget(widget_id=79), 
      verbose_name='Event description', 
      help_text='Provides description of any events represented in the i' \
      'mage corpus',
      blank=True, )

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
      verbose_name='Language description text', 
      help_text='Groups together all information relevant to the text mo' \
      'dule of a language description (e.g. format, languages, size etc.' \
      '); it is obligatory for all language descriptions',
      blank=True, null=True, )

    languageDescriptionVideoInfo = models.OneToOneField("languageDescriptionVideoInfoType_model", 
      verbose_name='Language description video', 
      help_text='Groups together all information relevant to the video p' \
      'arts of a language description (e.g. format, languages, size etc.' \
      '), if there are any (e.g. for sign language grammars)',
      blank=True, null=True, )

    languageDescriptionImageInfo = models.OneToOneField("languageDescriptionImageInfoType_model", 
      verbose_name='Language description image', 
      help_text='Groups together all information relevant to the image m' \
      'odule of a language description (e.g. format, languages, size etc' \
      '.), if there are any (e.g. for sign language grammars)',
      blank=True, null=True, )

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
      verbose_name='Lexical conceptual resource text', 
      help_text='Groups information on the textual part of the lexical/c' \
      'onceptual resource',
      blank=True, null=True, )

    lexicalConceptualResourceAudioInfo = models.OneToOneField("lexicalConceptualResourceAudioInfoType_model", 
      verbose_name='Lexical conceptual resource audio', 
      help_text='Groups information on the audio part of the lexical/con' \
      'ceptual resource',
      blank=True, null=True, )

    lexicalConceptualResourceVideoInfo = models.OneToOneField("lexicalConceptualResourceVideoInfoType_model", 
      verbose_name='Lexical conceptual resource video', 
      help_text='Groups information on the video part of the lexical con' \
      'ceptual resource',
      blank=True, null=True, )

    lexicalConceptualResourceImageInfo = models.OneToOneField("lexicalConceptualResourceImageInfoType_model", 
      verbose_name='Lexical conceptual resource image', 
      help_text='Groups information on the image part of the lexical/con' \
      'ceptual resource',
      blank=True, null=True, )

    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode

# pylint: disable-msg=C0103
class documentUnstructuredString_model(InvisibleStringModel, documentationInfoType_model):
    pass
