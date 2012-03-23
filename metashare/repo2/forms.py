import logging

from django import forms
from django.utils.translation import ugettext as _


from metashare.settings import LOG_LEVEL, LOG_HANDLER

from haystack.forms import FacetedSearchForm

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repo2.forms')
LOGGER.addHandler(LOG_HANDLER)


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


class LicenseSelectionForm(forms.Form):
    """
    A `Form` for presenting download licenses and selecting exactly one of them.
    """
    def __init__(self, licences, *args, **kwargs):
        """
        Initializes the `LicenseSelectionForm` with the given licenses.
        """
        super(LicenseSelectionForm, self).__init__(*args, **kwargs)
        self.fields['licence'] = forms.ChoiceField(choices=licences,
                                            widget=forms.widgets.RadioSelect())


class LicenseAgreementForm(forms.Form):
    """
    A `Form` for presenting a license to which the user must agree.
    """
    in_licence_agree_form = forms.BooleanField(initial=True,
                                               widget=forms.HiddenInput())
    licence_agree = forms.BooleanField(label=_('I agree to these licence ' \
                            'terms and would like to download the resource.'))

    def __init__(self, licence, *args, **kwargs):
        """
        Initializes the `LicenseAgreementForm` with the given licence.
        """
        super(LicenseAgreementForm, self).__init__(*args, **kwargs)
        self.fields['licence'] = forms.CharField(initial=licence,
                                                 widget=forms.HiddenInput())
