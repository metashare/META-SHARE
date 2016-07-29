#!/usr/bin/env python
import os
import sys
import django

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metashare.settings")

    # MS, 21.03.2012: Add a fail-early verification "hook"
    fail_early_commands = ('runserver', 'runfcgi')
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command in fail_early_commands:
            django.setup()
            from metashare.repository import verify_at_startup
            verify_at_startup() # may raise Exception, which we don't want to catch.

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

