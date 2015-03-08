#!/usr/bin/env python
import os
import sys
from metashare import settings

if __name__ == "__main__":
    # MS, 21.03.2012: Add a fail-early verification "hook"
    fail_early_commands = ('runserver', 'runfcgi')
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command in fail_early_commands:
            from django.core.management import setup_environ
            setup_environ(settings)
            from metashare.repository import verify_at_startup
            verify_at_startup() # may raise Exception, which we don't want to catch.

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metashare.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


