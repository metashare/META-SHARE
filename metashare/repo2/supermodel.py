"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging
import re

from django.core.cache import cache
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models.fields import related
from django.db import models, IntegrityError
from traceback import format_exc
from xml.etree.ElementTree import Element, fromstring, tostring

from metashare.repo2.fields import MultiSelectField, MultiTextField, \
  MetaBooleanField

from metashare.settings import LOG_LEVEL, LOG_HANDLER
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repo2.supermodel')
LOGGER.addHandler(LOG_HANDLER)

REQUIRED = 1
OPTIONAL = 2
RECOMMENDED = 3

XML_DECL = re.compile(r'\s*<\?xml version=".+" encoding=".+"\?>\s*\n?',
  re.I|re.S|re.U)

METASHARE_ID_REGEXP = re.compile('<metashareId>.+</metashareId>',
  re.I|re.S|re.U)

# pylint: disable-msg=W0611
from metashare import repo2

def pretty_xml(xml_string):
    """
    Pretty-print the given XML String with proper indentation.
    """
    xml_string = xml_string.decode('utf-8').replace('><', '>\n<')

    # Delete any XML declaration inside the given XML String.
    xml_string = XML_DECL.sub(u'', xml_string)

    output = u'<?xml version="1.0" encoding="UTF-8"?>\n'

    # Stores the current indentation level.
    indent_level = 0
    for line in xml_string.split('\n'):
        line = line.strip()

        if line.startswith('<') and line.endswith('/>'):
            output += u'{0}{1}\n'.format('  ' * indent_level, line)
            continue

        if line.startswith('</') and line.endswith('>'):
            indent_level -= 1
            output += u'{0}{1}\n'.format('  ' * indent_level, line)
            indent_level -= 1
            continue

        if line.startswith('<') and line.endswith('>') and '</' in line:
            output += u'{0}{1}\n'.format('  ' * indent_level, line)
            continue

        if line.startswith('<') and line.endswith('>') and (not '</' in line):
            indent_level += 1
            output += u'{0}{1}\n'.format('  ' * indent_level, line)
            indent_level += 1
            continue

        if not line.startswith('<') and line.endswith('>') and ('</' in line):
            output += u'{0}{1}\n'.format('  ' * indent_level, line)
            continue

        output += u'{0}{1}\n'.format('  ' * indent_level, line)

    return output

def _remove_namespace_from_tags(element_tree):
    """
    Removes any namespace information from the given element_tree instance.
    """
    element_tree.tag = element_tree.tag.split('}')[-1]
    
    for child in element_tree.getchildren():
        _remove_namespace_from_tags(child)
    
    return element_tree

def _classify(class_name):
    """
    Converts the given class name into the corresponding class type object.
    """
    try:
        return eval('repo2.models.{}'.format(class_name))

    except NameError:
        return None


def _make_choices_from_list(source_list):
    """
    Converts a given list of Strings to tuple choices.

    Returns a dictionary containing two keys:
    - max_length: the maximum char length for this source list,
    - choices: the list of (index, value) tuple choices.
    """
    _choices = []
    for index, value in enumerate(source_list):
        _choices.append((str(index), value))
    return {'max_length': len(_choices)/10+1, 'choices': tuple(_choices)}


