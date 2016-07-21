import logging
import re

from django import forms
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from metashare.recommendations.recommendations import get_more_from_same_creators, \
    get_more_from_same_projects
from metashare.repository.models import resourceInfoType_model
from metashare.repository.search_indexes import resourceInfoType_modelIndex
from metashare.settings import LOG_HANDLER

from haystack.forms import FacetedSearchForm
from haystack.query import SQ


# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)


# define special query prefixes
MORE_FROM_SAME_CREATORS = "mfsc"
MORE_FROM_SAME_PROJECTS = "mfsp"


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
            # extract special queries
            special_queries, query = \
              _extract_special_queries(self.cleaned_data.get('q'))
            if query:
                sqs = sqs.auto_query(query)
            if (special_queries):
                # for each special query, get the Django internal resource ids
                # matching the query and filter the SearchQuerySet accordingly
                for _sq in special_queries:
                    _res_ids = _process_special_query(_sq)
                    if _res_ids:
                        _sq = SQ()
                        for _id in _res_ids:
                            _sq.add(SQ(django_id=_id), SQ.OR)
                        sqs = sqs.filter(_sq)
                    else:
                        # force empty search result if no ids are returned
                        # for a special query
                        sqs = sqs.none()
                        break
        if self.load_all:
            sqs = sqs.load_all()
        # we need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:
        for facet in [f for f in self.selected_facets if ":" in f]:
            field, value = facet.split(":", 1)
            # only add facets which are also in the search index
            # pylint: disable-msg=E1101
            if not field in resourceInfoType_modelIndex.fields:
                LOGGER.info('Ignoring unknown facet field "%s".', field)
                continue
            if value:
                sqs = sqs.narrow(u'%s:"%s"' % (field, sqs.query.clean(value)))
        return sqs

    def clean(self):
        # add validation errors for unknown facet fields in the request:
        _errors = []
        for facet in self.selected_facets:
            field = facet.split(":", 1)[0]
            # pylint: disable-msg=E1101
            if not field in resourceInfoType_modelIndex.fields:
                _errors.append(
                    _("Ignoring an unknown filter from your query: %s") % field)
        if _errors:
            raise forms.ValidationError(_errors)

        return super(FacetedBrowseForm, self).clean()


def _extract_special_queries(query):
    """
    Extracts from the given query string all special queries;
    returns the original query that is stripped from the special queries
    and the extracted special queries;
    currently , we have two special queries:
    more-from-creator-of:<resource-id>
    more-from-project-of:<resource-id>
    """
    # here we collect the special queries
    special_queries = []
    
    for _token in query.split():
        if _token.startswith(MORE_FROM_SAME_CREATORS)\
          or _token.startswith(MORE_FROM_SAME_PROJECTS):
            special_queries.append(_token)
    # remove special queries from original query
    if special_queries:
        for _sq in special_queries:
            query = query.replace(_sq, "")
        ws_pattern = re.compile(r'\s+')
        query = re.sub(ws_pattern, " ", query)
        query = query.strip()
        
    return special_queries, query
         
         
def _process_special_query(query):
    """
    Processes the given special query;
    returns a list of resource ids matching the query;
    ids are the INTERNAL Django ids, not the StorageObject identifiers!!!
    """
    query_type, resource_id = query.split(":")
    # get resource
    try:
        res = resourceInfoType_model.objects.get(
            storage_object__identifier=resource_id)
    except resourceInfoType_model.DoesNotExist:
        LOGGER.info('Ignoring unknown storage identifier "%s" in "%s" query.',
            resource_id, query_type)
        return []
    
    # get related resources
    if query_type == MORE_FROM_SAME_CREATORS:
        rel_res = get_more_from_same_creators(res)
    elif query_type == MORE_FROM_SAME_PROJECTS:
        rel_res = get_more_from_same_projects(res)
    else:
        LOGGER.info('Ignoring unknown special query type "%s".', query_type)
        return []
    # return internal ids from related resources
    return [x.id for x in rel_res]
    

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
                           forms.widgets.RadioChoiceInput(self.name, self.value,
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


class DownloadContactForm(forms.Form):
    """
    A `Form` for sending a contact request regarding the download of a resource
    """
    userEmail = forms.EmailField(label=_("Your e-mail"))
    message = forms.CharField(label=_("Your message"), widget=forms.Textarea())
