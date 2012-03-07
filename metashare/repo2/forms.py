import logging
from django import forms
from metashare.settings import LOG_LEVEL, LOG_HANDLER


from haystack.forms import FacetedSearchForm

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repo2.forms')
LOGGER.addHandler(LOG_HANDLER)


class SimpleSearchForm(forms.Form):
    """
    A SimpleSearch form basically renders a single text input a la Google.
    """
    keywords = forms.CharField(max_length=200, required=False,
      label="Keywords:",
      widget=forms.TextInput(attrs={'class':'advancedbox'}))


class FacetedBrowseForm(FacetedSearchForm):
    """
    A custom `FacetedSearchForm` for faceted browsing and searching.
    """
    def search(self):
        """
        A blend of its super methods with only a different base
        `SearchQuerySet` in case of empty/invalid queries.
        """
        sqs = self.searchqueryset
        if self.is_valid() and self.cleaned_data.get('q'):
            sqs = sqs.auto_query(self.cleaned_data['q'])
        if self.load_all:
            sqs = sqs.load_all()
        # we need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:
        for facet in [f for f in self.selected_facets if ":" in f]:
            field, value = facet.split(":", 1)
            if value:
                sqs = sqs.narrow(u'%s:"%s"' % (field, sqs.query.clean(value)))
        return sqs
