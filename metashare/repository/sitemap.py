from django.contrib.sitemaps import Sitemap
from metashare.repository.models import resourceInfoType_model
from metashare.storage.models import PUBLISHED

class RepositorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    
    def items(self):
        return resourceInfoType_model.objects \
          .filter(storage_object__publication_status=PUBLISHED) \
          .filter(storage_object__deleted=False)
