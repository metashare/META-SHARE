"""
The XSD schema analysis (parsing) part of the generator
"""


## LICENSE

## Copyright (c) 2003 Dave Kuhlman

## Permission is hereby granted, free of charge, to any person obtaining
## a copy of this software and associated documentation files (the
## "Software"), to deal in the Software without restriction, including
## without limitation the rights to use, copy, modify, merge, publish,
## distribute, sublicense, and/or sell copies of the Software, and to
## permit persons to whom the Software is furnished to do so, subject to
## the following conditions:

## The above copyright notice and this permission notice shall be
## included in all copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
## EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
## MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
## IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
## CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
## TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
## SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



#from __future__ import generators   # only needed for Python 2.2

from collections import OrderedDict

import sys
from xml.sax import handler, make_parser
import logging
import keyword
import codecs
import StringIO
import textwrap

# Default logger configuration
## logging.basicConfig(level=logging.DEBUG,
##                     format='%(asctime)s %(levelname)s %(message)s')

## import warnings
## warnings.warn('importing IPShellEmbed', UserWarning)
## from IPython.Shell import IPShellEmbed
## args = ''
## ipshell = IPShellEmbed(args,
##     banner = 'Dropping into IPython',
##     exit_msg = 'Leaving Interpreter, back to program.')

# Then use the following line where and when you want to drop into the
# IPython shell:
#    ipshell('<some message> -- Entering ipshell.\\nHit Ctrl-D to exit')


#
# Global variables etc.
#

#
# Do not modify the following VERSION comments.
# Used by updateversion.py.
##VERSION##
VERSION = '2.7a'
##VERSION##

ElementDict = OrderedDict()

NamespacesDict = OrderedDict()
Targetnamespace = ""
SchemaVersion = ""

NameTable = OrderedDict({
    'type': 'type_',
    'float': 'float_',
    'build': 'build_',
    })
for kw in keyword.kwlist:
    NameTable[kw] = '%sxx' % kw


AttributeGroups = OrderedDict()
ElementGroups = OrderedDict()
SubstitutionGroups = OrderedDict()
#
# SubstitutionGroups can also include simple types that are
#   not (defined) elements.  Keep a list of these simple types.
#   These are simple types defined at top level.
SimpleElementDict = OrderedDict()
SimpleTypeDict = OrderedDict()
XsdNameSpace = ''
CurrentNamespacePrefix = 'xs:'
AnyTypeIdentifier = '__ANY__'

SchemaToPythonTypeMap = OrderedDict()

def set_type_constants(nameSpace):
    global CurrentNamespacePrefix, \
        StringType, TokenType, \
        IntegerType, DecimalType, \
        PositiveIntegerType, NegativeIntegerType, \
        NonPositiveIntegerType, NonNegativeIntegerType, \
        BooleanType, FloatType, DoubleType, \
        ElementType, ComplexTypeType, GroupType, SequenceType, ChoiceType, \
        AttributeGroupType, AttributeType, SchemaType, \
        DateTimeType, DateType, \
        SimpleContentType, ComplexContentType, ExtensionType, \
        IDType, IDREFType, IDREFSType, IDTypes, \
        NameType, NCNameType, QNameType, NameTypes, \
        AnyAttributeType, SimpleTypeType, RestrictionType, \
        WhiteSpaceType, ListType, EnumerationType, UnionType, \
        AppInfoType, MaxLengthType, RelationType, \
        AnyType, \
        AnnotationType, DocumentationType, \
        OtherSimpleTypes
    CurrentNamespacePrefix = nameSpace
    AttributeGroupType = nameSpace + 'attributeGroup'
    AttributeType = nameSpace + 'attribute'
    BooleanType = nameSpace + 'boolean'
    ChoiceType = nameSpace + 'choice'
    SimpleContentType = nameSpace + 'simpleContent'
    ComplexContentType = nameSpace + 'complexContent'
    ComplexTypeType = nameSpace + 'complexType'
    GroupType = nameSpace + 'group'
    SimpleTypeType = nameSpace + 'simpleType'
    RestrictionType = nameSpace + 'restriction'
    WhiteSpaceType = nameSpace + 'whiteSpace'
    AnyAttributeType = nameSpace + 'anyAttribute'
    DateTimeType = nameSpace + 'dateTime'
    DateType = nameSpace + 'date'
    IntegerType = (nameSpace + 'integer',
        nameSpace + 'unsignedShort',
        nameSpace + 'unsignedLong',
        nameSpace + 'unsignedInt',
        nameSpace + 'unsignedByte',
        nameSpace + 'byte',
        nameSpace + 'short',
        nameSpace + 'long',
        nameSpace + 'int',
        )
    DecimalType = nameSpace + 'decimal'
    PositiveIntegerType = nameSpace + 'positiveInteger'
    NegativeIntegerType = nameSpace + 'negativeInteger'
    NonPositiveIntegerType = nameSpace + 'nonPositiveInteger'
    NonNegativeIntegerType = nameSpace + 'nonNegativeInteger'
    DoubleType = nameSpace + 'double'
    ElementType = nameSpace + 'element'
    ExtensionType = nameSpace + 'extension'
    FloatType = nameSpace + 'float'
    IDREFSType = nameSpace + 'IDREFS'
    IDREFType = nameSpace + 'IDREF'
    IDType = nameSpace + 'ID'
    IDTypes = (IDREFSType, IDREFType, IDType, )
    SchemaType = nameSpace + 'schema'
    SequenceType = nameSpace + 'sequence'
    StringType = (nameSpace + 'string',
        nameSpace + 'duration',
        nameSpace + 'anyURI',
        nameSpace + 'base64Binary',
        nameSpace + 'normalizedString',
        nameSpace + 'NMTOKEN',
        nameSpace + 'ID',
        nameSpace + 'Name',
        nameSpace + 'language',
        ### BK: special types to map to string for META
        'httpURI',
        'emailAddress',
        'myStringURI'
        )
    TokenType = nameSpace + 'token'
    NameType = nameSpace + 'Name'
    NCNameType = nameSpace + 'NCName'
    QNameType = nameSpace + 'QName'
    NameTypes = (NameType, NCNameType, QNameType, )
    ListType = nameSpace + 'list'
    EnumerationType = nameSpace + 'enumeration'
    UnionType = nameSpace + 'union'
    AnnotationType = nameSpace + 'annotation'
    DocumentationType = nameSpace + 'documentation'
    AppInfoType = nameSpace + 'appinfo'
    MaxLengthType = nameSpace + 'maxLength'
    RelationType = u'relation'
    AnyType = nameSpace + 'any'
    OtherSimpleTypes = (
        nameSpace + 'ENTITIES',
        nameSpace + 'ENTITY',
        nameSpace + 'ID',
        nameSpace + 'IDREF',
        nameSpace + 'IDREFS',
        nameSpace + 'NCName',
        nameSpace + 'NMTOKEN',
        nameSpace + 'NMTOKENS',
        nameSpace + 'NOTATION',
        nameSpace + 'Name',
        nameSpace + 'QName',
        nameSpace + 'anyURI',
        nameSpace + 'base64Binary',
        nameSpace + 'boolean',
        nameSpace + 'byte',
        nameSpace + 'date',
        nameSpace + 'dateTime',
        nameSpace + 'decimal',
        nameSpace + 'double',
        nameSpace + 'duration',
        nameSpace + 'float',
        nameSpace + 'gDay',
        nameSpace + 'gMonth',
        nameSpace + 'gMonthDay',
        nameSpace + 'gYear',
        nameSpace + 'gYearMonth',
        nameSpace + 'hexBinary',
        nameSpace + 'int',
        nameSpace + 'integer',
        nameSpace + 'language',
        nameSpace + 'long',
        nameSpace + 'negativeInteger',
        nameSpace + 'nonNegativeInteger',
        nameSpace + 'nonPositiveInteger',
        nameSpace + 'normalizedString',
        nameSpace + 'positiveInteger',
        nameSpace + 'short',
        nameSpace + 'string',
        nameSpace + 'time',
        nameSpace + 'token',
        nameSpace + 'unsignedByte',
        nameSpace + 'unsignedInt',
        nameSpace + 'unsignedLong',
        nameSpace + 'unsignedShort',
        nameSpace + 'anySimpleType',
    )

    global SchemaToPythonTypeMap
    SchemaToPythonTypeMap = {
        BooleanType : 'bool',
        DecimalType : 'float',
        DoubleType : 'float',
        FloatType : 'float',
        NegativeIntegerType : 'int',
        NonNegativeIntegerType : 'int',
        NonPositiveIntegerType : 'int',
        PositiveIntegerType : 'int',
    }
    SchemaToPythonTypeMap.update(dict((x, 'int') for x in IntegerType))


