from django.conf.urls import patterns
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	 ( r'^$', 'statserver.stats.views.browse' ),
	 ( r'^stats/addnode$', 'statserver.stats.views.addnode' ),
	 ( r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

