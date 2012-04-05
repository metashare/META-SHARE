#!/usr/bin/env python
"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import os
import sys
import traceback
from zipfile import ZipFile
from xml.etree import ElementTree

# Magic python path, based on http://djangosnippets.org/snippets/281/
from os.path import abspath, dirname, join
parentdir = dirname(dirname(abspath(__file__)))
# Insert our dependencies:
sys.path.insert(0, join(parentdir, 'lib', 'python2.7', 'site-packages'))
# Insert our parent directory (the one containing the folder metashare/):
sys.path.insert(0, parentdir)


try:
    import settings # Assumed to be in the same directory.

except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the " \
      "directory containing %r. It appears you've customized things.\n" \
      "You'll have to run django-admin.py, passing it your settings " \
      "module.\n(If the file settings.py does indeed exist, it's causing" \
      " an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    PROJECT_HOME = os.path.normpath(os.getcwd() + "/..")
    sys.path.append(PROJECT_HOME)
    
    # Check command line parameters first.
    if len(sys.argv) < 2:
        print "\n\tusage: {0} <archive.zip> <upgrade-db>\n".format(
          sys.argv[0])
        print "\tWARNING: when providing the 'upgrade-db' switch, the " \
          "database will be upgraded\n\tto the latest schema " \
          "automatically. This step is not reversible which means the\n\t" \
          "database cannot be used with older versions of the META-SHARE " \
          "software anymore.\n"
        print "\tYou have been warned.\n"
        sys.exit(-1)
    
    if len(sys.argv) > 2 and sys.argv[2] == 'upgrade-db':
        # Automagically run syncdb to update database to the latest version.
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'syncdb', '--noinput'])
    
        # Make sure that ResourceInfo gets a schema update with AudioInfo,
        # ToolServiceInfo, and LanguageDescriptionInfo as syncdb won't do it.
        # Also patch in column textclassificationinfo as it seems necessary.
        import sqlite3
        conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
        patches = {
          'repository_resourceinfo': ('AudioInfo_id', 'ToolServiceInfo_id',
            'LanguageDescriptionInfo_id'),
          'repository_textclassificationinfo':
            ('conformanceToClassificationScheme',)
        }
        for table, columns in patches.items():
            try:
                for column in columns:
                    result = conn.execute('ALTER TABLE {0} ADD COLUMN ' \
                      '"{1}";'.format(table, column))
            
            except sqlite3.OperationalError:
                continue
    
        conn.close()
    
    # Disable verbose debug output for the import process...
    settings.DEBUG = False
    
    SUCCESSFUL_EXPORTS = 0
    ERRONEOUS_EXPORTS = 0
    RESOURCE_NO = 0
    from metashare.repository.models import resourceInfoType_model
    with ZipFile(sys.argv[1], 'w') as out:
        for resource in resourceInfoType_model.objects.all():
            try:
                RESOURCE_NO += 1
                root_node = resource.export_to_elementtree()
                xml_string = ElementTree.tostring(root_node, encoding="utf-8")
                resource_filename = 'resource-{0}.xml'.format(RESOURCE_NO)
                out.writestr(resource_filename, xml_string)
                SUCCESSFUL_EXPORTS += 1
            
            except Exception:
                ERRONEOUS_EXPORTS += 1
                print 'Could not export resource id={0}!'.format(resource.id)
                print traceback.format_exc()
    
    print "Done. Successfully exported {0} files from the database, errors " \
      "occured in {1} cases.".format(SUCCESSFUL_EXPORTS, ERRONEOUS_EXPORTS)
