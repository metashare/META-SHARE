#!/usr/bin/env python

#
# Generated  by generateDS.py.
#

import sys

import extensions2_sup as supermod

etree_ = None
Verbose_import_ = False
(   XMLParser_import_none, XMLParser_import_lxml,
    XMLParser_import_elementtree
    ) = range(3)
XMLParser_import_library = None
try:
    # lxml
    from lxml import etree as etree_
    XMLParser_import_library = XMLParser_import_lxml
    if Verbose_import_:
        print("running with lxml.etree")
except ImportError:
    try:
        # cElementTree from Python 2.5+
        import xml.etree.cElementTree as etree_
        XMLParser_import_library = XMLParser_import_elementtree
        if Verbose_import_:
            print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
            # ElementTree from Python 2.5+
            import xml.etree.ElementTree as etree_
            XMLParser_import_library = XMLParser_import_elementtree
            if Verbose_import_:
                print("running with ElementTree on Python 2.5+")
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree_
                XMLParser_import_library = XMLParser_import_elementtree
                if Verbose_import_:
                    print("running with cElementTree")
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree_
                    XMLParser_import_library = XMLParser_import_elementtree
                    if Verbose_import_:
                        print("running with ElementTree")
                except ImportError:
                    raise ImportError("Failed to import ElementTree from any known place")

def parsexml_(*args, **kwargs):
    if (XMLParser_import_library == XMLParser_import_lxml and
        'parser' not in kwargs):
        # Use the lxml ElementTree compatible parser so that, e.g.,
        #   we ignore comments.
        kwargs['parser'] = etree_.ETCompatXMLParser()
    doc = etree_.parse(*args, **kwargs)
    return doc

#
# Globals
#

ExternalEncoding = 'ascii'

#
# Data representation classes
#

class SpecialDateSub(supermod.SpecialDate):
    def __init__(self, SpecialProperty=None, valueOf_=None):
        super(SpecialDateSub, self).__init__(SpecialProperty, valueOf_, )
supermod.SpecialDate.subclass = SpecialDateSub
# end class SpecialDateSub


class ExtremeDateSub(supermod.ExtremeDate):
    def __init__(self, ExtremeProperty=None, valueOf_=None):
        super(ExtremeDateSub, self).__init__(ExtremeProperty, valueOf_, )
supermod.ExtremeDate.subclass = ExtremeDateSub
# end class ExtremeDateSub


class singleExtremeDateSub(supermod.singleExtremeDate):
    def __init__(self, ExtremeProperty=None, valueOf_=None):
        super(singleExtremeDateSub, self).__init__(ExtremeProperty, valueOf_, )
supermod.singleExtremeDate.subclass = singleExtremeDateSub
# end class singleExtremeDateSub


class containerTypeSub(supermod.containerType):
    def __init__(self, simplefactoid=None, mixedfactoid=None):
        super(containerTypeSub, self).__init__(simplefactoid, mixedfactoid, )
supermod.containerType.subclass = containerTypeSub
# end class containerTypeSub


class simpleFactoidTypeSub(supermod.simpleFactoidType):
    def __init__(self, relation=None):
        super(simpleFactoidTypeSub, self).__init__(relation, )
supermod.simpleFactoidType.subclass = simpleFactoidTypeSub
# end class simpleFactoidTypeSub


class mixedFactoidTypeSub(supermod.mixedFactoidType):
    def __init__(self, relation=None, valueOf_=None, mixedclass_=None, content_=None):
        super(mixedFactoidTypeSub, self).__init__(relation, valueOf_, mixedclass_, content_, )
supermod.mixedFactoidType.subclass = mixedFactoidTypeSub
# end class mixedFactoidTypeSub


class BaseTypeSub(supermod.BaseType):
    def __init__(self, BaseProperty1=None, BaseProperty2=None, valueOf_=None, extensiontype_=None):
        super(BaseTypeSub, self).__init__(BaseProperty1, BaseProperty2, valueOf_, extensiontype_, )
supermod.BaseType.subclass = BaseTypeSub
# end class BaseTypeSub


class DerivedTypeSub(supermod.DerivedType):
    def __init__(self, BaseProperty1=None, BaseProperty2=None, DerivedProperty1=None, DerivedProperty2=None, valueOf_=None):
        super(DerivedTypeSub, self).__init__(BaseProperty1, BaseProperty2, DerivedProperty1, DerivedProperty2, valueOf_, )
supermod.DerivedType.subclass = DerivedTypeSub
# end class DerivedTypeSub


class MyIntegerSub(supermod.MyInteger):
    def __init__(self, MyAttr=None, valueOf_=None):
        super(MyIntegerSub, self).__init__(MyAttr, valueOf_, )
supermod.MyInteger.subclass = MyIntegerSub
# end class MyIntegerSub


class MyBooleanSub(supermod.MyBoolean):
    def __init__(self, MyAttr=None, valueOf_=None):
        super(MyBooleanSub, self).__init__(MyAttr, valueOf_, )
supermod.MyBoolean.subclass = MyBooleanSub
# end class MyBooleanSub


class MyFloatSub(supermod.MyFloat):
    def __init__(self, MyAttr=None, valueOf_=None):
        super(MyFloatSub, self).__init__(MyAttr, valueOf_, )
supermod.MyFloat.subclass = MyFloatSub
# end class MyFloatSub


class MyDoubleSub(supermod.MyDouble):
    def __init__(self, MyAttr=None, valueOf_=None):
        super(MyDoubleSub, self).__init__(MyAttr, valueOf_, )
supermod.MyDouble.subclass = MyDoubleSub
# end class MyDoubleSub



def get_root_tag(node):
    tag = supermod.Tag_pattern_.match(node.tag).groups()[-1]
    rootClass = None
    if hasattr(supermod, tag):
        rootClass = getattr(supermod, tag)
    return tag, rootClass


def parse(inFilename):
    doc = parsexml_(inFilename)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'container'
        rootClass = supermod.containerType
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('<?xml version="1.0" ?>\n')
##     rootObj.export(sys.stdout, 0, name_=rootTag,
##         namespacedef_='')
    doc = None
    return rootObj


def parseString(inString):
    from StringIO import StringIO
    doc = parsexml_(StringIO(inString))
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'container'
        rootClass = supermod.containerType
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('<?xml version="1.0" ?>\n')
##     rootObj.export(sys.stdout, 0, name_=rootTag,
##         namespacedef_='')
    return rootObj


def parseLiteral(inFilename):
    doc = parsexml_(inFilename)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'container'
        rootClass = supermod.containerType
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('#from extensions2_sup import *\n\n')
##     sys.stdout.write('import extensions2_sup as model_\n\n')
##     sys.stdout.write('rootObj = model_.container(\n')
##     rootObj.exportLiteral(sys.stdout, 0, name_="container")
##     sys.stdout.write(')\n')
    return rootObj


USAGE_TEXT = """
Usage: python ???.py <infilename>
"""

def usage():
    print USAGE_TEXT
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    root = parse(infilename)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()


