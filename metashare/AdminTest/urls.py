from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

from test1 import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'AdminTest.views.home', name='home'),
    # url(r'^AdminTest/', include('AdminTest.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    
    url(r'^$', 'AdminTest.test1.view'),
    (r'^admin/', include(admin.site.urls)),
)
