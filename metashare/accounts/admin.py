"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.contrib.auth.models import Permission, Group
from django.db import transaction

from metashare.accounts.models import RegistrationRequest, ResetRequest, \
  UserProfile, EditorGroup, ManagerGroup


class RegistrationRequestAdmin(admin.ModelAdmin):
    """
    Administration interface for user registration requests.
    """
    list_display = ('shortname', 'firstname', 'lastname', 'email', 'uuid',
      'created')
    search_fields = ('shortname', 'firstname', 'lastname', 'email')


class ResetRequestAdmin(admin.ModelAdmin):
    """
    Administration interface for user reset requests.
    """
    list_display = ('user', 'uuid', 'created')
    search_fields = ('user',)


class UserProfileAdmin(admin.ModelAdmin):
    """
    Administration interface for user profiles.
    """
    list_display = ('user', 'uuid', 'modified', 'birthdate', 'affiliation',
      'position', 'homepage')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
      'birthdate', 'affiliation', 'position', 'homepage')


class EditorGroupAdmin(admin.ModelAdmin):
    """
    Administration interface for `EditorGroup`s.
    """
    list_display = ('name',)
    search_fields = ('name',)

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        """
        The 'add' admin view for this model.
        """
        # when showing a certain add view for the first time, prepopulate the
        # permissions field: we suggest that the new group has all permissions
        # that global editors have
        if request.method == 'GET':
            # request `QueryDict`s are immutable; create a copy before upadating
            request.GET = request.GET.copy()
            from metashare.repository.management import GROUP_GLOBAL_EDITORS
            _perms = ','.join([str(pk) for pk in Group.objects.get(name=
                GROUP_GLOBAL_EDITORS).permissions.values_list('pk', flat=True)])
            request.GET.update({'permissions': _perms})
        return super(EditorGroupAdmin, self).add_view(request,
                                form_url=form_url, extra_context=extra_context)


class ManagerGroupAdmin(admin.ModelAdmin):
    """
    Administration interface for `ManagerGroup`s.
    """
    list_display = ('name', 'managed_group')
    search_fields = ('name', 'managed_group')

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        """
        The 'add' admin view for this model.
        """
        # when showing a certain add view for the first time, prepopulate the
        # permissions field: we suggest that the new group has all required
        # model permissions for deleting language resources
        if request.method == 'GET':
            # request `QueryDict`s are immutable; create a copy before upadating
            request.GET = request.GET.copy()
            from metashare.repository.models import resourceInfoType_model
            opts = resourceInfoType_model._meta
            # pylint: disable-msg=E1101
            request.GET.update({'permissions': str(Permission.objects.filter(
                    content_type__app_label=opts.app_label,
                    codename=opts.get_delete_permission())[0].pk)})
        return super(ManagerGroupAdmin, self).add_view(request,
                                form_url=form_url, extra_context=extra_context)


admin.site.register(RegistrationRequest, RegistrationRequestAdmin)
admin.site.register(ResetRequest, ResetRequestAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(EditorGroup, EditorGroupAdmin)
admin.site.register(ManagerGroup, ManagerGroupAdmin)
