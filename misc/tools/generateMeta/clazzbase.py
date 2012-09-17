from collections import OrderedDict

import os
import sys
import logging
from parse_xsd import ElementDict, XschemaElementBase, XschemaElement
from gends_extract_simple_types import extract_descriptors
import re

#
# Globals
MULTI_ID = 0

#
# Tables of builtin types
Simple_type_table = {
    'string': None,
    'normalizedString': None,
    'token': None,
    'base64Binary': None,
    'hexBinary': None,
    'integer': None,
    'positiveInteger': None,
    'negativeInteger': None,
    'nonNegativeInteger': None,
    'nonPositiveInteger': None,
    'long': None,
    'unsignedLong': None,
    'int': None,
    'unsignedInt': None,
    'short': None,
    'unsignedShort': None,
    'byte': None,
    'unsignedByte': None,
    'decimal': None,
    'float': None,
    'double': None,
    'boolean': None,
    'duration': None,
    'dateTime': None,
    'date': None,
    'time': None,
    'gYear': None,
    'gYearMonth': None,
    'gMonth': None,
    'gMonthDay': None,
    'gDay': None,
    'Name': None,
    'QName': None,
    'NCName': None,
    'anyURI': None,
    'language': None,
    'ID': None,
    'IDREF': None,
    'IDREFS': None,
    'ENTITY': None,
    'ENTITIES': None,
    'NOTATION': None,
    'NMTOKEN': None,
    'NMTOKENS': None,
}
Integer_type_table = {
    'integer': None,
    'positiveInteger': None,
    'negativeInteger': None,
    'nonNegativeInteger': None,
    'nonPositiveInteger': None,
    'long': None,
    'unsignedLong': None,
    'int': None,
    'unsignedInt': None,
    'short': None,
    'unsignedShort': None,
}
Float_type_table = {
    'decimal': None,
    'float': None,
    'double': None,
}
String_type_table = {
    'string': None,
    'normalizedString': None,
    'token': None,
    'NCName': None,
    'ID': None,
    'IDREF': None,
    'IDREFS': None,
    'ENTITY': None,
    'ENTITIES': None,
    'NOTATION': None,
    'NMTOKEN': None,
    'NMTOKENS': None,
    'QName': None,
    'anyURI': None,
    'base64Binary': None,
    'duration': None,
    'Name': None,
    'language': None,
    'gYear': None,
}
Date_type_table = {
    'date': None,
}
DateTime_type_table = {
    'dateTime': None,
}
Boolean_type_table = {
    'boolean': None,
}

CHOICE_STRING_SUB_CLASSES = {}

DEFAULT_MAXLENGTH = 1000

MODELS_SUPERCLASS="SchemaModel"

CHOICE_TYPE_SUPERCLASS='SubclassableModel'

CHOICES_TEMPLATE = """
      max_length={0}['max_length'],
      choices={0}['choices'],
      """

MULTI_CHOICES_TEMPLATE = """
      max_length=1 + len({0}['choices']) / 4,
      choices={0}['choices'],
      """

CHOICES_TEMPLATE_MAXLEN = """
      max_length={1},
      choices={0}['choices'],
      """

SORTED_CHOICES_TEMPLATE_MAXLEN = """
      max_length={1},
      choices=sorted({0}['choices'],
                     key=lambda choice: choice[1].lower()),
      """

SORTED_INT_CHOICES_TEMPLATE_MAXLEN = """
      max_length={1},
      choices=sorted({0}['choices'],
                     key=lambda choice: choice[1]),
      """

MODEL_HEADER="""\
# pylint: disable-msg=C0302
import logging
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.template.defaultfilters import slugify

from metashare.accounts.models import EditorGroup
# pylint: disable-msg=W0611
from {0}supermodel import SchemaModel, SubclassableModel, \\
  _make_choices_from_list, InvisibleStringModel, \\
  REQUIRED, OPTIONAL, RECOMMENDED, \\
  _make_choices_from_int_list
from {0}editor.widgets import MultiFieldWidget
from {0}fields import MultiTextField, MetaBooleanField, \\
  MultiSelectField, DictField, XmlCharField, best_lang_value_retriever
from {0}validators import validate_lang_code_keys, \\
  validate_dict_values, validate_xml_schema_year, \\
  validate_matches_xml_char_production
from metashare.settings import DJANGO_BASE, LOG_HANDLER, DJANGO_URL
from metashare.stats.model_utils import saveLRStats, DELETE_STAT
from metashare.storage.models import StorageObject, MASTER, COPY_CHOICES


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

EMAILADDRESS_VALIDATOR = RegexValidator(r'[^@]+@[^\.]+\..+',
  'Not a valid emailAddress value.', ValidationError)

HTTPURI_VALIDATOR = RegexValidator(r'(https?://.*|ftp://.*|www*)',
  'Not a valid httpURI value.', ValidationError)

# namespace of the META-SHARE metadata XML Schema
SCHEMA_NAMESPACE = '{1}'
# version of the META-SHARE metadata XML Schema
SCHEMA_VERSION = '{2}'

def _compute_documentationInfoType_key():
    '''
    Prevents id collisions for documentationInfoType_model sub classes.
    
    These are:
    - documentInfoType_model;
    - documentUnstructuredString_model.
    
    '''
    _k1 = list(documentInfoType_model.objects.all().order_by('-id'))
    _k2 = list(documentUnstructuredString_model.objects.all().order_by('-id'))
    
    LOGGER.debug('k1: {{}}, k2: {{}}'.format(_k1, _k2))

    _k1_id = 0
    if len(_k1) > 0:
        _k1_id = _k1[0].id
    _k2_id = 0
    if len(_k2) > 0:
        _k2_id = _k2[0].id

    return max(_k1_id, _k2_id) + 1

"""


