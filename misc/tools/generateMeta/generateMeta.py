#!/usr/bin/env python
"""
Synopsis:
    Generate Python classes from XML Schema definition.
    Input is read from in_xsd_file or, if "-" (dash) arg, from stdin.
    Output is written to files named in "-o" and "-s" options.
Usage:
    python generateDS.py [ options ] <xsd_file>
    python generateDS.py [ options ] -
Options:
    -h, --help               Display this help information.
    -o <outfilename>         Output file name for data representation classes
    -p <prefix>              Prefix string to be pre-pended to the class names
    -a <namespaceabbrev>     Namespace abbreviation, e.g. "xsd:".
                             Default = 'xs:'.
    -m                       Generate properties for member variables
    --root-element="XXX"     Assume XXX is root element of instance docs.
                             Default is first element defined in schema.
                             Also see section "Recognizing the top level
                             element" in the documentation.
    --no-dates               Do not include the current date in the generated
                             files. This is useful if you want to minimize
                             the amount of (no-operation) changes to the
                             generated python code.
    --no-versions            Do not include the current version in the generated
                             files. This is useful if you want to minimize
                             the amount of (no-operation) changes to the
                             generated python code.
    --no-process-includes    Do not process included XML Schema files.  By
                             default, generateDS.py will insert content
                             from files referenced by <include ... />
                             elements into the XML Schema to be processed.
    --namespacedef='xmlns:abc="http://www.abc.com"'
                             Namespace definition to be passed in as the
                             value for the namespacedef_ parameter of
                             the export() method by the generated
                             parse() and parseString() functions.
                             Default=''.
    --external-encoding=<encoding>
                             Encode output written by the generated export
                             methods using this encoding.  Default, if omitted,
                             is the value returned by sys.getdefaultencoding().
                             Example: --external-encoding='utf-8'.
    --member-specs=list|dict
                             Generate member (type) specifications in each
                             class: a dictionary of instances of class
                             MemberSpec_ containing member name, type,
                             and array or not.  Allowed values are
                             "list" or "dict".  Default: do not generate.
    -q, --no-questions       Do not ask questios, for example,
                             force overwrite.
    --version                Print version and exit.
    --make-choices-optional  Turn all xs:choice elements optional.

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

import sys
import os.path
import time
import getopt
import logging

from parse_xsd import mapName, cleanupName, ElementDict, SimpleTypeDict, \
  set_type_constants, load_config, XsdNameSpace, parse_schema

from clazzbase import Clazz, ClazzAttributeMember, ClazzMember


# Magic setting of PYTHONPATH, to simplify use on multiple platforms:
# Magic python path, based on http://djangosnippets.org/snippets/281/
from os.path import abspath, dirname, join
thisdir = dirname(abspath(__file__))
# Rootdir is three levels up
rootdir = dirname(dirname(dirname(thisdir)))
# Insert our dependencies:
sys.path.insert(0, join(rootdir, 'lib', 'python2.7', 'site-packages'))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, thisdir)






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

GenerateProperties = 0
MemberSpecs = None
DelayedElements = []
AlreadyGenerated = []
PostponedExtensions = []

NoQuestions = False
Dirpath = []
ExternalEncoding = sys.getdefaultencoding()

def debug_show_root(root):
    print '-' * 60
    root.show(sys.stdout, 0)
    print '-' * 60
        
def debug_show_elements():
    #print 'ElementDict:', ElementDict
    print '=' * 60
    for name, obj in ElementDict.iteritems():
        print 'element:', name, obj.getName(), obj.type
    print '=' * 60
    
#
# Code generation
#

def getParentName(element):
    base = element.getBase()
    rBase = element.getRestrictionBaseObj()
    parentName = None
    parentObj = None
    if base and base in ElementDict:
        parentObj = ElementDict[base]
        parentName = cleanupName(parentObj.getName())
    elif rBase:
        base = element.getRestrictionBase()
        parentObj = ElementDict[base]
        parentName = cleanupName(parentObj.getName())
    return parentName, parentObj
# end getParentName

def get_clazz_name_from_element(element):
    name = cleanupName(element.getCleanName())
    return name #name[0].upper() + name[1:]

def createClazzMembers(clazz, element):
    for attrName, attrDef in element.getAttributeDefs().items():
        clazz.addMember(ClazzAttributeMember(clazz, attrName, attrDef))

    for child in element.getChildren():
        
        clazz.addMember(
          ClazzMember(clazz, get_clazz_name_from_element(child), child))

    simplebase = element.getSimpleBase()
    if element.getSimpleContent() or element.isMixed():
        if len(simplebase) == 1:
            simplebase = "%s" % (simplebase[0], )

        clazz.addMember(ClazzMember(clazz, 'valueOf_', simplebase))
    elif element.isMixed():
        clazz.addMember(ClazzMember(clazz, 'valueOf_', 'xs:string'))
# end createClazzMembers


def createClazz(prefix, element, processed):
    logging.debug("Generating class for: %s" % element)
    elementCleanName = get_clazz_name_from_element(element)
    processed.append(elementCleanName)
    if Clazz.ClazzDict.has_key(elementCleanName):
        return Clazz.ClazzDict[elementCleanName]
    
    parentName, base = getParentName(element)
    logging.debug("Element base: %s" % base)
    if not element.isExplicitDefine():
        logging.debug("Not an explicit define, returning.")
        return
    # If this element is an extension (has a base) and the base has
    #   not been generated, then postpone it.
    if parentName:
        if (parentName not in AlreadyGenerated and
            parentName not in SimpleTypeDict.keys()):
            PostponedExtensions.append(element)
            return
    elementName = element.getName()
    if elementName in AlreadyGenerated:
        return
    AlreadyGenerated.append(elementName)
    if element.getMixedExtensionError():
        err_msg('*** Element %s extension chain contains mixed and non-mixed content.  Not generated.\n' % (
            element.getName(), ))
        return
    new_clazz = Clazz(prefix, elementCleanName, parentName, element)
    # the access key form XSchemaElements to Clazzes is the
    # get_clazz_name_from_element(element)
    Clazz.ClazzDict[elementCleanName] = new_clazz
    
    createClazzMembers(new_clazz, element)
    
    parentName, parent = getParentName(element)
    superclass_name = 'None'
    if parentName and parentName in AlreadyGenerated:
        new_clazz.parentName = mapName(cleanupName(parentName))
# end createClazz


# Fool (and straighten out) the syntax highlighting.
# DUMMY = '''

def createFromTree(prefix, elements, processed):
    for element in elements:
        createClazz(prefix, element, processed)
        children = element.getChildren()
        if children:
            createFromTree(prefix, element.getChildren(), processed)


def createClazzes(prefix, root):
    global DelayedElements
    processed = []
    
    DelayedElements = []
    elements = root.getChildren()
    createFromTree(prefix, elements, processed)
    while 1:
        if len(DelayedElements) <= 0:
            break
        element = DelayedElements.pop()
        name = get_clazz_name_from_element(element)
        if name not in processed:
            processed.append(name)
            createClazz(prefix, element)
    #
    # Create the elements that were postponed because we had not
    #   yet created their base class.
    while 1:
        if len(PostponedExtensions) <= 0:
            break
        element = PostponedExtensions.pop()
        parentName, parent = getParentName(element)
        if parentName:
            if (parentName in AlreadyGenerated or
                parentName in SimpleTypeDict.keys()):
                createClazz(prefix, element)
            else:
                PostponedExtensions.insert(0, element)


#
# Functions
#

def parseAndGenerate(outfileName, prefix, xschemaFileName, processIncludes,
  package_prefix, force_optional_choices):
    root = parse_schema(xschemaFileName, processIncludes, force_optional_choices)
            
    Clazz.extract_descriptors(xschemaFileName)

    if DEBUG:
        debug_show_root(root)
    
    createClazzes(prefix, root)
    
    if DEBUG:
        for key, value in Clazz.ClazzDict.items():
            print 'clazzName: {}  elt: {}'.format(key, value.schema_element)
    
    Clazz.generate(prefix, root, package_prefix)


def err_msg(msg):
    sys.stderr.write(msg)


USAGE_TEXT = __doc__

def usage():
    print USAGE_TEXT
    sys.exit(1)


def main():
    global GenerateProperties, RootElement, \
        XsdNameSpace, \
        Namespacedef, NoDates, NoVersion, \
        Dirpath, \
        ExternalEncoding, MemberSpecs, NoQuestions, DEBUG

    args = sys.argv[1:]
    try:
        options, args = getopt.getopt(args, 'dhfyo:p:a:mu:q',
            ['help', 
            'root-element=',
            'no-process-includes',
            'namespacedef=', 'external-encoding=',
            'member-specs=', 'no-dates', 'no-versions',
            'no-questions',
            'version',
            'make-choices-optional',
            ])
    except getopt.GetoptError, exp:
        usage()
    prefix = ''
    outFilename = None
    nameSpace = 'xs:'
    processIncludes = 1
    namespacedef = ''
    ExternalEncoding = sys.getdefaultencoding()
    NoDates = False
    NoVersion = False
    NoQuestions = False
    showVersion = False
    xschemaFileName = None
    package_prefix = "metashare.repo2."
    DEBUG = False
    ForceOptionalChoices = False
    
    for option in options:
        if option[0] == '-h' or option[0] == '--help':
            usage()
        elif option[0] == '-d':
            DEBUG = True
        elif option[0] == '-p':
            prefix = option[1]
        elif option[0] == '-o':
            outFilename = option[1]
        elif option[0] == '-a':
            nameSpace = option[1]
        elif option[0] == '-m':
            GenerateProperties = 1
        elif option[0] == '--no-dates':
            NoDates = True
        elif option[0] == '--no-versions':
            NoVersion = True
        elif option[0] == '--root-element':
            RootElement = option[1]
        elif option[0] == '--no-process-includes':
            processIncludes = 0
        elif option[0] == "--namespacedef":
            namespacedef = option[1]
        elif option[0] == '--external-encoding':
            ExternalEncoding = option[1]
        elif option[0] in ('-q', '--no-questions'):
            NoQuestions = True
        elif option[0] == '--version':
            showVersion = True
        elif option[0] == '--make-choices-optional':
            ForceOptionalChoices = True
        elif option[0] == '--member-specs':
            MemberSpecs = option[1]
            if MemberSpecs not in ('list', ):
                raise RuntimeError('Option --member-specs must be "list".')
    if showVersion:
        print 'generateDS.py version %s' % VERSION
        sys.exit(0)
    XsdNameSpace = nameSpace
    Namespacedef = namespacedef
    set_type_constants(nameSpace)
    if DEBUG and False:
        logging.basicConfig(level=logging.DEBUG,)
    if xschemaFileName is None:
        if len(args) != 1:
            usage()
        else:
            xschemaFileName = args[0]
    load_config()
    parseAndGenerate(outFilename, prefix, xschemaFileName, processIncludes,
      package_prefix, ForceOptionalChoices)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()


