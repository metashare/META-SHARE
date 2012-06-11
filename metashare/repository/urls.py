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
  .facet("subjectFilter") \
  .facet("corporaAnnotationTypeFilter") \
  .facet("corporaAnnotationFormatFilter") \
  .facet("ldLanguageDescriptionTypeFilter") \
  .facet("ldEncodingLevelFilter") \
  .facet("ldGrammaticalPhenomenaCoverageFilter") \
  .facet("lcrLexicalResourceTypeFilter") \
  .facet("lcrEncodingLevelFilter") \
  .facet("lcrLinguisticInformationFilter") \
  .facet("tsToolServiceTypeFilter") \
  .facet("tsToolServiceSubTypeFilter") \
  .facet("tsLanguageDependentTypeFilter") \
  .facet("tsInputOutputResourceTypeFilter") \
  .facet("tsInputOutputMediaTypeFilter") \
  .facet("tsAnnotationTypeFilter") \
  .facet("tsAnnotationFormatFilter") \
  .facet("tsEvaluatedFilter") \
  .facet("textTextGenreFilter") \
  .facet("textTextTypeFilter") \
  .facet("textRegisterFilter") \
  .facet("audioAudioGenreFilter") \
  .facet("audioSpeechGenreFilter") \
  .facet("audioRegisterFilter") \
  .facet("audioSpeechItemsFilter") \
  .facet("audioNaturalityFilter") \
  .facet("audioConversationalTypeFilter") \
  .facet("audioScenarioTypeFilter") \
  .facet("videoVideoGenreFilter") \
  .facet("videoTypeOfVideoContentFilter") \
  .facet("videoNaturalityFilter") \
  .facet("videoConversationalTypeFilter") \
  .facet("videoScenarioTypeFilter") \
  .facet("imageImageGenreFilter") \
  .facet("imageTypeOfImageContentFilter") \
  .facet("tnTypeOfTnContentFilter") \
  .facet("tnGramBaseItemFilter") \
  .facet("tnGramOrderFilter")

urlpatterns = patterns('metashare.repository.views',
  (r'^browse/[\w\-]*/(?P<object_id>\w+)/$',
    'view'),
  (r'^download/(?P<object_id>\w+)/$',
    'download'),
  url(r'^search/$',
    search_view_factory(view_class=MetashareFacetedSearchView,
                        form_class=FacetedBrowseForm,
                        template='repository/search.html',
                        searchqueryset=sqs)),
)
