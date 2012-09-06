import logging

from django.db.models import get_models, signals
from metashare.sync import models as sync_models
from metashare import settings
from django.contrib.auth.models import User


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)


def create_syncuser(app, created_models, verbosity, **kwargs):
    from django.core.management import call_command
    
    syncusers = getattr(settings, "SYNC_USERS", {})
    
    for username, password in syncusers.iteritems():
        try:
            _user = User.objects.get(username=username)
            # the password may have been changed in the SYNC_USERS dict, so make
            # sure to always update it in the database
            _user.set_password(password)
            LOGGER.info("Reset password for sync user account %s to the "
                        "SYNC_USERS settings.", username)
            _user.save()
        except User.DoesNotExist:
            call_command("createsyncuser", username=username, password=password, verbosity=1)

# We must make sure that the post_syncdb hooks from auth.management are executed first,
# or else our code cannot find the permissions we want to use:\

from django.contrib.auth import management


signals.post_syncdb.connect(create_syncuser,
    sender=sync_models, dispatch_uid = "metashare.sync.management.create_syncuser")