def is_builtin_simple_type(type_val):
    if type_val in StringType or \
        type_val == TokenType or \
        type_val == DateTimeType or \
        type_val == DateType or \
        type_val in IntegerType or \
        type_val == DecimalType or \
        type_val == PositiveIntegerType or \
        type_val == NonPositiveIntegerType or \
        type_val == NegativeIntegerType or \
        type_val == NonNegativeIntegerType or \
        type_val == BooleanType or \
        type_val == FloatType or \
        type_val == DoubleType or \
        type_val in OtherSimpleTypes:
        return True
    else:
        return False
    
    
def cleanupName(oldName):
    newName = oldName.replace(':', '_')
    newName = newName.replace('-', '_')
    newName = newName.replace('.', '_')
    return newName


def mapName(oldName):
    global NameTable
    newName = oldName
    if NameTable:
        if oldName in NameTable:
            newName = NameTable[oldName]
    return newName


def strip_namespace(val):
    return val.split(':')[-1]

def showLevel(outfile, level):
    for idx in range(level):
        outfile.write('    ')

#
# For debugging.
#
def pplist(lst):
    for count, item in enumerate(lst):
        print '%d. %s' % (count, item)


    #ipshell('debug')
##     root.show(sys.stdout, 0)
##     print '=' * 50
##     response = raw_input('Press Enter')
##     root.show(sys.stdout, 0)
##     print '=' * 50
##     print ']]] root: ', root, '[[['

#
# Representation of element definition.
#


# Function that gets called recursively in order to expand nested references
# to element groups
def _expandGR(grp, visited):
    # visited is used for loop detection
    children = []
    changed = False
    for child in grp.children:
        groupRef = child.getElementGroup()
        if not groupRef:
            children.append(child)
            continue
        ref = groupRef.ref
        referencedGroup = ElementGroups.get(ref, None)
        if referencedGroup is None:
            ref = strip_namespace(ref)
            referencedGroup = ElementGroups.get(ref, None)
        if referencedGroup is None:
            #err_msg('*** Reference to unknown group %s' % groupRef.attrs['ref'])
            err_msg('*** Reference to unknown group %s\n' % groupRef.ref)
            continue
        if not id(grp) in visited:
            visited.appen(id(grp))
        if id(referencedGroup) in visited:
            #err_msg('*** Circular reference for %s' % groupRef.attrs['ref'])
            err_msg('*** Circular reference for %s\n' % groupRef.ref)
            continue
        changed = True
        _expandGR(referencedGroup, visited)
        children.extend(referencedGroup.children)
    if changed:
        # Avoid replacing the list with a copy of the list
        grp.children = children

def expandGroupReferences(grp):
    visited = []
    _expandGR(grp, visited)



class XschemaElementBase:
    def __init__(self):
        self.restrictionMaxLength = -1

    def getRestrictionMaxLength(self): return self.restrictionMaxLength
    def setRestrictionMaxLength(self, mxLen): self.restrictionMaxLength = mxLen


class SimpleTypeElement(XschemaElementBase):
    def __init__(self, name):
        XschemaElementBase.__init__(self)
        self.name = name
        self.base = None
        self.collapseWhiteSpace = 0
        # Attribute definitions for the current attributeGroup, if there is one.
        self.attributeGroup = None
        # Attribute definitions for the currect element.
        self.attributeDefs = OrderedDict()
        self.complexType = 0
        # Enumeration values for the current element.
        self.values = list()
        # The other simple types this is a union of.
        self.unionOf = list()
        self.simpleType = 0
        self.listType = 0
        self.documentation = ''
        
        # cfedermann: added appinfo for simple types to support v0 schema.
        self.appinfo = OrderedDict()
        
    def setName(self, name): self.name = name
    def getName(self): return self.name
    def setBase(self, base): self.base = base
    def getBase(self): return self.base
    def setSimpleType(self, simpleType): self.simpleType = simpleType
    def getSimpleType(self): return self.simpleType
    def getAttributeGroups(self): return self.attributeGroups
    def setAttributeGroup(self, attributeGroup): self.attributeGroup = attributeGroup
    def getAttributeGroup(self): return self.attributeGroup
    def setListType(self, listType): self.listType = listType
    def isListType(self): return self.listType
    def __str__(self):
        s1 = '<"%s" SimpleTypeElement instance at 0x%x>' % \
            (self.getName(), id(self))
        return s1

    def __repr__(self):
        s1 = '<"%s" SimpleTypeElement instance at 0x%x>' % \
            (self.getName(), id(self))
        return s1

    def resolve_list_type(self):
        if self.isListType():
            return 1
        elif self.getBase() in SimpleTypeDict:
            base = SimpleTypeDict[self.getBase()]
            return base.resolve_list_type()
        else:
            return 0
    
    # cfedermann: added appinfo for simple types to support v0 schema.
    def addAppInfo(self, name, value):
        if name in self.appinfo:
            self.appinfo[name] = self.appinfo[name] + value
        else:
            self.appinfo[name] = value


