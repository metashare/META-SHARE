"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
# pylint: disable-msg=W0611
from django.conf.urls.defaults import patterns, include, handler404, \
  handler500
from django.contrib import admin
from django.contrib.sitemaps import Sitemap, FlatPageSitemap
from django.views.generic.simple import direct_to_template

from metashare.settings import MEDIA_ROOT, DEBUG, DJANGO_BASE, SITEMAP_URL
from metashare.repository.editor import admin_site as editor_site
from repository.sitemap import *

admin.autodiscover()

urlpatterns = patterns('',
  (r'^{0}$'.format(DJANGO_BASE),
    'metashare.views.frontpage'),
  (r'^{0}login/$'.format(DJANGO_BASE),
    'metashare.views.login', {'template_name': 'login.html'}),
  (r'^{0}logout/$'.format(DJANGO_BASE),
    'metashare.views.logout', {'next_page': '/{0}'.format(DJANGO_BASE)}),
  (r'^{0}admin/'.format(DJANGO_BASE),
    include(admin.site.urls)),
  (r'^{0}editor/'.format(DJANGO_BASE),
    include(editor_site.urls)),
)

urlpatterns += patterns('metashare.accounts.views',
  (r'^{0}accounts/'.format(DJANGO_BASE), include('metashare.accounts.urls')),
)

urlpatterns += patterns('metashare.storage.views',
  (r'^{0}storage/'.format(DJANGO_BASE), include('metashare.storage.urls')),
)

urlpatterns += patterns('metashare.stats.views',
  (r'^{0}stats/'.format(DJANGO_BASE), include('metashare.stats.urls')),
)

urlpatterns += patterns('metashare.repository.views',
  (r'^{0}repository/'.format(DJANGO_BASE), include('metashare.repository.urls')),
)

urlpatterns += patterns('metashare.sync.views',
  (r'^{0}sync/'.format(DJANGO_BASE), include('metashare.sync.urls')),
)

urlpatterns += patterns('',
  (r'^{0}selectable/'.format(DJANGO_BASE), include('selectable.urls')),
)

sitemaps = {
  'site': RepositorySitemap,
}

if DJANGO_BASE != "":
    urlpatterns += patterns('',
      (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    )

urlpatterns += patterns('',
  (r'^robots\.txt$', direct_to_template, 
    {'template': 'robots.txt', 'mimetype': 'text/plain', 'extra_context' : { 'sitemap_url' : SITEMAP_URL }}),
)

if DEBUG:
    urlpatterns += patterns('',
      (r'^{0}site_media/(?P<path>.*)$'.format(DJANGO_BASE),
        'django.views.static.serve', {'document_root': MEDIA_ROOT})
    )