UNICODE_METHOD_TEMPLATE='''\
    def real_unicode_(self):
        # pylint: disable-msg=C0301
        formatargs = [{1}]
        formatstring = u\'{0}\'
        return self.unicode_(formatstring, formatargs)
'''

UNICODE_DEFAULT_TEMPLATE='''\
    def __unicode__(self):
        _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode
'''

UNICODE_CHOICE_TYPE_TEMPLATE='''\
    def __unicode__(self):
        try:
            # pylint: disable-msg=E0602,E1101,C0301
            _unicode = self.as_subclass().__unicode__()
        except:
            _unicode = u'<{} id="{}">'.format(self.__schema_name__, self.id)
        return _unicode
'''

INLINE_TEMPLATE='''\
# pylint: disable-msg=C0103
class {}_model_inline{}(SchemaModelInline):
    model = {}_model
{}

'''

INLINE_SNIPPET_COLLAPSE='''\
    collapse = True
'''

INLINE_SNIPPET_TABULAR='''\
    template = 'admin/edit_inline/tabular.html'
'''

INLINE_SNIPPET_FK_NAME='''\
    fk_name = 'back_to_{}_model'
'''


MANUAL_ADMIN_REGISTRATION_TEMPLATE = '''

from metashare.repository.editor import manual_admin_registration
manual_admin_registration.register()
'''

COMPLEX_MODEL_TEMPLATE='''
# pylint: disable-msg=C0103
class {}_model({}):
{}
    class Meta:
        verbose_name = "{}"
{}
'''

CHOICE_SUPERCLASS_TEMPLATE = '''
# pylint: disable-msg=C0103
class {}_model({}):
{}
    __schema_name__ = \'SUBCLASSABLE\'

    class Meta:
        verbose_name = "{}"
{}
'''

VERBOSE_NAME_PLURAL_SNIPPET = '''\
        verbose_name_plural = "{}"
'''

CHOICE_STRING_SUB_CLASS_ADMIN_TEMPLATE = '''
from metashare.repository.models import {0}_model
admin.site.register({0}_model)

'''

CHOICE_STRING_SUB_CLASS_TEMPLATE = '''
# pylint: disable-msg=C0103
class {0}_model(InvisibleStringModel, {1}):
    def save(self, *args, **kwargs):
        """
        Prevents id collisions for documentationInfoType_model sub classes.
        """
        # pylint: disable-msg=E0203
        if not self.id:
            # pylint: disable-msg=W0201
            self.id = _compute_documentationInfoType_key()
        super({0}_model, self).save(*args, **kwargs)
'''

TOP_LEVEL_TYPE_EXTRA_CODE_TEMPLATE = '''
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
            LOGGER.warning('Trying to modify non master copy {0}, ' \\
              'aborting!'.format(self.storage_object))
            return
        
        self.storage_object.save()
        # REMINDER: the SOLR indexer in search_indexes.py relies on us
        # calling storage_object.save() from resourceInfoType_model.save().
        # Should we ever change that, we must modify 
        # resourceInfoType_modelIndex._setup_save() accordingly!
        
        # Call save() method from super class with all arguments.
        super(resourceInfoType_model, self).save(*args, **kwargs)

    def delete(self, keep_stats=False, *args, **kwargs):
        """
        Overrides the predefined delete() method to update the statistics.
        Includes deletion of statistics; use keep_stats optional parameter to
        suppress deletion of statistics
        """
        if not keep_stats:
            saveLRStats(self, DELETE_STAT)
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

'''

REUSABLE_ENTITY_SNIPPET = '''
    source_url = models.URLField(verify_exists=False, 
      default=DJANGO_URL,
      help_text="(Read-only) base URL for the server where the master copy of " \\
      "the associated entity instance is located.")
    
    copy_status = models.CharField(default=MASTER, max_length=1, choices=COPY_CHOICES,
        help_text="Generalized copy status flag for this entity instance.")

'''

REUSABLE_ENTITIES = ('documentInfoType', 'personInfoType', 'organizationInfoType', 'projectInfoType', )

GYEAR_VALIDATOR_OPTION_SNIPPET = "validators=[validate_xml_schema_year], "


#
# Local functions

def _escape_non_ascii_chars(string):
    """
    Returns a copy of the given string with all non-ASCII characters replaced
    in Python Unicode-Escape encoding (e.g., '\u2013').
    """
    return ''.join([(ord(c) < 128 and c) or r'\u{0:0>4x}'.format(ord(c))
                    for c in string])

def _truncate_long_string(string, max_length, indent=0):
    """
    Returns a multi-line version of string with each line shorter max_length.
    """
    _string = string
    _separator = _string[0]
    
    # Make sure occurences of _separator within the string are escaped!
    _string = _string.replace(_separator, '\{}'.format(_separator))
    _string = _string[1:len(_string)-2] + _separator
    
    # For the first line, we have to consider the help_text= prefix which has
    # a length of 10.  For all remaining lines, we need to consider indent.
    _initial = 10 + indent
    _result = []
    while len(_string) > (max_length - _initial):
        _line  = _string[:max_length - _initial]
        _line = u'{}{} \\'.format(_line, _separator)
        _result.append(_line)
        _string = _separator + _string[max_length - _initial:]
        _initial = indent

    if not _string.startswith(_separator):
        _string = _separator + _string

    _result.append(_string)
    
    return u'\n{}'.format(' '*indent).join(_result)

def cleanupName(oldName):
    newName = oldName.replace(':', '_')
    newName = newName.replace('-', '_')
    newName = newName.replace('.', '_')
    return newName

def getVerboseName(verbose_name):
    verbose_name = re.sub(r'(Type|Info)?(Type)?(_model)?',r'', verbose_name)
    verbose_name = re.sub(r'([a-z])([A-Z])',r'\1 \2', verbose_name)
    verbose_name = verbose_name[0].upper() + verbose_name[1:].lower()
    return verbose_name