class XschemaElement(XschemaElementBase):
    def __init__(self, attrs):
        XschemaElementBase.__init__(self)
        self.cleanName = ''
        self.attrs = dict(attrs)
        name_val = ''
        type_val = ''
        ref_val = ''
        if 'name' in self.attrs:
            name_val = strip_namespace(self.attrs['name'])
        if 'type' in self.attrs:
            if (len(XsdNameSpace) > 0 and
                self.attrs['type'].startswith(XsdNameSpace)):
                type_val = self.attrs['type']
            else:
                type_val = strip_namespace(self.attrs['type'])
        if 'ref' in self.attrs:
            ref_val = strip_namespace(self.attrs['ref'])
        if type_val and not name_val:
            name_val = type_val
        if ref_val and not name_val:
            name_val = ref_val
        if ref_val and not type_val:
            type_val = ref_val
        if name_val:
            self.attrs['name'] = name_val
        if type_val:
            self.attrs['type'] = type_val
        if ref_val:
            self.attrs['ref'] = ref_val
        # fix_abstract
        abstract_type = attrs.get('abstract', 'false').lower()
        self.abstract_type = abstract_type in ('1', 'true')
        self.default = self.attrs.get('default')
        self.name = name_val
        self.children = []
        self.optional = False
        self.minOccurs = 1
        self.maxOccurs = 1
        self.complex = 0
        self.complexType = 0
        self.type = 'NoneType'
        self.mixed = 0
        self.base = None
        self.mixedExtensionError = 0
        self.collapseWhiteSpace = 0
        # Attribute definitions for the currect element.
        self.attributeDefs = OrderedDict()
        # Attribute definitions for the current attributeGroup, if there is one.
        self.attributeGroup = None
        # List of names of attributes for this element.
        # We will add the attribute defintions in each of these groups
        #   to this element in annotate().
        self.attributeGroupNameList = []
        # similar things as above, for groups of elements
        self.elementGroup = None
        self.appinfo = OrderedDict()
        self.topLevel = 0
        # Does this element contain an anyAttribute?
        self.anyAttribute = 0
        self.explicit_define = 0
        self.simpleType = None
        # Enumeration values for the current element.
        self.values = list()
        # The parent choice for the current element.
        self.choice = None
        self.listType = 0
        self.simpleBase = []
        self.documentation = ''
        self.restrictionBase = None
        self.simpleContent = False
        self.extended = False

    def addChild(self, element):
        self.children.append(element)
    def getChildren(self): return self.children
    def getName(self): return self.name
    def getCleanName(self): return self.cleanName
    def getUnmappedCleanName(self): return self.unmappedCleanName
    def setName(self, name): self.name = name
    def getAttrs(self): return self.attrs
    def setAttrs(self, attrs): self.attrs = attrs
    def getMinOccurs(self): return self.minOccurs
    def getMaxOccurs(self): return self.maxOccurs
    def getOptional(self): return self.optional
    def getRawType(self): return self.type
    def setExplicitDefine(self, explicit_define):
        self.explicit_define = explicit_define
    def isExplicitDefine(self): return self.explicit_define
    def isAbstract(self): return self.abstract_type
    def setListType(self, listType): self.listType = listType
    def isListType(self): return self.listType
    def getType(self):
        returnType = self.type
        if ElementDict.has_key(self.type):
            typeObj = ElementDict[self.type]
            typeObjType = typeObj.getRawType()
            if is_builtin_simple_type(typeObjType):
                returnType = typeObjType
        return returnType
    def isComplex(self): return self.complex
    def addAttributeDefs(self, attrs): self.attributeDefs.append(attrs)
    def getAttributeDefs(self): return self.attributeDefs
    def isMixed(self): return self.mixed
    def setMixed(self, mixed): self.mixed = mixed
    def setBase(self, base): self.base = base
    def getBase(self): return self.base
    def getMixedExtensionError(self): return self.mixedExtensionError
    def getAttributeGroups(self): return self.attributeGroups
    def addAttribute(self, name, attribute):
        self.attributeGroups[name] = attribute
    def setAttributeGroup(self, attributeGroup): self.attributeGroup = attributeGroup
    def getAttributeGroup(self): return self.attributeGroup
    def setElementGroup(self, elementGroup): self.elementGroup = elementGroup
    def getElementGroup(self): return self.elementGroup
    def addAppInfo(self, name, value):
        if name in self.appinfo:
            self.appinfo[name] = self.appinfo[name] + value
        else:
            self.appinfo[name] = value
    def getAppInfo(self, name): 
        if self.appinfo:
            return self.appinfo.get(name)
        return None
    def setTopLevel(self, topLevel): self.topLevel = topLevel
    def getTopLevel(self): return self.topLevel
    def setAnyAttribute(self, anyAttribute): self.anyAttribute = anyAttribute
    def getAnyAttribute(self): return self.anyAttribute
    def setSimpleType(self, simpleType): self.simpleType = simpleType
    def getSimpleType(self): return self.simpleType
    def setDefault(self, default): self.default = default
    def getDefault(self): return self.default
    def getSimpleBase(self): return self.simpleBase
    def setSimpleBase(self, simpleBase): self.simpleBase = simpleBase
    def addSimpleBase(self, simpleBase): self.simpleBase.append(simpleBase)
    def getRestrictionBase(self): return self.restrictionBase
    def setRestrictionBase(self, base): self.restrictionBase = base
    def getRestrictionBaseObj(self):
        rBaseObj = None
        rBaseName = self.getRestrictionBase()
        if rBaseName and rBaseName in ElementDict:
            rBaseObj = ElementDict[rBaseName]
        return rBaseObj
    def setSimpleContent(self, simpleContent):
        self.simpleContent = simpleContent
    def getSimpleContent(self):
        return self.simpleContent
    def getExtended(self): return self.extended
    def setExtended(self, extended): self.extended = extended
    def setValues(self, values): self.values = values
    def getValues(self): return self.values

    def getHelpText(self):
        if self.documentation :
            s2 = ' '.join(self.documentation.strip().split())
            s2 = s2.encode('utf-8')
            if s2[0] == '"' or s2[-1] == '"':
                s2 = '\' %s \'' % (s2, )
            else:
                s2 = '\'%s\'' % (s2, )
            return s2
        else:
            return ""

    def getDocumentation(self):
        if self.documentation :
            s2 = ' '.join(self.documentation.strip().split())
            s2 = s2.encode('utf-8')
            s2 = textwrap.fill(s2, width=68, subsequent_indent='    ')
            s2 = '    """\n    %s\n    """\n' % (s2, )
            return s2
        else:
            return ""

    def show(self, out, level):
        outfile = codecs.getwriter("UTF-8")(out)
        if self.name == 'Reference' or True: # what's Reference?
            showLevel(outfile, level)
            outfile.write('Name: %s  Type: %s  id: %d\n' % (self.name,
                self.getType(), id(self),))
            showLevel(outfile, level)
            outfile.write('  - Complex: %d  MaxOccurs: %d  MinOccurs: %d\n' % \
                (self.complex, self.maxOccurs, self.minOccurs))
            showLevel(outfile, level)
            outfile.write('  - Attrs: %s\n' % self.attrs)
            showLevel(outfile, level)
            #outfile.write('  - AttributeDefs: %s\n' % self.attributeDefs)
            if self.getAttributeDefs():
                outfile.write('  - AttributeDefs:\n')
                for key, value in self.getAttributeDefs().items():
                    showLevel(outfile, level + 1)
                    outfile.write('- key: %s  value: %s\n' % (key, value, ))
            if self.choice:
                showLevel(outfile, level)
                outfile.write('  - choice: %s\n' % self.choice)
            if self.documentation:
                showLevel(outfile, level)
                outfile.write('  - documentation: %s\n' % self.documentation)
            if self.appinfo:
                showLevel(outfile, level)
                outfile.write('  - AppInfos: %s\n' % self.appinfo)
            if self.values:
                showLevel(outfile, level)
                outfile.write('  - values:')
                for value in self.values:
                    try:
                        outfile.write(' %s' % value)
                    except:
                        f = codecs.open('###wrongval###', encoding='utf-8', mode='w+')
                        f.write(value)
                        f.close()
                    outfile.write('\n');
        for child in self.children:
            child.show(outfile, level + 1)

    def annotate(self):
        # resolve group references within groups
        for grp in ElementGroups.values():
            expandGroupReferences(grp)
        # Recursively expand group references
        visited = []
        self.expandGroupReferences_tree(visited)
        self.collect_element_dict()
        self.annotate_find_type()
        self.annotate_tree()
        self.fix_dup_names()
        self.coerce_attr_types()
        self.checkMixedBases()
        self.markExtendedTypes()

    def markExtendedTypes(self):
        base = self.getBase()
        if base and base in ElementDict:
            parent = ElementDict[base]
            parent.setExtended(True)
        for child in self.children:
            child.markExtendedTypes()

    def expandGroupReferences_tree(self, visited):
        if self.getName() in visited:
            return
        visited.append(self.getName())
        expandGroupReferences(self)
        for child in self.children:
            child.expandGroupReferences_tree(visited)

    def collect_element_dict(self):
        base = self.getBase()
        if self.getTopLevel() or len(self.getChildren()) > 0 or \
            len(self.getAttributeDefs()) > 0 or base:
            ElementDict[self.name] = self
        for child in self.children:
            child.collect_element_dict()

    def build_element_dict(self, elements):
        base = self.getBase()
        if self.getTopLevel() or len(self.getChildren()) > 0 or \
            len(self.getAttributeDefs()) > 0 or base:
            if self.name not in elements:
                elements[self.name] = self
        for child in self.children:
            child.build_element_dict(elements)

    def get_element(self, element_name):
        if self.element_dict is None:
            self.element_dict = dict()
            self.build_element_dict(self.element_dict)
        return self.element_dict.get(element_name)

    # If it is a mixed-content element and it is defined as
    #   an extension, then all of its bases (base, base of base, ...)
    #   must be mixed-content.  Mark it as an error, if not.
    def checkMixedBases(self):
        self.rationalizeMixedBases()
        self.collectSimpleBases()
        self.checkMixedBasesChain(self, self.mixed)
        for child in self.children:
            child.checkMixedBases()

    def collectSimpleBases(self):
        if self.base:
            self.addSimpleBase(self.base.encode('utf-8'))
        if self.simpleBase:
            base1 = SimpleTypeDict.get(self.simpleBase[0])
            if base1:
                base2 = base1.base or None
            else:
                base2 = None
            while base2:
                self.addSimpleBase(base2.encode('utf-8'))
                base2 = SimpleTypeDict.get(base2)
                if base2:
                    base2 = base2.getBase()

    def rationalizeMixedBases(self):
        mixed = self.hasMixedInChain()
        if mixed:
            self.equalizeMixedBases()

    def hasMixedInChain(self):
        if self.isMixed():
            return True
        base = self.getBase()
        if base and base in ElementDict:
            parent = ElementDict[base]
            return parent.hasMixedInChain()
        else:
            return False

    def equalizeMixedBases(self):
        if not self.isMixed():
            self.setMixed(True)
        base = self.getBase()
        if base and base in ElementDict:
            parent = ElementDict[base]
            parent.equalizeMixedBases()

    def checkMixedBasesChain(self, child, childMixed):
        base = self.getBase()
        if base and base in ElementDict:
            parent = ElementDict[base]
            if childMixed != parent.isMixed():
                self.mixedExtensionError = 1
                return
            parent.checkMixedBasesChain(child, childMixed)

    def resolve_type(self):
        self.complex = 0
        # If it has any attributes, then it's complex.
        attrDefs = self.getAttributeDefs()
        if len(attrDefs) > 0:
            self.complex = 1
            # type_val = ''
        type_val = self.resolve_type_1()
        if type_val == AnyType:
            return AnyType
        if type_val in SimpleTypeDict:
            self.addSimpleBase(type_val.encode('utf-8'))
            simple_type = SimpleTypeDict[type_val]
            list_type = simple_type.resolve_list_type()
            self.setListType(list_type)
        if type_val:
            if type_val in ElementDict:
                type_val1 = type_val
                # The following loop handles the case where an Element's
                # reference element has no sub-elements and whose type is
                # another simpleType (potentially of the same name). Its
                # fundamental function is to avoid the incorrect
                # categorization of "complex" to Elements which are not and
                # correctly resolve the Element's type as well as its
                # potential values. It also handles cases where the Element's
                # "simpleType" is so-called "top level" and is only available
                # through the global SimpleTypeDict.
                i = 0
                while True:
                    element = ElementDict[type_val1]
                    # Resolve our potential values if present
                    self.values = element.values
                    # If the type is available in the SimpleTypeDict, we
                    # know we've gone far enough in the Element hierarchy
                    # and can return the correct base type.
                    t = element.resolve_type_1()
                    if t in SimpleTypeDict:
                        _simple_type = SimpleTypeDict[t]
                        type_val1 = _simple_type.getBase()
                        if type_val1 and not is_builtin_simple_type(type_val1):
                            type_val1 = strip_namespace(type_val1)
                        # Resolve our potential maxLength restriction if present
                        self.setRestrictionMaxLength(
                            _simple_type.getRestrictionMaxLength())
                        break
                    # If the type name is the same as the previous type name
                    # then we know we've fully resolved the Element hierarchy
                    # and the Element is well and truely "complex". There is
                    # also a need to handle cases where the Element name and
                    # its type name are the same (ie. this is our first time
                    # through the loop). For example:
                    #   <xsd:element name="ReallyCool" type="ReallyCool"/>
                    #   <xsd:simpleType name="ReallyCool">
                    #     <xsd:restriction base="xsd:string">
                    #       <xsd:enumeration value="MyThing"/>
                    #     </xsd:restriction>
                    #   </xsd:simpleType>
                    if t == type_val1 and i != 0:
                        break
                    # If the type is not in the ElementDict, then `element` may
                    # have been resolved previously already (?) and we can
                    # inherit properties like the maxLength restriction
                    if t not in ElementDict:
                        type_val1 = t
                        # inherit a maxLength restriction if present
                        self.setRestrictionMaxLength(
                            element.getRestrictionMaxLength())
                        break
                    type_val1 = t
                    i += 1
                if is_builtin_simple_type(type_val1):
                    type_val = type_val1
                else:
                    self.complex = 1
            elif type_val in SimpleTypeDict:
                count = 0
                type_val1 = type_val
                while True:
                    element = SimpleTypeDict[type_val1]
                    type_val1 = element.getBase()
                    # inherit a maxLength restriction if present
                    self.setRestrictionMaxLength(
                        element.getRestrictionMaxLength())
                    if type_val1 and not is_builtin_simple_type(type_val1):
                        type_val1 = strip_namespace(type_val1)
                    if type_val1 is None:
                        # Something seems wrong.  Can't find base simple type.
                        #   Give up and use default.
                        type_val = StringType[0]
                        break
                    if type_val1 in SimpleTypeDict:
                        count += 1
                        if count > 10:
                            # Give up.  We're in a loop.  Use default.
                            type_val = StringType[0]
                            break
                    else:
                        type_val = type_val1
                        break
            else:
                if is_builtin_simple_type(type_val):
                    pass
                else:
                    type_val = StringType[0]
        else:
            type_val = StringType[0]
        return type_val

    def resolve_type_1(self):
        type_val = ''
        if 'type' in self.attrs:
            type_val = self.attrs['type']
            if type_val in SimpleTypeDict:
                self.simpleType = type_val
        elif 'ref' in self.attrs:
            type_val = strip_namespace(self.attrs['ref'])
        elif 'name' in self.attrs:
            type_val = strip_namespace(self.attrs['name'])
            #type_val = self.attrs['name']
        return type_val

    def annotate_find_type(self):
        if self.type == AnyTypeIdentifier:
            pass
        else:
            type_val = self.resolve_type()
            self.attrs['type'] = type_val
            self.type = type_val
        if not self.complex:
            SimpleElementDict[self.name] = self
        for child in self.children:
            child.annotate_find_type()

    def annotate_tree(self):
        # If there is a namespace, replace it with an underscore.
        if self.base:
            self.base = strip_namespace(self.base)
        self.unmappedCleanName = cleanupName(self.name)
        self.cleanName = mapName(self.unmappedCleanName)
        self.replace_attributeGroup_names()
        # Resolve "maxOccurs" attribute
        if 'maxOccurs' in self.attrs.keys():
            maxOccurs = self.attrs['maxOccurs']
        elif self.choice and 'maxOccurs' in self.choice.attrs.keys():
            maxOccurs = self.choice.attrs['maxOccurs']
        else:
            maxOccurs = 1
        # Resolve "minOccurs" attribute
        if 'minOccurs' in self.attrs.keys():
            minOccurs = self.attrs['minOccurs']
        elif self.choice and 'minOccurs' in self.choice.attrs.keys():
            minOccurs = self.choice.attrs['minOccurs']
        else:
            minOccurs = 1
        
        # cfedermann: allows to turn all choices optional.  See issue #197:
        # - https://github.com/metashare/META-SHARE-Software/issues/197
        if ForceOptionalChoices and self.choice:
            logging.warn('Forcing choice element {} to be optional!'.format(
              self.name))
            minOccurs = 0
        
        # Cleanup "minOccurs" and "maxOccurs" attributes
        try:
            minOccurs = int(minOccurs)
            if minOccurs == 0:
                self.optional = True
        except ValueError:
            err_msg('*** %s  minOccurs must be integer.\n' % self.getName())
            sys.exit(1)
        try:
            if maxOccurs == 'unbounded':
                maxOccurs = 99999
            else:
                maxOccurs = int(maxOccurs)
        except ValueError:
            err_msg('*** %s  maxOccurs must be integer or "unbounded".\n' % (
                self.getName(), ))
            sys.exit(1)
        self.minOccurs = minOccurs
        self.maxOccurs = maxOccurs

        # If it does not have a type, then make the type the same as the name.
        if self.type == 'NoneType' and self.name:
            self.type = self.name
        # Is it a mixed-content element definition?
        if 'mixed' in self.attrs.keys():
            mixed = self.attrs['mixed'].strip()
            if mixed == '1' or mixed.lower() == 'true':
                self.mixed = 1
        # If this element has a base and the base is a simple type and
        #   the simple type is collapseWhiteSpace, then mark this
        #   element as collapseWhiteSpace.
        base = self.getBase()
        if base and base in SimpleTypeDict:
            parent = SimpleTypeDict[base]
            if isinstance(parent, SimpleTypeElement) and \
                parent.collapseWhiteSpace:
                self.collapseWhiteSpace = 1
        # Do it recursively for all descendents.
        for child in self.children:
            child.annotate_tree()

    #
    # For each name in the attributeGroupNameList for this element,
    #   add the attributes defined for that name in the global
    #   attributeGroup dictionary.
    def replace_attributeGroup_names(self):
        for groupName in self.attributeGroupNameList:
            key = None
            if AttributeGroups.has_key(groupName):
                key =groupName
            else:
                # Looking for name space prefix
                keyList = groupName.split(':')
                if len(keyList) > 1:
                    key1 = keyList[1]
                    if AttributeGroups.has_key(key1):
                        key = key1
            if key is not None:
                attrGroup = AttributeGroups[key]
                for name in attrGroup.getKeys():
                    attr = attrGroup.get(name)
                    self.attributeDefs[name] = attr
            else:
                err_msg('*** Error. attributeGroup %s not defined.\n' % (
                    groupName, ))

    def __str__(self):
        s1 = '<XschemaElement name: "%s" type: "%s">' % \
            (self.getName(), self.getType(), )
        return s1
    __repr__ = __str__

    def fix_dup_names(self):
        # Patch-up names that are used for both a child element and an attribute.
        #
        attrDefs = self.getAttributeDefs()
        # Collect a list of child element names.
        #   Must do this for base (extension) elements also.
        elementNames = []
        self.collectElementNames(elementNames, 0)
        replaced = []
        # Create the needed new attributes.
        keys = attrDefs.keys()
        for key in keys:
            attr = attrDefs[key]
            name = attr.getName()
            if name in elementNames:
                newName = name + '_attr'
                newAttr = XschemaAttribute(newName)
                attrDefs[newName] = newAttr
                replaced.append(name)
        # Remove the old (replaced) attributes.
        for name in replaced:
            del attrDefs[name]
        for child in self.children:
            child.fix_dup_names()

    def collectElementNames(self, elementNames, count):
        for child in self.children:
            elementNames.append(cleanupName(child.cleanName))
        base = self.getBase()
        if base and base in ElementDict:
            parent = ElementDict[base]
            count += 1
            if count > 100:
                msg = ('Extension/restriction recursion detected.  ' +
                      'Suggest you check definitions of types ' +
                      '%s and %s.'
                      )
                msg = msg % (self.getName(), parent.getName(), )
                raise RuntimeError(msg)
            parent.collectElementNames(elementNames, count)

    def coerce_attr_types(self):
        replacements = []
        attrDefs = self.getAttributeDefs()
        for idx, name in enumerate(attrDefs):
            attr = attrDefs[name]
            attrType = attr.getData_type()
            if attrType == IDType or \
                attrType == IDREFType or \
                attrType == IDREFSType:
                attr.setData_type(StringType[0])
        for child in self.children:
            child.coerce_attr_types()
