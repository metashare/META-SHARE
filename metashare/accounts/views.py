"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging
from smtplib import SMTPException

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from metashare.accounts.forms import RegistrationRequestForm, ResetRequestForm, \
    UserProfileForm, EditorGroupApplicationForm, AddDefaultEditorGroupForm, \
    RemoveDefaultEditorGroupForm, OrganizationApplicationForm
from metashare.accounts.models import RegistrationRequest, ResetRequest, \
    EditorGroupApplication, EditorGroupManagers, EditorGroup, \
    OrganizationApplication, OrganizationManagers, Organization
from metashare.settings import DJANGO_URL, LOG_LEVEL, LOG_HANDLER


# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.accounts.views')
LOGGER.addHandler(LOG_HANDLER)


def confirm(request, uuid):
    """
    Confirms the user account request for the given user id.
    """
    # Loads the RegistrationRequest instance for the given uuid.
    registration_request = get_object_or_404(RegistrationRequest, uuid=uuid)

    # Activate the corresponding User instance.
    user = registration_request.user
    user.is_active = True
    # For convenience, log user in:
    # (We would actually have to authenticate the user before logging in,
    # however, as we don't know the password, we manually set the authenication
    # backend.)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    user.save()
    login(request, user)

    # Delete registration request instance.
    registration_request.delete()

    # Render activation email template with correct values.
    data = {'firstname': user.first_name, 'lastname': user.last_name,
      'shortname': user.username}
    email = render_to_string('accounts/activation.email', data)
    try:
        # Send an activation email.
        send_mail('Your META-SHARE user account has been activated',
        email, 'no-reply@meta-share.eu', [user.email], fail_silently=False)
    except: # SMTPException:
        # there was a problem sending the activation e-mail -- not too bad
        pass

    # Add a message to the user after successful creation.
    messages.success(request, "We have activated your user account.")
    
    # Redirect the user to the front page.
    return redirect('metashare.views.frontpage')


def create(request):
    """
    Creates a new user account request from a new user.
    """
    # Check if the creation form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = RegistrationRequestForm(request.POST)
        
        # Check if the form has validated successfully.
        if form.is_valid():
            # Create a new (inactive) User account so that we can discard the
            # plain text password. This will also create a corresponding
            # `UserProfile` instance by post_save "magic".
            _user = User.objects.create_user(form.cleaned_data['shortname'],
                form.cleaned_data['email'], form.cleaned_data['password'])
            _user.first_name = form.cleaned_data['first_name']
            _user.last_name = form.cleaned_data['last_name']
            _user.is_active = False
            _user.save()
            # Create new RegistrationRequest instance.
            new_object = RegistrationRequest(user=_user)
            # Save new RegistrationRequest instance to django database.
            new_object.save()
            
            # Render confirmation email template with correct values.
            data = {'firstname': _user.first_name,
              'lastname': _user.last_name,
              'shortname': _user.username, 'node_url': DJANGO_URL,
              'confirmation_url': '{0}/accounts/confirm/{1}/'.format(
                DJANGO_URL, new_object.uuid)}
            email = render_to_string('accounts/confirmation.email', data)
            
            try:
                # Send out confirmation email to the given email address.
                send_mail('Please confirm your META-SHARE user account',
                email, 'no-reply@meta-share.eu', [_user.email],
                fail_silently=False)
            except: #SMTPException:
                # If the email could not be sent successfully, tell the user
                # about it and also give the confirmation URL.
                messages.error(request,
                  "There was an error sending out the confirmation email " \
                  "for your registration account.  You can confirm your " \
                  "account by <a href='{0}'>clicking here</a>.".format(
                    data['confirmation_url']))
                
                # Redirect the user to the front page.
                return redirect('metashare.views.frontpage')
            
            # Add a message to the user after successful creation.
            messages.success(request,
              "We have received your registration data and sent you an " \
              "email with further activation instructions.")
            
            # Redirect the user to the front page.
            return redirect('metashare.views.frontpage')
    
    # Otherwise, create an empty RegistrationRequestForm instance.
    else:
        form = RegistrationRequestForm()
    
    dictionary = {'title': 'Create Account', 'form': form}
    return render_to_response('accounts/create_account.html', dictionary,
      context_instance=RequestContext(request))


