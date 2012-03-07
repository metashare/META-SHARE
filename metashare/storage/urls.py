"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.conf.urls.defaults import patterns

urlpatterns = patterns('metashare.storage.views',
  (r'^revision/(?P<identifier>[0-9a-f]{64})/$',
    'get_latest_revision'),
  (r'^export/(?P<identifier>[0-9a-f]{64})/$',
    'get_export_for_single_object'),
  (r'^export/(?:(?P<from_date>\d{4}-\d{2}-\d{2})/)?$',
    'get_export_for_all_objects'),
)