# end class XschemaElement

class XschemaAttributeGroup:
    def __init__(self, name='', group=None):
        self.name = name
        if group:
            self.group = group
        else:
            self.group = OrderedDict()
    def setName(self, name): self.name = name
    def getName(self): return self.name
    def setGroup(self, group): self.group = group
    def getGroup(self): return self.group
    def get(self, name, default=None):
        if self.group.has_key(name):
            return self.group[name]
        else:
            return default
    def getKeys(self):
        return self.group.keys()
    def add(self, name, attr):
        self.group[name] = attr
    def delete(self, name):
        if self.group.has_key(name):
            del self.group[name]
            return 1
        else:
            return 0
# end class XschemaAttributeGroup

class XschemaGroup:
    def __init__(self, ref):
        self.ref = ref
# end class XschemaGroup

class XschemaAttribute:
    def __init__(self, name, data_type='xs:string', use='optional', default=None):
        self.name = name
        self.data_type = data_type
        self.use = use
        self.default = default
        # Enumeration values for the attribute.
        self.values = list()
    def setName(self, name): self.name = name
    def getName(self): return self.name
    def setData_type(self, data_type): self.data_type = data_type
    def getData_type(self): return self.data_type
    def getType(self):
        returnType = self.data_type
        if SimpleElementDict.has_key(self.data_type):
            typeObj = SimpleElementDict[self.data_type]
            typeObjType = typeObj.getRawType()
            if typeObjType in StringType or \
                typeObjType == TokenType or \
                typeObjType == DateTimeType or \
                typeObjType == DateType or \
                typeObjType in IntegerType or \
                typeObjType == DecimalType or \
                typeObjType == PositiveIntegerType or \
                typeObjType == NegativeIntegerType or \
                typeObjType == NonPositiveIntegerType or \
                typeObjType == NonNegativeIntegerType or \
                typeObjType == BooleanType or \
                typeObjType == FloatType or \
                typeObjType == DoubleType:
                returnType = typeObjType
        return returnType
    def setUse(self, use): self.use = use
    def getUse(self): return self.use
    def setDefault(self, default): self.default = default
    def getDefault(self): return self.default
    def setValues(self, values): self.values = values
    def getValues(self): return self.values
