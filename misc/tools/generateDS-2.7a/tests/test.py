#!/usr/bin/env python

import os
import sys
import subprocess
import getopt
import unittest


class GenTest(unittest.TestCase):
    def execute(self, cmd, cwd = None):
        p = subprocess.Popen(cmd, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True)
        stdout, stderr = p.communicate()
        return stdout, stderr

    def setUp(self):
        cmd = 'python generateDS.py --no-dates --no-versions -f -o tests/out2_sup.py -s tests/out2_sub.py --super=out2_sup -u gends_user_methods tests/people.xsd'
        stdout, stderr = self.execute(cmd, cwd='..')
        self.failUnlessEqual(len(stdout), 0)
        self.failUnlessEqual(len(stderr), 0)

##     def tearDown(self):
##         for f in [ "out2_sub.py", "out2_sup.py" ]:
##             try:
##                 os.unlink(f)
##             except OSError:
##                 pass

    def test_001_compare_superclasses(self):
        cmd = 'diff out1_sup.py out2_sup.py'
        result, err = self.execute(cmd)
        #print 'len(result):', len(result)
        # Ignore the differing lines containing the date/time.
        #self.failUnless(len(result) < 130 and result.find('Generated') > -1)
        self.check_result(result, err, ())

    def test_002_compare_subclasses(self):
        cmd = 'diff out1_sub.py out2_sub.py'
        result, err = self.execute(cmd)
        # Ignore the differing lines containing the date/time.
        #self.failUnless(len(result) < 130 and result.find('Generated') > -1)
        self.check_result(result, err, ())

    def test_003_element_groups(self):
        cmdTempl = 'python generateDS.py --no-dates --silence --member-specs=list -f -o tests/%s_sup.py -s tests/%s_sub.py --super=%s_sup tests/%s.xsd'
        t_ = 'groups'
        cmd = cmdTempl % (t_, t_, t_, t_)
        result, err = self.execute(cmd, cwd='..')
        # Verify the structure
        cmdTempl = '''python -c "import %s_sub; print [ x.name for x in %s_sub.node1TypeSub.member_data_items_ ]; print [ x.name for x in %s_sub.node2TypeSub.member_data_items_ ]"'''
        cmd = cmdTempl % (t_, t_, t_)
        result, err = self.execute(cmd)
        self.failUnlessEqual(result, """\
['node1node1', 'group1', 'group2', 'node1node2']
['node2node1', 'group1', 'group2', 'node2node2']
""")
        # load the XML, and verify the proper data was loaded
        cmdTempl = '''python -c "import %s_sub; obj = %s_sub.parse('%s.xml'); fields = [ x.name for x in obj.node1.member_data_items_ ]; print [ getattr(obj.node1, x) for x in fields ]; fields = [ x.name for x in obj.node2.member_data_items_ ]; print [ getattr(obj.node2, x) for x in fields ]"'''
        cmd = cmdTempl % (t_, t_, t_)
        result, err = self.execute(cmd)
        self.failUnlessEqual(result, """\
['value 1 1', 'group1 1', 'group2 1', 'value 1 2']
['value 2 1', 'group1 2', 'group2 2', 'value 2 2']
""")

    def test_004_valueof(self):
        cmdTempl = 'python generateDS.py --no-dates --silence --member-specs=list -f -o tests/%s_sup.py -s tests/%s_sub.py --super=%s_sup tests/%s.xsd'
        t_ = 'valueof'
        cmd = cmdTempl % (t_, t_, t_, t_)
        result, err = self.execute(cmd, cwd='..')
        # load the XML, and verify the proper data was loaded
        # Run these commands::
        #     import valueof_sub
        #     obj = valueof_sub.parse('valueof.xml')
        #     children = obj.get_child()
        #     print [ (x.get_name(), x.get_valueOf_()) for x in children ]
        #
        cmdTempl = '''python -c "import %s_sub; obj = %s_sub.parse('%s.xml'); children = obj.get_child(); print [ (x.get_name(), x.get_valueOf_()) for x in children ]"'''
        cmd = cmdTempl % (t_, t_, t_)
        result, err = self.execute(cmd)
        self.failUnlessEqual(result, """\
[('child1', 'value1'), ('child1', 'value2')]
""")
        # Now try to create a node, make sure the value of valueOf_ is passed
        # in
        # Run these commands::
        #     import valueof_sub
        #     node = valueof_sub.childTypeSub.factory(name='child1', valueOf_ = 'value1')
        #     print (node.get_name(), node.get_valueOf_())

        cmdTempl = '''python -c "import %s_sub; node = %s_sub.childTypeSub.factory(name='child1', valueOf_ = 'value1'); print (node.get_name(), node.get_valueOf_())"'''
        cmd = cmdTempl % (t_, t_)
        print 'cmd:', cmd
        result, err = self.execute(cmd)
        print 'result: %s' % result
        self.failUnlessEqual(result, """\
('child1', 'value1')
""")

    ns_for_import_xml1 = """\
<root xmlns="http://a" xmlns:bl="http://blah">
  <bl:sra>
    <childa1/>
  </bl:sra>
</root>
"""

    ns_for_import_xml2 = """\
<root xmlns="http://b" xmlns:bl="http://blah">
  <bl:srb1>
    <childb1/>
    <childb2/>
  </bl:srb1>
</root>
"""

    ns_for_import_xml_result = """\
<root xmlns="http://a" xmlns:bl="http://blah">
  <bl:sra>
    <childa1/>
  </bl:sra>
<bl:srb1 xmlns="http://b">
    <childb1/>
    <childb2/>
  </bl:srb1>
</root>
"""

    def test_005_ns_for_import(self):
        from lxml import etree
        root1 = etree.fromstring(GenTest.ns_for_import_xml1)
        root2 = etree.fromstring(GenTest.ns_for_import_xml2)
        for child in root2.getchildren():
            root1.append(child.__copy__())
        #print etree.tostring(root1, pretty_print = True)
        result = etree.tostring(root1, pretty_print = True)
        self.failUnlessEqual(GenTest.ns_for_import_xml_result, result)

    def test_006_anysimpletype(self):
        cmdTempl = 'python generateDS.py --no-dates --no-versions --silence --member-specs=list -f -o tests/%s2_sup.py -s tests/%s2_sub.py --super=%s2_sup tests/%s.xsd'
        t_ = 'anysimpletype'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, err = self.execute(cmd, cwd='..')
        cmd = 'diff anysimpletype1_sup.py anysimpletype2_sup.py'
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff anysimpletype1_sub.py anysimpletype2_sub.py'
        result, err = self.execute(cmd)
        self.check_result(result, err, ())

    def test_007_simpletype_memberspecs(self):
        cmdTempl = 'python generateDS.py --no-dates --no-versions --silence --member-specs=list -f -o tests/%s2_sup.py -s tests/%s2_sub.py --super=%s2_sup tests/%s.xsd'
        t_ = 'simpletype_memberspecs'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())

    def test_008_extensions(self):
        cmdTempl = 'python generateDS.py --no-dates --no-versions --silence --member-specs=list -f -o tests/%s2_sup.py -s tests/%s2_sub.py --super=%s2_sup tests/%s.xsd'
        t_ = 'extensions'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())

    def test_009_literal(self):
        import out2_sup
        save_stdout = sys.stdout
        sys.stdout = open('literal2.py', 'w')
        out2_sup.parseLiteral('people.xml')
        sys.stdout.close()
        sys.stdout = save_stdout
        infile = open('literal1.py', 'r')
        content1 = infile.read()
        infile.close()
        infile = open('literal2.py', 'r')
        content2 = infile.read()
        infile.close()
        self.failUnlessEqual(content1, content2)

    def test_010_extensions(self):
        cmdTempl = 'python generateDS.py --no-dates --no-versions --silence --member-specs=list -f -o tests/%s2_sup.py -s tests/%s2_sub.py --super=%s2_sup tests/%s.xsd'
        t_ = 'simplecontent_restriction'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())


    def test_011_annotations(self):
        cmdTempl = 'python generateDS.py --no-dates --no-versions --silence --member-specs=list -f -o tests/%s2_sup.py -s tests/%s2_sub.py --super=%s2_sup tests/%s.xsd'
        t_ = 'annotations'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())


    def test_012_abstracttype(self):
        cmdTempl = 'python generateDS.py --no-dates --no-versions --silence --member-specs=list -f -o tests/%s2_sup.py -s tests/%s2_sub.py --super=%s2_sup tests/%s.xsd'
        t_ = 'abstract_type'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())


    def test_013_procincl(self):
        cmdTempl = ('python generateDS.py --no-dates --no-versions '
            '--silence --member-specs=list -f '
            '-o tests/%s2_sup.py -s tests/%s2_sub.py '
            '--super=%s2_sup '
            'tests/%s.xsd'
            )
        t_ = 'people_procincl'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())


    def test_014_xsi_type(self):
        cmdTempl = 'python generateDS.py --no-dates --no-versions --member-specs=list -f -o tests/%s2_sup.py -s tests/%s2_sub.py --super=%s2_sup tests/%s.xsd'
        t_ = 'ipo'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())
        cmdTempl = 'python tests/%s2_sup.py tests/ipo.xml > tests/%s2_out.xml'
        cmd = cmdTempl % (t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_out.xml %s2_out.xml' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())


    def test_015_recursive_simpletype(self):
        cmdTempl = ('python generateDS.py --no-dates --no-versions '
            '--silence --member-specs=list -f '
            '-o tests/%s2_sup.py -s tests/%s2_sub.py '
            '--super=%s2_sup '
            'tests/%s.xsd'
            )
        t_ = 'recursive_simpletype'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())


    def test_016_anywildcard(self):
        cmdTempl = ('python generateDS.py --no-dates --no-versions '
            '--silence --member-specs=list -f '
            '-o tests/%s2_sup.py -s tests/%s2_sub.py '
            '--super=%s2_sup '
            'tests/%s.xsd'
            )
        t_ = 'anywildcard'
        cmd = cmdTempl % (t_, t_, t_, t_, )
        result, _ = self.execute(cmd, cwd='..')
        cmd = 'diff %s1_sup.py %s2_sup.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ('sys.stdout.write',))
        cmd = 'diff %s1_sub.py %s2_sub.py' % (t_, t_, )
        result, err = self.execute(cmd)
        self.check_result(result, err, ())


    def check_result(self, result, err, ignore_strings):
        self.failUnlessEqual(len(result), 0)
        self.failUnlessEqual(len(err), 0)
        return True
