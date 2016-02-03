from django.conf.urls import patterns
from metashare.settings import DJANGO_BASE

urlpatterns = patterns('metashare.accounts.views',
  (r'create/$',
    'create'),
  (r'confirm/(?P<uuid>[0-9a-f]{32})/$',
    'confirm'),
  (r'contact/$',
    'contact'),
  (r'reset/(?:(?P<uuid>[0-9a-f]{32})/)?$',
    'reset'),
  (r'profile/$',
    'edit_profile'),
  (r'editor_group_application/$',
    'editor_group_application'),
  (r'organization_application/$',
    'organization_application'),
  (r'update_default_editor_groups/$',
    'update_default_editor_groups'),
)

urlpatterns += patterns('django.contrib.auth.views',
  (r'^profile/change_password/$', 'password_change', 
        {'post_change_redirect' : '/{0}accounts/profile/change_password/done/'.format(DJANGO_BASE), 'template_name': 'accounts/change_password.html'}),
  (r'^profile/change_password/done/$', 'password_change_done', 
        {'template_name': 'accounts/change_password_done.html'}),
)