@login_required
def edit_profile(request):
    """
    Edits user account profile for the logged in user.
    """
    # Get UserProfile instance corresponding to the current user.
    profile = request.user.get_profile()

    # Check if the edit form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = UserProfileForm(request.POST)
        
        # Check if the form has validated successfully.
        if form.is_valid():

            # Loop over all editable fields and check for updates.
            _profile_requires_save = False
            for __field__ in profile.__editable_fields__:
                # Check if the form contains new data for the current field.
                if form.cleaned_data.has_key(__field__):
                    _value = form.cleaned_data.get(__field__)
                    
                    # If field data has changed, update the field.
                    if _value != getattr(profile, __field__):
                        _profile_requires_save = True
                        setattr(profile, __field__, _value)
            
            # Check if the profile needs to saved.
            if _profile_requires_save:
                profile.save()
                
                # Add a message to the user after successful creation.
                messages.success(request,
                  "You have successfully updated your profile information.")
            
            # Redirect the user to the front page.
            return redirect('metashare.views.frontpage')
    
    # Otherwise, fill UserProfileForm instance from current UserProfile.
    else:
        form = UserProfileForm({'birthdate': profile.birthdate,
          'affiliation': profile.affiliation, 'position': profile.position,
          'homepage': profile.homepage})

    dictionary = {'title': 'Edit profile information', 'form': form, 
        'groups_applied_for': [edt_reg.editor_group.name for edt_reg
                in EditorGroupApplication.objects.filter(user=profile.user)],
        'organizations_applied_for': [org_reg.organization.name for org_reg
                in OrganizationApplication.objects.filter(user=profile.user)],
        'editor_groups_member_of': [{'name': eg.name, 'default':
                profile.default_editor_groups.filter(name=eg.name).count() != 0}
            for eg in EditorGroup.objects.filter(name__in=
                        profile.user.groups.values_list('name', flat=True))],
        'editor_group_managers_member_of': [edt_grp_mgrs.name for edt_grp_mgrs
                in EditorGroupManagers.objects.filter(name__in=profile.user.groups.values_list('name', flat=True))],
        'organizations_member_of': [orga.name for orga
                in Organization.objects.filter(name__in=profile.user.groups.values_list('name', flat=True))],
        'organization_managers_member_of': [org_mgrs.name for org_mgrs
                in OrganizationManagers.objects.filter(name__in=profile.user.groups.values_list('name', flat=True))]}
    
    return render_to_response('accounts/edit_profile.html', dictionary,
      context_instance=RequestContext(request))


@login_required
def editor_group_application(request):
    """
    Apply for Editor Groups membership.
    """
    # Exclude from the list the editor groups the user cannot apply for:
    # - editor groups for which the user is already a member
    # - editor groups for which the user has already applied
    available_editor_groups = EditorGroup.objects \
        .exclude(name__in=request.user.groups.values_list('name', flat=True)) \
        .exclude(name__in=EditorGroupApplication.objects.filter(
            user=request.user).values_list('editor_group__name', flat=True))

    # Check if the edit form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = EditorGroupApplicationForm(available_editor_groups, request.POST)
        # Check if the form has validated successfully.
        if form.is_valid():
            edt_grp = form.cleaned_data['editor_group']

            if EditorGroupApplication.objects.filter(
                    user=request.user, editor_group=edt_grp).count() != 0:
                messages.success(request, _('An older application of yours for '
                    'editor group "%s" is still pending.') % (edt_grp.name,))
            else:
                new_object = EditorGroupApplication(user=request.user,
                    editor_group=edt_grp)
                new_object.save()

                # Send a notification email to the relevant managers/superusers
                emails = []
                # Find out the relevant group managers' emails
                for manager in edt_grp.get_managers():
                    emails.append(manager.email)
                # Find out the superusers' emails
                for superuser in User.objects.filter(is_superuser=True):
                    emails.append(superuser.email)
                # Render notification email template with correct values.
                data = {'editor_group': edt_grp.name,
                  'shortname': request.user,
                  'confirmation_url': '{0}/admin/accounts/editorgroupapplication/'.format(
                    DJANGO_URL)}
                try:
                    # Send out notification email to the managers and superusers
                    send_mail('New editor membership request',
                        render_to_string('accounts/notification_editor_group_managers_application.email', data),
                        'no-reply@meta-share.eu', emails, fail_silently=False)
                except: #SMTPException:
                    # If the email could not be sent successfully, tell the user
                    # about it.
                    messages.error(request,
                      "There was an error sending out the request email " \
                      "for your editor group application.")
                else:
                    messages.success(request, _('You have successfully ' \
                        'applied for editor group "%s".') % (edt_grp.name,))

            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')

    # Otherwise, render a new EditorGroupApplicationForm instance
    else:
        # Check whether there is an editor group the user can apply for.
        if available_editor_groups.count() == 0:
            # If there is no editor group created yet, send an error message.
            messages.error(request, _('There are no editor groups in the '
                'database, yet, for which you could apply. Please ask the '
                'system administrator to create one.'))
            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')
        
        form = EditorGroupApplicationForm(available_editor_groups)

    dictionary = {'title': 'Apply for editor group membership', 'form': form}
    return render_to_response('accounts/editor_group_application.html',
                        dictionary, context_instance=RequestContext(request))