# end class XschemaAttribute


#
# SAX handler
#
class XschemaHandler(handler.ContentHandler):
    def __init__(self):
        handler.ContentHandler.__init__(self)
        self.stack = []
        self.root = None
        self.inElement = 0
        self.inComplexType = 0
        self.inNonanonymousComplexType = 0
        self.inSequence = 0
        self.inChoice = 1
        self.inAttribute = 0
        self.inAttributeGroup = 0
        self.inSimpleType = 0
        self.inSimpleContent = 0
        self.inRestrictionType = 0
        self.inAnnotationType = 0
        self.inDocumentationType = 0
        self.inAppInfoType = 0
        self.appInfoTag = ''
        # The last attribute we processed.
        self.lastAttribute = None
        # Simple types that exist in the global context and may be used to
        # qualify the type of many elements and/or attributes.
        self.topLevelSimpleTypes = list()
        # The current choice type we're in
        self.currentChoice = None
        self.firstElement = True

    def getRoot(self):
        return self.root

    def extractSchemaNamespace(self, attrs):
        schemaUri = 'http://www.w3.org/2001/XMLSchema'
        keys = [ x for x, v in attrs.items() if v == schemaUri ]
        if not keys:
            return None
        keys = [ x[6:] for x in keys if x.startswith('xmlns:') ]
        if not keys:
            return None
        return keys[0]

    def startElement(self, name, attrs):
        global Targetnamespace, SchemaVersion, NamespacesDict, XsdNameSpace
        logging.debug("Start element: %s %s" % (name, repr(attrs.items())))
        if len(self.stack) == 0 and self.firstElement:
            self.firstElement = False
            schemaNamespace = self.extractSchemaNamespace(attrs)
            if schemaNamespace:
                XsdNameSpace = schemaNamespace
                set_type_constants(schemaNamespace + ':')
            else:
                if len(name.split(':')) == 1:
                    XsdNameSpace = ''
                    set_type_constants('')
        if name == SchemaType:
            self.inSchema = 1
            element = XschemaElement(attrs)
            if len(self.stack) == 1:
                element.setTopLevel(1)
            self.stack.append(element)
            # If there is an attribute "xmlns" and its value is
            #   "http://www.w3.org/2001/XMLSchema", then remember and
            #   use that namespace prefix.
            for name, value in attrs.items():
                if name[:6] == 'xmlns:':
                    nameSpace = name[6:] + ':'
                    NamespacesDict[value] = nameSpace
                elif name == 'targetNamespace':
                    Targetnamespace = value
                elif name == 'version':
                    SchemaVersion = value
        elif (name == ElementType or
            ((name == ComplexTypeType) and (len(self.stack) == 1))
            ):
            self.inElement = 1
            self.inNonanonymousComplexType = 1
            element = XschemaElement(attrs)
            if not 'type' in attrs.keys() and not 'ref' in attrs.keys():
                element.setExplicitDefine(1)
            if len(self.stack) == 1:
                element.setTopLevel(1)
            if 'substitutionGroup' in attrs.keys() and 'name' in attrs.keys():
                substituteName = attrs['name']
                headName = attrs['substitutionGroup']
                if headName not in SubstitutionGroups:
                    SubstitutionGroups[headName] = []
                SubstitutionGroups[headName].append(substituteName)
            if name == ComplexTypeType:
                element.complexType = 1
            if self.inChoice and self.currentChoice:
                element.choice = self.currentChoice
            self.stack.append(element)
        elif name == ComplexTypeType:
            # If it have any attributes and there is something on the stack,
            #   then copy the attributes to the item on top of the stack.
            if len(self.stack) > 1 and len(attrs) > 0:
                parentDict = self.stack[-1].getAttrs()
                for key in attrs.keys():
                    parentDict[key] = attrs[key]
            self.inComplexType = 1
        elif name == AnyType:
            element = XschemaElement(attrs)
            element.type = AnyTypeIdentifier
            self.stack.append(element)
        elif name == GroupType:
            element = XschemaElement(attrs)
            if len(self.stack) == 1:
                element.setTopLevel(1)
            self.stack.append(element)
        elif name == SequenceType:
            self.inSequence = 1
        elif name == ChoiceType:
            self.currentChoice = XschemaElement(attrs)
            self.inChoice = 1
        elif name == AttributeType:
            self.inAttribute = 1
            if 'name' in attrs.keys():
                name = attrs['name']
            elif 'ref' in attrs.keys():
                name = strip_namespace(attrs['ref'])
            else:
                name = 'no_attribute_name'
            if 'type' in attrs.keys():
                data_type = attrs['type']
            else:
                data_type = StringType[0]
            if 'use' in attrs.keys():
                use = attrs['use']
            else:
                use = 'optional'
            if 'default' in attrs.keys():
                default = attrs['default']
            else:
                default = None
            if self.stack[-1].attributeGroup:
                # Add this attribute to a current attributeGroup.
                attribute = XschemaAttribute(name, data_type, use, default)
                self.stack[-1].attributeGroup.add(name, attribute)
            else:
                # Add this attribute to the element/complexType.
                attribute = XschemaAttribute(name, data_type, use, default)
                self.stack[-1].attributeDefs[name] = attribute
            self.lastAttribute = attribute
        elif name == AttributeGroupType:
            self.inAttributeGroup = 1
            # If it has attribute 'name', then it's a definition.
            #   Prepare to save it as an attributeGroup.
            if 'name' in attrs.keys():
                name = strip_namespace(attrs['name'])
                attributeGroup = XschemaAttributeGroup(name)
                element = XschemaElement(attrs)
                if len(self.stack) == 1:
                    element.setTopLevel(1)
                element.setAttributeGroup(attributeGroup)
                self.stack.append(element)
            # If it has attribute 'ref', add it to the list of
            #   attributeGroups for this element/complexType.
            if 'ref' in attrs.keys():
                self.stack[-1].attributeGroupNameList.append(attrs['ref'])
        elif name == SimpleContentType:
            self.inSimpleContent = 1
            if len(self.stack) > 0:
                self.stack[-1].setSimpleContent(True)
        elif name == ComplexContentType:
            pass
        elif name == ExtensionType:
            if 'base' in attrs.keys() and len(self.stack) > 0:
                extensionBase = attrs['base']
                if extensionBase in StringType or \
                    extensionBase in IDTypes or \
                    extensionBase in NameTypes or \
                    extensionBase == TokenType or \
                    extensionBase == DateTimeType or \
                    extensionBase == DateType or \
                    extensionBase in IntegerType or \
                    extensionBase == DecimalType or \
                    extensionBase == PositiveIntegerType or \
                    extensionBase == NegativeIntegerType or \
                    extensionBase == NonPositiveIntegerType or \
                    extensionBase == NonNegativeIntegerType or \
                    extensionBase == BooleanType or \
                    extensionBase == FloatType or \
                    extensionBase == DoubleType or \
                    extensionBase in OtherSimpleTypes:
                    if (len(self.stack) > 0 and
                        isinstance(self.stack[-1], XschemaElement)):
                        self.stack[-1].addSimpleBase(extensionBase.encode('utf-8'))
                else:
                    self.stack[-1].setBase(extensionBase)
        elif name == AnyAttributeType:
            # Mark the current element as containing anyAttribute.
            self.stack[-1].setAnyAttribute(1)
        elif name == SimpleTypeType:
            # fixlist
            if self.inAttribute:
                pass
            elif self.inSimpleType and self.inRestrictionType:
                pass
            else:
                # Save the name of the simpleType, but ignore everything
                #   else about it (for now).
                if 'name' in attrs.keys():
                    stName = cleanupName(attrs['name'])
                elif len(self.stack) > 0:
                    stName = cleanupName(self.stack[-1].getName())
                else:
                    stName = None
                # If the parent is an element, mark it as a simpleType.
                if len(self.stack) > 0:
                    self.stack[-1].setSimpleType(1)
                element = SimpleTypeElement(stName)
                SimpleTypeDict[stName] = element
                self.stack.append(element)
            self.inSimpleType = 1
        elif name == RestrictionType:
            if self.inAttribute:
                if attrs.has_key('base'):
                    self.lastAttribute.setData_type(attrs['base'])
            else:
                # If we are in a simpleType, capture the name of
                #   the restriction base.
                if ((self.inSimpleType or self.inSimpleContent) and
                    'base' in attrs.keys()):
                    self.stack[-1].setBase(attrs['base'])
                else:
                    if 'base' in attrs.keys():
                        self.stack[-1].setRestrictionBase(attrs['base'])
            self.inRestrictionType = 1
        elif name == EnumerationType:
            if self.inAttribute and attrs.has_key('value'):
                # We know that the restriction is on an attribute and the
                # attributes of the current element are un-ordered so the
                # instance variable "lastAttribute" will have our attribute.
                self.lastAttribute.values.append(attrs['value'])
            elif self.inElement and attrs.has_key('value'):
                # We're not in an attribute so the restriction must have
                # been placed on an element and that element will still be
                # in the stack. We search backwards through the stack to
                # find the last element.
                element = None
                if self.stack:
                    for entry in reversed(self.stack):
                        if isinstance(entry, XschemaElement):
                            element = entry
                            break
                if element is None:
                    err_msg('Cannot find element to attach enumeration: %s\n' % (
                            attrs['value']), )
                    sys.exit(1)
                element.values.append(attrs['value'])
            elif self.inSimpleType and attrs.has_key('value'):
                # We've been defined as a simpleType on our own.
                self.stack[-1].values.append(attrs['value'])
        elif name == UnionType:
            # Union types are only used with a parent simpleType and we want
            # the parent to know what it's a union of.
            parentelement = self.stack[-1]
            if (isinstance(parentelement, SimpleTypeElement) and
                attrs.has_key('memberTypes')):
                for member in attrs['memberTypes'].split(" "):
                    self.stack[-1].unionOf.append(member)
        elif name == WhiteSpaceType and self.inRestrictionType:
            if attrs.has_key('value'):
                if attrs.getValue('value') == 'collapse':
                    self.stack[-1].collapseWhiteSpace = 1
        elif name == ListType:
            self.inListType = 1
            # fixlist
            if self.inSimpleType: # and self.inRestrictionType:
                self.stack[-1].setListType(1)
            if self.inSimpleType:
                if attrs.has_key('itemType'):
                    self.stack[-1].setBase(attrs['itemType'])
        elif name == AnnotationType:
            self.inAnnotationType = 1
        elif name == DocumentationType:
            if self.inAnnotationType:
                self.inDocumentationType = 1
        elif name == AppInfoType:
            if self.inAnnotationType:
                self.inAppInfoType = 1
        elif self.inAppInfoType:
            self.appInfoTag = name
        elif name == MaxLengthType:
            # currently we only handle "maxLength" elements in restrictions
            if self.inRestrictionType and attrs.has_key('value'):
                self.stack[-1].setRestrictionMaxLength(attrs.getValue('value'))
        logging.debug("Start element stack: %d" % len(self.stack))

    def endElement(self, name):
        logging.debug("End element: %s" % (name))
        logging.debug("End element stack: %d" % (len(self.stack)))
        if name == SimpleTypeType: # and self.inSimpleType:
            self.inSimpleType = 0
            if self.inAttribute:
                pass
            else:
                # If the simpleType is directly off the root, it may be used to
                # qualify the type of many elements and/or attributes so we
                # don't want to loose it entirely.
                simpleType = self.stack.pop()
                # fixlist
                if len(self.stack) == 1:
                    self.topLevelSimpleTypes.append(simpleType)
                    self.stack[-1].setListType(simpleType.isListType())
        elif name == RestrictionType and self.inRestrictionType:
            self.inRestrictionType = 0
        elif name == ElementType or (name == ComplexTypeType and self.stack[-1].complexType):
            self.inElement = 0
            self.inNonanonymousComplexType = 0
            if len(self.stack) >= 2:
                element = self.stack.pop()
                self.stack[-1].addChild(element)
        elif name == AnyType:
            if len(self.stack) >= 2:
                element = self.stack.pop()
                self.stack[-1].addChild(element)
        elif name == ComplexTypeType:
            self.inComplexType = 0
        elif name == SequenceType:
            self.inSequence = 0
        elif name == ChoiceType:
            self.currentChoice = None
            self.inChoice = 0
        elif name == AttributeType:
            self.inAttribute = 0
        elif name == AttributeGroupType:
            self.inAttributeGroup = 0
            if self.stack[-1].attributeGroup:
                # The top of the stack contains an XschemaElement which
                #   contains the definition of an attributeGroup.
                #   Save this attributeGroup in the
                #   global AttributeGroup dictionary.
                attributeGroup = self.stack[-1].attributeGroup
                name = attributeGroup.getName()
                AttributeGroups[name] = attributeGroup
                self.stack[-1].attributeGroup = None
                self.stack.pop()
            else:
                # This is a reference to an attributeGroup.
                # We have already added it to the list of attributeGroup names.
                # Leave it.  We'll fill it in during annotate.
                pass
        elif name == GroupType:
            element = self.stack.pop()
            name = element.getAttrs()['name']
            elementGroup = XschemaGroup(element.name)
            ref = element.getAttrs().get('ref')
            if len(self.stack) == 1 and ref is None:
                # This is the definition
                ElementGroups[name] = element
            elif len(self.stack) > 1 and ref is not None:
                # This is a reference. Add it to the parent's children. We
                # need to preserve the order of elements.
                element.setElementGroup(elementGroup)
                self.stack[-1].addChild(element)
        elif name == SchemaType:
            self.inSchema = 0
            if len(self.stack) != 1:
                # fixlist
                err_msg('*** error stack.  len(self.stack): %d\n' % (
                    len(self.stack), ))
                sys.exit(1)
            if self.root: #change made to avoide logging error
                logging.debug("Previous root: %s" % (self.root.name))
            else:
                logging.debug ("Prvious root:   None")
            self.root = self.stack[0]
            if self.root:
                logging.debug("New root: %s"  % (self.root.name))
            else:
                logging.debug("New root: None")
        elif name == SimpleContentType:
            self.inSimpleContent = 0
        elif name == ComplexContentType:
            pass
        elif name == ExtensionType:
            pass
        elif name == ListType:
            # List types are only used with a parent simpleType and can have a
            # simpleType child. So, if we're in a list type we have to be
            # careful to reset the inSimpleType flag otherwise the handler's
            # internal stack will not be unrolled correctly.
            self.inSimpleType = 1
            self.inListType = 0
        elif name == AnnotationType:
            self.inAnnotationType = 0
        elif name == DocumentationType:
            if self.inAnnotationType:
                self.inDocumentationType = 0
        elif name == AppInfoType:
            if self.inAnnotationType:
                self.inAppInfoType = 0
        elif self.inAppInfoType:
            if name != self.appInfoTag:
                logging.debug("%s wrongly closes %s"  % (self.appInfoTag, name))
            else:
                self.appInfoTag = ''    
            
    def characters(self, chrs):
        # Careful! If the cases are not exclusive, one can hide the other!
        if self.inDocumentationType:
            # If there is an annotation/documentation element, save it.
            if len(self.stack) > 1 and len(chrs) > 0:
                self.stack[-1].documentation += chrs
        elif self.inAppInfoType and self.appInfoTag:
            self.stack[-1].addAppInfo(self.appInfoTag, chrs)
        elif self.inElement:
            pass
        elif self.inComplexType:
            pass
        elif self.inSequence:
            pass
        elif self.inChoice:
            pass

def err_msg(msg):
    sys.stderr.write(msg)

def load_config():
    try:
        #print '1. updating NameTable'
        import generateds_config
        NameTable.update(generateds_config.NameTable)
        #print '2. updating NameTable'
    except ImportError, exp:
        pass

def parse_schema(xschemaFileName, processIncludes, force_optional_choices):
    global ForceOptionalChoices
    ForceOptionalChoices = force_optional_choices
    parser = make_parser()
    dh = XschemaHandler()
##    parser.setDocumentHandler(dh)
    parser.setContentHandler(dh)
    if xschemaFileName == '-':
        infile = sys.stdin
    else:
        infile = open(xschemaFileName, 'r')
    if processIncludes:
        import process_includes
        outfile = StringIO.StringIO()
        process_includes.process_include_files(infile, outfile,
            inpath=xschemaFileName)
        outfile.seek(0)
        infile = outfile
    parser.parse(infile)
    root = dh.getRoot()
    root.annotate()
    return root
