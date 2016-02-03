from django import forms
from metashare.accounts.models import UserProfile, EditorGroupApplication, \
    OrganizationApplication, Organization, OrganizationManagers, EditorGroup, \
    EditorGroupManagers
from django.conf import settings
from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


class ModelForm(forms.ModelForm):
    """
    Base form for META-SHARE model forms -- disables the colon after a label,
    and formats error messages as expected by the templates.
    """
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        # Avoid the default ':' suffix
        self.label_suffix = ''
        
    required_css_class = 'required'
    error_css_class = 'error'
    
    def as_table(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(
            normal_row = u'<tr%(html_class_attr)s><th>%(label)s%(errors)s</th><td>%(field)s%(help_text)s</td></tr>',
            error_row = u'<tr><td colspan="2">%s</td></tr>',
            row_ender = u'</td></tr>',
            help_text_html = u'<br /><span class="helptext">%s</span>',
            errors_on_separate_row = False)


class Form(forms.Form):
    """
    Base form for META-SHARE forms -- disables the colon after a label,
    and formats error messages as expected by the templates.
    """
    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        # Avoid the default ':' suffix
        self.label_suffix = ''
        
    required_css_class = 'required'
    error_css_class = 'error'
    
    def as_table(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(
            normal_row = u'<tr%(html_class_attr)s><th>%(label)s%(errors)s</th><td>%(field)s%(help_text)s</td></tr>',
            error_row = u'<tr><td colspan="2">%s</td></tr>',
            row_ender = u'</td></tr>',
            help_text_html = u'<br /><span class="helptext">%s</span>',
            errors_on_separate_row = False)
    

class RegistrationRequestForm(Form):
    """
    Form used to create user account requests from new users.
    """
    shortname = forms.CharField(User._meta.get_field('username').max_length,
                                label=_("Desired account name"))
    first_name = forms.CharField(User._meta.get_field('first_name').max_length,
                                 label=_("First name"))
    last_name = forms.CharField(User._meta.get_field('last_name').max_length,
                                label=_("Last name"))
    email = forms.EmailField(label=_("E-mail"))
    password = forms.CharField(User._meta.get_field('password').max_length,
        label=_("Password"), widget=forms.PasswordInput())
    confirm_password = forms.CharField(
        User._meta.get_field('password').max_length,
        label=_("Password confirmation"), widget=forms.PasswordInput())
    accepted_tos = forms.BooleanField()

    def clean_shortname(self):
        """
        Make sure that the user name is still available.
        """
        _user_name = self.cleaned_data['shortname']
        try:
            User.objects.get(username=_user_name)
        except:
            pass
        else:
            raise ValidationError(_('User account name already exists, ' \
                                    'please choose another one.'))
        return _user_name

    def clean_email(self):
        """
        Make sure that there is no account yet registered with this email.
        """
        _email = self.cleaned_data['email']
        try:
            User.objects.get(email=_email)
        except:
            pass
        else:
            raise ValidationError(_('There is already an account registered ' \
                                    'with this e-mail address.'))
        return _email

    def clean_confirm_password(self):
        """
        Make sure that the password confirmation is the same as password.
        """
        pswrd = self.cleaned_data.get('password', None)
        pswrd_conf = self.cleaned_data['confirm_password']
        if pswrd != pswrd_conf:
            raise ValidationError('The two password fields did not match.')
        return pswrd

    # cfedermann: possible extensions for future improvements.
    # - add validation for shortname for forbidden characters


class ContactForm(Form):
    """
    Form used to contact the superusers of the META-SHARE node.
    """
    subject = forms.CharField(min_length=6, max_length=80,
        error_messages={'min_length': _('Please provide a meaningful and '
                                        'sufficiently indicative subject.')})
    message = forms.CharField(min_length=30, max_length=2500,
        widget=forms.Textarea, error_messages={'min_length': _('Your message '
            'appears to be rather short. Please make sure to phrase your '
            'request as precise as possible. This will help us to process it '
            'as quick as possible.')})


class ResetRequestForm(Form):
    """
    Form used to reset an existing user account.
    """
    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    
    def clean(self):
        cleaned_data = self.cleaned_data
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        if username and email:
            # Only do something if both fields are valid so far.
            user = User.objects.filter(username=username, email=email)
            if not user:
                raise forms.ValidationError('Not a valid username-email combination.')

        return cleaned_data
    

class UserProfileForm(ModelForm):
    """
    Form used to update the user account profile information.
    """
    class Meta:
        """
        Meta class connecting to UserProfile object model.
        """
        model = UserProfile
        exclude = ('user', 'modified', 'uuid', 'default_editor_groups')


class EditorGroupApplicationForm(ModelForm):
    """
    Form used to apply to new editor groups membership.
    """
    class Meta:
        """
        Meta class connecting to EditorGroupApplication object model.
        """
        model = EditorGroupApplication
        exclude = ('user', 'created')

    def __init__(self, editor_group_qs, *args, **kwargs):
        """
        Initializes the `EditorGroupApplicationForm` with the editor groups
        of the given query set.
        """
        super(EditorGroupApplicationForm, self).__init__(*args, **kwargs)
        # If there is a list of editor groups, then modify the ModelChoiceField
        self.fields['editor_group'].queryset = editor_group_qs


class UpdateDefaultEditorGroupForm(ModelForm):
    """
    Form used to update default editor groups.
    """
    default_editor_groups = forms.ModelMultipleChoiceField([],
        widget=widgets.FilteredSelectMultiple(_("default editor groups"),
                                              is_stacked=False),
        required=False)

    class Media:
        css = {
            # required by the FilteredSelectMultiple widget
            'all':['{}admin/css/widgets.css'.format(settings.STATIC_URL)],
        }
        # required by the FilteredSelectMultiple widget
        js = ['/{}admin/jsi18n/'.format(settings.DJANGO_BASE)]

    class Meta:
        """
        Meta class connecting to UserProfile object model.
        """
        model = UserProfile
        exclude = ('user', 'modified', 'uuid', 'birthdate', 'affiliation', \
          'position', 'homepage')

    def __init__(self, available_editor_group, chosen_editor_group, *args, **kwargs):
        """
        Initializes the `UpdateDefaultEditorGroupForm` with the editor groups
        of the given query set.
        """
        super(UpdateDefaultEditorGroupForm, self).__init__(*args, **kwargs)
        # If there is a list of editor groups, then modify the ModelChoiceField
        self.fields['default_editor_groups'].queryset = available_editor_group
        self.fields['default_editor_groups'].initial = chosen_editor_group


class OrganizationApplicationForm(ModelForm):
    """
    Form used to apply to new organizations membership.
    """
    class Meta:
        """
        Meta class connecting to OrganizationApplication object model.
        """
        model = OrganizationApplication
        exclude = ('user', 'created')

    def __init__(self, organization_qs, *args, **kwargs):
        """
        Initializes the `OrganizationApplicationForm` with the organizations
        of the given query set.
        """
        super(OrganizationApplicationForm, self).__init__(*args, **kwargs)
        # If there is a list of organizations, then modify the ModelChoiceField
        self.fields['organization'].queryset = organization_qs


class EditorGroupForm(ModelForm):
    """
    Form used to render the add/change admin views for `EditorGroup` model
    instances.
    """
    class Meta:
        model = EditorGroup
        widgets = {
            'permissions': forms.widgets.MultipleHiddenInput
        }


class EditorGroupManagersForm(ModelForm):
    """
    Form used to render the add/change admin views for `EditorGroupManagers`
    model instances.
    """
    class Meta:
        model = EditorGroupManagers
        widgets = {
            'permissions': forms.widgets.MultipleHiddenInput
        }


class OrganizationForm(ModelForm):
    """
    Form used to render the add/change admin views for `Organization` model
    instances.
    """
    class Meta:
        model = Organization
        widgets = {
            'permissions': widgets.FilteredSelectMultiple(
                Organization._meta.get_field('permissions').verbose_name, False)
        }


class OrganizationManagersForm(ModelForm):
    """
    Form used to render the add/change admin views for `OrganizationManagers`
    model instances.
    """
    class Meta:
        model = OrganizationManagers
        widgets = {
            'permissions': widgets.FilteredSelectMultiple(OrganizationManagers \
                    ._meta.get_field('permissions').verbose_name, False)
        }
