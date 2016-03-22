from django.conf.urls import patterns


urlpatterns = patterns('metashare.sync.views',
  (r'^$', 'inventory'),
  (r'^(?P<resource_uuid>[0-9a-fA-F]{64})/metadata/$', 'full_metadata'),
)
