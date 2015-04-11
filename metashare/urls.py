from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from metashare.repository.editor import admin_site as editor_site
from metashare.repository.sitemap import RepositorySitemap
from metashare.settings import MEDIA_ROOT, DEBUG, DJANGO_BASE, SITEMAP_URL


admin.autodiscover()

urlpatterns = patterns('',
  url(r'^{0}$'.format(DJANGO_BASE), 'metashare.views.frontpage'),
  url(r'^{0}info/$'.format(DJANGO_BASE),
     TemplateView.as_view(template_name='metashare-info.html'), name="info"),
  url(r'^{0}login/$'.format(DJANGO_BASE),
    'metashare.views.login', {'template_name': 'login.html'}),
  url(r'^{0}logout/$'.format(DJANGO_BASE),
    'metashare.views.logout', {'next_page': '/{0}'.format(DJANGO_BASE)}),
  url(r'^{0}admin/'.format(DJANGO_BASE), include(admin.site.urls)),
  url(r'^{0}editor/'.format(DJANGO_BASE), include(editor_site.urls)),
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

class RobotsTemplateView(TemplateView):
    """ This class is defined as a need for migrating from function-based
        generic views that existed in django-1.2 to class-based generic views.
        https://docs.djangoproject.com/en/1.4/topics/generic-views-migration/
    """
    def render_to_response(self, context, **kwargs):
        """ This method is overloaded to provide the content_type parameter.
            Django-1.5 supports content_type argument so this method will
            be removed in the django-1.5 META-SHARE version as the content_type
            will be used in the instantiation.
            Django-1.4: RobotsTemplateView.as_view(template_name='robots.txt')
            Django-1.5: RobotsTemplateView.as_view(template_name='robots.txt', content_type="text/plain")
        """
        return super(RobotsTemplateView, self).render_to_response(context,
                        content_type='text/plain', **kwargs)

    def get_context_data(self, **kwargs):
        """ This method is overloaded to pass the SITEMAP_URL into the context data"""
        context = super(RobotsTemplateView, self).get_context_data(**kwargs)
        context.update({'sitemap_url': SITEMAP_URL})
        return context


if DJANGO_BASE == "":
    urlpatterns += patterns('',
      (r'^{}robots\.txt$'.format(DJANGO_BASE), RobotsTemplateView.as_view(template_name='robots.txt')),
    )

urlpatterns += staticfiles_urlpatterns()

