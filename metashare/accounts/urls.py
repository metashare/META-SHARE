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
  (r'editor_group_application/$',
    'editor_group_application'),
  (r'add_default_editor_groups/$',
    'add_default_editor_groups'),
  (r'remove_default_editor_groups/$',
    'remove_default_editor_groups'),
  (r'sso/(?P<uuid>[0-9a-f]{32})0(?P<timestamp>\d+)1(?P<token>[0-9a-f]{32})/$',
    'sso'),
  (r'sso/(?P<uuid>[0-9a-f]{32})1(?P<timestamp>\d+)0(?P<token>.+)/$',
    'sso'),
)
urlpatterns += patterns('django.contrib.auth.views',
  (r'^profile/change_password/$', 'password_change', 
        {'post_change_redirect' : '/accounts/profile/change_password/done/', 'template_name': 'accounts/change_password.html'}),
  (r'^profile/change_password/done/$', 'password_change_done', 
        {'template_name': 'accounts/change_password_done.html'}),
)
