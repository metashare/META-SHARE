
import sys
from generateds_definedsimpletypes import Defined_simple_type_table


#
# Globals


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

#MODELS_SUPERCLASS="models.Model"
MODELS_SUPERCLASS="SchemaModel"

CHOICES_TEMPLATE = """
      max_length={0}['max_length'],
      choices={0}['choices'],
      """

#
# Classes

class GeneratedsSuper(object):
    def gds_format_string(self, input_data, input_name=''):
        return input_data
    def gds_format_integer(self, input_data, input_name=''):
        return '%d' % input_data
    def gds_format_float(self, input_data, input_name=''):
        return '%f' % input_data
    def gds_format_double(self, input_data, input_name=''):
        return '%e' % input_data
    def gds_format_boolean(self, input_data, input_name=''):
        return '%s' % input_data
    def gds_str_lower(self, instring):
        return instring.lower()

    @classmethod
    def get_prefix_name(cls, tag):
        prefix = ''
        name = ''
        items = tag.split(':')
        if len(items) == 2:
            prefix = items[0]
            name = items[1]
        elif len(items) == 1:
            name = items[0]
        return prefix, name


    """ This method will generate all the anonymous choice types,
        as well as compute the __schema_XXX__ fields of Christian
    """
    @classmethod
    def generate_embedded_types_(cls, not_generated):
        class_name = cls.__name__
        schema_fields = list()
        schema_classes = dict()
        embedded_enums = list()
        multi_id = 0
        for spec in cls.member_data_items_:
            name = spec.get_name()
            prefix, name = cls.get_prefix_name(name)
            data_type = spec.get_data_type()
            prefix, data_type = cls.get_prefix_name(data_type)
            if data_type in Defined_simple_type_table:
                data_type = Defined_simple_type_table[data_type]
                prefix, data_type = cls.get_prefix_name(data_type.type_name)
            name = cleanupName(name)
            if name == 'id':
                name += 'x'
            elif name.endswith('_'):
                name += 'x'
            schema_fields.append( (name, name) )
            data_type = cleanupName(data_type)
            if data_type in Simple_type_table:
                if data_type in Integer_type_table:
                    pass
                elif data_type in Float_type_table:
                    pass
                elif data_type in Date_type_table:
                    pass
                elif data_type in DateTime_type_table:
                    pass
                elif data_type in Boolean_type_table:
                    pass
                elif data_type in String_type_table:
                    if isinstance(spec.get_data_type_chain(), list) and \
                      spec.get_values():
                        embedded_enums.append('\n{}_{}_CHOICES = _make_choices_from_list({!r})\n' \
                          .format(class_name, name.upper(), spec.get_values()))
                    
                    if spec.get_container() == 0:
                        # Simple Text Field
                        pass
                    else:
                        # MultiTextField
                        multi_id = multi_id + 1
                else:
                    sys.stderr.write('Unhandled simple type: %s %s\n' % (
                        name, data_type, ))
            else:
                if data_type in not_generated:
                    # this type must be postponed
                    return None
                schema_classes[name] = data_type
                if spec.get_container() == 0:
                    # ForeignKey
                    pass
                else:
                    # ManyToManyField
                    pass
        return (schema_fields, schema_classes, embedded_enums)

    """
    Generate a model for the given class cls
    
    schema_data is a pair of schema_fields and schema_classes
    """
    @classmethod
    def generate_model_(cls, wrtmodels, wrtforms, schema_data):
        class_name = cls.__name__
        wrtmodels('\nclass {}_model({}):\n'.format(class_name, MODELS_SUPERCLASS))
        wrtforms('\nclass %s_form(forms.Form):\n' % (class_name, ))
        
        wrtmodels("\n    __schema_name__ = '{}'\n".format(class_name))
        if schema_data[0]: 
            wrtmodels('    __schema_fields__ = (\n')
            for pair in schema_data[0]:
                wrtmodels('      {!r},\n'.format(pair))
            wrtmodels('    )\n')
        if schema_data[1]: 
            wrtmodels("    __schema_classes__ = {\n")
            for key, value in schema_data[1].items():
                wrtmodels('      {!r}:{}_model,\n'.format(key, value))
            wrtmodels('    }\n')
        wrtmodels('\n')
        
        if cls.superclass is not None:
            wrtmodels('    %s = models.ForeignKey("%s_model")\n' % (
                cls.superclass.__name__, cls.superclass.__name__, ))
        multi_id = 0
        for spec in cls.member_data_items_:
            name = spec.get_name()
            prefix, name = cls.get_prefix_name(name)
            data_type = spec.get_data_type()
            prefix, data_type = cls.get_prefix_name(data_type)
            if data_type in Defined_simple_type_table:
                data_type = Defined_simple_type_table[data_type]
                prefix, data_type = cls.get_prefix_name(data_type.type_name)
            name = cleanupName(name)
            if name == 'id':
                name += 'x'
            elif name.endswith('_'):
                name += 'x'
            data_type = cleanupName(data_type)
            if data_type in Simple_type_table:
                if spec.get_required() == 0:
                    options = 'blank=True'
                else:
                    options = 'blank=False'
                if data_type in Integer_type_table:
                    wrtmodels('    %s = models.IntegerField(%s)\n' % (
                        name, options, ))
                    wrtforms('    %s = forms.IntegerField(%s)\n' % (
                        name, options, ))
                elif data_type in Float_type_table:
                    wrtmodels('    %s = models.FloatField(%s)\n' % (
                        name, options, ))
                    wrtforms('    %s = forms.FloatField(%s)\n' % (
                        name, options, ))
                elif data_type in Date_type_table:
                    wrtmodels('    %s = models.DateField(%s)\n' % (
                        name, options, ))
                    wrtforms('    %s = forms.DateField(%s)\n' % (
                        name, options, ))
                elif data_type in DateTime_type_table:
                    wrtmodels('    %s = models.DateTimeField(%s)\n' % (
                        name, options, ))
                    wrtforms('    %s = forms.DateTimeField(%s)\n' % (
                        name, options, ))
                elif data_type in Boolean_type_table:
                    wrtmodels('    %s = models.BooleanField(%s)\n' % (
                        name, options, ))
                    wrtforms('    %s = forms.BooleanField(%s)\n' % (
                        name, options, ))
                elif data_type in String_type_table:
                    if isinstance(spec.get_data_type_chain(), list) and \
                      spec.get_values():
                        choice_name = '{}_{}_CHOICES' \
                          .format(class_name, name.upper(), spec.get_values())
                        choice_options = CHOICES_TEMPLATE.format(choice_name)
                    else:
                        choice_options = "max_length=1000, "
                        
                    if spec.get_container() == 0:
                        wrtmodels(
                            '    %s = models.CharField(%s%s)\n' % (
                                name, choice_options, options, ))
                        wrtforms(
                            '    %s = forms.CharField(%s%s)\n' % (
                                name, choice_options, options, ))
                    else:
                        wrtmodels(
                            '    %s = MultiTextField(%swidget = MultiFieldWidget(widget_id=%d), %s)\n' % (
                                name, choice_options, multi_id, options, ))
                        wrtforms(
                            '    %s = forms.CharField(%s%s)### FIX_ME: MULTITEXT %d\n' % (
                                name, choice_options, options, multi_id, ))
                        multi_id = multi_id + 1
                else:
                    sys.stderr.write('Unhandled simple type: %s %s\n' % (
                        name, data_type, ))
            else:
                related_name = ''
                if data_type == 'myString':
                    # the s after %(class) is important, _ gives errors
                    related_name=', related_name="%(class)s_{}_{}_model"'.format(name, data_type)
                    #related_name=', related_name="{}_{}_{}_model"'.format(class_name, name, data_type)
                if spec.get_container() == 0:
                    wrtmodels(
                        '    %s = models.ForeignKey("%s_model"%s)\n' % (
                            name, data_type, related_name, ))
                    wrtforms(
                        '    %s = forms.MultipleChoiceField(%s_model.objects.all())\n' % (
                            name, data_type, ))
                else:
                    wrtmodels(
                        '    %s = models.ManyToManyField("%s_model"%s)\n' % (
                            name, data_type, related_name, ))
                    wrtforms(
                        '    %s = forms.MultipleChoiceField(%s_model.objects.all())### FIX_ME: ManyToMany\n' % (
                            name, data_type, ))

        wrtmodels('    def __unicode__(self):\n')
        wrtmodels('        return "id: %s" % (self.id, )\n')


#
# Local functions

def cleanupName(oldName):
    newName = oldName.replace(':', '_')
    newName = newName.replace('-', '_')
    newName = newName.replace('.', '_')
    return newName


