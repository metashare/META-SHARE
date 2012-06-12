from django.db.models import get_models, signals
from metashare.sync import models as sync_models
from metashare import local_settings
from django.contrib.auth.models import User

def create_syncuser(app, created_models, verbosity, **kwargs):
    from django.core.management import call_command
    
    syncusers = getattr(local_settings, "SYNC_USERS", {})
    
    for username, password in syncusers.iteritems():
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            call_command("createsyncuser", username=username, password=password, verbosity=1)

# We must make sure that the post_syncdb hooks from auth.management are executed first,
# or else our code cannot find the permissions we want to use:\

from django.contrib.auth import management


signals.post_syncdb.connect(create_syncuser,
    sender=sync_models, dispatch_uid = "metashare.sync.management.create_syncuser")
