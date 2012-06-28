"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging
from Crypto.PublicKey import RSA
from datetime import datetime
# pylint: disable-msg=E0611
from hashlib import md5
from smtplib import SMTPException
from time import mktime
from traceback import format_exc
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.mail import send_mail
from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest, \
  HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils.translation import ugettext as _

from metashare.accounts.forms import RegistrationRequestForm, \
  ResetRequestForm, UserProfileForm, EditorRegistrationRequestForm
from metashare.accounts.models import RegistrationRequest, ResetRequest, \
  UserProfile, EditorRegistrationRequest
from metashare.settings import SSO_SECRET_KEY, DJANGO_URL, \
  PRIVATE_KEY_PATH, LOG_LEVEL, LOG_HANDLER, MAX_LIFETIME_FOR_SSO_TOKENS
from metashare.accounts.models import EditorGroup

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
    
    # We are using randomly generated passwords for the moment.
    random_password = User.objects.make_random_password()
    
    # Create a new User instance from the registration request data.
    user = User.objects.create_user(registration_request.shortname,
      registration_request.email, random_password)
    
    # Update User instance attributes and activate it.
    user.first_name = registration_request.firstname
    user.last_name = registration_request.lastname
    user.is_active = True
    
    # Save the new User instance to the django database.  This will also
    # create a corresponding UserProfile instance by post_save "magic".
    user.save()
    
    # Delete registration request instance.
    registration_request.delete()
    
    # For convenience, log user in:
    authuser = authenticate(username=user.username, password=random_password)
    login(request, authuser)
    request.session['METASHARE_UUID'] = uuid

    
    # Render activation email template with correct values.
    data = {'firstname': user.first_name, 'lastname': user.last_name,
      'shortname': user.username, 'random_password': random_password}
    email = render_to_string('accounts/activation.email', data)
    
    try:
        # Send out activation email containing the random password.
        send_mail('Your META-SHARE user account has been activated',
        email, 'no-reply@meta-share.eu', [user.email], fail_silently=False)
    
    except: # SMTPException:
        # If the email could not be sent successfully, tell the user about it.
        messages.error(request,
          "There was an error sending out the activation email " \
          "for your user account.  Your password is <b>{0}</b>.".format(
            random_password))
        
        # Redirect the user to the front page.
        return redirect('metashare.views.frontpage')
    
    # Add a message to the user after successful creation.
    messages.success(request,
      "We have activated your user account and sent you an email with " \
      "your personal password which allows you to login to the website.")
    
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
            # Create new RegistrationRequest instance.
            new_object = RegistrationRequest(
              shortname=form.cleaned_data['shortname'],
              firstname=form.cleaned_data['firstname'],
              lastname=form.cleaned_data['lastname'],
              email=form.cleaned_data['email'])
            
            # Save new RegistrationRequest instance to django database.
            new_object.save()
            
            # Render confirmation email template with correct values.
            data = {'firstname': new_object.firstname,
              'lastname': new_object.lastname,
              'shortname': new_object.shortname,
              'confirmation_url': '{0}/accounts/confirm/{1}/'.format(
                DJANGO_URL, new_object.uuid)}
            email = render_to_string('accounts/confirmation.email', data)
            
            try:
                # Send out confirmation email to the given email address.
                send_mail('Please confirm your META-SHARE user account',
                email, 'no-reply@meta-share.eu', [new_object.email],
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
    
    # Otherwise, create an empty UploadCreateForm instance.
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
    # The "virtual" MetaShareUser cannot edit profile information!
    if request.user.username == 'MetaShareUser':
        return redirect('metashare.views.frontpage')
    
    # Check if the edit form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = UserProfileForm(request.POST)
        
        # Check if the form has validated successfully.
        if form.is_valid():
            # Get UserProfile instance corresponding to the current user.
            profile = request.user.get_profile()
            
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
        # Get UserProfile instance corresponding to the current user.
        profile = request.user.get_profile()
        
        # Fill UserProfileForm from current UserProfile instance.
        form = UserProfileForm({'birthdate': profile.birthdate,
          'affiliation': profile.affiliation, 'position': profile.position,
          'homepage': profile.homepage})

    dictionary = {'title': 'Edit profile information', 'form': form, 
        'groups_applied_for': [edt_reg.editor_group.name for edt_reg
                in EditorRegistrationRequest.objects.filter(user=profile.user)]}
    return render_to_response('accounts/edit_profile.html', dictionary,
      context_instance=RequestContext(request))

@login_required
def editor_registration_request(request):
    """
    Apply for Editor Groups membership.
    """
    # The "virtual" MetaShareUser cannot apply for membership
    if request.user.username == 'MetaShareUser':
        return redirect('metashare.views.frontpage')

    # Check if the edit form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = EditorRegistrationRequestForm(request.POST)
        
        # Check if the form has validated successfully.
        if form.is_valid():
            edt_grp = form.cleaned_data['editor_group']
            if EditorRegistrationRequest.objects.filter(
                    user=request.user, editor_group=edt_grp).count() != 0:
                messages.success(request, _('An older application of yours for '
                    'editor group "%s" is still pending.') % (edt_grp.name,))
            else:
                new_object = EditorRegistrationRequest(user=request.user,
                    editor_group=edt_grp)
                new_object.save()

                # send a notification email to the relevant managers/superusers
                emails = []
                # find out the relevant group managers' emails
                for manager in edt_grp.get_managers():
                    emails.append(manager.email)
                # find out the superusers' emails
                for superuser in User.objects.filter(is_superuser=True):
                    emails.append(superuser.email)
                # Render notification email template with correct values.
                data = {'editor_group': edt_grp.name,
                  'shortname': request.user,
                  'confirmation_url': '{0}/admin/accounts/editorregistrationrequest/'.format(
                    DJANGO_URL)}
                try:
                    # send out notification email to the managers and superusers
                    send_mail('New editor membership request',
                        render_to_string('accounts/notification.email', data),
                        'no-reply@meta-share.eu', emails, fail_silently=False)
                except: #SMTPException:
                    # If the email could not be sent successfully, tell the user
                    # about it.
                    messages.error(request,
                      "There was an error sending out the request email " \
                      "for your editor registration.")
                else:
                    messages.success(request, _('You have successfully ' \
                        'applied for editor group "%s".') % (edt_grp.name,))

            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')

    # Otherwise, render a new EditorRegistrationRequestForm instance
    else:
        if EditorGroup.objects.count() == 0:
            # If there is no editor group created yet, send an error message.
            messages.error(request, _('There are no editor groups in the '
                'database, yet, for which you could apply. Please ask the '
                'system administrator to create one.'))
            # Redirect the user to the edit profile page.
            return redirect('metashare.views.edit_profile')
        form = EditorRegistrationRequestForm()

    dictionary = {'title': 'Apply for editor group membership', 'form': form}
    return render_to_response('accounts/editor_registration_request.html',
                        dictionary, context_instance=RequestContext(request))


def update(request):
    """
    Updates the user information with the given serialized data.
    
    This method only accepts encrypted data sent via HTTP POST and raises an
    AssertionError in case of other connections.  The received data is decoded
    using the local private key and from the decrypted data a list of User and
    UserProfile is de-serialized.  These data are then used to update the user
    information in the Django database.
    
    Please note that permissions and groups for User objects are NOT sync'ed
    by this method as they cannot be transmitted reliably in a post_save hook.
    """
    assert(request.method == "POST"), "Requires a HTTP POST connection."
    
    # First, we extract the message from the HTTP POST QueryDict.
    _message = request.POST.get('message', None)
    
    # If there is no message, this is a bad request.
    if not _message:
        return HttpResponseBadRequest()
    
    # Otherwise, we have to eval() the message to re-construct the list.
    else:
        _message = eval(_message)
    
    # Load private key from PRIVATE_KEY_PATH file.
    with open(PRIVATE_KEY_PATH, 'r') as pem:
        my_private_pem = pem.read()
    
    # Create private key for local django instance.
    my_private_key = RSA.importKey(my_private_pem)
    
    # Reconstruct original message from encrypted chunks.
    _chunks = []
    for _chunk in _message:
        _chunks.append(my_private_key.decrypt(_chunk))
    message = ''.join(_chunks)
    
    # Extract profiles and user instances from the serialized message.
    profiles = []
    users = []
    
    # We have to pass the DeserializedObject instances here in order to
    # preserve the m2m_data dictionary which is required to synchronize
    # user groups and user_permissions.
    try:
        for obj in serializers.deserialize("xml", message):
            if isinstance(obj.object, UserProfile):
                profiles.append(obj)
            
            elif isinstance(obj.object, User):
                users.append(obj)
    
    except:
        LOGGER.error(format_exc())
        return HttpResponseBadRequest(format_exc(), mimetype='text/plain')
    
    # We assume profiles and user instances to be in order, e.g. profiles[0]
    # belongs to users[0], etc.  For django 1.3, this seems to be working.
    for profile, user in zip(profiles, users):
        _create_or_update_user_data(profile, user)
    
    # Return a minimal HTTP 200 OK response.
    return HttpResponse("OK", mimetype='text/plain')

def _create_or_update_user_data(profile, user):
    """
    Updates or creates the given user data.
    """
    # Check if there exists a local profile for the given uuid.
    local_profile = UserProfile.objects.filter(uuid=profile.object.uuid)
    
    # Also, check if there exists a local user with matching email, username.
    local_user = User.objects.filter(email=user.object.email,
      username=user.object.username)
    
    # We are assuming that a UserProfile and the related User must co-exist.
    # Otherwise, something wrong must have happened and we raise an exception.
    if not local_profile:
        assert(not local_user), "Stale user without attached profile found!"
        
        # If both the User and corresponding UserProfile are new, all we have
        # to do is to save them into the django database.
        profile.save()
        user.save()
        
        # We also have to make sure that the user relation is correct.
        profile.user = user
        profile.save()
    
    # If a local UserProfile has been found, we also expect the local User
    # instance to be available. Otherwise, we raise an exception.
    else:
        assert(local_user), "Stale profile without attached user found!"
        
        # Convert QuerySets to single UserProfile and User instances.
        local_profile = local_profile[0]
        local_user = local_user[0]
        
        # Verify that the UserProfile and User instances are connected.
        assert(local_profile.user == local_user), "Disconnected user data!"
        
        # Check if the local profile is more recent than the received version.
        if local_profile.modified >= profile.object.modified:
            # We can return without any further changes.
            LOGGER.info('Local profile is more recent than received version.')
            return
        
        # Copy received profile data to local profile instance.
        for __field__ in profile.object.__synchronized_fields__:
            _value = getattr(profile.object, __field__, None)
            LOGGER.info("Setting UserProfile.{0} = {1}.".format(__field__,
              _value))
            setattr(local_profile, __field__, _value)
        
        # Save updated local UserProfile instance.
        local_profile.save()
        
        # Copy received user attributes to local user instance.
        __synchronized_user_fields__ = ('username', 'first_name', 'last_name',
          'email', 'password', 'is_active', 'is_staff', 'is_superuser',
          'last_login', 'date_joined')
        for __field__ in __synchronized_user_fields__:
            _value = getattr(user.object, __field__)
            LOGGER.info("Setting User.{0} = {1}.".format(__field__, _value))
            setattr(local_user, __field__, _value)
        
        # Save updated local User instance.
        local_user.save()

def permissions(request):
    """
    Updates groups and permissions for a list of serialized User instances.
    """
    assert(request.method == "POST"), "Requires a HTTP POST connection."
    
    # First, we extract the message from the HTTP POST QueryDict.
    _message = request.POST.get('message', None)
    
    # If there is no message, this is a bad request.
    if not _message:
        return HttpResponseBadRequest()
    
    # Otherwise, we have to eval() the message to re-construct the list.
    else:
        _message = eval(_message)
    
    # Load private key from PRIVATE_KEY_PATH file.
    with open(PRIVATE_KEY_PATH, 'r') as pem:
        my_private_pem = pem.read()
    
    # Create private key for local django instance.
    my_private_key = RSA.importKey(my_private_pem)
    
    # Reconstruct original message from encrypted chunks.
    _chunks = []
    for _chunk in _message:
        _chunks.append(my_private_key.decrypt(_chunk))
    message = ''.join(_chunks)
    
    # Extract user instances from the serialized message.
    users = []
    
    # We have to pass the DeserializedObject instances here in order to
    # preserve the m2m_data dictionary which is required to synchronize
    # user groups and user_permissions.
    try:
        for obj in serializers.deserialize("xml", message):
            if isinstance(obj.object, User):
                users.append(obj)
    
    except:
        LOGGER.error(format_exc())
        return HttpResponseBadRequest(format_exc(), mimetype='text/plain')
    
    # Loop over the given User objects and update the corresponding groups and
    # permission settings for each of these.
    for user in users:
        # Check if there exists a local user with matching email, username.
        local_user = User.objects.filter(email=user.object.email,
          username=user.object.username)
        
        if not local_user:
            LOGGER.error('No such user: {0}.'.format(user.object.username))
            continue
        
        # Copy user groups and permissions wherever possible.
        if user.m2m_data.has_key('groups'):
            # We overwrite local groups completely, hence first we erase them.
            local_user.groups.clear()
            
            # Loop over all group_ids inside the many-to-many group data.
            for group_id in user.m2m_data['groups']:
                try:
                    # If there exists a group with this group_id, add it.
                    group = Group.objects.get(pk=group_id)
                    LOGGER.info('Group: {0}'.format(group))
                    local_user.groups.add(group)
                
                except (ObjectDoesNotExist, MultipleObjectsReturned):
                    # We simply ignore non-existing groups for the moment.
                    continue
        
        # Same routine for user permissions.
        if user.m2m_data.has_key('user_permissions'):
            # Again, we first erase old, local permissions.
            local_user.user_permissions.clear()
            
            # Then, we loop over all many-to-many user permissions.
            for permission_id in user.m2m_data['user_permissions']:
                try:
                    # If there exists a permission matching the id, add it.
                    permission = Permission.objects.get(pk=permission_id)
                    LOGGER.info('Permission: {0}'.format(permission))
                    local_user.user_permissions.add(permission)
                
                except (ObjectDoesNotExist, MultipleObjectsReturned):
                    # We also ignore non-existing permissions for the moment.
                    continue

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
                # Check if there exists a User instance with matching username
                # and email inside the django database.
                user = User.objects.filter(
                  username=form.cleaned_data['username'],
                  email=form.cleaned_data['email'])
                
                # Marc, 25 Aug 2011:
                # The check that this exists is now done in ResetRequestForm.clean(),
                # so we trust we have a user when we get here
#                
#                # If not, redirect the user to the front page.
#                if not user:
#                    return redirect('metashare.views.frontpage')
#                
#                # Otherwise, create a new ResetRequest instance for this User.                
                # Otherwise, create a new ResetRequest instance for this User.
                user = user[0]
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

def _compute_sso_token(uuid, timestamp=None):
    """
    Returns a triple containing (uuid, timestamp, token) for SSO.
    """
    # If no timestamp is given, we use the current time.
    if not timestamp:
        # Convert time tuple to timestamp String.
        timestamp = str(int(mktime(datetime.now().timetuple())))
    
    # Create MD5 hash instance and fill in uuid, timestamp, SSO secret key.
    _md5 = md5()
    _md5.update('{0}{1}{2}'.format(uuid, timestamp, SSO_SECRET_KEY))
    
    # Compute SSO token in hexadecimal form.
    token = _md5.hexdigest()
    
    # Return triple containing valid SSO information for the given uuid.
    # Note that this information will become invalid after a time interval of
    # MAX_LIFETIME_FOR_SSO_TOKENS seconds has expired.  If you need more time,
    # you will have to used a future-based timestamp...
    return (uuid, timestamp, token)

def _check_sso_token(uuid, timestamp, token):
    """
    Verifies the given SSO token wrt. the given uuid and timestamp.
    """
    # Compute timedelta between now and the given timestamp.
    _delta =  datetime.now() - datetime.fromtimestamp(int(timestamp))

    # Is the timestamp outdated? Compare to MAX_LIFETIME_FOR_SSO_TOKENS.
    if abs(_delta.total_seconds()) >= MAX_LIFETIME_FOR_SSO_TOKENS:
        LOGGER.info('Outdated SSO token used!')
        return False
    
    # Re-compute the SSO token wrt. the given uuid and timestamp.
    dummy1, dummy2, recomputed_token = _compute_sso_token(uuid, timestamp)
    
    # Check if token and recomputed_token are identical.
    return token == recomputed_token

def sso(request, uuid, timestamp, token):
    """
    Verifies the given SSO token and logs in the given user on success.
    """
    # Try to authenticate given the SSO token, UUID and timestamp.
    # Falls back to the SingleSignOnTokenBackend class for authentication.
    user = authenticate(uuid=uuid, timestamp=timestamp, token=token)
    
    # If authentication is not successful, access has to be forbidden!
    if not user:
        return HttpResponseForbidden('Forbidden')
    
    # Login user and update session to include corresponding UUID.
    login(request, user)
    request.session['METASHARE_UUID'] = uuid
    
    # CHECK: check what are the best session settings for META-SHARE?
    #       Do we want to use SESSION_EXPIRE_AT_BROWSER_CLOSE?
    # - http://docs.djangoproject.com/en/dev/topics/http/sessions/#settings
    
    # Redirect the user to the front page.
    return redirect('metashare.views.frontpage')
