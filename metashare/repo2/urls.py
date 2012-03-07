"""
Project: META-SHARE prototype implementation
Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.conf.urls.defaults import patterns, url
from haystack.views import search_view_factory
from haystack.query import SearchQuerySet

from metashare.repo2.forms import FacetedBrowseForm
from metashare.repo2.views import MetashareFacetedSearchView

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

urlpatterns = patterns('metashare.repo2.views',
  (r'^browse/$',
    'simple_search'),
  (r'^browse/(?P<object_id>\d+)/$',
    'view'),
  (r'^download/(?P<object_id>.+)/$',
    'download'),
  (r'^licence/(?P<object_id>.+)/$',
    'getlicence'),

  # TODO: at some later stage replace the above URL configurations so that they
  # work with Haystack; the following URL pattern won't be needed anymore then:
  url(r'^search2/$',
    search_view_factory(view_class=MetashareFacetedSearchView,
                        form_class=FacetedBrowseForm,
                        template='repo2/search.html',
                        searchqueryset=sqs)),
)
