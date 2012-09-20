"""
Management utility to create users with the permission to access syncrhonization
data.
"""

import getpass
import re
import sys
from optparse import make_option
from django.contrib.auth.models import User, Permission
from django.core.management.base import BaseCommand

RE_VALID_USERNAME = re.compile('[\w.@+-]+$')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username for the user.'),
    )
    help = 'Used to create a user with synchronization permissions.'

    def handle(self, *args, **options):
        username = options.get('username', None)
        verbosity = int(options.get('verbosity', 1))

        # If not provided, create the user with an unusable password
        password = options.get('password', None)

        # Prompt for username/email/password. Enclose this whole thing in a
        # try/except to trap for a keyboard interrupt and exit gracefully.
        try:

            # Get a username
            while 1:
                if not username:
                    input_msg = 'Username'
                    username = raw_input(input_msg + ': ')
                if not RE_VALID_USERNAME.match(username):
                    sys.stderr.write("Error: That username is invalid. Use only letters, digits and underscores.\n")
                    username = None
                    continue
                try:
                    User.objects.get(username=username)
                except User.DoesNotExist:
                    break
                else:
                    sys.stderr.write("Error: That username is already taken.\n")
                    username = None

            # Get an email
            email = u'{0}@metashare-dummy.org'.format(username)

            # Get a password
            while 1:
                if not password:
                    password = getpass.getpass()
                    password2 = getpass.getpass('Password (again): ')
                    if password != password2:
                        sys.stderr.write("Error: Your passwords didn't match.\n")
                        password = None
                        continue
                if password.strip() == '':
                    sys.stderr.write("Error: Blank passwords aren't allowed.\n")
                    password = None
                    continue
                break
        except KeyboardInterrupt:
            sys.stderr.write("\nOperation cancelled.\n")
            sys.exit(1)

        user = User.objects.create_user(username, email, password)
        grant_sync_permissions(user)
        if verbosity >= 1:
            self.stdout.write("User '{0}' with synchronization permissions created successfully.\n".format(username))


def grant_sync_permissions(user):
    """
    Grant the permissions required for syncing to the given `User` object.
    """
    sync_permission = Permission.objects.get(codename='can_sync',
        content_type__app_label='storage')
    user.user_permissions.add(sync_permission)