def get_data_type_chain(element):
    if isinstance(element, str):
        return element
    name = cleanupName(element.getCleanName())
    simplebase = element.getSimpleBase()
    if simplebase:
        if len(simplebase) == 1:
            base_name = "%s" % (simplebase[0], )
        else:
            base_name = simplebase
    else:
        element1 = ElementDict.get(name)
        if element1:
            base_name = "%s" % element1.getType()
        else:
            base_name = "%s" % (element.getType(), )
    return base_name

def get_data_type(element):
    data_type = get_data_type_chain(element)
    if isinstance(data_type, list):
        if len(data_type) > 0:
            return data_type[-1]
        else:
            return 'xs:string'
    else:
        return data_type

def get_prefix_name(tag):
    prefix = ''
    name = ''
    items = tag.split(':')
    if len(items) == 2:
        prefix = items[0]
        name = items[1]
    elif len(items) == 1:
        name = items[0]
    return prefix, name


#
# Classes

class Writer(object):
    def __init__(self, outfilename, stdout_also=False):
        self.outfilename = outfilename
        self.outfile = open(outfilename, 'w')
        self.stdout_also = stdout_also
        self.line_count = 0
    def get_count(self):
        return self.line_count
    def write(self, content):
        self.outfile.write(content)
        if self.stdout_also:
            sys.stdout.write(content)
        count = content.count('\n')
        self.line_count += count
    def close(self):
        self.outfile.close()



