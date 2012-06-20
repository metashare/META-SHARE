"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django import forms
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.contrib.auth.models import Permission, Group
from django.db import transaction
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect

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
      'position', 'homepage', 'editor_group', 'manager_group')
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
      'birthdate', 'affiliation', 'position', 'homepage')

class EditorGroupAdmin(admin.ModelAdmin):
    """
    Administration interface for `EditorGroup`s.
    """
    list_display = ('name', 'get_users', 'get_managers')
    search_fields = ('name',)
    actions = ('add_user_profile_to_editor_group', 'remove_user_profile_from_editor_group', )

    class AddUserProfiletoEditorGroupForm(forms.Form):
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            
            def __init__(self, choices = None, *args, **kwargs):
                super(forms.Form, self).__init__(*args, **kwargs)
                if choices is not None:
                    self.choices = choices
                    self.fields['user profiles'] = forms.ModelMultipleChoiceField(self.choices)
    
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
        qs = super(EditorGroupAdmin, self).queryset(request)

        if request.user.is_superuser:
            return qs

        user_qs = UserProfile.objects.filter(user=request.user)
        mg_user = user_qs[0].managergroup.all()
        return qs.filter(managergroup__in=mg_user)

    def add_user_profile_to_editor_group(self, request, queryset):
            form = None
            if 'cancel' in request.POST:
                self.message_user(request, 'Cancelled adding user profiles to the editor group.')
                return
            elif 'add_user_profile_to_editor_group' in request.POST:
                q = UserProfile.objects.all()
                form = self.AddUserProfiletoEditorGroupForm(q, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['user profiles']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            if UserProfile.objects.filter(user=request.user)[0].has_editor_group_add_user_permission(obj):
                                userprofile.editorgroup.add(obj)
                            else:
                                self.message_user(request, 'You need to be group manager to add a user to this editor group.')
                                return HttpResponseRedirect(request.get_full_path())
                    self.message_user(request, 'Successfully added user profiles to editor group.')
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
               userprofiles = UserProfile.objects.all()
               form = self.AddUserProfiletoEditorGroupForm(choices=userprofiles, initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
            
            return render_to_response('accounts/add_user_profile_to_editor_group.html', \
                                      {'selected_editorgroups': queryset, 'form': form, 'path':request.get_full_path()}, \
                                      context_instance=RequestContext(request))

    add_user_profile_to_editor_group.short_description = "Add user profiles to selected editor groups"

    def remove_user_profile_from_editor_group(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, 'Cancelled removing user profiles from the editor group.')
                return
            elif 'remove_user_profile_from_editor_group' in request.POST:
                q = UserProfile.objects.all()
                form = self.AddUserProfiletoEditorGroupForm(q, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['user profiles']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            if UserProfile.objects.filter(user=request.user)[0].has_editor_group_add_user_permission(obj):
                                userprofile.editorgroup.remove(obj)
                            else:
                                self.message_user(request, 'You need to be group manager to remove a user from this editor group.')
                                return HttpResponseRedirect(request.get_full_path())
                    self.message_user(request, 'Successfully remove user profiles from editor group.')
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.all()                    
                form = self.AddUserProfiletoEditorGroupForm(choices=userprofiles, initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
            return render_to_response('accounts/remove_user_profile_from_editor_group.html', \
                                      {'selected_editorgroups': queryset, 'form': form, 'path':request.get_full_path()}, \
                                      context_instance=RequestContext(request))

    remove_user_profile_from_editor_group.short_description = "Remove user profiles from selected editor groups"

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