@login_required
def add_default_editor_groups(request):
    """
    Add default Editor Groups.
    """
    # Get UserProfile instance corresponding to the current user.
    profile = request.user.get_profile()

    # Exclude from the list the editor groups for which the user is not a member
    available_editor_groups = EditorGroup.objects \
        .filter(name__in=request.user.groups.values_list('name', flat=True)) \
        .exclude(name__in=profile.default_editor_groups.values_list('name', flat=True))

    # Check if the form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = AddDefaultEditorGroupForm(available_editor_groups, request.POST)
        # Check if the form has validated successfully.
        if form.is_valid():
            # Get submitted editor groups
            dflt_edt_grps = form.cleaned_data['default_editor_groups']

            for dflt_edt_grp in dflt_edt_grps:
                for edt_grp in EditorGroup.objects.filter(name=dflt_edt_grp.name):
                    profile.default_editor_groups.add(edt_grp)
                    messages.success(request, _('You have successfully ' \
                      'added default editor group "%s".') % (dflt_edt_grp.name,))
            profile.save()

            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')

    # Otherwise, render a new AddDefaultEditorGroupForm instance
    else:
        # Check whether there is an editor group the user can add to the default list.
        if available_editor_groups.count() == 0:
            # If there is no editor group created yet, send an error message.
            messages.error(request, _('There are no editor groups you can '
                'add to your default list.'))
            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')
        
        form = AddDefaultEditorGroupForm(available_editor_groups)

    dictionary = {'title': 'Add default editor group', 'form': form}
    return render_to_response('accounts/add_default_editor_group.html',
                        dictionary, context_instance=RequestContext(request))


@login_required
def remove_default_editor_groups(request):
    """
    Remove default Editor Groups.
    """
    # Get UserProfile instance corresponding to the current user.
    profile = request.user.get_profile()

    # Include in the list only the default editor groups of the user
    available_editor_groups = EditorGroup.objects \
        .filter(name__in=profile.default_editor_groups.values_list('name', flat=True))

    # Check if the form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = RemoveDefaultEditorGroupForm(available_editor_groups, request.POST)
        # Check if the form has validated successfully.
        if form.is_valid():
            # Get submitted editor groups
            dflt_edt_grps = form.cleaned_data['default_editor_groups']

            for dflt_edt_grp in dflt_edt_grps:
                for edt_grp in EditorGroup.objects.filter(name=dflt_edt_grp.name):
                    profile.default_editor_groups.remove(edt_grp)
                    messages.success(request, _('You have successfully ' \
                      'removed default editor group "%s".') % (dflt_edt_grp.name,))
            profile.save()

            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')

    # Otherwise, render a new RemoveDefaultEditorGroupForm instance
    else:
        # Check whether there is an editor group the user can remove from the default list.
        if available_editor_groups.count() == 0:
            # If there is no editor group created yet, send an error message.
            messages.error(request, _('There are no editor groups you can '
                'remove from your default list.'))
            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')
        
        form = RemoveDefaultEditorGroupForm(available_editor_groups)

    dictionary = {'title': 'Remove default editor group', 'form': form}
    return render_to_response('accounts/remove_default_editor_group.html',
                        dictionary, context_instance=RequestContext(request))


