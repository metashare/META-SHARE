#!/usr/bin/env python

#
# Generated Tue Feb  1 14:34:02 2011 by generateDS.py version 2.5a.
#

import sys

import peoplesup as supermod

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

class peopleSub(supermod.people):
    def __init__(self, comments=None, person=None, specialperson=None, programmer=None, python_programmer=None, java_programmer=None):
        super(peopleSub, self).__init__(comments, person, specialperson, programmer, python_programmer, java_programmer, )
supermod.people.subclass = peopleSub
# end class peopleSub


class commentsSub(supermod.comments):
    def __init__(self, emp=None, bold=None, valueOf_=None, mixedclass_=None, content_=None):
        super(commentsSub, self).__init__(emp, bold, valueOf_, mixedclass_, content_, )
supermod.comments.subclass = commentsSub
# end class commentsSub


class personSub(supermod.person):
    def __init__(self, vegetable=None, fruit=None, ratio=None, id=None, value=None, name=None, interest=None, category=None, agent=None, promoter=None, description=None):
        super(personSub, self).__init__(vegetable, fruit, ratio, id, value, name, interest, category, agent, promoter, description, )
supermod.person.subclass = personSub
# end class personSub


class specialpersonSub(supermod.specialperson):
    def __init__(self, vegetable=None, fruit=None, ratio=None, id=None, value=None, name=None, interest=None, category=None, agent=None, promoter=None, description=None):
        super(specialpersonSub, self).__init__(vegetable, fruit, ratio, id, value, name, interest, category, agent, promoter, description, )
supermod.specialperson.subclass = specialpersonSub
# end class specialpersonSub


class programmerSub(supermod.programmer):
    def __init__(self, vegetable=None, fruit=None, ratio=None, id=None, value=None, name=None, interest=None, category=None, agent=None, promoter=None, description=None, language=None, area=None, attrnegint=None, attrposint=None, attrnonnegint=None, attrnonposint=None, email=None, elposint=None, elnonposint=None, elnegint=None, elnonnegint=None, eldate=None, eltoken=None, elshort=None, ellong=None, elparam=None, elarraytypes=None):
        super(programmerSub, self).__init__(vegetable, fruit, ratio, id, value, name, interest, category, agent, promoter, description, language, area, attrnegint, attrposint, attrnonnegint, attrnonposint, email, elposint, elnonposint, elnegint, elnonnegint, eldate, eltoken, elshort, ellong, elparam, elarraytypes, )
supermod.programmer.subclass = programmerSub
# end class programmerSub


class paramSub(supermod.param):
    def __init__(self, semantic=None, name=None, flow=None, sid=None, type_=None, id=None, valueOf_=None):
        super(paramSub, self).__init__(semantic, name, flow, sid, type_, id, valueOf_, )
supermod.param.subclass = paramSub
# end class paramSub


class python_programmerSub(supermod.python_programmer):
    def __init__(self, vegetable=None, fruit=None, ratio=None, id=None, value=None, name=None, interest=None, category=None, agent=None, promoter=None, description=None, language=None, area=None, attrnegint=None, attrposint=None, attrnonnegint=None, attrnonposint=None, email=None, elposint=None, elnonposint=None, elnegint=None, elnonnegint=None, eldate=None, eltoken=None, elshort=None, ellong=None, elparam=None, elarraytypes=None, nick_name=None, favorite_editor=None):
        super(python_programmerSub, self).__init__(vegetable, fruit, ratio, id, value, name, interest, category, agent, promoter, description, language, area, attrnegint, attrposint, attrnonnegint, attrnonposint, email, elposint, elnonposint, elnegint, elnonnegint, eldate, eltoken, elshort, ellong, elparam, elarraytypes, nick_name, favorite_editor, )
supermod.python_programmer.subclass = python_programmerSub
# end class python_programmerSub


