from django import forms
from django.contrib import admin, messages
from django.contrib.admin.options import csrf_protect_m
from django.contrib.auth.models import Permission, Group, User
from django.db import transaction
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django.template.loader import render_to_string

from metashare.accounts.forms import EditorGroupForm, OrganizationForm, \
  OrganizationManagersForm, EditorGroupManagersForm
from metashare.accounts.models import RegistrationRequest, ResetRequest, \
  UserProfile, EditorGroup, EditorGroupApplication, EditorGroupManagers, \
  Organization, OrganizationApplication, OrganizationManagers
from metashare.utils import create_breadcrumb_template_params


class RegistrationRequestAdmin(admin.ModelAdmin):
    """
    Administration interface for user registration requests.
    """
    list_display = ('user',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
                     'user__email')


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
    list_display = ('user', 'modified', 'birthdate', 'affiliation', 'position',
      'homepage', '_editor_group_display', '_managed_editor_groups_display',
      '_organization_display', '_managed_organizations_display')
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

    def _managed_editor_groups_display(self, obj):
        """
        Returns a string representing a list of the editor groups that the user
        manages.
        """
        return ', '.join([mgr_group.managed_group.name for mgr_group
            in EditorGroupManagers.objects.filter(name__in=
                            obj.user.groups.values_list('name', flat=True))])

    _managed_editor_groups_display.short_description = \
        _('Managed Editor Groups')

    def _organization_display(self, obj):
        """
        Returns a string representing a list of the the organizations of a user
        profile.
        """
        return ', '.join([organization.name for organization
            in Organization.objects.filter(name__in=
                            obj.user.groups.values_list('name', flat=True))])

    _organization_display.short_description = _('Organizations')

    def _managed_organizations_display(self, obj):
        """
        Returns a string representing a list of the organization that the user
        manages.
        """
        return ', '.join([org_mgr_group.managed_organization.name
                for org_mgr_group in OrganizationManagers.objects.filter(
                    name__in=obj.user.groups.values_list('name', flat=True))])

    _managed_organizations_display.short_description = \
        _('Managed organizations')