@login_required
def organization_application(request):
    """
    Apply for Organization membership.
    """
    # Exclude from the list the organization that the user cannot apply for:
    # - organization for which the user is already a member
    # - organization for which the user has already applied
    available_organization = Organization.objects \
        .exclude(name__in=request.user.groups.values_list('name', flat=True)) \
        .exclude(name__in=OrganizationApplication.objects.filter(
            user=request.user).values_list('organization__name', flat=True))

    # Check if the edit form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = OrganizationApplicationForm(available_organization, request.POST)
        # Check if the form has validated successfully.
        if form.is_valid():
            organization = form.cleaned_data['organization']

            if OrganizationApplication.objects.filter(
                    user=request.user, organization=organization).count() != 0:
                messages.success(request, _('An older application of yours for '
                    'organization "%s" is still pending.') % (organization.name,))
            else:
                new_object = OrganizationApplication(user=request.user,
                    organization=organization)
                new_object.save()

                # Send a notification email to the relevant organization managers/superusers
                emails = []
                # Find out the relevant group managers' emails
                for org_manager in organization.get_managers():
                    emails.append(org_manager.email)
                # Find out the superusers' emails
                for superuser in User.objects.filter(is_superuser=True):
                    emails.append(superuser.email)
                # Render notification email template with correct values.
                data = {'organization': organization.name,
                  'shortname': request.user,
                  'confirmation_url': '{0}/admin/accounts/organizationapplication/'.format(
                    DJANGO_URL)}
                try:
                    # Send out notification email to the organization managers and superusers
                    send_mail('New organization membership request',
                        render_to_string('accounts/notification_organization_managers_application.email', data),
                        'no-reply@meta-share.eu', emails, fail_silently=False)
                except: #SMTPException:
                    # If the email could not be sent successfully, tell the user
                    # about it.
                    messages.error(request,
                      "There was an error sending out the request email " \
                      "for your organization application.")
                else:
                    messages.success(request, _('You have successfully ' \
                        'applied for organization "%s".') % (organization.name,))

            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')

    # Otherwise, render a new OrganizationApplicationForm instance
    else:
        # Check whether there is an organization the user can apply for.
        if available_organization.count() == 0:
            # If there is no organization created yet, send an error message.
            messages.error(request, _('There are no organizations in the '
                'database, yet, for which you could apply. Please ask the '
                'system administrator to create one.'))
            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')
        
        form = OrganizationApplicationForm(available_organization)

    dictionary = {'title': 'Apply for organization membership', 'form': form}
    return render_to_response('accounts/organization_application.html',
                        dictionary, context_instance=RequestContext(request))

def reset(request, uuid=None):
    """
    Resets the password for the given reset id.
    """
    # If the uuid argument is not available, we have to render the reset form.
    if not uuid:
        # Check if the ResetRequestForm form has been submitted.
        if request.method == "POST":
            # If so, bind the reset form to HTTP POST values.
            form = ResetRequestForm(request.POST)
            
            # Check if the form has validated successfully.
            if form.is_valid():
                # Create a new ResetRequest instance for the User.
                user = User.objects.get(
                  username=form.cleaned_data['username'],
                  email=form.cleaned_data['email'])
                new_object = ResetRequest(user=user)
                new_object.save()
                
                # Render reset email template with correct values.
                data = {'firstname': user.first_name,
                  'lastname': user.last_name,
                  'shortname': user.username,
                  'confirmation_url': '{0}/accounts/reset/{1}/'.format(
                    DJANGO_URL, new_object.uuid)}
                email = render_to_string('accounts/reset.email', data)
                
                try:
                    # Send out reset email to the given email address.
                    send_mail('Please confirm your META-SHARE reset request',
                    email, 'no-reply@meta-share.eu', [user.email],
                    fail_silently=False)
                
                except SMTPException:
                    # If the email could not be sent successfully, we simply
                    # redirect the user to the front page.
                    return redirect('metashare.views.frontpage')
                
                # Add a message to the user after successful creation.
                messages.success(request,
                  "We have received your reset request and sent you an " \
                  "email with further reset instructions.")
                
                # Redirect the user to the front page.
                return redirect('metashare.views.frontpage')
        
        # Otherwise, create an empty ResetRequestForm instance.
        else:
            form = ResetRequestForm()
        
        dictionary = {'title': 'Reset user account', 'form': form}
        return render_to_response('accounts/reset_account.html', dictionary,
          context_instance=RequestContext(request))
    
    # If the uuid is given, we have to process the corresponding ResetRequest.
    # We lookup the ResetRequest instance and create a new, random password.
    user_reset = get_object_or_404(ResetRequest, uuid=uuid)
    random_password = User.objects.make_random_password()
    
    # Then we update the corresponding User instance with the new password.
    user = user_reset.user
    user.set_password(random_password)
    user.save()
    
    # Delete reset request instance.
    user_reset.delete()
    
    # Render re-activation email template with correct values.
    data = {'firstname': user_reset.user.first_name,
      'lastname': user.last_name,
      'shortname': user.username,
      'random_password': random_password}
    email = render_to_string('accounts/activation.email', data)
    
    try:
        # Send out re-activation email to the given email address.
        send_mail('Your META-SHARE user account has been re-activated',
        email, 'no-reply@meta-share.eu', [user.email], fail_silently=False)
    
    except SMTPException:
        # If the email could not be sent successfully, tell the user about it.
        messages.error(request,
          "There was an error sending out the activation email " \
          "for your user account. Please contact the administrator.")
        
        # Redirect the user to the front page.
        return redirect('metashare.views.frontpage')
    
    # Add a message to the user after successful creation.
    messages.success(request,
      "We have re-activated your user account and sent you an email with " \
      "your personal password which allows you to login to the website.")
    
    # Redirect the user to the front page.
    return redirect('metashare.views.frontpage')
