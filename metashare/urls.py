from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

from metashare.repository.editor import admin_site as editor_site
from metashare.repository.sitemap import RepositorySitemap
from metashare.settings import MEDIA_ROOT, DEBUG, DJANGO_BASE, SITEMAP_URL


admin.autodiscover()

urlpatterns = patterns('',
  url(r'^{0}$'.format(DJANGO_BASE),
    'metashare.views.frontpage', name='frontpage'),
  url(r'^{0}info/$'.format(DJANGO_BASE), TemplateView.as_view(template_name='metashare-info.html'), name='info'),
  url(r'^{0}login/$'.format(DJANGO_BASE),
    'metashare.views.login', {'template_name': 'login.html'}, name='login'),
  url(r'^{0}logout/$'.format(DJANGO_BASE),
    'metashare.views.logout', {'next_page': '/{0}'.format(DJANGO_BASE)}, name='logout'),
  url(r'^{0}admin/'.format(DJANGO_BASE),
    include(admin.site.urls)),
  url(r'^{0}editor/'.format(DJANGO_BASE),
    include(editor_site.urls)),
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

urlpatterns += patterns('metashare.bcp47.xhr',
  (r'^{0}bcp47/'.format(DJANGO_BASE), include('metashare.bcp47.urls')),
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

class RobotView(TemplateView):
    
    def get_context_data(self, **kwargs):
        context = super(RobotView, self).get_context_data(**kwargs)
        context['sitemap_url'] = SITEMAP_URL
        return context
    
if DJANGO_BASE == "":
    urlpatterns += patterns('',
    (r'^{}robots\.txt$'.format(DJANGO_BASE), RobotView.as_view(template_name='robots.txt'))
    )

if DEBUG:
    urlpatterns += patterns('',
      (r'^{0}site_media/(?P<path>.*)$'.format(DJANGO_BASE),
        'django.views.static.serve', {'document_root': MEDIA_ROOT})
    )
