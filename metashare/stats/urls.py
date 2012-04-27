"""
Project: META-SHARE prototype implementation
 Author: Christian Girardi <cgirardi@fbk.eu>
"""
from django.conf.urls.defaults import patterns

urlpatterns = patterns('metashare.stats.views',
  (r'top/$',
    'topstats'),
  (r'repo/$',
    'repostats'),
  (r'mystats/$',
    'mystats'),
  (r'usage/$',
    'usagestats'),
  (r'days',
    'statdays'),
  (r'get.*',
    'getstats'),
)

