from django.contrib.sitemaps import Sitemap, FlatPageSitemap
from models import *
import datetime
from settings import FULL_DJANGO_URL
from django.core.urlresolvers import *

class RepositorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    
    def items(self):
        return resourceInfoType_model.objects.all()
    
    def location(self, obj):
        url = '{}/{}'.format(FULL_DJANGO_URL, obj.get_relative_url())
        # Specific to sitemap module. It insists on prepending a
        # "http://" before the url.
        if url.startswith("http://"):
			url = url[7:]
        return url
