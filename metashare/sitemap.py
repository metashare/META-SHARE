from django.contrib.sitemaps import Sitemap, FlatPageSitemap
from repository.models import resourceInfoType_model

class RepositorySitemap(Sitemap):
    changefreq = "never"
    priority = 0.5
    
    def items(self):
        return resourceInfoType_model.objects.all()