class Clazz(object):
    ClazzDict = OrderedDict()
    simple_type_table = None

    def __str__(self):
        s1 = '<Clazz name: "%s" elt: "%s">' % \
            (self.name, self.schema_element, )
        return s1
    __repr__ = __str__

    @classmethod
    def extract_descriptors(cls, xschemaFileName):
        cls.ClazzDict = OrderedDict()
        cls.simple_type_table = extract_descriptors(xschemaFileName)

    @classmethod
    def get_clazz_for_element(cls, element):
        if isinstance(element, XschemaElementBase):
            data_type = get_data_type(element)
            if cls.ClazzDict.has_key(data_type):
                return cls.ClazzDict[data_type]
        else:
            return None

    @classmethod
    def is_one_to_many(cls, member):
        dummy, data_type = get_prefix_name(member.get_data_type())
        return data_type not in Simple_type_table \
            and data_type not in cls.simple_type_table \
            and data_type != 'myString' \
            and member.is_one_to_many()

    @classmethod
    def is_valid_one_to_many(cls, member):
        if cls.is_one_to_many(member):
            data_type = member.get_data_type()
            child_clazz = cls.ClazzDict[data_type]
            return isinstance(child_clazz.backreference, ClazzBaseMember) or \
                isinstance(child_clazz.backreference, tuple)

    @classmethod
    def has_multiple_one_to_many_references(cls, member):
        '''
        Returns True if member is the many side of more than one one-to-many reference, False otherwise.
        '''
        if cls.is_one_to_many(member):
            data_type = member.get_data_type()
            child_clazz = cls.ClazzDict[data_type]
            if isinstance(child_clazz.backreference, tuple) and len(child_clazz.backreference) > 1:
                return True
        return False
        

    @classmethod
    def establish_one_to_many(cls):
        for clazz in cls.ClazzDict.values():
            for member in clazz.members:
                if cls.is_one_to_many(member):
                    child_clazz = cls.ClazzDict[member.get_data_type()]
                    # establish backward connection
                    child_clazz.set_one_to_many(member)

    def __init__(self, prefix, name, parentName, element):
        self.prefix = prefix
        self.name = name
        self.parentName = parentName
        self.schema_element = element
        self.members = list()
        self.backreference = None
        self.schema_fields = list()
        self.schema_classes = OrderedDict()
        self.embedded_enums = list()
        self.choice_of = list()
        self.choice_parent = None
        self.inlines = list()
        self.dependants = list()
        self.visited = False

    def _update_schema_classes(self, name, data_type):
        """
        Updates self.schema_classes adding name->data_type if possible.

        Prints a warning to the logger if a name is used with multiple types.
        """
        if not name in self.schema_classes.keys():
            self.schema_classes[name] = data_type

        elif self.schema_classes[name] != data_type:
            logging.warn('__schema_classes__[{!r}] seems multi-' \
              'typed: {} != {}'.format(name, data_type,
              self.schema_classes[name]))

    def addMember(self, clazz_member):
        self.members.append(clazz_member)

    def set_one_to_many(self, clazz_member):
        if self.backreference is None:
            self.backreference = ()
        self.backreference += (clazz_member, )

    def is_empty(self):
        return not self.members

    def collect_data(self):
        """
        This method will generate all the anonymous choice types,
        as well as compute the __schema_XXX__ fields of Christian

        Furthermore, it collects information which types depend on others
        either because:
        - a member of self points to another type
        - self has a back reference and depends on the "parent" type
        - self is a choice type (depends on the choice types)
        
        """
        class_name = self.name

        # Luckily, back references are not a dependency, only schema_classes!
        #if self.backreference:
        #    member = self.backreference
        #    data_type = member.get_generated_type(member.source.name)
        #    back_clazz = self.ClazzDict[data_type]
        #    back_clazz.dependants.append(self)

        for member in self.members:
            name = member.get_generated_name()
            data_type = member.get_generated_type(member.get_data_type())
            if isinstance(member.child, XschemaElementBase):
                if member.child.choice:
                    if self.ClazzDict.has_key(data_type):
                        choice_type = self.ClazzDict[data_type]
                        self.choice_of.append((member.name, choice_type))
                        # self must be defined before choice_type since it's
                        # its superclass
                        if not choice_type in self.dependants:
                            self.dependants.append(choice_type)
                        if choice_type.choice_parent:
                            logging.error('Element used twice in choice: ' \
                              '{}'.format(data_type))
                        else:
                            choice_type.choice_parent = self

                        _inline_classname_suffix = ''
                        # Choice admin model inlines may not be collapsed,
                        # so do not use the INLINE_COLLAPSE_SNIPPET
                        _inline_template_snippets = ''
                        self.inlines.append((member.name, _inline_classname_suffix, data_type, _inline_template_snippets))

                    else:
                        self.choice_of.append((member.name, data_type))
                    # do not generate ordinary fields for this member
                    continue
                else:
                    if self.choice_of:
                        logging.warn('Mixture of choice and non-choice ' \
                          'members: {}'.format(name))
            else:
                #print(member.child)
                pass

            if data_type in Simple_type_table:
                if data_type in Integer_type_table:
                    if isinstance(member.get_data_type_chain(), list) and \
                      member.get_values():
                        _choice_name = class_name.upper()
                        _choice_values = []
                        _line = ''
                        for _choice_value in member.get_values():
                            _line = '{0}{1}, '.format(_line, int(_choice_value))
                            _choice_values.append(int(_choice_value))
                        
                        
                        self.embedded_enums.append('\n{}_{}_CHOICES = ' \
                          '_make_choices_from_int_list([\n{}\n])\n'.format(
                            _choice_name, name.upper(),
                            _line))
                elif data_type in Float_type_table:
                    pass
                elif data_type in Date_type_table:
                    pass
                elif data_type in DateTime_type_table:
                    pass
                elif data_type in Boolean_type_table:
                    pass
                elif data_type in String_type_table:
                    if isinstance(member.get_data_type_chain(), list) and \
                      member.get_values():
                        _choice_name = class_name.upper()
                        _choice_values = []
                        _line = '  '
                        for _choice_value in member.get_values():
                            if len(_line) + len(_choice_value) + 4 < 77:
                                _line += '{!r}, '.format(_choice_value)
                            else:
                                _choice_values.append(_line.rstrip())
                                _line = '  {!r},'.format(_choice_value)
                        
                        _choice_values.append(_line)
                        
                        self.embedded_enums.append('\n{}_{}_CHOICES = ' \
                          '_make_choices_from_list([\n{}\n])\n'.format(
                            _choice_name, name.upper(),
                            '\n'.join(_choice_values)))

                else:
                    logging.warn('Unhandled simple type: %s %s\n' % (
                        name, data_type, ))
            else:
                if (data_type != 'myString'):
                    self._update_schema_classes(name, data_type)
                    member_clazz = self.ClazzDict[data_type]

                if not member.is_unbounded():
                    # one-to-one relation, maybe optional
                    pass
                else:
                    # ManyToManyField, backward pointer in case of one-to-many
                    if self.is_valid_one_to_many(member):
                        # replace by backward pointing shadow field
                        _inline_classname_suffix = ''
                        _inline_template_snippets = ''
                        _optional = member.get_required() != 'REQUIRED'
                        _inline_type = member.child.getAppInfo('inline-type')
                        _tabular = (_inline_type == 'tabular')
                        if _tabular:
                            _inline_template_snippets += INLINE_SNIPPET_TABULAR
                        if _optional and not _tabular:
                            _inline_template_snippets += INLINE_SNIPPET_COLLAPSE
                        if self.has_multiple_one_to_many_references(member):
                            member_data_type = member.get_generated_type(member.source.name)
                            # TODO: remove warning
                            logging.warn('Multiple one-to-many: {}->{}'.format(member_data_type, data_type ))
                            _inline_classname_suffix = '_{}_model'.format(member_data_type)
                            _inline_template_snippets += INLINE_SNIPPET_FK_NAME.format(member_data_type.lower())
                        self.inlines.append((name, _inline_classname_suffix, data_type, _inline_template_snippets))

                    else:
                        #schema_classes[name] = data_type
                        pass


    def generate_simple_field(self, name, field_name, options, required):
        options += required
        
        if name == 'metaShareId':
            options += 'default="NOT_DEFINED_FOR_V2", '
        
        # XmlCharField, MetaBooleanField and MultiSelectField don't need the
        # "models." prefix as they are custom fields imported from
        # "metashare.repository.fields".
        if field_name in ('XmlCharField', 'MetaBooleanField',
                          'MultiSelectField'):
            self.wrtmodels('    %s = %s(%s)\n' % ( name, field_name, options, ))
        else:
            self.wrtmodels('    %s = models.%s(%s)\n' % ( name, field_name, options, ))
        self.wrtforms('    %s = forms.%s(%s)\n' % ( name, field_name, options, ))

    def generate_simple_member(self, member, name, data_type, multi_id, options):
        if not member.is_required():
            required = 'blank=True, null=True, '
        else:
            required = ''

        if isinstance(member.child, XschemaElement):
            helptext = member.child.getHelpText()
            if helptext:
                _help_text = _truncate_long_string(helptext, 72, 6)
                options += '\n      help_text={},\n      '.format(_help_text)

        if data_type in Integer_type_table:
            if isinstance(member.get_data_type_chain(), list) and \
              member.get_values():
                _choice_name = self.name.upper()
                choice_name = '{}_{}_CHOICES' \
                  .format(_choice_name, name.upper(), member.get_values())
                maxlen = member.get_maxlength()
                if maxlen:
                    logging.warn("max_length overwritten for choice of " \
                      "strings: {}".format(member))
                    if member.is_unbounded():
                        choice_options = \
                          CHOICES_TEMPLATE_MAXLEN.format(choice_name, maxlen)
                    else:
                        choice_options = \
                          SORTED_INT_CHOICES_TEMPLATE_MAXLEN.format(choice_name, maxlen)
                else:
                    choice_options = CHOICES_TEMPLATE.format(choice_name)
                
                # cfedermann: MultiSelectField generation...
                if member.is_unbounded():
                    choice_options = MULTI_CHOICES_TEMPLATE.format(choice_name)
                    
                    self.generate_simple_field(name, 'MultiSelectField',
                      options + choice_options, required)

                else:
                    self.generate_simple_field(name, 'IntegerField',
                      options + choice_options, required)
            else:
                self.generate_simple_field(name, 'IntegerField', options, required)
        elif data_type in Float_type_table:
            self.generate_simple_field(name, 'FloatField', options, required)
        elif data_type in Date_type_table:
            self.generate_simple_field(name, 'DateField', options, required)
        elif data_type in DateTime_type_table:
            self.generate_simple_field(name, 'DateTimeField', options, required)
        elif data_type in Boolean_type_table:
            if not member.is_required():
                required = 'blank=True, '
            self.generate_simple_field(name, 'MetaBooleanField', options, required)
        elif data_type in String_type_table:
            fixed_value = member.get_fixed()
            if fixed_value:
                options += 'default="{0}", editable=False, '.format(fixed_value)
            if not member.is_required():
                options += 'blank=True, '
            if isinstance(member.get_data_type_chain(), list) and \
              member.get_values():
                _choice_name = self.name.upper()
                choice_name = '{}_{}_CHOICES' \
                  .format(_choice_name, name.upper(), member.get_values())
                maxlen = member.get_maxlength()
                if maxlen:
                    logging.warn("max_length overwritten for choice of " \
                      "strings: {}".format(member))
                    if member.is_unbounded():
                        choice_options = \
                          CHOICES_TEMPLATE_MAXLEN.format(choice_name, maxlen)
                    else:
                        choice_options = \
                          SORTED_CHOICES_TEMPLATE_MAXLEN.format(choice_name, maxlen)
                else:
                    choice_options = CHOICES_TEMPLATE.format(choice_name)
                
                # cfedermann: MultiSelectField generation...
                if member.is_unbounded():
                    choice_options = MULTI_CHOICES_TEMPLATE.format(choice_name)
                    
                    self.generate_simple_field(name, 'MultiSelectField',
                      options + choice_options, '')

                else:
                    self.generate_simple_field(name, 'CharField',
                      options + choice_options, '')
            else:
                if data_type == 'gYear':
                    options += GYEAR_VALIDATOR_OPTION_SNIPPET

                maxlen = member.get_maxlength()
                if not maxlen:
                    maxlen = DEFAULT_MAXLENGTH
                choice_options = "max_length={}, ".format(maxlen)

                if not member.is_unbounded():
                    self.generate_simple_field(name, 'XmlCharField',
                      options + choice_options, '')
                else:
                    if not 'validators=' in options:
                        options += 'validators=[validate_matches_xml_char_production], '
                    self.wrtmodels(
                      '    %s = MultiTextField(%swidget=MultiFieldWidget('
                      'widget_id=%d, max_length=%s), %s)\n' % (
                        name, choice_options, multi_id, maxlen, options, ))
                    self.wrtforms(
                      '    %s = forms.CharField(%s%s)### FIX_ME: MULTITEXT %d\n' % (
                        name, choice_options, options, multi_id, ))
                    multi_id += 1
        else:
            logging.warn('Unhandled simple type: {} {}\n'.format(name, data_type))
        return multi_id

    def generate_myString_member(self, member, name, options):
        maxlen = member.get_maxlength()
        if maxlen:
            options += "\n      max_val_length={}, ".format(maxlen)

        help_string = member.child.getHelpText()
        if help_string:
            _help_text = _truncate_long_string(help_string, 72, 6)
            options += '\n      help_text={},\n      '.format(_help_text)

        if not member.is_required():
            options += 'blank=True'

        self.wrtmodels(
          '    %s = DictField(validators=[validate_lang_code_keys, validate_dict_values],\n'
          '      default_retriever=best_lang_value_retriever, %s)\n' % (
            name, options, ))

    def generate_complex_member(self, member, name, data_type, options):
        help_string = member.child.getHelpText()
        if help_string:
            _help_text = _truncate_long_string(help_string, 72, 6)
            options += '\n      help_text={},\n      '.format(_help_text)

        if data_type == 'myString':
            # myString is handled in a special way
            # the s after %(class) is important, _ gives errors
            #options =', related_name="%(class)s_{}_{}_model"'.format(name, data_type)
            #related_name=', related_name="{}_{}_{}_model"'.format(class_name, name, data_type)
            self.generate_myString_member(member, name, options)
        else:
            if not member.is_unbounded():
                field_type = member.child.getAppInfo('relation')
                model_field_name = 'OneToOneField'
                if field_type:
                    if field_type == 'many-to-one':
                        # A reusable component which can occur only once in this context:
                        model_field_name = 'ForeignKey'
                    elif field_type == 'many-to-many' or field_type == 'one-to-many':
                        # Complain but default to one-to-one
                        logging.warn(('wrong {} declaration for member {} '+ \
                                      'with at most one element').format(field_type, member))
                # this is a many-to-one or a one-to-one relation, maybe optional
                if not member.is_required():
                    options += 'blank=True, null=True, on_delete=models.SET_NULL, '


                self.wrtmodels(
                    '    %s = models.%s("%s_model", %s)\n' % (
                        name, model_field_name, data_type, options, ))
                self.wrtforms(
                    '    %s = forms.MultipleChoiceField(%s_model.objects.all())\n' % (
                        name, data_type, ))
            #else: # This was the previous solution: many-to-many is default
            elif not self.is_valid_one_to_many(member):
                if not member.is_required():
                    options += 'blank=True, null=True, '

                options += 'related_name="{}_%(class)s_related", '.format(name)
                self.wrtmodels(
                    '    %s = models.ManyToManyField("%s_model", %s)\n' % (
                        name, data_type, options, ))
                self.wrtforms(
                    '    %s = forms.MultipleChoiceField(%s_model.objects.all())### FIX_ME: ManyToMany\n' % (
                        name, data_type, ))
            else:
                self.wrtmodels('    # OneToMany field: {0}\n'.format(name))
                self.wrtforms('    # OneToMany field: {0}\n'.format(name))

    def generate_backref_members(self):
        """
        Generate a backreference (inverse one-to-many pointer)

        This only generates a back reference if it's in this Clazz object.
        
        """
        # treat a one-to-many relation as reverse foreign key
        if isinstance(self.backreference, ClazzBaseMember):
            self.generate_one_backref_member(self.backreference, required=True)
        elif isinstance(self.backreference, tuple):
            for member in self.backreference:
                self.generate_one_backref_member(member, required=False)

    def generate_one_backref_member(self, member, required):
        #name = member.get_generated_name()
        data_type = member.get_generated_type(member.source.name)

        # cfedermann: disabled related_name generation as it breaks export
        # of _model_set fields at the moment. This needs to be checked!
        options = ''#'related_name=\'back_to_{0}_model_from_{1}_model\', '\
        #  .format(data_type.lower(), self.name.lower())
        # Marc, 27 Feb 12: for the editor we need back references to corpusMediaType
        # to be optional at least in the database:
        if data_type == 'corpusMediaTypeType':
            required = False
        if not required:
            options += ' blank=True, null=True'

        # back reference fields are ALWAYS required
        #if not member.is_required():
        #    options = options + ', blank=True'
        #else:
        #    options = options + ', blank=False'
        self.wrtmodels(#'    %s_BACK = models.ForeignKey("%s_model"%s)\n\n' % (
          '    back_to_{0}_model = models.ForeignKey("{1}_model", {2})\n\n'
          .format(data_type.lower(), data_type, options, ))
        # TODO what about forms

    def generate_unicode_method(self):
        rendering_hint = self.schema_element.getAppInfo('render-short')
        if not rendering_hint:
            self.wrtmodels(UNICODE_DEFAULT_TEMPLATE)
        else:
            start = 0
            formatstring = ''
            formatargs = ''
            for match in re.finditer(r'{([^}]*)}', rendering_hint):
                formatstring += _escape_non_ascii_chars(
                        rendering_hint[start:match.start(1)]) \
                    + rendering_hint[match.end(1):match.end(0)]
                start = match.end(0)
                formatargs += '\'' + match.group(1) + '\', '
            formatstring += _escape_non_ascii_chars(rendering_hint[start:])
            self.wrtmodels(UNICODE_METHOD_TEMPLATE.format(formatstring,
              formatargs))

    def generate_choice_model_(self):
        """
        Generate a model for the given choice class

        choices is a list of the choice classes that this class represents.
        
        """
        verbose_name = self.schema_element.getAppInfo("label")
        if not verbose_name:
            verbose_name = getVerboseName(self.name)
        verbose_name_plural = self.schema_element.getAppInfo("label-plural")
        plural_snippet  = ''
        if verbose_name_plural:
            plural_snippet = VERBOSE_NAME_PLURAL_SNIPPET.format(verbose_name_plural)
        self.wrtmodels(CHOICE_SUPERCLASS_TEMPLATE.format(
          self.name, CHOICE_TYPE_SUPERCLASS,
          self.schema_element.getDocumentation(), verbose_name, plural_snippet))
        
        self.wrtforms('\nclass %s_form(forms.Form):\n' % (self.name, ))

        self.generate_backref_members()

    def generate_model_(self):
        """
        Generate a model for the given clazz self
        """
        for enum in self.embedded_enums:
            self.wrtmodels(enum)

        documentation = ''
        if isinstance(self.schema_element, XschemaElement):
            documentation = self.schema_element.getDocumentation()
        model_superclass = MODELS_SUPERCLASS
        if self.choice_parent:
            model_superclass = self.choice_parent.name + "_model"

        verbose_name = self.schema_element.getAppInfo("label")
        if not verbose_name:
            verbose_name = getVerboseName(self.name)
        verbose_name_plural = self.schema_element.getAppInfo("label-plural")
        plural_snippet  = ''
        if verbose_name_plural:
            plural_snippet = VERBOSE_NAME_PLURAL_SNIPPET.format(verbose_name_plural)
        self.wrtmodels(COMPLEX_MODEL_TEMPLATE.format(self.name,
          model_superclass, documentation, verbose_name, plural_snippet))

        self.wrtforms('\nclass %s_form(forms.Form):\n' % (self.name, ))
        if self.is_empty():
            self.wrtforms('    pass\n')

        _schema_name = self.name
        if self.name == 'resourceInfoType':
            _schema_name = 'resourceInfo'

        self.wrtmodels("\n    __schema_name__ = '{}'\n".format(_schema_name))
        if self.members:
            self.wrtmodels('    __schema_fields__ = (\n')
            for member in self.members:
                data_type = member.get_generated_type(member.get_data_type())
                django_field_name = member.get_generated_name()
                if not data_type in Simple_type_table \
                  and member.is_unbounded() \
                  and self.is_valid_one_to_many(member):
                    django_field_name = data_type.lower() + '_model_set'
                # choice child will only be not None if this member points to
                # a type that represents a type which is a xs:choice
                choice_child = None
                if self.ClazzDict.has_key(data_type):
                    choice_child = self.ClazzDict[data_type]
                    if not choice_child.choice_of:
                        choice_child = None
                if not choice_child:
                    self.wrtmodels('      ( {!r}, {!r}, {!s} ),\n'.format(
                      member.get_generated_name(), django_field_name,
                      member.get_required()))
                else:
                    for sub_choice in choice_child.choice_of:
                        if isinstance(sub_choice[1], Clazz):
                            data_type = sub_choice[1].name

                        else:
                            data_type = sub_choice[0] + "String"
                            parent_type = choice_child.name + "_model"

                            if not data_type in CHOICE_STRING_SUB_CLASSES.keys():
                                CHOICE_STRING_SUB_CLASSES[data_type] = [parent_type]

                            else:
                                if not parent_type in CHOICE_STRING_SUB_CLASSES[data_type]:
                                    CHOICE_STRING_SUB_CLASSES[data_type].append(parent_type)

                        self.wrtmodels('      ( \'{}/{}\', \'{}' \
                          '\', {!s} ),\n'.format(member.get_name(),
                          sub_choice[0], django_field_name,
                          member.get_required()))

                        # For xs:choice fields, we don't have to generate a
                        # class information entry for the super class; hence
                        # we remove it from self.schema_classes now.
                        if member.get_name() in self.schema_classes.keys():
                            self.schema_classes.pop(member.get_name())

                        self._update_schema_classes(sub_choice[0], data_type)

            self.wrtmodels('    )\n')
        if self.schema_classes:
            self.wrtmodels("    __schema_classes__ = {\n")
            _class_names = self.schema_classes.keys()
            _class_names.sort()
            for class_name in _class_names:
                data_type = self.schema_classes[class_name]
                self.wrtmodels('      {!r}: "{}_model",\n'.format(class_name,
                  data_type))
            self.wrtmodels('    }\n')

        self.wrtmodels('\n')

        # cfedermann: is this block EVER reached? If not, remove it!
        if self.parentName:
            raise AssertionError('self.parentName if block actually reached!')
            self.wrtmodels('    %s = models.ForeignKey("%s_model")\n' % (
               self.parentName, self.parentName, ))

        global MULTI_ID
        multi_id = MULTI_ID
        for member in self.members:
            name = member.get_generated_name()
            data_type = member.get_generated_type(member.get_data_type())
            verbose_name = None
            if isinstance(member.child, XschemaElement):
                verbose_name = member.child.getAppInfo('label')
            if not verbose_name:
                verbose_name = getVerboseName(name)
            options = '\n      verbose_name=\'{}\', '.format(verbose_name)
            
            if member.get_data_type() == 'xs:anyURI':
                options += 'validators=[HTTPURI_VALIDATOR], '
            
            elif member.name == 'email':
                options += 'validators=[EMAILADDRESS_VALIDATOR], '
            
            if data_type == 'myString':
                self.generate_myString_member(member, name, options)
            elif data_type in Simple_type_table:
                # simple type member
                multi_id = self.generate_simple_member(member, name, data_type,
                  multi_id, options)
                MULTI_ID = multi_id
            else:
                # complex type member
                self.generate_complex_member(member, name, data_type, options)
            self.wrtmodels('\n')

        if not self.choice_parent:
            self.generate_backref_members()

        if self.name in REUSABLE_ENTITIES:
            self.wrtmodels(REUSABLE_ENTITY_SNIPPET)

        if self.name == 'documentInfoType':
            self.wrtmodels('''    def save(self, *args, **kwargs):
        """
        Prevents id collisions for documentationInfoType_model sub classes.
        """
        # pylint: disable-msg=E0203
        if not self.id:
            # pylint: disable-msg=W0201
            self.id = _compute_documentationInfoType_key()
        super(documentInfoType_model, self).save(*args, **kwargs)

''')

        self.generate_unicode_method()

        if self.name == 'resourceInfoType':
            self.wrtmodels(TOP_LEVEL_TYPE_EXTRA_CODE_TEMPLATE)
    # end generate_model

    def topo_sort_rec(self, result):
        self.visited = 1
        for dependant in self.dependants:
            if not dependant.visited:
                dependant.topo_sort_rec(result)
            elif dependant.visited == 1:
                logging.error('dependency graph is cyclic')
        self.visited = 2
        result.append(self)

    @classmethod
    def topo_sort(cls, clazz_list):
        for clazz in clazz_list:
            clazz.visited = 0
        result = list()
        while clazz_list:
            clazz = clazz_list.pop()
            if not clazz.visited:
                cls.topo_sort_rec(clazz, result)
        result.reverse()
        return result

    @classmethod
    def generate(cls, outDirName, prefix, root, target_ns, schema_version,
                 package_prefix):
        cls.establish_one_to_many()

        models_file_name = os.path.join(outDirName, 'models.py')
        forms_file_name = os.path.join(outDirName, 'forms.py')
        admin_file_name = os.path.join(outDirName, 'admin.py')

        models_writer = Writer(models_file_name)
        forms_writer = Writer(forms_file_name)
        admin_writer = Writer(admin_file_name)
        cls.wrtmodels = models_writer.write
        cls.wrtforms = forms_writer.write
        cls.wrtadmin = admin_writer.write
        cls.wrtmodels(MODEL_HEADER.format(package_prefix, target_ns,
                                          schema_version))
        cls.wrtforms('from django import forms\n\n')

        exportableClassList = list()

        cls.wrtadmin('from django.contrib import admin\n')
        cls.wrtadmin('from {0}editor.superadmin import SchemaModelAdmin\n'.format(
          package_prefix))
        cls.wrtadmin('from {0}editor.inlines import SchemaModelInline\n'.format(
          package_prefix))

        for clazz in cls.ClazzDict.values():
            clazz.collect_data()
            if clazz.is_empty():
                if clazz.schema_element.isComplex():
                    exportableClassList.append(clazz)
                    logging.warn('empty type {}'.format(clazz))

                    # cfedermann: this would not be written inside the class.
                    # Hence we have to remove it later!
                    #
                    #cls.wrtforms('    pass\n')

            else:
                exportableClassList.append(clazz)

        clazz_list = Clazz.topo_sort(exportableClassList)

        if False: # to debug dependencies
            for clazz in exportableClassList:
                sys.stdout.write("{}: ".format(clazz.name))
                for dep in clazz.dependants:
                    sys.stdout.write("{}, ".format(dep.name))
                sys.stdout.write('\n')
            sys.stdout.write('\n')
            for clazz in clazz_list:
                sys.stdout.write("{}, ".format(clazz.name))
            sys.stdout.write('\n')

        for clazz in clazz_list:
            if clazz.choice_of:
                clazz.generate_choice_model_()
            else:
                clazz.generate_model_()

        _choice_names = CHOICE_STRING_SUB_CLASSES.keys()
        _choice_names.sort()

        for class_name in _choice_names:
            parent_types = CHOICE_STRING_SUB_CLASSES[class_name]
            cls.wrtmodels(CHOICE_STRING_SUB_CLASS_TEMPLATE.format(class_name,
              ', '.join(parent_types)))

            cls.wrtadmin(CHOICE_STRING_SUB_CLASS_ADMIN_TEMPLATE.format(class_name))

        # Sort clazzes to achieve consistent output order in admin.py.
        clazz_list.sort(key=lambda x:x.name)

        cls.wrtadmin('\nfrom {0}models import \\\n'.format(package_prefix))
        first_time = True
        for clazz in clazz_list:
            if first_time:
                cls.wrtadmin('    %s_model' % (clazz.name, ))
                first_time = False
            else:
                cls.wrtadmin(', \\\n    %s_model' % (clazz.name, ))
        cls.wrtadmin('\n\n\n')
        _inlines = []
        for clazz in clazz_list:
            _inlines.extend(clazz.inlines)

        _inlines.sort(key=lambda x:x[0])
        for _inline in _inlines:
            cls.wrtadmin(INLINE_TEMPLATE.format(_inline[0], _inline[1],
              _inline[2], _inline[3]))

        for clazz in clazz_list:
            cls.wrtadmin('admin.site.register({}_model, SchemaModelAdmin)\n'.format(
              clazz.name))
        cls.wrtadmin(MANUAL_ADMIN_REGISTRATION_TEMPLATE)
        cls.wrtadmin('\n')
        models_writer.close()
        forms_writer.close()
        admin_writer.close()
        cls.wrtmodels = None
        cls.wrtforms = None
        cls.wrtadmin = None
        print 'Wrote %d lines to models.py' % (models_writer.get_count(), )
        print 'Wrote %d lines to forms.py' % (forms_writer.get_count(), )
        print 'Wrote %d lines to admin.py' % (admin_writer.get_count(), )