##         if len(err) > 0:
##             return False
##         lines = result.split('\n')
##         len1 = len(lines)
##         if len1 > 5:
##             return False
##         elif len1 > 1 and len1 <= 5:
##             s1 = '\n'.join(lines[:4])
##             found = False
##             for s2 in ignore_strings:
##                 if s1.find(s2) > -1:
##                     found = True
##                     break
##             if not found:
##                 return False
##         return True


# Make the test suite.
def suite():
    # The following is obsolete.  See Lib/unittest.py.
    #return unittest.makeSuite(GenTest)
    loader = unittest.TestLoader()
    testsuite = loader.loadTestsFromTestCase(GenTest)
    return testsuite


# Make the test suite and run the tests.
def test():
    testsuite = suite()
    runner = unittest.TextTestRunner(sys.stdout, verbosity=2)
    runner.run(testsuite)


USAGE_TEXT = """
Usage:
    python test.py [options]
Options:
    -h, --help      Display this help message.
Example:
    python test.py
"""

def usage():
    print USAGE_TEXT
    sys.exit(-1)


def main():
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'h', ['help'])
    except:
        usage()
    relink = 1
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
    if len(args) != 0:
        usage()
    test()


if __name__ == '__main__':
    main()
    #import pdb
    #pdb.run('main()')

