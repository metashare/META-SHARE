from django.conf.urls.defaults import patterns


urlpatterns = patterns('metashare.sync.views',
  (r'^$', 'inventory'),
)