class EditorGroupAdmin(admin.ModelAdmin):
    """
    Administration interface for `EditorGroup`s.
    """
    list_display = ('name', '_members_display', '_managing_group_display',
                    '_managers_display')
    search_fields = ('name',)
    actions = ('add_user_to_editor_group', 'remove_user_from_editor_group', )
    form = EditorGroupForm

    def _members_display(self, obj):
        """
        Returns a string representing a list of the members of the given
        `EditorGroup` object.
        """
        return ', '.join(member.username for member in obj.get_members())

    _members_display.short_description = _('Members')
    
    def _managing_group_display(self, obj):
        """
        Returns a string representing a list of the managing groups of the
        given `EditorGroup` object.
        """
        return ', '.join(mgr_group.name for mgr_group
                         in EditorGroupManagers.objects.filter(managed_group=obj))

    _managing_group_display.short_description = _('Managing groups')
    
    def _managers_display(self, obj):
        """
        Returns a string representing a list of the managers of the given
        `EditorGroup`.
        """
        return ', '.join(usr.username
            for mgr_group in EditorGroupManagers.objects.filter(managed_group=obj)
            for usr in User.objects.filter(groups__name=mgr_group.name))

    _managers_display.short_description = _('Managers')

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
            # request `QueryDict`s are immutable; create a copy before updating
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
        return queryset.filter(editorgroupmanagers__in=EditorGroupManagers.objects.filter(
                name__in=request.user.groups.values_list('name', flat=True)))

    def add_user_to_editor_group(self, request, queryset):
        form = None
        if 'cancel' in request.POST:
            self.message_user(request, _('Cancelled adding users to the editor group.'))
            return
        elif 'add_user_profile_to_editor_group' in request.POST:
            objs_up = UserProfile.objects.filter(user__is_active=True)
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
            userprofiles = UserProfile.objects.filter(user__is_active=True)
            form = self.UserProfileinEditorGroupForm(choices=userprofiles,
                initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
        dictionary = {'title': _('Add Users to Editor Group'),
                      'selected_editorgroups': queryset,
                      'form': form,
                      'path': request.get_full_path()
                     }
        dictionary.update(create_breadcrumb_template_params(self.model, _('Add user')))
        
        return render_to_response('accounts/add_user_profile_to_editor_group.html',
                                  dictionary,
                                  context_instance=RequestContext(request))

    add_user_to_editor_group.short_description = _("Add users to selected editor groups")

    def remove_user_from_editor_group(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled removing users from the editor group.'))
                return
            elif 'remove_user_profile_from_editor_group' in request.POST:
                objs_up = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinEditorGroupForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            userprofile.user.groups.remove(obj)
                    self.message_user(request, _('Successfully removed users from editor group.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinEditorGroupForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
            dictionary = {'title': _('Remove Users from Editor Group'),
                          'selected_editorgroups': queryset,
                          'form': form,
                          'path': request.get_full_path()
                         }
            dictionary.update(create_breadcrumb_template_params(self.model, _('Remove user')))
        
            return render_to_response('accounts/remove_user_profile_from_editor_group.html',
                                      dictionary,
                                      context_instance=RequestContext(request))

    remove_user_from_editor_group.short_description = _("Remove users from selected editor groups")


class EditorGroupApplicationAdmin(admin.ModelAdmin):
    """
    Administration interface for user editor group application.
    """
    list_display = ('user', 'editor_group', 'created')
    actions = ('accept_selected', 'delete_selected')

    def accept_selected(self, request, queryset):
        """
        The action to accept editor group applications.
        """
        if not request.user.is_superuser and \
                not request.user.get_profile().has_manager_permission():
            messages.error(request,
                _('You must be superuser or group manager to accept applications.'))
            return HttpResponseRedirect(request.get_full_path())
        if queryset.count() == 0:
            return HttpResponseRedirect(request.get_full_path())

        _total_groups = 0
        _accepted_groups = 0
        for req in queryset:
            _total_groups += 1

            if request.user.get_profile().has_manager_permission(
                    req.editor_group) or request.user.is_superuser:
                req.user.groups.add(req.editor_group)
                req.delete()
                _accepted_groups += 1
                # if the applying user is not a staff user, yet, then we have
                # to make sure that she becomes a staff user for being an editor
                if not req.user.is_staff:
                    req.user.is_staff = True
                    req.user.save()

                # Render notification email template with correct values.
                data = {'editor_group': req.editor_group,
                  'shortname': req.user.get_full_name() }
                try:
                    # Send out notification email to the user
                    send_mail('Application accepted',
                      render_to_string('accounts/notification_editor_group_application_accepted.email', data),
                      'no-reply@meta-share.eu', (req.user.email,),
                      fail_silently=False)
                except: #SMTPException:
                    # If the email could not be sent successfully, tell the user
                    # about it.
                    messages.error(request, _("There was an error sending " \
                                   "out an application acceptance e-mail."))
                else:
                    messages.success(request, _('You have successfully ' \
                        'accepted "%s" as member of the editor group "%s".')
                            % (req.user.get_full_name(), req.editor_group,))

        if _total_groups != _accepted_groups:
            messages.warning(request, _('Successfully accepted %(accepted)d of '
                '%(total)d applications. You have no permissions to accept the '
                'remaining applications.') % {'accepted': _accepted_groups,
                                          'total': _total_groups})
        else:
            messages.success(request,
                             _('Successfully accepted all requests.'))
            return HttpResponseRedirect(request.get_full_path())

    accept_selected.short_description = \
        _("Accept selected editor group applications")

    def get_readonly_fields(self, request, obj=None):
        """
        Return the list of fields to be in readonly mode.
        
        Managers cannot modify applications, they can only add them or delete them.
        """
        if not request.user.is_superuser:
            # for non-superusers no part of the group application is editable
            return [field.name for field
                    in EditorGroupApplication._meta.fields]
        return super(EditorGroupApplicationAdmin, self) \
            .get_readonly_fields(request, obj)

    def queryset(self, request):
        result = super(EditorGroupApplicationAdmin, self).queryset(request)
        if request.user.is_superuser:
            return result
        # non-superusers may only see the applications that they may also handle
        return result.filter(editor_group__name__in=
                             request.user.groups.values_list('name', flat=True))

    # pylint: disable-msg=W0622
    def log_deletion(self, request, obj, object_repr):
        """
        When an application is turned down by a manager, send an email to the user before
        logging the deletion
        """
        # Render notification email template with correct values.
        data = {'editor_group': obj.editor_group,
          'shortname': obj.user.get_full_name() }
        try:
            # Send out notification email to the user
            send_mail('Application turned down', render_to_string('accounts/'
                            'notification_editor_group_application_turned_down.email', data),
                'no-reply@meta-share.eu', (obj.user.email,),
                fail_silently=False)
        except: #SMTPException:
            # If the email could not be sent successfully, tell the user
            # about it.
            messages.error(request, _("There was an error sending out an "
                           "e-mail about turning down the application."))
        else:
            messages.success(request, _('You have successfully turned down "%s" ' \
              'from the editor group "%s".') % (obj.user.get_full_name(),
                                                obj.editor_group,))

        super(EditorGroupApplicationAdmin, self).log_deletion(request, obj, object_repr)        

    def delete_selected(self, request, queryset):
        """
        The action to turn down editor group applications.
        """
        from django import template
        from django.contrib.admin.util import get_deleted_objects, model_ngettext
        from django.contrib.admin import helpers
        from django.db import router
        from django.utils.encoding import force_unicode
        from django.core.exceptions import PermissionDenied

        opts = self.model._meta
        app_label = opts.app_label
    
        # Check that the user has delete permission for the actual model
        if not self.has_delete_permission(request):
            raise PermissionDenied
    
        using = router.db_for_write(self.model)
    
        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, self.admin_site, using)
    
        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if request.POST.get('post'):
            if perms_needed:
                raise PermissionDenied
            n_count = queryset.count()
            if n_count:
                for obj in queryset:
                    obj_display = force_unicode(obj)
                    self.log_deletion(request, obj, obj_display)
                queryset.delete()
                self.message_user(request, _("Successfully turned down %(count)d %(items)s.") % {
                    "count": n_count, "items": model_ngettext(self.opts, n_count)
                })
            # Return None to display the change list page again.
            return None
    
        if len(queryset) == 1:
            objects_name = force_unicode(opts.verbose_name)
        else:
            objects_name = force_unicode(opts.verbose_name_plural)
    
        if perms_needed or protected:
            title = _("Cannot turn down %(name)s") % {"name": objects_name}
        else:
            title = _("Are you sure?")
    
        context = {
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "root_path": self.admin_site.root_path,
            "app_label": app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }
    
        # Display the confirmation page
        return render_to_response("accounts/delete_editor_group_application_selected_confirmation.html", \
          context, context_instance=template.RequestContext(request))

    delete_selected.short_description = \
        _("Turn down selected editor group applications")

class EditorGroupManagersAdmin(admin.ModelAdmin):
    """
    Administration interface for `EditorGroupManagers`s.
    """
    list_display = ('name', 'managed_group', '_members_display')
    search_fields = ('name', 'managed_group')
    actions = ('add_user_to_editor_group_managers', 'remove_user_from_editor_group_managers', )
    form = EditorGroupManagersForm

    def _members_display(self, obj):
        """
        Returns a string representing a list of the members of the given
        `EditorGroupManagers` object.
        """
        return ', '.join(member.username for member in obj.get_members())

    _members_display.short_description = _('Members')

    class UserProfileinEditorGroupManagersForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

        def __init__(self, choices = None, *args, **kwargs):
            super(EditorGroupManagersAdmin.UserProfileinEditorGroupManagersForm, self).__init__(*args, **kwargs)
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
        # model permissions for deleting language resources and for changing and
        # deleting editor group application requests
        if request.method == 'GET':
            # request `QueryDict`s are immutable; create a copy before updating
            request.GET = request.GET.copy()
            request.GET.update({'permissions': ','.join(str(_perm.pk) for _perm
                    in EditorGroupManagersAdmin.get_suggested_manager_permissions())})
        return super(EditorGroupManagersAdmin, self).add_view(request,
                                form_url=form_url, extra_context=extra_context)

    @staticmethod
    def get_suggested_manager_permissions():
        """
        Returns a list of `Permission`s that all `EditorGroupManagers`s should have.
        """
        result = []
        # add language resource delete permission
        from metashare.repository.models import resourceInfoType_model
        opts = resourceInfoType_model._meta
        result.append(Permission.objects.filter(
                content_type__app_label=opts.app_label,
                codename=opts.get_delete_permission())[0])
        # add editor group application request change/delete permission
        opts = EditorGroupApplication._meta
        result.append(Permission.objects.filter(
                content_type__app_label=opts.app_label,
                codename=opts.get_change_permission())[0])
        result.append(Permission.objects.filter(
                content_type__app_label=opts.app_label,
                codename=opts.get_delete_permission())[0])
        return result

    def add_user_to_editor_group_managers(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled adding users to the editor group managers.'))
                return
            elif 'add_user_profile_to_editor_group_managers' in request.POST:
                objs_up = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinEditorGroupManagersForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            userprofile.user.groups.add(obj)
                    self.message_user(request, _('Successfully added users to editor group managers.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinEditorGroupManagersForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
            
            dictionary = {'title': _('Add Users to Editor Group Managers'),
                          'selected_editorgroupmanagers': queryset,
                          'form': form,
                          'path': request.get_full_path()
                         }
            dictionary.update(create_breadcrumb_template_params(self.model, _('Add user')))
        
            return render_to_response('accounts/add_user_profile_to_editor_group_managers.html',
                                      dictionary,
                                      context_instance=RequestContext(request))
        else:
            self.message_user(request, _('You need to be a superuser to add ' \
                                    'a user to these editor group managers.'))
            return HttpResponseRedirect(request.get_full_path())

    add_user_to_editor_group_managers.short_description = _("Add users to selected editor group managers")

    def remove_user_from_editor_group_managers(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled removing users from ' \
                                             'editor group managers.'))
                return
            elif 'remove_user_profile_from_editor_group_managers' in request.POST:
                objs_up = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinEditorGroupManagersForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            userprofile.user.groups.remove(obj)
                    self.message_user(request, _('Successfully removed users ' \
                                                 'from editor group managers.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.filter(user__is_active=True)                    
                form = self.UserProfileinEditorGroupManagersForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
            dictionary = {'title': _('Remove Users from Editor Group Managers'),
                          'selected_editorgroupmanagers': queryset,
                          'form': form,
                          'path': request.get_full_path()
                         }
            dictionary.update(create_breadcrumb_template_params(self.model, _('Remove user')))
        
            return render_to_response('accounts/remove_user_profile_from_editor_group_managers.html',
                                      dictionary,
                                      context_instance=RequestContext(request))
        else:
            self.message_user(request, _('You need to be a superuser to ' \
                            'remove a user from these editor group managers.'))
            return HttpResponseRedirect(request.get_full_path())

    remove_user_from_editor_group_managers.short_description = _("Remove users from selected editor group managers")


class OrganizationAdmin(admin.ModelAdmin):
    """
    Administration interface for `Organization`s.
    """
    list_display = ('name', '_members_display', '_organization_managing_group_display',
                    '_organization_managers_display')
    search_fields = ('name',)
    actions = ('add_user_to_organization', 'remove_user_from_organization', )
    form = OrganizationForm

    def _members_display(self, obj):
        """
        Returns a string representing a list of the members of the given
        `Organization` object.
        """
        return ', '.join(member.username for member in obj.get_members())

    _members_display.short_description = _('Members')
    
    def _organization_managing_group_display(self, obj):
        """
        Returns a string representing a list of the organization managing groups of the
        given `Organization` object.
        """
        return ', '.join(org_mgr_group.name for org_mgr_group
                         in OrganizationManagers.objects.filter(managed_organization=obj))

    _organization_managing_group_display.short_description = _('Managing groups')
    
    def _organization_managers_display(self, obj):
        """
        Returns a string representing a list of the managers of the given
        `Organization`.
        """
        return ', '.join(usr.username
            for org_mgr_group in OrganizationManagers.objects.filter(managed_organization=obj)
            for usr in User.objects.filter(groups__name=org_mgr_group.name))

    _organization_managers_display.short_description = _('Managers')

    class UserProfileinOrganizationForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

        def __init__(self, choices = None, *args, **kwargs):
            super(OrganizationAdmin.UserProfileinOrganizationForm, self).__init__(*args, **kwargs)
            if choices is not None:
                self.choices = choices
                self.fields['users'] = forms.ModelMultipleChoiceField(self.choices)

    def queryset(self, request):
        queryset = super(OrganizationAdmin, self).queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(organizationmanagers__in=OrganizationManagers.objects.filter(
                name__in=request.user.groups.values_list('name', flat=True)))

    def add_user_to_organization(self, request, queryset):
        form = None
        if 'cancel' in request.POST:
            self.message_user(request, _('Cancelled adding users to the organization.'))
            return
        elif 'add_user_profile_to_organization' in request.POST:
            objs_up = UserProfile.objects.filter(user__is_active=True)
            form = self.UserProfileinOrganizationForm(objs_up, request.POST)
            if form.is_valid():
                userprofiles = form.cleaned_data['users']
                for userprofile in userprofiles:
                    for obj in queryset:
                        if UserProfile.objects.filter(user=request.user)[0].has_organization_manager_permission(obj):
                            userprofile.user.groups.add(obj)
                        else:
                            self.message_user(request,
                                _('You need to be organization managers to add a user to this organization.'))
                            return HttpResponseRedirect(request.get_full_path())
                self.message_user(request, _('Successfully added users to organization.'))
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            userprofiles = UserProfile.objects.filter(user__is_active=True)
            form = self.UserProfileinOrganizationForm(choices=userprofiles,
                initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
            dictionary = {'title': _('Add Users to Organization'),
                          'selected_organizations': queryset,
                          'form': form,
                          'path': request.get_full_path()
                         }
            dictionary.update(create_breadcrumb_template_params(self.model, _('Add user')))
        
        return render_to_response('accounts/add_user_profile_to_organization.html',
                                  dictionary,
                                  context_instance=RequestContext(request))

    add_user_to_organization.short_description = _("Add users to selected organizations")

    def remove_user_from_organization(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled removing users from the organization.'))
                return
            elif 'remove_user_profile_from_organization' in request.POST:
                objs_up = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinOrganizationForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            userprofile.user.groups.remove(obj)
                    self.message_user(request, _('Successfully removed users from organization.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinOrganizationForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
            dictionary = {'title': _('Remove Users from Organization'),
                          'selected_organizations': queryset,
                          'form': form,
                          'path': request.get_full_path()
                         }
            dictionary.update(create_breadcrumb_template_params(self.model, _('Remove user')))
        
            return render_to_response('accounts/remove_user_profile_from_organization.html',
                                      dictionary,
                                      context_instance=RequestContext(request))

    remove_user_from_organization.short_description = _("Remove users from selected organizations")


class OrganizationApplicationAdmin(admin.ModelAdmin):
    """
    Administration interface for user organization application.
    """
    list_display = ('user', 'organization', 'created')
    actions = ('accept_selected', 'delete_selected')

    def accept_selected(self, request, queryset):
        """
        The action to accept organization applications.
        """
        if not request.user.is_superuser and \
                not request.user.get_profile().has_organization_manager_permission():
            messages.error(request,
                _('You must be superuser or organization manager to accept applications.'))
            return HttpResponseRedirect(request.get_full_path())
        if queryset.count() == 0:
            return HttpResponseRedirect(request.get_full_path())

        _total_groups = 0
        _accepted_groups = 0
        for req in queryset:
            _total_groups += 1

            if request.user.get_profile().has_organization_manager_permission(
                    req.organization) or request.user.is_superuser:
                req.user.groups.add(req.organization)
                req.delete()
                _accepted_groups += 1

                # Render notification email template with correct values.
                data = {'organization': req.organization,
                  'shortname': req.user.get_full_name() }
                try:
                    # Send out notification email to the user
                    send_mail('Application accepted',
                      render_to_string('accounts/notification_organization_application_accepted.email', data),
                      'no-reply@meta-share.eu', (req.user.email,),
                      fail_silently=False)
                except: #SMTPException:
                    # If the email could not be sent successfully, tell the user
                    # about it.
                    messages.error(request, _("There was an error sending " \
                                   "out an application acceptance e-mail."))
                else:
                    messages.success(request, _('You have successfully ' \
                          'accepted "%s" as member of the organization "%s".')
                              % (req.user.get_full_name(), req.organization,))

        if _total_groups != _accepted_groups:
            messages.warning(request, _('Successfully accepted %(accepted)d of '
                '%(total)d applications. You have no permissions to accept the '
                'remaining applications.') % {'accepted': _accepted_groups,
                                          'total': _total_groups})
        else:
            messages.success(request,
                             _('Successfully accepted all requests.'))
            return HttpResponseRedirect(request.get_full_path())

    accept_selected.short_description = \
        _("Accept selected organization applications")

    def get_readonly_fields(self, request, obj=None):
        """
        Return the list of fields to be in readonly mode.
        
        Organization managers cannot modify applications, they can only add them or delete them.
        """
        if not request.user.is_superuser:
            # for non-superusers no part of the organization application is editable
            return [field.name for field
                    in OrganizationApplication._meta.fields]
        return super(OrganizationApplicationAdmin, self) \
            .get_readonly_fields(request, obj)

    # pylint: disable-msg=W0622
    def log_deletion(self, request, obj, object_repr):
        """
        When an application is turned down by an organization manager, send an email to the user before
        logging the deletion
        """
        # Render notification email template with correct values.
        data = {'organization': obj.organization,
          'shortname': obj.user.get_full_name() }
        try:
            # Send out notification email to the user
            send_mail('Application turned down', render_to_string('accounts/'
                            'notification_organization_application_turned_down.email', data),
                'no-reply@meta-share.eu', (obj.user.email,),
                fail_silently=False)
        except: #SMTPException:
            # If the email could not be sent successfully, tell the user
            # about it.
            messages.error(request, _("There was an error sending out an "
                           "e-mail about turning down the application."))
        else:
            messages.success(request, _('You have turned down the application' \
                    ' of "%s" for membership in the organization "%s".')
                            % (obj.user.get_full_name(), obj.organization,))

        super(OrganizationApplicationAdmin, self).log_deletion(request, obj, object_repr)        

    def delete_selected(self, request, queryset):
        """
        The action to turn down organization applications.
        """
        from django import template
        from django.contrib.admin.util import get_deleted_objects, model_ngettext
        from django.contrib.admin import helpers
        from django.db import router
        from django.utils.encoding import force_unicode
        from django.core.exceptions import PermissionDenied

        opts = self.model._meta
        app_label = opts.app_label
    
        # Check that the user has delete permission for the actual model
        if not self.has_delete_permission(request):
            raise PermissionDenied
    
        using = router.db_for_write(self.model)
    
        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, self.admin_site, using)
    
        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if request.POST.get('post'):
            if perms_needed:
                raise PermissionDenied
            n_count = queryset.count()
            if n_count:
                for obj in queryset:
                    obj_display = force_unicode(obj)
                    self.log_deletion(request, obj, obj_display)
                queryset.delete()
                self.message_user(request, _("Successfully turned down %(count)d %(items)s.") % {
                    "count": n_count, "items": model_ngettext(self.opts, n_count)
                })
            # Return None to display the change list page again.
            return None
    
        if len(queryset) == 1:
            objects_name = force_unicode(opts.verbose_name)
        else:
            objects_name = force_unicode(opts.verbose_name_plural)
    
        if perms_needed or protected:
            title = _("Cannot turn down %(name)s") % {"name": objects_name}
        else:
            title = _("Are you sure?")
    
        context = {
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "root_path": self.admin_site.root_path,
            "app_label": app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }
    
        # Display the confirmation page
        return render_to_response("accounts/delete_organization_application_selected_confirmation.html", \
          context, context_instance=template.RequestContext(request))

    delete_selected.short_description = \
        _("Turn down selected organization applications")


class OrganizationManagersAdmin(admin.ModelAdmin):
    """
    Administration interface for `OrganizationManagers`s.
    """
    list_display = ('name', 'managed_organization', '_members_display')
    search_fields = ('name', 'managed_organization')
    actions = ('add_user_to_organization_managers', 'remove_user_from_organization_managers', )
    form = OrganizationManagersForm

    def _members_display(self, obj):
        """
        Returns a string representing a list of the members of the given
        `OrganizationManagers` object.
        """
        return ', '.join(member.username for member in obj.get_members())

    _members_display.short_description = _('Members')

    class UserProfileinOrganizationManagersForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

        def __init__(self, choices = None, *args, **kwargs):
            super(OrganizationManagersAdmin.UserProfileinOrganizationManagersForm, self).__init__(*args, **kwargs)
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
        # model permissions for deleting language resources and for changing and
        # deleting organization application requests
        if request.method == 'GET':
            # request `QueryDict`s are immutable; create a copy before upadating
            request.GET = request.GET.copy()
            request.GET.update({'permissions': ','.join(str(_perm.pk) for _perm
                    in OrganizationManagersAdmin.get_suggested_organization_manager_permissions())})
        return super(OrganizationManagersAdmin, self).add_view(request,
                                form_url=form_url, extra_context=extra_context)

    @staticmethod
    def get_suggested_organization_manager_permissions():
        """
        Returns a list of `Permission`s that all `OrganizationManagers`s should
        have.
        """
        result = []
        # add organization application request change/delete permission
        opts = OrganizationApplication._meta
        result.append(Permission.objects.filter(
                content_type__app_label=opts.app_label,
                codename=opts.get_change_permission())[0])
        result.append(Permission.objects.filter(
                content_type__app_label=opts.app_label,
                codename=opts.get_delete_permission())[0])
        return result

    def add_user_to_organization_managers(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled adding users to the organization managers.'))
                return
            elif 'add_user_profile_to_organization_managers' in request.POST:
                objs_up = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinOrganizationManagersForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        user = userprofile.user
                        for obj in queryset:
                            user.groups.add(obj)
                            user.groups.add(obj.managed_organization)
                    self.message_user(request, _('Successfully added users to organization managers.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinOrganizationManagersForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
            
            dictionary = {'title': _('Add Users to Organization Manager Group'),
                          'selected_organizationmanagers': queryset,
                          'form': form,
                          'path': request.get_full_path()
                         }
            dictionary.update(create_breadcrumb_template_params(self.model, _('Add user')))
        
            return render_to_response('accounts/add_user_profile_to_organization_managers.html',
                                      dictionary,
                                      context_instance=RequestContext(request))
        else:
            self.message_user(request, _('You need to be a superuser to add ' \
                                    'a user to these organization managers.'))
            return HttpResponseRedirect(request.get_full_path())

    add_user_to_organization_managers.short_description = _("Add users to selected organization managers")

    def remove_user_from_organization_managers(self, request, queryset):
        form = None
        if request.user.is_superuser:
            if 'cancel' in request.POST:
                self.message_user(request, _('Cancelled removing users from the organization managers.'))
                return
            elif 'remove_user_profile_from_organization_managers' in request.POST:
                objs_up = UserProfile.objects.filter(user__is_active=True)
                form = self.UserProfileinOrganizationManagersForm(objs_up, request.POST)
                if form.is_valid():
                    userprofiles = form.cleaned_data['users']
                    for userprofile in userprofiles:
                        for obj in queryset:
                            userprofile.user.groups.remove(obj)
                    self.message_user(request, _('Successfully removed users from organization managers.'))
                    return HttpResponseRedirect(request.get_full_path())
    
            if not form:
                userprofiles = UserProfile.objects.filter(user__is_active=True)                    
                form = self.UserProfileinOrganizationManagersForm(choices=userprofiles,
                    initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
            dictionary = {'title':
                            _('Remove Users from Organization Manager Group'),
                          'selected_organizationmanagers': queryset,
                          'form': form,
                          'path': request.get_full_path()
                         }
            dictionary.update(create_breadcrumb_template_params(self.model, _('Remove user')))
        
            return render_to_response('accounts/remove_user_profile_from_organization_managers.html',
                                      dictionary,
                                      context_instance=RequestContext(request))
        else:
            self.message_user(request, _('You need to be a superuser to ' \
                            'remove a user from these organization managers.'))
            return HttpResponseRedirect(request.get_full_path())

    remove_user_from_organization_managers.short_description = _("Remove users from selected organization managers")


admin.site.register(RegistrationRequest, RegistrationRequestAdmin)
admin.site.register(ResetRequest, ResetRequestAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(EditorGroup, EditorGroupAdmin)
admin.site.register(EditorGroupApplication, EditorGroupApplicationAdmin)
admin.site.register(EditorGroupManagers, EditorGroupManagersAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(OrganizationApplication, OrganizationApplicationAdmin)
admin.site.register(OrganizationManagers, OrganizationManagersAdmin)
