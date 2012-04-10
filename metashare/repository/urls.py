"""
Project: META-SHARE prototype implementation
Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.conf.urls.defaults import patterns, url
from haystack.views import search_view_factory
from haystack.query import SearchQuerySet

from metashare.repository.forms import FacetedBrowseForm
from metashare.repository.views import MetashareFacetedSearchView

sqs = SearchQuerySet() \
  .facet("languageNameFilter") \
  .facet("resourceTypeFilter") \
  .facet("mediaTypeFilter") \
  .facet("availabilityFilter") \
  .facet("licenceFilter") \
  .facet("restrictionsOfUseFilter") \
  .facet("validatedFilter") \
  .facet("foreseenUseFilter") \
  .facet("useNlpSpecificFilter") \
  .facet("lingualityTypeFilter") \
  .facet("multilingualityTypeFilter") \
  .facet("modalityTypeFilter") \
  .facet("mimeTypeFilter") \
  .facet("bestPracticesFilter") \
  .facet("domainFilter") \
  .facet("geographicCoverageFilter") \
  .facet("timeCoverageFilter") \
  .facet("subjectFilter")

urlpatterns = patterns('metashare.repository.views',
  (r'^browse/(?P<object_id>[123456789]\d*)/$',
    'view'),
  (r'^download/(?P<object_id>[123456789]\d*)/$',
    'download'),
  url(r'^search/$',
    search_view_factory(view_class=MetashareFacetedSearchView,
                        form_class=FacetedBrowseForm,
                        template='repository/search.html',
                        searchqueryset=sqs)),
)
