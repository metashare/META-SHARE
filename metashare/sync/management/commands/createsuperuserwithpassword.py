from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username for the user.'),
        make_option('--password', dest='password', default=None,
            help='Specifies the password for the user.'),
        make_option('--email', dest='email', default="",
            help='Specifies the e-mail for the user. (optional)'),
    )
    def handle(self, *args, **options):
        username = options.get('username', None)
        password = options.get('password', None)
        email = options.get('email', "")
        if username is None or password is None:
            print "Missing username or password"
            return

        user = User.objects.create_superuser(username, email, password)
        if user is None:
            print "Error in creating user"
            return

        print "Super user successfully created"
