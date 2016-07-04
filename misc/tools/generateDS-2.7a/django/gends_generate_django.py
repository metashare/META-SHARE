#!/usr/bin/env python
"""
Synopsis:
    Generate Django model and form definitions.
    Write to forms.py and models.py.
Usage:
    python gen_model.py [options]
Options:
    -f, --force
            Overwrite models.py and forms.py without asking.
    -h, --help
            Show this help message.
"""


import sys
import os
import getopt
import importlib

#import nexmllib as supermod



#
# Globals
#

supermod = None

#
# Classes
#

class ProgramOptions(object):
    def get_force_(self):
        return self.force_
    def set_force_(self, force):
        self.force_ = force
    force = property(get_force_, set_force_)


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


META_MODEL_HEADER="""\
from supermodel import SchemaModel, _make_choices_from_list
from widgets import MultiFieldWidget
from fields import MultiTextField

"""

#
# Functions
#

def generate_model(options, module_name):
    global supermod
    supermod = importlib.import_module(module_name)
    models_file_name = 'models.py'
    forms_file_name = 'forms.py'
    admin_file_name = 'admin.py'
    if (    (os.path.exists(models_file_name) or 
            os.path.exists(forms_file_name) or
            os.path.exists(admin_file_name)
            )
        and not options.force):
        sys.stderr.write('\nmodels.py or forms.py or admin.py exists.  Use -f/--force to overwrite.\n\n')
        sys.exit(1)
    globals_dict = globals()
    models_writer = Writer(models_file_name)
    forms_writer = Writer(forms_file_name)
    admin_writer = Writer(admin_file_name)
    wrtmodels = models_writer.write
    wrtforms = forms_writer.write
    wrtadmin = admin_writer.write
    wrtmodels('from django.db import models\n\n')
    wrtforms('from django import forms\n\n')
    wrtmodels(META_MODEL_HEADER)
    not_generated = set()
    for clazz in supermod.__all__:
        not_generated.add(clazz)
    while not_generated:
        for class_name in supermod.__all__:
            if class_name in not_generated:
                if hasattr(supermod, class_name):
                    cls = getattr(supermod, class_name)
                    schema_data = cls.generate_embedded_types_(not_generated)
                    if not schema_data:
                        continue
                    for enum in schema_data[2]:
                        wrtmodels(enum)
                    cls.generate_model_(wrtmodels, wrtforms, schema_data)
                    not_generated.remove(class_name)
                else:
                    sys.stderr.write('class %s not defined\n' % (class_name, ))
    wrtadmin('from django.contrib import admin\n')
    wrtadmin('from models import \\\n')
    first_time = True
    for class_name in supermod.__all__:
        if first_time:
            wrtadmin('    %s_model' % (class_name, ))
            first_time = False
        else:
            wrtadmin(', \\\n    %s_model' % (class_name, ))
    wrtadmin('\n\n')
    for class_name in supermod.__all__:
        wrtadmin('admin.site.register(%s_model)\n' % (class_name, ))
    wrtadmin('\n')
    models_writer.close()
    forms_writer.close()
    admin_writer.close()
    print 'Wrote %d lines to models.py' % (models_writer.get_count(), )
    print 'Wrote %d lines to forms.py' % (forms_writer.get_count(), )
    print 'Wrote %d lines to admin.py' % (admin_writer.get_count(), )



USAGE_TEXT = __doc__

def usage():
    print USAGE_TEXT
    sys.exit(1)


def main():
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'hfs:', ['help', 'force',
            'suffix=', ])
    except:
        usage()
    options = ProgramOptions()
    options.force = False
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-f', '--force'):
            options.force = True
    if len(args) != 1:
        usage()
    module_name = args[0]
    generate_model(options, module_name)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()


