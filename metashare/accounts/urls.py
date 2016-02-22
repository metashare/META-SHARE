from django.conf.urls import patterns, url
from metashare.settings import DJANGO_BASE

urlpatterns = patterns('metashare.accounts.views',
  url(r'create/$',
    'create', name='create'),
  url(r'confirm/(?P<uuid>[0-9a-f]{32})/$',
    'confirm', name='confirm'),
  url(r'contact/$',
    'contact', name='contact'),
  url(r'reset/(?:(?P<uuid>[0-9a-f]{32})/)?$',
    'reset', name='reset'),
  url(r'profile/$',
    'edit_profile', name='edit_profile'),
  url(r'editor_group_application/$',
    'editor_group_application', name='editor_group_application'),
  url(r'organization_application/$',
    'organization_application', name='organization_application'),
  url(r'update_default_editor_groups/$',
    'update_default_editor_groups', name='update_default_editor_groups'),
)

urlpatterns += patterns('django.contrib.auth.views',
  url(r'^profile/change_password/$', 'password_change', 
        {'post_change_redirect' : '/{0}accounts/profile/change_password/done/'.format(DJANGO_BASE), 'template_name': 'accounts/change_password.html'}, name='password_change'),
  url(r'^profile/change_password/done/$', 'password_change_done', 
        {'template_name': 'accounts/change_password_done.html'}, name='password_change_done'),
)
