from django.contrib.sitemaps import Sitemap
from metashare.repository.models import resourceInfoType_model
from metashare.settings import DJANGO_FULL_URL
from metashare.storage.models import PUBLISHED

class RepositorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    
    def items(self):
        return resourceInfoType_model.objects.filter(storage_object__publication_status=PUBLISHED).filter(storage_object__deleted=False)

    def location(self, obj):
        url = '{}/{}'.format(DJANGO_FULL_URL, obj.get_relative_url())
        # Specific to sitemap module. It insists on prepending a
        # "http://" before the url.
        if url.startswith("http://"):
            url = url[7:]
        return url
