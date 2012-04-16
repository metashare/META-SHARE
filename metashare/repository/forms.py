import logging

from django import forms
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


from metashare.settings import LOG_LEVEL, LOG_HANDLER

from haystack.forms import FacetedSearchForm

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repository.forms')
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
        class _LicenseSelectionRenderer(forms.widgets.RadioFieldRenderer):
            """
            A custom `RadioSelectRenderer` for rendering license selections.
        
            This widget does not only contain radio buttons with license name
            labels but additionally short license information blocks for each
            license.
            """
            def __iter__(self):
                for i, choice in enumerate(self.choices):
                    yield (licences[choice[0]][0],
                           forms.widgets.RadioInput(self.name, self.value,
                                                self.attrs.copy(), choice, i))

            def render(self):
                return mark_safe(u'<ul>{0}\n</ul>'.format(
                    u'\n'.join([u'<li><div>{0}</div>\n{1}</li>' \
                                    .format(force_unicode(w),
                                            self._create_restrictions_block(l,
                                                                w.choice_value))
                                for (l, w) in self])))

            def _create_restrictions_block(self, licence_info, licence_name):
                """
                Creates an HTML block element string containing the restrictions
                of the given license information.
                """
                result = u'<div><p>{0}</p>\n<ul>' \
                    .format(_('Restrictions of use:'))
                r_list = licence_info.get_restrictionsOfUse_display_list()
                if r_list:
                    for restr in r_list:
                        result += u'<li>{0}</li>'.format(restr)
                if licences[licence_name][1]:
                    direct_download_msg = _('direct download available')
                else:
                    direct_download_msg = _('no direct download available')
                result += u'<li>{0}</li></ul></div>'.format(direct_download_msg)
                return result

        self.fields['licence'] = \
            forms.ChoiceField(choices=[(name, name) for name in licences],
                              widget=forms.widgets.RadioSelect(
                                        renderer=_LicenseSelectionRenderer))


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
