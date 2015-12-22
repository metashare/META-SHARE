from django.conf.urls.defaults import patterns

urlpatterns = patterns('metashare.stats.views',
  (r'top/$',
    'topstats'),
  (r'mystats/$',
    'mystats'),
  (r'usage/$',
    'usagestats'),
  (r'days',
    'statdays'),
  (r'get.*',
    'getstats'),
  (r'portalstats/$',
   'portalstats'),
)

