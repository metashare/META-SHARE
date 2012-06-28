"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django import forms
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.contrib.auth.models import Permission, Group, User
from django.db import transaction
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from metashare.accounts.models import RegistrationRequest, ResetRequest, \
  UserProfile, EditorGroup, EditorRegistrationRequest, ManagerGroup

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
      'position', 'homepage', '_editor_group_display', '_manager_group_display')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
      'birthdate', 'affiliation', 'position', 'homepage')

    def _editor_group_display(self, obj):
        """
        Returns a string representing a list of the the editor groups of a user
        profile.
        """
        return ', '.join([editor_group.name for editor_group
            in EditorGroup.objects.filter(name__in=
                            obj.user.groups.values_list('name', flat=True))])

    _editor_group_display.short_description = _('Editor groups')

    def _manager_group_display(self, obj):
        """
        Returns a string representing a list of the the manager groups of a user
        profile.
        """
        return ', '.join([mgr_group.name for mgr_group
            in ManagerGroup.objects.filter(name__in=
                            obj.user.groups.values_list('name', flat=True))])

    _manager_group_display.short_description = _('Manager groups')


class EditorGroupAdmin(admin.ModelAdmin):
    """
    Administration interface for `EditorGroup`s.
    """
    list_display = ('name', '_members_display', '_managing_group_display',
                    '_managers_display')
    search_fields = ('name',)
    actions = ('add_user_to_editor_group', 'remove_user_from_editor_group', )
    
    def _members_display(self, obj):
        """
        Returns a string representing a list of the members of the given
        `EditorGroup` object.
        """
        return ', '.join(member.username for member in obj.get_members())

    _members_display.short_description = _('Members')
    
    def _managing_group_display(self, obj):
        """
        Returns a string representing a list of the the managing groups of the
        given `EditorGroup` object.
        """
        return ', '.join(mgr_group.name for mgr_group
                         in ManagerGroup.objects.filter(managed_group=obj))

    _managing_group_display.short_description = _('Managing groups')
    
    def _managers_display(self, obj):
        """
        Returns a string representing a list of the the managers of the given
        `EditorGroup`.
        """
        return ', '.join(usr.name
            for mgr_group in ManagerGroup.objects.filter(managed_group=obj)
            for usr in User.objects.filter(groups__name=mgr_group.name))

    _managing_group_display.short_description = _('Managing groups')

    class UserProfileinEditorGroupForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

        def __init__(self, choices = None, *args, **kwargs):
            super(EditorGroupAdmin.UserProfileinEditorGroupForm, self).__init__(*args, **kwargs)
            if choices is not None:
                self.choices = choices
                self.fields['users'] = forms.ModelMultipleChoiceField(self.choices)

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

    def queryset(self, request):
        queryset = super(EditorGroupAdmin, self).queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(managergroup__in=ManagerGroup.objects.filter(
                name__in=request.user.groups.values_list('name', flat=True)))

    def add_user_to_editor_group(self, request, queryset):
        form = None
        if 'cancel' in request.POST:
            self.message_user(request, _('Cancelled adding users to the editor group.'))
            return
        elif 'add_user_profile_to_editor_group' in request.POST:
            objs_up = UserProfile.objects.all()
            form = self.UserProfileinEditorGroupForm(objs_up, request.POST)
            if form.is_valid():
                userprofiles = form.cleaned_data['users']
                for userprofile in userprofiles:
                    for obj in queryset:
                        if UserProfile.objects.filter(user=request.user)[0].has_manager_permission(obj):
                            userprofile.user.groups.add(obj)
                        else:
                            self.message_user(request,
                                _('You need to be group manager to add a user to this editor group.'))
                            return HttpResponseRedirect(request.get_full_path())
                self.message_user(request, _('Successfully added users to editor group.'))
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            userprofiles = UserProfile.objects.all()
            form = self.UserProfileinEditorGroupForm(choices=userprofiles,
                initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
        return render_to_response('accounts/add_user_profile_to_editor_group.html',
                                  {
                                   'selected_editorgroups': queryset,
                                   'form': form,
                                   'path':request.get_full_path()
                                  },
                                  context_instance=RequestContext(request))

    add_user_to_editor_group.short_description = _("Add users to selected editor groups")

    def remove_user_from_editor_group(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled removing users from the editor group.'))
                return
            elif 'remove_user_profile_from_editor_group' in request.POST:
                objs_up = UserProfile.objects.all()
                form = self.UserProfileinEditorGroupForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            userprofile.user.groups.remove(obj)
                    self.message_user(request, _('Successfully removed users from editor group.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.all()
                form = self.UserProfileinEditorGroupForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
            return render_to_response('accounts/remove_user_profile_from_editor_group.html',
                                      {
                                       'selected_editorgroups': queryset,
                                       'form': form,
                                       'path':request.get_full_path()
                                      },
                                      context_instance=RequestContext(request))

    remove_user_from_editor_group.short_description = _("Remove users from selected editor groups")


class EditorRegistrationRequestAdmin(admin.ModelAdmin):
    """
    Administration interface for user editor registration requests.
    """
    list_display = ('user', 'editor_groups', 'created')
    actions = ('accept_request', )

    def accept_request(self, request, queryset):
        """
        The action to accept editor registration requests.
        """
        if request.user.is_superuser:
            for req in queryset:
                for obj in req.editorgroups.all():
                    req.user.groups.add(obj)
                EditorRegistrationRequest.objects.filter(uuid=req.uuid).delete()
            self.message_user(request, 'Successfully added user to editor groups.')
            return HttpResponseRedirect(request.get_full_path())
        self.message_user(request, 'You must be super user to accept the requests.')
        return HttpResponseRedirect(request.get_full_path())

    accept_request.short_description = "Accept selected editor registration requests"

class ManagerGroupAdmin(admin.ModelAdmin):
    """
    Administration interface for `ManagerGroup`s.
    """
    list_display = ('name', 'managed_group', '_members_display')
    search_fields = ('name', 'managed_group')
    actions = ('add_user_to_manager_group', 'remove_user_from_manager_group', )
    
    def _members_display(self, obj):
        """
        Returns a string representing a list of the members of the given
        `ManagerGroup` object.
        """
        return ', '.join(member.username for member in obj.get_members())

    _members_display.short_description = _('Members')

    class UserProfileinManagerGroupForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

        def __init__(self, choices = None, *args, **kwargs):
            super(ManagerGroupAdmin.UserProfileinManagerGroupForm, self).__init__(*args, **kwargs)
            if choices is not None:
                self.choices = choices
                self.fields['users'] = forms.ModelMultipleChoiceField(self.choices)

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

    def add_user_to_manager_group(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled adding users to the manager group.'))
                return
            elif 'add_user_profile_to_manager_group' in request.POST:
                objs_up = UserProfile.objects.all()
                form = self.UserProfileinManagerGroupForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            userprofile.user.groups.add(obj)
                    self.message_user(request, _('Successfully added users to manager group.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.all()
                form = self.UserProfileinManagerGroupForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
            
            return render_to_response('accounts/add_user_profile_to_manager_group.html',
                                      {
                                       'selected_managergroups': queryset,
                                       'form': form,
                                       'path':request.get_full_path()
                                      },
                                      context_instance=RequestContext(request))
        else:
            self.message_user(request,
                _('You need to be a superuser to add a user to this manager group.'))
            return HttpResponseRedirect(request.get_full_path())

    add_user_to_manager_group.short_description = _("Add users to selected manager groups")

    def remove_user_from_manager_group(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled removing users from the manager group.'))
                return
            elif 'remove_user_profile_from_manager_group' in request.POST:
                objs_up = UserProfile.objects.all()
                form = self.UserProfileinManagerGroupForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            userprofile.user.groups.remove(obj)
                    self.message_user(request, _('Successfully removed users from manager group.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.all()                    
                form = self.UserProfileinManagerGroupForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
            return render_to_response('accounts/remove_user_profile_from_manager_group.html',
                                      {
                                       'selected_managergroups': queryset,
                                       'form': form,
                                       'path':request.get_full_path()
                                      },
                                      context_instance=RequestContext(request))
        else:
            self.message_user(request,
                _('You need to be a superuser to remove a user to this manager group.'))
            return HttpResponseRedirect(request.get_full_path())

    remove_user_from_manager_group.short_description = _("Remove users from selected manager groups")


admin.site.register(RegistrationRequest, RegistrationRequestAdmin)
admin.site.register(ResetRequest, ResetRequestAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(EditorGroup, EditorGroupAdmin)
admin.site.register(EditorRegistrationRequest, EditorRegistrationRequestAdmin)
admin.site.register(ManagerGroup, ManagerGroupAdmin)
