"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging

from uuid import uuid1

from django.contrib.auth.models import User, Group
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from metashare.settings import LOG_LEVEL, LOG_HANDLER


# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.accounts.models')
LOGGER.addHandler(LOG_HANDLER)


def _create_uuid():
    """
    Creates a unique id using UUID-1, checks for collisions.
    """
    # Create new UUID-1 id.
    new_id = uuid1().hex
    
    # Re-create id in case of collision(s).
    while RegistrationRequest.objects.filter(uuid=new_id) or \
      ResetRequest.objects.filter(uuid=new_id) or \
      UserProfile.objects.filter(uuid=new_id):
        new_id = uuid1().hex
    return new_id


class RegistrationRequest(models.Model):
    """
    Contains user data related to a user registration request.
    """
    shortname = models.CharField('Username', max_length=30, unique=True)
    firstname = models.CharField('First name', max_length=30)
    lastname = models.CharField('Last name', max_length=30)
    email = models.EmailField(unique=True)
    
    uuid = models.CharField(max_length=32, verbose_name="UUID",
      default=_create_uuid)
    created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        """
        Return Unicode representation for this instance.
        """
        return u'<RegistrationRequest "{0}">'.format(self.shortname)


class ResetRequest(models.Model):
    """
    Contains authentication key to reset the user password.
    """
    user = models.ForeignKey(User)
    uuid = models.CharField(max_length=32, verbose_name="UUID",
      default=_create_uuid)
    created = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        """
        Return Unicode representation for this instance.
        """
        return u'<ResetRequest "{0}">'.format(self.user.username)


class EditorGroup(Group):
    """
    A specialized `Group` subtype which is used to group resources that can only
    be edited by users who are member of this group.
    
    The corresponding `ModelAdmin` class suggests basic resource edit
    permissions for this group. 
    """
    # Currently the group is just used as a marker, i.e., in order to
    # differentiate its instances from other Django `Group`s. That's why it
    # doesn't have any custom fields.

    def get_members(self):
        return User.objects.filter(groups__name=self.name)

    def get_managers(self):
        return User.objects.filter(groups__name__in=
            ManagerGroup.objects.filter(managed_group__name=self.name)
                .values_list('name', flat=True))


class EditorRegistrationRequest(models.Model):
    """
    Contains user data related to a user application for being an editor.
    """
    user = models.ForeignKey(User)
    editor_group = models.OneToOneField(EditorGroup)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        """
        Return Unicode representation for this instance.
        """
        return u'<EditorRegistrationRequest of "{0}" for "{1}">'.format(
                self.user, self.editor_group)


class ManagerGroup(Group):
    """
    A specialized `Group` which gives its members permissions to manage language
    resources belonging to a certain (managed) group.
    
    Group members may choose the members of the managed group and they may
    ingest/publish resources belonging to the managed group. Delete permission
    for a resource is suggested by the corresponding `ModelAdmin` class.
    """
    # the `EditorGroup` which is managed by members of this `ManagerGroup`
    managed_group = models.OneToOneField(EditorGroup)

    def get_members(self):
        return User.objects.filter(groups__name=self.name)


class UserProfile(models.Model):
    """
    Contains additional user data related to a Django User instance.
    """
    class Meta:
        # global permissions for which there does not seem to be any better
        # place around ...
        permissions = (
            ("ms_associate_member", "Is a META-SHARE associate member."),
            ("ms_full_member", "Is a META-SHARE full member."),
        )

    user = models.OneToOneField(User)
    modified = models.DateTimeField(auto_now=True)
    uuid = models.CharField(max_length=32, verbose_name="UUID",
      default=_create_uuid)
    
    birthdate = models.DateField("Date of birth", blank=True,
      null=True)
    affiliation = models.TextField("Affiliation(s)", blank=True)
    position = models.CharField(max_length=50, blank=True)
    homepage = models.URLField(blank=True)
    
    # These fields can be edited by the user in the browser.
    __editable_fields__ = ('birthdate', 'affiliation', 'position', 'homepage')
    
    # These fields are synchronized between META-SHARE nodes.
    __synchronized_fields__ = ('modified', 'birthdate',
      'affiliation', 'position', 'homepage')
    
    def __unicode__(self):
        """
        Return Unicode representation for this instance.
        """
        return u'<UserProfile "{0}">'.format(self.user.username)
    
    def delete(self, *args, **kwargs):
        """
        Only deletes the instance if the related User instance is gone.
        """
        if not self.user:
            super(UserProfile, self).delete(*args, **kwargs)

# cfedermann: of course, we will now also have to call synchronise methods for
#             delete() calls.  For this, we have to create receivers listening
#             to the post_delete signal.  Again, this has to be tested!

    def has_manager_permission(self, editor_group=None):
        """
        Return whether the user profile has permission to manage the given
        editor group.
        
        If no editor group is given, then the method returns whether the user
        profile has manager permission for any editor group.
        """
        if self.user.is_superuser:
            return True
        mgr_groups = ManagerGroup.objects.filter(
            name__in=self.user.groups.values_list('name', flat=True))
        if editor_group:
            return any(editor_group.name == mgr_group.managed_group.name
                       for mgr_group in mgr_groups)
        else:
            return mgr_groups.count() != 0


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    Create a corresponding profile whenever a User object is created.
    
    Also, make sure to synchronise local changes with other nodes.
    """
    # Check if the User instance has just been created; if so, create the
    # corresponding UserProfile instance.
    if created:
        # pylint: disable-msg=W0612
        profile, new = UserProfile.objects.get_or_create(user=instance)
    
    # Otherwise, the corresponding UserProfile for this User instance has to
    # be saved in order to update the modified timestamp.  This will trigger
    # synchronise_profile() and perform synchronisation if required.
    else:
        profile = instance.get_profile()
        profile.save()

# cfedermann: the following code allows to catch the m2m update signals, i.e.
#             pre/post_{clear,add,remove}.
#
#from django.db.models.signals import m2m_changed
#
#def do_something_with_permissions(sender, instance, action, **kwargs):
#    """
#    We want to use the "post_" actions: post_add, post_remove, post_clear.
#    - https://docs.djangoproject.com/en/dev/ref/signals/ \
#      #django.db.models.signals.m2m_changed
#    """
#    LOGGER.debug('Action: {0} for instance: {1}'.format(action, instance))
#
#m2m_changed.connect(do_something_with_permissions, sender=User.user_permissions.through)

@receiver(user_logged_in)
def add_uuid_to_session(sender, request, user, **kwargs):
    """
    Add the logged in user's UUID to the session object.
    """
    request.session['METASHARE_UUID'] = user.get_profile().uuid

@receiver(user_logged_out)
def del_uuid_from_session(sender, request, user, **kwargs):
    """
    Delete the current UUID from the session object.
    """
    request.session['METASHARE_UUID'] = None