class java_programmerSub(supermod.java_programmer):
    def __init__(self, vegetable=None, fruit=None, ratio=None, id=None, value=None, name=None, interest=None, category=None, agent=None, promoter=None, description=None, language=None, area=None, attrnegint=None, attrposint=None, attrnonnegint=None, attrnonposint=None, email=None, elposint=None, elnonposint=None, elnegint=None, elnonnegint=None, eldate=None, eltoken=None, elshort=None, ellong=None, elparam=None, elarraytypes=None, status=None, nick_name=None, favorite_editor=None):
        super(java_programmerSub, self).__init__(vegetable, fruit, ratio, id, value, name, interest, category, agent, promoter, description, language, area, attrnegint, attrposint, attrnonnegint, attrnonposint, email, elposint, elnonposint, elnegint, elnonnegint, eldate, eltoken, elshort, ellong, elparam, elarraytypes, status, nick_name, favorite_editor, )
supermod.java_programmer.subclass = java_programmerSub
# end class java_programmerSub


class agentSub(supermod.agent):
    def __init__(self, firstname=None, lastname=None, priority=None, info=None, vehicle=None):
        super(agentSub, self).__init__(firstname, lastname, priority, info, vehicle, )
supermod.agent.subclass = agentSub
# end class agentSub


class special_agentSub(supermod.special_agent):
    def __init__(self, firstname=None, lastname=None, priority=None, info=None):
        super(special_agentSub, self).__init__(firstname, lastname, priority, info, )
supermod.special_agent.subclass = special_agentSub
# end class special_agentSub


class boosterSub(supermod.booster):
    def __init__(self, member_id=None, firstname=None, lastname=None, other_name=None, classxx=None, other_value=None, type_=None, client_handler=None):
        super(boosterSub, self).__init__(member_id, firstname, lastname, other_name, classxx, other_value, type_, client_handler, )
supermod.booster.subclass = boosterSub
# end class boosterSub


class client_handlerSub(supermod.client_handler):
    def __init__(self, fullname=None, refid=None):
        super(client_handlerSub, self).__init__(fullname, refid, )
supermod.client_handler.subclass = client_handlerSub
# end class client_handlerSub


class infoSub(supermod.info):
    def __init__(self, rating=None, type_=None, name=None, valueOf_=None):
        super(infoSub, self).__init__(rating, type_, name, valueOf_, )
supermod.info.subclass = infoSub
# end class infoSub


class vehicleSub(supermod.vehicle):
    def __init__(self, wheelcount=None):
        super(vehicleSub, self).__init__(wheelcount, )
supermod.vehicle.subclass = vehicleSub
# end class vehicleSub


class automobileSub(supermod.automobile):
    def __init__(self, wheelcount=None, drivername=None):
        super(automobileSub, self).__init__(wheelcount, drivername, )
supermod.automobile.subclass = automobileSub
# end class automobileSub


class airplaneSub(supermod.airplane):
    def __init__(self, wheelcount=None, pilotname=None):
        super(airplaneSub, self).__init__(wheelcount, pilotname, )
supermod.airplane.subclass = airplaneSub
# end class airplaneSub



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
        rootTag = 'people'
        rootClass = supermod.people
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\n')
    rootObj.export(sys.stdout, 0, name_=rootTag,
        namespacedef_='xmlns:pl="http://kuhlman.com/people.xsd"')
    doc = None
    return rootObj


def parseString(inString):
    from StringIO import StringIO
    doc = parsexml_(StringIO(inString))
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'people'
        rootClass = supermod.people
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\n')
    rootObj.export(sys.stdout, 0, name_=rootTag,
        namespacedef_='xmlns:pl="http://kuhlman.com/people.xsd"')
    return rootObj


def parseLiteral(inFilename):
    doc = parsexml_(inFilename)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'people'
        rootClass = supermod.people
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('#from peoplesup import *\n\n')
    sys.stdout.write('import peoplesup as model_\n\n')
    sys.stdout.write('rootObj = model_.people(\n')
    rootObj.exportLiteral(sys.stdout, 0, name_="people")
    sys.stdout.write(')\n')
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


