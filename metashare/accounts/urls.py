"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""

from django.conf.urls.defaults import patterns

urlpatterns = patterns('metashare.accounts.views',
  (r'create/$',
    'create'),
  (r'confirm/(?P<uuid>[0-9a-f]{32})/$',
    'confirm'),
  (r'reset/(?:(?P<uuid>[0-9a-f]{32})/)?$',
    'reset'),
  (r'update/$',
    'update'),
  (r'profile/$',
    'edit_profile'),
  (r'editor_registration_request/$',
    'editor_registration_request'),
  (r'sso/(?P<uuid>[0-9a-f]{32})0(?P<timestamp>\d+)1(?P<token>[0-9a-f]{32})/$',
    'sso'),
  (r'sso/(?P<uuid>[0-9a-f]{32})1(?P<timestamp>\d+)0(?P<token>.+)/$',
    'sso'),
)
