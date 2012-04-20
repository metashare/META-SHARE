import sys
from xml.etree.ElementTree import tostring
from django.test import TestCase
from metashare import test_utils
from metashare.settings import ROOT_PATH
from metashare.repository.models import resourceInfoType_model
from metashare.repository.supermodel import pretty_xml

class ModelTest(TestCase):
    """
    Tests the import/export properties of the generated object model.
    """
    def setUp(self):
        """
        Set up the email test
        """
        test_utils.setup_test_storage()
        _fixture = '{0}/repository/fixtures/testfixture.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_fixture)
        self.resource_id = _result[0].id
    
    def tearDown(self):
        """
        Clean up the test
        """
        resourceInfoType_model.objects.all().delete()
    
    def testRollbackOnImportError(self):
        """
        Checks that a complete rollback is performed on import error.
        """
        _database = {}
        _models = [x for x in dir(sys.modules['metashare.repository.models'])
          if x.endswith('_model')]
        
        for _model in _models:
            if hasattr(sys.modules['metashare.repository.models'], _model):
                _inst = getattr(sys.modules['metashare.repository.models'], _model)
                _database[_model] = _inst.objects.count()
        
        _broken_fixture = '{0}/repository/fixtures/broken.xml'.format(ROOT_PATH)
        result = test_utils.import_xml(_broken_fixture)
        
        self.assertEqual(result[:2], (None, []))
        
        errors = []
        for _model in _models:
            if hasattr(sys.modules['metashare.repository.models'], _model):
                _inst = getattr(sys.modules['metashare.repository.models'], _model)
                print "Testing rollback for {}...".format(_model)
                if _database[_model] != _inst.objects.count():
                    errors.append(_model)
        
        self.assertEqual(errors, [])
    
    def testImportExportRoundtrip(self):
        """
        Checks that there is no data lost when exporting an imported XML.
        """
        _roundtrip = '{0}/repository/fixtures/roundtrip.xml'.format(ROOT_PATH)
        _result = test_utils.import_xml(_roundtrip)
        
        with open(_roundtrip) as _import_file:
            _import_xml = _import_file.read()
        
        _export_xml = tostring(_result[0].export_to_elementtree())
        
        # cfedermann: uncomment these lines to dump import/export XML to file.
        #
        #with open('/tmp/_import.xml', 'w') as _out:
        #    _out.write(pretty_xml(_import_xml).encode('utf-8'))
        #with open('/tmp/_export.xml', 'w') as _out:
        #    _out.write(pretty_xml(_export_xml).encode('utf-8'))
        
        _pretty_import = pretty_xml(_import_xml).strip().encode('utf-8')
        _pretty_export = pretty_xml(_export_xml).strip().encode('utf-8')
        
        self.assertEqual(_pretty_import, _pretty_export)
