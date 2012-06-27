"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django import forms
from metashare.accounts.models import RegistrationRequest, UserProfile, \
    EditorRegistrationRequest, EditorGroup
from django.contrib.auth.models import User


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
    

class RegistrationRequestForm(ModelForm):
    """
    Form used to create user account requests from new users.
    """

        
    class Meta:
        """
        Meta class connecting to RegistrationRequest object model.
        """
        model = RegistrationRequest
        exclude = ('uuid', 'created')
    
    # cfedermann: possible extensions for future improvements.
    #
    # - add validation for email address which checks that it's unique.
    # - add validation for shortname for max_length and forbidden characters
    # - add validation for firstname for max_length
    # - add validation for lastname for max_length
    


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
        exclude = ('user', 'modified', 'uuid')

class EditorRegistrationRequestForm(ModelForm):
    """
    Form used to apply to new editor groups membership.
    """

    class Meta:
        """
        Meta class connecting to EditorRegistrationRequest object model.
        """
        model = EditorRegistrationRequest
        exclude = ('user', 'uuid', 'created')
