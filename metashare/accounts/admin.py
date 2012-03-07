"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.contrib import admin
from metashare.accounts.models import RegistrationRequest, ResetRequest, \
  UserProfile

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

admin.site.register(RegistrationRequest, RegistrationRequestAdmin)
admin.site.register(ResetRequest, ResetRequestAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