class ClazzBaseMember(object):
    def get_name(self):
        return self.name

    def get_generated_name(self):
        name = self.get_name()
        dummy, name = get_prefix_name(name)
        name = cleanupName(name)
        if name == 'id':
            name += 'x'
        elif name.endswith('_'):
            name += 'x'
        #name = name[0].upper() + name[1:]
        return name

    def get_generated_type(self, data_type):
        dummy, data_type = get_prefix_name(data_type)
        if data_type in Clazz.simple_type_table:
            data_type = Clazz.simple_type_table[data_type]
            dummy, data_type = get_prefix_name(data_type.type_name)
        data_type = cleanupName(data_type)
        #data_type = data_type[0].upper() + data_type[1:]
        return data_type

    def get_required(self):
        if self.is_required():
            if isinstance(self.child, XschemaElement):
                if self.child.getAppInfo('recommended') == 'true':
                    logging.warn('{} is required, but tagged *recommended*'\
                        .format(self))
            return 'REQUIRED'
        else:
            if isinstance(self.child, XschemaElement):
                if self.child.getAppInfo('recommended') == 'true':
                    return 'RECOMMENDED'
            return 'OPTIONAL'

    def get_maxlength(self):
        if isinstance(self.child, XschemaElementBase):
            result = self.child.getRestrictionMaxLength()
            if result != -1:
                return result
        return None


