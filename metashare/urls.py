from django.conf.urls.defaults import patterns, include
from django.contrib import admin
from django.views.generic.simple import direct_to_template

from metashare.repository.editor import admin_site as editor_site
from metashare.repository.sitemap import RepositorySitemap
from metashare.settings import MEDIA_ROOT, DEBUG, DJANGO_BASE, SITEMAP_URL


admin.autodiscover()

urlpatterns = patterns('',
  (r'^{0}$'.format(DJANGO_BASE),
    'metashare.views.frontpage'),
  (r'^{0}info/$'.format(DJANGO_BASE),
     direct_to_template, {'template': 'metashare-info.html'}, "info"),
  (r'^{0}login/$'.format(DJANGO_BASE),
    'metashare.views.login', {'template_name': 'login.html'}),
  (r'^{0}logout/$'.format(DJANGO_BASE),
    'metashare.views.logout', {'next_page': '/{0}'.format(DJANGO_BASE)}),
  (r'^{0}admin/'.format(DJANGO_BASE),
    include(admin.site.urls)),
  (r'^{0}editor/'.format(DJANGO_BASE),
    include(editor_site.urls)),
  (r'^{0}update_lang_variants/'.format(DJANGO_BASE),
    'metashare.bcp47.views.update_lang_variants'),
  (r'^{0}update_var_variants/'.format(DJANGO_BASE),
    'metashare.bcp47.views.update_var_variants'),
  (r'^{0}update_lang_variants_with_script/'.format(DJANGO_BASE),
    'metashare.bcp47.views.update_lang_variants_with_script'),
)

urlpatterns += patterns('metashare.accounts.views',
  (r'^{0}accounts/'.format(DJANGO_BASE), include('metashare.accounts.urls')),
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

urlpatterns += patterns('',
  (r'^{}sitemap\.xml$'.format(DJANGO_BASE), 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
)

if DJANGO_BASE == "":
    urlpatterns += patterns('',
      (r'^{}robots\.txt$'.format(DJANGO_BASE), direct_to_template, 
        {'template': 'robots.txt', 'mimetype': 'text/plain', 'extra_context' : { 'sitemap_url' : SITEMAP_URL }}),
    )

if DEBUG:
    urlpatterns += patterns('',
      (r'^{0}site_media/(?P<path>.*)$'.format(DJANGO_BASE),
        'django.views.static.serve', {'document_root': MEDIA_ROOT})
    )