class SchemaModel(models.Model):
    """
    Super class for all XSD schema types/components.
    """
    __schema_name__ = 'UNDEFINED'
    __schema_fields__ = ()
    __schema_attrs__ = ()
    __schema_classes__ = {}
    __schema_parent__ = None
    
    class Meta:
        """
        This is an abstract super class for all schema models.
        """
        abstract = True

    @classmethod
    def get_many_to_many_fields(cls):
        """
        Returns a list containing all ManyToManyField fields for this model.
        """
        return [field.name for field in cls._meta.local_many_to_many]

    @classmethod
    def get_fields_flat(cls, unique_values=True):
        """
        Return all fields in a flat list
        """
        _fields = []
        for _, _field, _ in cls.__schema_fields__:
            if unique_values and _field in _fields:
                continue
            _fields.append(_field)

        return _fields

    @classmethod
    def get_fields(cls, unique_values=True):
        """
        Returns a dictionary containing all fields.
        """
        _fields = {'required': [], 'recommended': [], 'optional': []}
        for _not_used, _field, _required in cls.__schema_fields__:
            if _required == REQUIRED:
                if unique_values and _field in _fields['required']:
                    continue

                _fields['required'].append(_field)

            elif _required == RECOMMENDED:
                if unique_values and _field in _fields['recommended']:
                    continue

                _fields['recommended'].append(_field)

            else:
                if unique_values and _field in _fields['optional']:
                    continue

                _fields['optional'].append(_field)

        return _fields

    @classmethod
    def get_field_sets(cls, unique_values=True):
        """
        Returns a dictionary containing just "*_set" fields.
        """
        _field_sets = {'required': [], 'recommended': [], 'optional': []}
        for _not_used, _field, _required in cls.__schema_fields__:
            if _field.endswith('_set'):
                if _required == REQUIRED:
                    if unique_values and _field in _field_sets['required']:
                        continue

                    _field_sets['required'].append(_field)

                elif _required == RECOMMENDED:
                    if unique_values and _field in _field_sets['recommended']:
                        continue

                    _field_sets['recommended'].append(_field)

                else:
                    if unique_values and _field in _field_sets['optional']:
                        continue

                    _field_sets['optional'].append(_field)

        return _field_sets

    @classmethod
    def get_verbose_name(cls, fieldname):
        """
        For a real field such as 'firstName'
        or a pseudo-field such as 'contactinfotype_model_set',
        obtain the best possible verbose name that we can give.
        """
        #fields = cls._meta.get_field_by_name(fieldname)
        #if fields:
        #    field = fields[0]
        #    return field.verbose_name
        try:
            field = cls._meta.get_field(fieldname)
            return field.verbose_name
        except:
            remote = getattr(cls, fieldname, None)
            if isinstance(remote, ForeignRelatedObjectsDescriptor):
                return remote.related.model._meta.verbose_name
            return fieldname

    @staticmethod
    def _python_to_xml(value):
        """
        Converts the given Python value to its XML representation.
        """
        # Boolean values need to be rendered as 'true' or 'false' Strings.
        if isinstance(value, bool):
            if value:
                return 'true'
            else:
                return 'false'

        # String instances are converted to Unicode instances.
        elif isinstance(value, basestring):
            return unicode(value)

        # All other values are encoded as Strings.
        else:
            return str(value)

    @staticmethod
    def _xml_to_python(value, field):
        """
        Converts the given XML value to its Python representation for field.
        """
        # If no field is given, we have to return the value unmodified.
        if field is None:
            return value

        result = value

        # Handle fields with choices as we need to convert the current value
        # to the database representation value of the respective choice.
        if len(field.choices) > 0:
            # MetaBooleanField instances are a special case: here, we need to
            # return either 'Yes' or 'No', depending on the given value.
            if isinstance(field, MetaBooleanField):
                if value.strip().lower() in ('true', 'yes', '1'):
                    result = 'Yes'

                elif value.strip().lower() in ('false', 'no', '0'):
                    result = 'No'
                
                else:
                    LOGGER.error(u'Value {} not a valid MetaBooleanField ' \
                      'choice for {}'.format(repr(value), field.name))

            else:
                for _db_value, _readable_value in field.choices:
                    if _readable_value == value:
                        result = _db_value

                if result == value:
                    LOGGER.error(u'Value {} not found in choices for ' \
                      '{}'.format(repr(value), field.name))

        elif isinstance(field, models.BooleanField) \
          or isinstance(field, models.NullBooleanField):
            if value.strip().lower() == 'true':
                result = True

            elif value.strip().lower() == 'false':
                result = False

            else:
                LOGGER.error(u'Value {} not a valid Boolean for {}'.format(
                  repr(value), field.name))

        elif isinstance(field, models.TextField) \
          or isinstance(field, MultiTextField):
            if value is None:
                result = ''

        return result

    def export_to_elementtree(self):
        """
        Exports this instance to an XML ElementTree.
        """
        if self.__schema_name__ == "SUBCLASSABLE":
            # pylint: disable-msg=E1101
            return self.as_subclass().export_to_elementtree()

        _root = Element(self.__schema_name__)

        # Fix namespace attributes for the resourceInfo root element.
        if _root.tag == 'resourceInfo':
            _root.attrib['xmlns:ms'] = "http://www.ilsp.gr/META-XMLSchema"
            _root.attrib['xmlns:xsi'] = "http://www.w3.org/2001/" \
              "XMLSchema-instance"
            _root.attrib['xsi:schemaLocation'] = "http://www.ilsp.gr/META-" \
              "XMLSchema META-SHARE-Resource.xsd"

        # We first serialize all schema attributes.  For the moment, we just
        # assume that attributes are Strings only.  This holds for the v1.1
        # representative XSD, still more clever value handling might actually
        # be required for version v2; depends on the final schema...
        for _xsd_attr, _model_field, _not_used in self.__schema_attrs__:
            try:
                # First, we check if there is a get_FOO_display() method.
                _func = getattr(self, 'get_{0}_display'.format(_model_field))

                # If so, we call this method to determine the current value.
                _value = _func()

            except AttributeError:
                # Otherwise, we try to retrieve the value via getattr().
                _value = getattr(self, _model_field, None)

            # If a value could be found, it becomes an attribute of the node.
            if _value is not None:
                _root.attrib[_xsd_attr] = SchemaModel._python_to_xml(_value)

        # Then, we loop over all schema fields, retrieve their values and put
        # XML-ified versions of these values into the XML tree.
        for _xsd_field, _model_field, _not_used in self.__schema_fields__:
            try:
                # Again, we first check for a get_FOO_display() method.
                _func = getattr(self, 'get_{0}_display'.format(_model_field))
                _value = _func()

            except AttributeError:
                # Only falling back to getattr() if it doesn't exist.
                _value = getattr(self, _model_field, None)

            if _value is not None:
                _model_set_value = _model_field.endswith('_model_set')

                # For ManyToManyFields, compute all related objects.
                if isinstance(_value, models.Manager):
                    _value = _value.all()

                # For MetaBooleanFields, we actually need the database value.
                elif isinstance(_value, MetaBooleanField):
                    _value = getattr(self, _model_field, None)

                # If the value is not yet of list type, we wrap it in a list.
                elif not isinstance(_value, list):
                    _value = [_value]

                # Iterate over all values inside the current _value list.
                for _sub_value in _value:
                    # For SubclassableModel instances, we have to check if the
                    # sub class type matches the current XSD name; otherwise
                    # we have to ignore the current value.
                    if isinstance(_sub_value, SubclassableModel):
                        _clazz = _sub_value.as_subclass()
                        _clazz_name = _clazz.__class__.__name__
                        _choice_name = None
                        _xsd_name = _xsd_field.split('/')[-1]

                        if _xsd_name in self.__schema_classes__.keys():
                            _choice_name = self.__schema_classes__[_xsd_name]

                        if _clazz_name != _choice_name:
                            LOGGER.debug(u'Skipping choice value {}'.format(
                              _xsd_name))
                            continue

                        # If this is the correct sub class type, copy _clazz
                        # to the _sub_value variable for further processing...
                        _sub_value = _clazz

                    # Handle element paths inside _xsd_field names.  Supports
                    # element paths such as e.g. affiliation/OrganizationInfo.
                    _current_node = _root
                    _path = _xsd_field.split('/')
                    if len(_path) > 1:
                        # Iterate over all intermediate names and then create
                        # the corresponding element for these.
                        for _tag in _path[:-1]:
                            # Only create a new intermediate element if there
                            # is not already one available...
                            _element = None
                            if _model_set_value:
                                _element = _current_node.find(_tag)

                            if _element is None:
                                _element = Element(_tag)
                                _current_node.append(_element)

                            _current_node = _element

                    # The last name inside the path becomes our _xsd_name.
                    _xsd_name = _path[-1]

                    # For complex values, we recursively call this method.
                    if isinstance(_sub_value, SchemaModel):
                        if _sub_value.__schema_name__ == "STRINGMODEL":
                            _element = Element(_xsd_name)
                            _element.text = SchemaModel._python_to_xml(_sub_value.value)
                            _current_node.append(_element)

                        else:
                            _sub_value = _sub_value.export_to_elementtree()

                            # We fix the sub value's tag as it may be "wrong".
                            # E.g., PersonInfo is sometimes called contactPerson.
                            _sub_value.tag = _xsd_name

                            # And append the sub structure to the current node.
                            _current_node.append(_sub_value)

                    # Simple values are added to a new element and appended.
                    else:
                        _element = Element(_xsd_name)
                        _element.text = SchemaModel._python_to_xml(_sub_value)
                        _current_node.append(_element)

        # Return root node of the ElementTree; can be converted to String
        # using: xml.etree.ElementTree.tostring(_root, encoding="utf-8")
        return _root

    @classmethod
    def _check_for_duplicates(cls, _object):
        """
        Checks if the given _object is a redundant copy of another object.

        Returns a list containing all existing objects that are equal to the
        given _object instance, sorted by primary key 'id'.

        """
        _was_duplicate = False
        _related_objects = []

        # We collect all value constraints in a dictionary.
        kwargs = {}

        # Build list of field names for this class type.  Using introspection
        # with cls._meta.get_all_field_names() would not work as it contains
        # additional fields such as id and related fields that would break our
        # comparison code.
        _fields = [x[1] for x in cls.__schema_fields__]
        _fields.extend([x[1] for x in cls.__schema_attrs__])

        # Ensure that "back_to_" pointers are available for checking.
        for _field in cls._meta.fields:
            if isinstance(_field, related.ForeignKey):
                if _field.name.startswith('back_to_') and \
                  not _field.name in _fields:
                    _fields.append(_field.name)

        # We iterate over all model fields of the current _object.
        for field_name in _fields:
            # OneToMany fields need to be handled later, hence we add these to
            # our _related_objects list and continue with the loop.
            if field_name.endswith('_set'):
                _related_objects.append(field_name)
                LOGGER.debug(u'Skipping OneToMany "{}"'.format(field_name))
                continue

            # Retrieve the model field value using getattr().  This is enough
            # as even if a get_FOO_display() method would exist for a field,
            # the "raw" values needed to be compared anyway.
            _value = getattr(_object, field_name, None)

            # Retrieve model field instance to allow type checking.
            _field = _object._meta.get_field_by_name(field_name)[0]

            # For ManyToManyFields, compute the list of related objects.
            if isinstance(_field, related.ManyToManyField):
                _value = _value.all()

                # If there is no related object for this ManyToManyField, we
                # have to constrain kwargs[field_name] with the None value.
                if not len(_value):
                    _value = None

            # Finally, OneToOneField instances have to be checked as related
            # objects and hence need to be put into _related_objects.
            elif isinstance(_field, related.OneToOneField):
                LOGGER.debug(u'Skipping OneToOne "{}"'.format(field_name))
                _related_objects.append(field_name)
                continue

            # For ForeignKey instances, we have to check their name first.
            # "back_to_" fields need to be put into _related_objects, while
            # "normal" ForeignKey fields can be checked with our QuerySet.
            elif isinstance(_field, related.ForeignKey):
                if field_name.startswith('back_to_'):
                    LOGGER.debug(u'Skipping back_to "{}"'.format(field_name))
                    _related_objects.append(field_name)
                    continue

            # If the field value is not None or the field allows None as value
            # we set the current value as constraint in our kwargs dictionary.
            if _value is not None:
                kwargs[field_name] = _value

            elif _field.null:
                kwargs[field_name] = None

            # Otherwise, we print a message that we skip the current field.
            else:
                LOGGER.debug(u'Skipping {0}={1} ({2})'.format(field_name,
                  _value, type(_field)))

        # Use **magic to create a constrained QuerySet from kwargs.
        query_set = cls.objects.filter(**kwargs)

        LOGGER.debug('cls: {}'.format(cls))
        LOGGER.debug('kwargs: {}'.format(kwargs))

        _duplicates = []
        if query_set.count() > 1:
            # We now know that there may exist at least one duplicate for the
            # given _object;  we have to check the related objects to be sure.

            # As the META-SHARE id is not yet defined for 
            _msg = u'Ignoring META-SHARE id in _check_for_duplicates() as ' \
              'it is not yet defined.'
            LOGGER.warning(_msg)
            
            # Convert the current object into its serialised XML String and
            # remove any META-SHARE related id from this String.
            _obj_value = tostring(_object.export_to_elementtree())
            _obj_value = METASHARE_ID_REGEXP.sub('', _obj_value)

            # Iterate over all potential duplicates, ordered by increasing id.
            for _candidate in query_set.order_by('id'):
                # Skip the current candidate if it is our _object itself.
                if _candidate == _object:
                    continue

                # Convert candidate into XML String and remove META-SHARE id.
                _check = tostring(_candidate.export_to_elementtree())
                _check = METASHARE_ID_REGEXP.sub('', _check)

                # If both XML Strings are equal, we have found a duplicate!
                if _obj_value == _check:
                    _duplicates.append(_candidate)

            LOGGER.debug('FINAL _duplicates: {}'.format(_duplicates))

        return _duplicates

    @staticmethod
    def _cleanup(objects, only_remove_duplicates=False):
        """
        Deletes all objects within the given objects list.

        The objects list contains tuples (obj, status) where obj is a Django
        object instance and status is in {'C', 'D', 'O'}.

        * 'C' == 'Created':   The corresponding object has just been created.

        * 'D' == 'Duplicate': The corresponding object is a duplicate.

        * 'O' == 'Original':  The corresponding object pre-existed in the DB.

        If only_remove_duplicates=True, only object instances with status='D'
        will be deleted while other instances are kept.
        
        Returns a list containing all instances which have not been deleted.

        """
        _objects = []
        for (obj, status) in objects:
            if only_remove_duplicates and status != 'D':
                LOGGER.debug(u'Keeping object {} ({})'.format(obj, status))
                _objects.append((obj, status))
                continue

            if obj.id:
                try:
                    LOGGER.debug(u'Deleting object {0}'.format(obj))
                    obj.delete()

                except ObjectDoesNotExist:
                    continue
        
        return _objects

    # pylint: disable-msg=R0911
    @classmethod
    def import_from_elementtree(cls, element_tree, cleanup=True, parent=None):
        """
        Imports the given XML ElementTree into an instance of type cls.

        Returns a tuple containing a reference to the created object instance
        as first value and the list of all objects that have been created when
        import the given XML ElementTree as second value.

        Returns (None, []) in case of errors.
        """
        LOGGER.debug(u'parent: {0}'.format(parent))
        
        # We ignore name space information in tags, hence we remove it.
        element_tree = _remove_namespace_from_tags(element_tree)

        # First, we make sure that the given element_tree has the right tag.
        if element_tree is None \
          or element_tree.tag != cls.__schema_name__:
            _msg = u"Tags don't match: {}!={}".format(element_tree.tag,
              cls.__schema_name__)
            LOGGER.error(_msg)
            return (None, [], _msg)

        # We collect a list of all objects that are (recursively) created by
        # the importing process.  This is required if rollback has to be done.
        _created = []

        # We also need to instantiate a new instance of this class type.
        _object = cls()

        # If a parent instance is given, add it to the object instance.
        if parent:
            _class_name = parent.__class__.__name__.lower()
            _foreign_key_name = 'back_to_{0}'.format(_class_name)

            try:
                LOGGER.debug(u'Setting schema parent {0}={1}'.format(
                  _foreign_key_name, parent))

                _ = _object._meta.get_field_by_name(_foreign_key_name)[0]
                setattr(_object, _foreign_key_name, parent)

            except (models.FieldDoesNotExist, AttributeError) as _exc:
                _msg = u"Could not set schema parent! ({})".format(_exc)
                LOGGER.error(_msg)
                SchemaModel._cleanup(_created)
                return (None, [], _msg)

        for xsd_attr, _model_field, _not_used in cls.__schema_attrs__:
            # Get attribute value and field instance for this xsd_attr.
            _attr = element_tree.attrib.get(xsd_attr, None)
            _field = _object._meta.get_field_by_name(_model_field)[0]

            # Convert attribute value to its Python representation for field.
            _value = SchemaModel._xml_to_python(_attr, _field)

            # If a value could be found, set the model field value.
            if _value is not None:
                setattr(_object, _model_field, _value)

        # Iterate over all model fields for an cls instance.  These need to be
        # sorted so that any _set fields are processed at the end!
        _fields_before_sets = list(cls.__schema_fields__)

        # The following allows to sort all ManyToMany field instances to the
        # end of the list; this is required to ensure that all required fields
        # can be handled and filled before saving this instance for handling
        # the ManyToMany fields...
        _fields_before_sets.sort(key=lambda x: x[2] == REQUIRED, reverse=True)

        _many_to_many_fields = []
        for _field in _fields_before_sets:
            if _field[1].endswith('_set'):
                continue

            _model_field = _object._meta.get_field_by_name(_field[1])[0]
            if isinstance(_model_field, related.ManyToManyField):
                _many_to_many_fields.append(_field)
                _fields_before_sets.remove(_field)

        _fields_before_sets.extend(_many_to_many_fields)

        _fields_before_sets.sort(cmp=lambda x, y: -y[1].endswith('_set'))

        for xsd_field, _model_field, _required in _fields_before_sets:
            # We want to collect all values for the current model field.  This
            # may be several, e.g., for multiple contactPerson elements.
            _values = []
            _parent = None

            # If we are handling a field set, we have to make sure that our
            # object instance has a valid identifier to be used as parent.
            # If the object instance's id is None, we have to save it first!
            if _model_field.endswith('_set'):
                if _object.id is None:
                    try:
                        LOGGER.debug(u'Saving parent object for {0}'.format(
                          _model_field))
                        _object.save()

                    except IntegrityError as _exc:
                        # pylint: disable-msg=E1101
                        _msg = u'Could not save {} object! ({})'.format(
                          _object.__class__, _exc)
                        LOGGER.error(_msg)

                        LOGGER.error(u'cls.__schema_parent__: {0}'.format(
                          cls.__schema_parent__))
                        LOGGER.error(u'parent: {0}'.format(parent))
                        if parent:
                            LOGGER.error(u'parent.__class__.__name__: ' \
                              u'{0}'.format(parent.__class__.__name__))

                        SchemaModel._cleanup(_created)
                        return (None, [], _msg)

                # Set current object instance as parent for recursive import.
                _parent = _object

            # Iterate over all sub elements with the current XSD field name.
            for _value in element_tree.findall(xsd_field):
                # As field sets are virtual, we set _field=None for them.
                if _model_field.endswith('_set'):
                    _field = None

                else:
                    _field = _object._meta.get_field_by_name(_model_field)[0]

                # If the current value is simple-typed, append its text value.
                if not len(_value.getchildren()):
                    _text = SchemaModel._xml_to_python(_value.text, _field)
                    LOGGER.debug(u'_value.tag: {}, _value.text: {}'.format(
                      _value.tag, _text))

                    # We skipt empty, simple-typed elements.
                    if not _text:
                        continue

                    if _value.tag in cls.__schema_classes__.keys():
                        LOGGER.debug(u'_schema_classes__[{}] = {}'.format(
                          _value.tag, cls.__schema_classes__[_value.tag]))
                        _sub_cls = _classify(
                          cls.__schema_classes__[_value.tag])
                        if _sub_cls.__schema_name__ == "STRINGMODEL":
                            LOGGER.debug(u'Creating STRINGMODEL {}.'.format(
                              _text))
                            _instance = _sub_cls()
                            _instance.value = _text
                            _instance.save()
                            _created.append(_instance)
                            _text = _instance

                    _values.append(_text)

                # Otherwise, we have to handle the complex structure of value.
                else:
                    # For this, we have defined a mapping from XSD element
                    # names to Django model classes inside __schema_classes__.
                    if not _value.tag in cls.__schema_classes__.keys():
                        _msg = u'Unsupported tag: {} not in {}'.format(
                          _value.tag, cls.__schema_classes__.keys())
                        LOGGER.error(_msg)

                        # There has been an error during import hence we have
                        # to rollback any changes made so far using _cleanup()
                        # and return an empty result.
                        SchemaModel._cleanup(_created)
                        return (None, [], _msg)

                    # Retrieve sub class type for current element tag.
                    _sub_cls = _classify(cls.__schema_classes__[_value.tag])

                    # Create a copy of this Element as we have to change its
                    # tag value which would modify the original ElementTree.
                    LOGGER.debug(u'Creating copy of {0} as it has to be ' \
                      u'modified'.format(_value.tag))
                    _value_copy = fromstring(tostring(_value))
                    _value = _value_copy

                    # Fix the tag name for the current element as it may be
                    # different, e.g., for contactPerson vs. PersonInfo.
                    _value.tag = _sub_cls.__schema_name__

                    # If the current field is NOT a OneToOne field, we have to
                    # check for duplicates after creating of the sub object!
                    
                    # The initial assumption is that duplicate objects should
                    # be deleted immediately;  this does not hold for OneToOne
                    # and OneToMany fields (where _parent is not None), only.
                    _delete_duplicate_objects = True
                    
                    if isinstance(_field, related.OneToOneField) or _parent:
                        _delete_duplicate_objects = False

                    # Try to import the sub element from the current value.
                    LOGGER.debug(u'Trying to import sub object {0}'.format(
                      _value.tag))
                    _sub_result = _sub_cls.import_from_elementtree(_value,
                      cleanup=_delete_duplicate_objects, parent=_parent)

                    _sub_object = _sub_result[0]
                    _sub_created = _sub_result[1]
                    _sub_error = None
                    if len(_sub_result) > 2:
                        _sub_error = _sub_result[2]

                    # If an error occured, _sub_object is None and we have to
                    # perform cleanup and return an empty result.
                    if not _sub_object:
                        _msg = u'Sub object {} could not be imported!'.format(
                          _value.tag)
                        LOGGER.error(_msg)
                        LOGGER.error(_sub_error)
                        SchemaModel._cleanup(_created)
                        return (None, [], _sub_error)

                    # Otherwise, we add the newly created, related instances
                    # the list of _created objects for this import operation.
                    else:
                        _created.extend(_sub_created)

                    _values.append(_sub_object)

            # If there are no values for the current field, we don't have to
            # save anything and can continue.
            if not len(_values):
                continue

            # Otherwise we need to save the values in the class instance.
            LOGGER.debug(u'Setting {0} ({1}) = {2}'.format(_model_field,
              type(_field).__name__, [unicode(x) for x in _values]))

            # If the model field is a ManyToManyField instance, we have to
            # ensure that the current _object is instantiated in the database
            # as otherwise it would not have an id value.  Afterwards, we loop
            # over all values for this field and add these to the field set.
            if isinstance(_field, related.ManyToManyField):
                # Save the current _object to obtain an id.  If the something
                # bad happens during saving, catch the exception and rollback.
                try:
                    _object.save()

                except IntegrityError as _exc:
                    # pylint: disable-msg=E1101
                    _msg = u'Could not save {} object! ({})'.format(
                      _object.__class__, _exc)
                    LOGGER.error(_msg)

                    LOGGER.error(u'cls.__schema_parent__: {0}'.format(
                      cls.__schema_parent__))
                    LOGGER.error(u'parent: {0}'.format(parent))
                    if parent:
                        LOGGER.error(u'parent.__class__.__name__: {0}'.format(
                          parent.__class__.__name__))
                    LOGGER.error(u'_parent: {0}'.format(_parent))
                    if _parent:
                        LOGGER.error(u'_parent.__class__.__name__: {}'.format(
                          _parent.__class__.__name__))

                    SchemaModel._cleanup(_created)
                    return (None, [], _msg)

                # Retrieve setter for current model field.
                _model_setter = getattr(_object, _model_field)

                # Loop over all values and add each value to field set.
                for _value in _values:
                    _model_setter.add(_value)

            # For MultiSelectField instances, we have to assign the list.
            elif isinstance(_field, MultiSelectField):
                setattr(_object, _model_field, _values)

            # If the model field is a MultiTextField, we have to retrieve the
            # model field setter and append values to the field list.
            elif isinstance(_field, MultiTextField):
                _model_setter = getattr(_object, _model_field)
                for _value in _values:
                    _model_setter.append(_value)

            # Otherwise, we are handling a single-valued field.  Similar to
            # ForeignKey fields, this can be handled using setattr().
            elif _field is not None:
                try:
                    # assert(len(_values) == 1)
                    setattr(_object, _model_field, _values[0])

                except AssertionError:
                    _msg = u'Single value required: {0}:{1}'.format(
                      _model_field, _values)
                    LOGGER.error(_msg)
                    SchemaModel._cleanup(_created)
                    return (None, [], _msg)

        # This raises a django.db.IntegrityError if the current object does
        # not validate;  if that is the  case, we have to rollback any changes
        # we performed so far!  We can do so by calling _cleanup.
        try:
            _object.full_clean()
            _object.save()

            # Check if the current _object instance is a duplicate.
            _duplicates = cls._check_for_duplicates(_object)
            _was_duplicate = len(_duplicates) > 0

            LOGGER.debug(u'_object: {0}, _was_duplicate: {1}, ' \
              'cleanup: {2}'.format(_object, _was_duplicate, cleanup))

            # Add current _object instance to the _created list with correct
            # status: 'D' if it was a duplicate, 'C' otherwise.
            if _was_duplicate:
                _created.append((_object, 'D'))

                # If we are allowed to perform cleanup, we do so and also
                # replace our _object instance with the "original" object.
                if cleanup:
                    _created = SchemaModel._cleanup(_created,
                      only_remove_duplicates=True)

                    # Replace _object instance with "original" object.
                    _object = _duplicates[0]
                    _created.append((_object, 'O'))

            else:
                _created.append((_object, 'C'))

        except (IntegrityError, ValidationError) as _exc:
            detail = u''
            if hasattr(_exc, 'message_dict'):
                for key in _exc.message_dict:
                    value = _exc.message_dict[key]
                    if isinstance(value, list):
                        value = ', '.join(value)
                    if len(detail) > 0:
                        detail += '; '
                    detail += u"'{}': {}".format(key, value)
            else:
                detail = str(_exc)
            
            _msg = u'Could not import <{}>! ({})'.format(element_tree.tag,
              detail)
            LOGGER.error(_msg)

            LOGGER.error(u'cls.__schema_parent__: {0}'.format(
              cls.__schema_parent__))
            LOGGER.error(u'parent: {0}'.format(parent))
            if parent:
                LOGGER.error(u'parent.__class__.__name__: {0}'.format(
                  parent.__class__.__name__))

            SchemaModel._cleanup(_created)
            return (None, [], _msg)

        # TODO: the _created list might contain invalidated instances which
        # have been deleted during duplication resolution!  This needs to be
        # fixed by looping over the created set and checking if a QuerySet
        # with the corresponding pk is empty or not...

        # If we get here, the _object validates and is not a duplicate.  Hence
        # we return a tuple containing a reference to the object and the list
        # of related object instances that have been created during import.
        return (_object, set(_created))

    @classmethod
    def import_from_string(cls, element_string, parent=None):
        """
        Imports the given string representation of an XML element tree
        into an instance of type cls.

        Returns a tuple containing a reference to the created object instance
        as first value and the list of all objects that have been created when
        import the given XML ElementTree as second value.

        Returns (None, []) in case of errors.
        """
        return cls.import_from_elementtree(fromstring(element_string),
          parent=parent)

    def get_unicode(self, field_spec, separator):
        field_path = re.split(r'/', field_spec)
        return self.get_unicode_rec_(field_path, separator)

    def get_unicode_rec_(self, field_path, separator):
        field_spec = field_path[0]
        if len(field_path) == 1:
            value = getattr(self, field_spec, None)
            if not value:
                return u''
            model_field = self._meta.get_field_by_name(field_spec)
            if isinstance(model_field[0], models.CharField) or \
              isinstance(model_field[0], MultiSelectField):
                # see if it's an enum CharField with options and return the
                # string instead of the option number
                display = getattr(self,
                  'get_{}_display'.format(field_spec), None)
                if display:
                    value = display()
                return value
            elif isinstance(model_field[0], MultiTextField):
                return separator.join(value)
            if hasattr(value, 'all') and \
              hasattr(getattr(value, 'all'), '__call__'):
                return separator.join([u'{}'.format(child) for child in value.all()])
            else:
                try:
                    return separator.join([u'{}'.format(child) for child in value])
                except TypeError:
                    pass
                if (isinstance(model_field[0], models.DateField) or \
                  isinstance(model_field[0], models.BooleanField) or \
                  isinstance(model_field[0], models.IntegerField)):
                    return u'{}'.format(value)

                return u'*{}*'.format(value)
        else:
            for xsd_name, field_name , _not_used in self.__schema_fields__:
                if xsd_name.startswith(field_spec):
                    values = getattr(self, field_name, None)
                    if not values:
                        return u''
                    if isinstance(values, SchemaModel):
                        return values.get_unicode_rec_(field_path[1:],
                          separator)
                    # these are multiple values, possibly a query set of django
                    if hasattr(values, 'all') and \
                      hasattr(getattr(values, 'all'), '__call__'):
                        return separator.join([
                          child.get_unicode_rec_(field_path[1:], separator) 
                          for child in values.all()
                        ])
                    try:
                        return separator.join([u'{}'.format(value) for value in values])
                    except TypeError:
                        pass
                    return u'*{}*'.format(values)
        return u'*FAILURE*'

    def unicode_(self, formatstring, args):
        formatvalues = []
        #print u'{!r}'.format(formatstring)
        #print u'{!r}'.format(args)
        for formatarg in args:
            separator = u' '
            if isinstance(formatarg, tuple):
                separator = formatarg[1]
                formatarg = formatarg[0]
            formatvalue = self.get_unicode(formatarg, separator)
            formatvalues.append(formatvalue)
        _unicode = formatstring.format(*formatvalues)
        return _unicode

    def __unicode__(self):
        cache_key = '{}_{}'.format(self.__schema_name__, self.id)
        #print u'cache key: >>{}<<'.format(cache_key)
        cached = cache.get(cache_key, None) # set to None for no caching
        if cached is None:
            try:
                # pylint: disable-msg=E1101
                cached = self.real_unicode_()
            # pylint: disable-msg=W0703
            except Exception, e:
                LOGGER.error('in unicode: {}'.format(e))
                LOGGER.error(format_exc())
                cached = u'<{} id="{}>'.format(self.__schema_name__, self.id)
            #print u'not cached: {} -> >>{}<<'.format(cache_key, cached)
            #sys.stdout.write('-')
            cache.set(cache_key, cached) # comment this for no caching
        else:
            #sys.stdout.write('+')
            #print u'CACHED: {} -> >>{}<<'.format(cache_key, cached)
            pass
        return cached
    
    def save(self, force_insert=False, force_update=False, using=None):
        '''
            Override the superclass method to trigger cache updating.
        '''
        super(SchemaModel, self).save(force_insert, force_update, using)
        cache_key = '{}_{}'.format(self.__schema_name__, self.id)
        #print u'deleting {}_{}'.format(self.__schema_name__, self.id)
        cache.delete(cache_key)


class SubclassableModel(SchemaModel):
    """
    Generic superclass for all models that want to allow getting a
    subclass instance from a superclass table, e.g. via ForeignKey
    or ManyToManyField.
    """
    def get_class_name(self):
        return self.__class__.__name__

    def as_subclass(self):
        # pylint: disable-msg=E1101
        subclasses = self.__class__.__subclasses__()
        for subclass in subclasses:
            subclass_name = subclass.__name__
            candidate_fieldname = subclass_name.lower()
            if hasattr(self, candidate_fieldname):
                childinstance = getattr(self, candidate_fieldname)
                return childinstance.as_subclass() # recursive
        return self

    def __unicode__(self):
        subclass = self.as_subclass()
        if type(subclass) != type(self):
            return subclass.__unicode__()
        else:
            return SchemaModel.__unicode__(self)
        return '{0} {1}'.format(self.__class__.__name__, self.id)
    class Meta:
        abstract = True


class InvisibleStringModel(SchemaModel):
    """
    For xs:string choices: a field whose relation name will not be rendered
    and has special im-/export functionality
    """
    __schema_name__ = 'STRINGMODEL'

    value = models.TextField()

    def __unicode__(self):
        if not self.value:
            return u''
        return self.value
