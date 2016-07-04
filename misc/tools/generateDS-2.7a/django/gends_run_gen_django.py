#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Synopsis:
    Generate Django models.py and forms.py from XML schema.
Usage:
    python gends_run_gen_django.py [options] <schema_file>
Options:
    -h, --help      Display this help message.
    -f, --force     Overwrite the following files without asking:
                        <schema>lib.py
                        generateds_definedsimpletypes.py
                        models.py
                        forms.py
    -v, --verbose   Display additional information while running.
Example:
    python gends_run_gen_django.py my_schema.xsd

"""


#
# Imports

import sys
import getopt
import os
from subprocess import Popen, PIPE
from gends_generate_django import generate_model

#
# Globals and constants


#
# Functions for external use


#
# Classes

class GenerateDjangoError(Exception):
    pass


#
# Functions for internal use and testing

def generate(options, schema_file_name):
    schema_name_stem = os.path.splitext(os.path.split(schema_file_name)[1])[0]
    bindings_file_name = '%slib.py' % (schema_name_stem, )
    bindings_file_stem = os.path.splitext(bindings_file_name)[0]
    model_file_name = 'models.py'
    form_file_name = 'forms.py'
    admin_file_name = 'admin.py'
    dbg_msg(options, 'schema_name_stem: %s\n' % (schema_name_stem, ))
    dbg_msg(options, 'bindings_file_name: %s\n' % (bindings_file_name, ))
    if not options['force']:
        flag1 = exists(bindings_file_name)
        flag2 = exists(model_file_name)
        flag3 = exists(form_file_name)
        flag4 = exists(admin_file_name)
        if (flag1 or flag2 or flag3 or flag4):
            return
    args = ('generateDS.py', '-f',
        '-o', '%s' % (bindings_file_name, ),
        '--member-specs=list',
        schema_file_name,
        )
    if not run_cmd(options, args):
        return
    args = ('gends_extract_simple_types.py', '-f',
        schema_file_name,
        )
    if not run_cmd(options, args):
        return
    
    class ProgramOptions(object):
        def get_force_(self):
            return self.force_
        def set_force_(self, force):
            self.force_ = force
        force = property(get_force_, set_force_)
    
    opts = ProgramOptions();
    opts.force = True;
    generate_model(opts, bindings_file_stem)
    
#    args = ('gends_generate_django.py', '-f',
#        bindings_file_stem,
#        )
#    if not run_cmd(options, args):
#        return


def run_cmd(options, args):
    dbg_msg(options, '*** running %s\n' % (' '.join(args), ))
    process = Popen(args, stderr=PIPE, stdout=PIPE)
    content1 = process.stderr.read()
    content2 = process.stdout.read()
    if content1:
        sys.stderr.write('*** error ***\n')
        sys.stderr.write(content1)
        sys.stderr.write('*** error ***\n')
        return False
    if content2:
        dbg_msg(options, '*** message ***\n')
        dbg_msg(options, content2)
        dbg_msg(options, '*** message ***\n')
        return True
    return True


def exists(file_name):
    if os.path.exists(file_name):
        msg = 'File %s exists.  Use -f/--force to overwrite.\n' % (file_name, )
        sys.stderr.write(msg)
        return True
    return False


def dbg_msg(options, msg):
    if options['verbose']:
        sys.stdout.write(msg)


USAGE_TEXT = __doc__

def usage():
    sys.stderr.write(USAGE_TEXT)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'hvf', ['help', 'verbose',
            'force', ])
    except:
        usage()
    options = {}
    options['force'] = False
    options['verbose'] = False
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-f', '--force'):
            options['force'] = True
        elif opt in ('-v', '--verbose'):
            options['verbose'] = True
    if len(args) != 1:
        usage()
    schema_name = args[0]
    generate(options, schema_name)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()


