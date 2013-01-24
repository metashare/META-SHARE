import logging

from uuid import uuid1

from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from metashare.settings import LOG_HANDLER
from metashare import repository

# Setup logging support.
LOGGER = logging.getLogger(__name__)
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
    user = models.OneToOneField(User)
    uuid = models.CharField(max_length=32, verbose_name="UUID",
                            default=_create_uuid)
    created = models.DateTimeField(auto_now_add=True)
    
    def __init__(self, *args, **kwargs):
        super(RegistrationRequest, self).__init__(*args, **kwargs)

    @staticmethod
    def _delete_related_user(instance, **kwargs):
        """
        Deletes the related `User` object of the given deleted
        `RegistrationRequest` instance, if the former is not active, yet.
        """
        try:
            _related_user = instance.user
        except User.DoesNotExist:
            # in case the user account is deleted before the registration
            # request is deleted (e.g., by a superuser), then we do not have to
            # do anything here
            pass
        else:
            # only delete the corresponding user account, if it is not active,
            # yet (it may have been activated manually by a superuser)
            if not _related_user.is_active:
                _related_user.delete()

    def __unicode__(self):
        """
        Return Unicode representation for this instance.
        """
        return u'<RegistrationRequest "{0}">'.format(self.user.username)

# make sure to delete the related `User` object of a deleted
# `RegistrationRequest`, if necessary
post_delete.connect(RegistrationRequest._delete_related_user,
                    sender=RegistrationRequest)


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
            EditorGroupManagers.objects.filter(managed_group__name=self.name)
                .values_list('name', flat=True))


class EditorGroupApplication(models.Model):
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
        return u'<EditorGroupApplication of "{0}" for "{1}">'.format(
                self.user, self.editor_group)


class EditorGroupManagers(Group):
    """
    A specialized `Group` which gives its members permissions to manage language
    resources belonging to a certain (managed) group.
    
    Group members may choose the members of the managed group and they may
    ingest/publish resources belonging to the managed group. Delete permission
    for a resource is suggested by the corresponding `ModelAdmin` class.
    """
    # the `EditorGroup` which is managed by members of this `EditorGroupManagers`
    managed_group = models.OneToOneField(EditorGroup)

    class Meta:
        verbose_name = "editor group managers group"

    def get_members(self):
        return User.objects.filter(groups__name=self.name)


class Organization(Group):
    """
    A specialized `Group` subtype which is used to group users from a same organization
    who get specific access rights to the resources.
    """

    def get_members(self):
        return User.objects.filter(groups__name=self.name)

    def get_managers(self):
        return User.objects.filter(groups__name__in=
            OrganizationManagers.objects.filter(managed_organization__name=self.name)
                .values_list('name', flat=True))


class OrganizationApplication(models.Model):
    """
    Contains user data related to a user application for being member of an organization.
    """
    user = models.ForeignKey(User)
    organization = models.OneToOneField(Organization)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        """
        Return Unicode representation for this instance.
        """
        return u'<OrganizationApplication of "{0}" for "{1}">'.format(
                self.user, self.organization)


class OrganizationManagers(Group):
    """
    A specialized `Group` which gives its members permissions to manage a certain organization.
    """
    # the `Organization` which is managed by members of this `OrganizationManagers`
    managed_organization = models.OneToOneField(Organization)

    class Meta:
        verbose_name = "organization managers group"

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
    
    default_editor_groups = models.ManyToManyField(EditorGroup, blank=True)

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
                

    def has_editor_permission(self):
        """
        Returns `True` if there are any resources that the user behind this
        profile can edit or create; `False` otherwise.
        """
        if self.user.is_superuser:
            return True      

        return self.user.is_staff and \
            (EditorGroup.objects.filter(name__in=
                self.user.groups.values_list('name', flat=True)).exists()
             or repository.models.resourceInfoType_model.objects \
                .filter(owners__username=self.user.username).exists())

    def has_manager_permission(self, editor_group=None):
        """
        Return whether the user profile has permission to manage the given
        editor group.
        
        If no editor group is given, then the method returns whether the user
        profile has manager permission for any editor group.
        """
        if self.user.is_superuser:
            return True
        mgr_groups = EditorGroupManagers.objects.filter(
            name__in=self.user.groups.values_list('name', flat=True))
        if editor_group:
            return any(editor_group.name == mgr_group.managed_group.name
                       for mgr_group in mgr_groups)
        else:
            return mgr_groups.count() != 0

    def has_organization_manager_permission(self, organization=None):
        """
        Return whether the user profile has permission to manage the given
        organization.
        
        If no organization is given, then the method returns whether the user
        profile has manager permission for any organization.
        """
        if self.user.is_superuser:
            return True
        org_mgr_groups = OrganizationManagers.objects.filter(
            name__in=self.user.groups.values_list('name', flat=True))
        if organization:
            return any(organization.name == org_mgr_group.managed_organization.name
                       for org_mgr_group in org_mgr_groups)
        else:
            return org_mgr_groups.count() != 0


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