class ClazzAttributeMember(ClazzBaseMember):
    def __init__(self, source_clazz, name, child):
        # the clazz where this member is embedded
        self.source = source_clazz
        # the name of the attribute
        self.name = name
        # the name of the base class
        self.child = child

    def get_data_type_chain(self):
        return self.child.getType()

    def get_data_type(self):
        return self.child.getType()

    # TODO
    def is_required(self):
        return 0 #(self.child.getMinOccurs() != 0)

    def is_unbounded(self):
        return 0

    def get_values(self):
        return []



class ClazzMember(ClazzBaseMember):
    def __init__(self, source_clazz, name, child):
        # the clazz where this member is embedded
        self.source = source_clazz
        # the name of the attribute
        self.name = name
        # the value (type) of this member
        self.child = child

    def get_data_type_chain(self):
        return get_data_type_chain(self.child)

    def get_data_type(self):
        return get_data_type(self.child)

    def is_required(self):
        if isinstance(self.child, str):
            return False
        return (self.child.getMinOccurs() != 0)

    def is_unbounded(self):
        if isinstance(self.child, str):
            return False
        return (self.child.getMaxOccurs() > 1)

    def get_values(self):
        if isinstance(self.child, str):
            return []
        return self.child.getValues()
    
    def get_fixed(self):
        if isinstance(self.child, str):
            return None
        attrs = self.child.getAttrs()
        if 'fixed' in attrs:
            return attrs['fixed']
        return None

    def is_one_to_many(self):
        if not self.is_unbounded():
            return False
        # this field can have unboundedly many values
        field_type = self.child.getAppInfo('relation')
        if not field_type or field_type == 'many-to-many':
            # assume default: many-to-many
            return False
        if field_type != "one-to-many":
            logging.warn(('wrong specification {} for unbounded member {}, ' + \
              'assuming one-to-many').format(field_type, self))
        return True

    def __str__(self):
        return "{}->{}->{}".format(self.source.name, self.name,
          self.get_data_type())

