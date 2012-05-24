"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""

import logging

from datetime import datetime
from os.path import split, getsize
from urllib import urlopen
from mimetypes import guess_type

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext

from haystack.views import FacetedSearchView

from metashare.repository.forms import LicenseSelectionForm, LicenseAgreementForm
from metashare.repository.models import licenceInfoType_model, resourceInfoType_model
from metashare.repository.search_indexes import resourceInfoType_modelIndex
from metashare.settings import LOG_LEVEL, LOG_HANDLER, MEDIA_URL
from metashare.stats.model_utils import getLRStats, saveLRStats, \
    saveQueryStats, VIEW_STAT, DOWNLOAD_STAT


MAXIMUM_READ_BLOCK_SIZE = 4096

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repository.views')
LOGGER.addHandler(LOG_HANDLER)


def _convert_to_template_tuples(element_tree):
    """
    Converts the given ElementTree instance to template tuples.

    A template tuple contains:
    - a two-tuple (component, values) for complex nodes, and
    - a one-tuple ((key, value),) for simple tags.

    The length distinction allows for recursive rendering in the template.
    See repository/detail.html and repository/detail_view.html for more information.

    Rendering recursively inside the Django template system needs this trick:
    - http://blog.elsdoerfer.name/2008/01/22/recursion-in-django-templates/

    """
    # If we are dealing with a complex node containing children nodes, we have
    # to first recursively collect the data values from the sub components.
    if len(element_tree.getchildren()):
        values = []
        for child in element_tree.getchildren():
            values.append(_convert_to_template_tuples(child))
        return (element_tree.tag, values)

    # Otherwise, we return a tuple containg (key, value, required), 
    # i.e., (tag, text, <0,1>).
    # The "required" element was added to the tree, for passing 
    # information about whether a field is required or not, to correctly
    # render the single resource view.
    else:
        # cfedermann: use proper getattr access to prevent an AttributeError
        # being thrown for cases, like /repository/browse/1222/, where some
        # required attributes seem to be missing.
        required = getattr(element_tree, 'required', 0)
        return ((element_tree.tag, element_tree.text, required),)


# a type providing an enumeration of META-SHARE member types
MEMBER_TYPES = type('MemberEnum', (), dict(GOD=100, FULL=3, ASSOCIATE=2, NON=1))


# a dictionary holding a URL for each download licence and a member type which
# is required at a minimum to be able to download the associated resource
# straight away; otherwise the licence requires a hard-copy signature
LICENCEINFOTYPE_URLS_LICENCE_CHOICES = {
  'AGPL': (MEDIA_URL + 'licences/GNU_agpl-3.0.htm', MEMBER_TYPES.NON),
  'LGPL': (MEDIA_URL + 'licences/GNU_lgpl-2.0.htm', MEMBER_TYPES.NON),
  'LGPLv3': (MEDIA_URL + 'licences/GNU_lgpl-3.0.htm', MEMBER_TYPES.NON),
  'CC0': (MEDIA_URL + 'licences/CC0v1.0.htm', MEMBER_TYPES.NON),
  'CC_BY-SA_3.0': (MEDIA_URL + 'licences/CC-BYSAv3.0.htm', MEMBER_TYPES.NON),
  'CC_BY-NC-ND': (MEDIA_URL + 'licences/CC-BYNCNDv3.0.htm', MEMBER_TYPES.NON),
  'CC_BY-NC-SA': (MEDIA_URL + 'licences/CC-BYNCSAv2.5.htm', MEMBER_TYPES.NON),
  'CC_BY-NC': (MEDIA_URL + 'licences/CC-BYNCv3.0.htm', MEMBER_TYPES.NON),
  'CC_BY-ND': (MEDIA_URL + 'licences/CC-BYNDv3.0.htm', MEMBER_TYPES.NON),
  'CC_BY-SA': (MEDIA_URL + 'licences/CC-BYSAv2.5.htm', MEMBER_TYPES.NON),
  'CC_BY': (MEDIA_URL + 'licences/CC-BYv3.0.htm', MEMBER_TYPES.NON),
  'CC_BY-NC-SA_3.0': (MEDIA_URL + 'licences/CC-BYNCSAv3.0.htm',
                      MEMBER_TYPES.NON),
  'MSCommons_BY': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BY_v1.0.htm',
                   MEMBER_TYPES.FULL),
  'MSCommons_BY-NC': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNC_v1.0.htm',
                      MEMBER_TYPES.FULL),
  'MSCommons_BY-NC-ND': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNCND_' \
                         'v1.0.htm', MEMBER_TYPES.FULL),
  'MSCommons_BY-NC-SA': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNCSA' \
                         '_v1.0.htm', MEMBER_TYPES.FULL),
  'MSCommons_BY-ND': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYND_v1.0.htm',
                      MEMBER_TYPES.FULL),
  'MSCommons_BY-SA': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYSA_v1.0.htm',
                      MEMBER_TYPES.FULL),
  'MSCommons_COM-NR-FF': (MEDIA_URL + 'licences/META-SHARE_Commercial_' \
        'NoRedistribution_For-a-Fee_v0.7.htm', MEMBER_TYPES.GOD),
  'MSCommons_COM-NR': (MEDIA_URL + 'licences/META-SHARE_Commercial_' \
        'NoRedistribution_v0.7.htm', MEMBER_TYPES.GOD),
  'MSCommons_COM-NR-ND-FF': (MEDIA_URL + 'licences/META-SHARE_Commercial_' \
        'NoRedistribution_NoDerivatives_For-a-fee-v1.0.htm', MEMBER_TYPES.GOD),
  'MSCommons_COM-NR-ND': (MEDIA_URL + 'licences/META-SHARE_Commercial_' \
        'NoRedistribution_NoDerivatives-v1.0.htm', MEMBER_TYPES.GOD),
  'MSCommons_NoCOM-NC-NR-ND-FF': (MEDIA_URL + 'licences/META-SHARE_' \
        '_NoRedistribution_NoDerivatives_For-a-fee-v1.0.htm', MEMBER_TYPES.GOD),
  'MSCommons_NoCOM-NC-NR-ND': (MEDIA_URL + 'licences/META-SHARE_Commercial_' \
        'NoRedistribution_NoDerivatives-v1.0.htm', MEMBER_TYPES.GOD),
  'MSCommons_NoCOM-NC-NR-FF': (MEDIA_URL + 'licences/META-SHARE_NonCommercial' \
        '_NoRedistribution_For-a-Fee-v1.0.htm', MEMBER_TYPES.GOD),
  'MSCommons_NoCOM-NC-NR': (MEDIA_URL + 'licences/META-SHARE_NonCommercial_' \
        'NoRedistribution-v1.0.htm', MEMBER_TYPES.GOD),
  'ELRA_EVALUATION': (MEDIA_URL + 'licences/EVALUATION.htm', MEMBER_TYPES.GOD),
  'ELRA_VAR': (MEDIA_URL + 'licences/VAR-v3_2007.htm', MEMBER_TYPES.GOD),
  'ELRA_END_USER': (MEDIA_URL + 'licences/ENDUSER-v3_2007.htm',
                    MEMBER_TYPES.GOD),
  'proprietary': ('', MEMBER_TYPES.GOD),
  'CLARIN_PUB': ('', MEMBER_TYPES.GOD),
  'CLARIN_ACA-NC': ('', MEMBER_TYPES.GOD),
  'CLARIN_ACA': ('', MEMBER_TYPES.GOD),
  'CLARIN_RES': ('', MEMBER_TYPES.GOD),
  'Princeton_Wordnet': (MEDIA_URL + 'licences/WordNet-3.0.txt',
                        MEMBER_TYPES.NON),
  'GPL': (MEDIA_URL + 'licences/GNU_gpl-3.0.htm', MEMBER_TYPES.NON),
  'GFDL': (MEDIA_URL + 'licences/GNU_fdl-1.3.htm', MEMBER_TYPES.NON),
  'ApacheLicence_V2.0': (MEDIA_URL + 'licences/Apache-2.0.htm',
                         MEMBER_TYPES.NON),
  'BSD-style': (MEDIA_URL + 'licences/BSD_licence.htm', MEMBER_TYPES.NON),
  'underNegotiation': ('', MEMBER_TYPES.GOD),
  'other': ('', MEMBER_TYPES.GOD)
}


def _get_user_membership(user):
    """
    Returns a `MEMBER_TYPES` type based on the permissions of the given
    authenticated user. 
    """
    if user.has_perm('accounts.ms_full_member'):
        return MEMBER_TYPES.FULL
    elif user.has_perm('accounts.ms_associate_member'):
        return MEMBER_TYPES.ASSOCIATE
    return MEMBER_TYPES.NON


def _get_licences(resource, user_membership):
    """
    Returns the licences under which a download/purchase of the given resource
    is possible for the given user membership.
    
    The result is a dictionary mapping from licence names to pairs. Each pair
    contains the corresponding `licenceInfoType_model` and a boolean denoting
    whether the resource may (and can) be directly downloaded or if there need
    to be further negotiations of some sort.
    """
    licence_infos = tuple(licenceInfoType_model.objects \
        .filter(back_to_distributioninfotype_model__id=\
                resource.distributionInfo.id))
    
    all_licenses = dict([(l_name, l_info) for l_info in licence_infos
                         for l_name in l_info.get_licence_display_list()])
    result = {}
    for name, info in all_licenses.items():
        access = LICENCEINFOTYPE_URLS_LICENCE_CHOICES.get(name, None)
        if access == None:
            LOGGER.warn("Unknown license name discovered in the database for " \
                        "object #{}: {}".format(resource.id, name))
            del all_licenses[name]
        elif user_membership >= access[1] \
                and (info.downloadLocation \
                     or resource.storage_object.has_local_download_copy()):
            # the resource can be downloaded somewhere under the current license
            # terms and the user's membership allows her to immediately download
            # the resource
            result[name] = (info, True)
        else:
            # further negotiations are required with the current license
            result[name] = (info, False)
    return result


@login_required
def download(request, object_id):
    """
    Renders the resource download/purchase view including license selection,
    etc.
    """
    if not request.user.is_active:
        return HttpResponseForbidden()
    user_membership = _get_user_membership(request.user)

    # here we are only interested in licenses (or their names) of the specified
    # resource that allow the current user a download/purchase
    resource = get_object_or_404(resourceInfoType_model,
                                 storage_object__identifier=object_id)
    licences = _get_licences(resource, user_membership)

    licence_choice = None
    if request.method == "POST":
        licence_choice = request.POST.get('licence', None)
        if licence_choice and 'in_licence_agree_form' in request.POST:
            la_form = LicenseAgreementForm(licence_choice, data=request.POST)
            if la_form.is_valid():
                # before really providing the download, we have to make sure
                # that the user hasn't tried to circumvent the permission system
                if licences[licence_choice][1]:
                    return _provide_download(request, resource,
                                licences[licence_choice][0].downloadLocation)
            else:
                return render_to_response('repository/licence_agreement.html',
                    { 'form': la_form, 'resource': resource,
                      'licence_path': \
                      LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licence_choice][0],
                      'download_available': licences[licence_choice][1] },
                    context_instance=RequestContext(request))
        elif licence_choice and not licence_choice in licences:
            licence_choice = None

    if len(licences) == 1:
        # no need to manually choose amongst 1 license ...
        licence_choice = licences.iterkeys().next()

    if licence_choice:
        return render_to_response('repository/licence_agreement.html',
            { 'form': LicenseAgreementForm(licence_choice),
              'resource': resource,
              'licence_path': \
                LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licence_choice][0],
              'download_available': licences[licence_choice][1] },
            context_instance=RequestContext(request))
    elif len(licences) > 1:
        return render_to_response('repository/licence_selection.html',
            { 'form': LicenseSelectionForm(licences), 'resource': resource },
            context_instance=RequestContext(request))
    else:
        return render_to_response('repository/lr_not_downloadable.html',
                                  { 'resource': resource,
                                    'reason': 'no_suitable_license' },
                                  context_instance=RequestContext(request))


def _provide_download(request, resource, download_urls):
    """
    Returns an HTTP response with a download of the given resource.
    """
    if resource.storage_object.has_local_download_copy():
        try:
            dl_path = resource.storage_object.get_download()
            def dl_stream_generator():
                with open(dl_path, 'rb') as _local_data:
                    _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)
                    while _chunk:
                        yield _chunk
                        _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)

            # build HTTP response with a guessed mime type; the response
            # content is a stream of the download file
            filemimetype , encod = guess_type(dl_path)
            if not filemimetype:
                filemimetype = "application/octet-stream"
            response = HttpResponse(dl_stream_generator(),
                                    mimetype=filemimetype)
            response['Content-Length'] = getsize(dl_path) 
            response['Content-Disposition'] = 'attachment; filename={0}' \
                                                .format(split(dl_path)[1])

            # maintain download statistics and return the response for download
            saveLRStats(resource, request.user.username,
                        _get_sessionid(request), DOWNLOAD_STAT)
            LOGGER.info("Offering a local download of resource #{0}." \
                        .format(resource.id))
            return response
        except:
            LOGGER.warn("An error has occurred while trying to provide the " \
                        "local download copy of resource #{0}." \
                        .format(resource.id))
    # redirect to a download location, if available
    elif download_urls:
        for url in download_urls:
            status_code = urlopen(url).getcode()
            if not status_code or status_code < 400:
                saveLRStats(resource, request.user.username,
                            _get_sessionid(request), DOWNLOAD_STAT)
                LOGGER.info("Redirecting to {0} for the download of resource " \
                            "#{1}.".format(url, resource.id))
                return redirect(url)
        LOGGER.warn("No download could be offered for resource #{0}. These " \
                    "URLs were tried: {1}".format(resource.id, download_urls))
    else:
        LOGGER.error("No download could be offered for resource #{0} with " \
                     "storage object identifier #{1} although our code " \
                     "considered it to be downloadable!".format(resource.id,
                                           resource.storage_object.identifier))

    # no download could be provided
    return render_to_response('repository/lr_not_downloadable.html',
                              { 'resource': resource, 'reason': 'internal' },
                              context_instance=RequestContext(request))


def _get_sessionid(request):
    """
    Returns the session ID stored in the cookies of the given request.
    
    The empty string is returned, if there is no session ID available.
    """
    if request.COOKIES:
        return request.COOKIES.get('sessionid', '')
    return ''


@login_required
def create(request):
    """
    Redirects to the Django admin backend editor for resources.
    """
    return redirect(reverse('admin:repository_resourceinfotype_model_add'))


def view(request, object_id=None):
    """
    Render browse or detail view for the repository application.
    """
    resource = get_object_or_404(resourceInfoType_model, storage_object__identifier=object_id)

    # Convert resource to ElementTree and then to template tuples.
    resource_tree = resource.export_to_elementtree()
    lr_content = _convert_to_template_tuples(resource_tree)

    # we need to know if the resource is published or not
    resource_published = resource.storage_object.published

    # Define context for template rendering.
    context = {'resource': resource, 'lr_content': lr_content,
               'RESOURCE_PUBLISHED': resource_published}
    template = 'repository/lr_view.html'

    # For staff users, we have to add LR_EDIT which contains the URL of
    # the Django admin backend page for this resource.
    if request.user.is_staff:
        context['LR_EDIT'] = reverse(
            'admin:repository_resourceinfotype_model_change', args=(object_id,))

    # in general, only logged in users may download/purchase any resources
    context['LR_DOWNLOAD'] = request.user.is_active

    # Update statistics and create a report about the user actions on LR
    if hasattr(resource.storage_object, 'identifier'):
        sessionid = ""
        if request.COOKIES:
            sessionid = request.COOKIES.get('sessionid', '')
        saveLRStats(resource, request.user.username, sessionid, VIEW_STAT)
        context['LR_STATS'] = getLRStats(resource.storage_object.identifier)

    # Render and return template with the defined context.
    ctx = RequestContext(request)
    return render_to_response(template, context, context_instance=ctx)


class MetashareFacetedSearchView(FacetedSearchView):
    """
    A modified `FacetedSearchView` which makes sure that only such results will
    be returned that are accessible by the current user.
    """
    def get_results(self):
        sqs = super(MetashareFacetedSearchView, self).get_results()
        if not self.request.user.is_staff:
            sqs = sqs.filter(published=True)

        # Sort the results (on only one sorting value)
        if 'sort' in self.request.GET:
            sort_list = self.request.GET.getlist('sort')
            
            if sort_list[0] == 'resourcename_asc':
                sqs = sqs.order_by('resourceNameSort_exact')
            elif sort_list[0] == 'resourcename_desc':
                sqs = sqs.order_by('-resourceNameSort_exact')
            elif sort_list[0] == 'resourcetype_asc':
                sqs = sqs.order_by('resourceTypeSort_exact')
            elif sort_list[0] == 'resourcetype_desc':
                sqs = sqs.order_by('-resourceTypeSort_exact')
            elif sort_list[0] == 'mediatype_asc':
                sqs = sqs.order_by('mediaTypeSort_exact')
            elif sort_list[0] == 'mediatype_desc':
                sqs = sqs.order_by('-mediaTypeSort_exact')
            elif sort_list[0] == 'languagename_asc':
                sqs = sqs.order_by('languageNameSort_exact')
            elif sort_list[0] == 'languagename_desc':
                sqs = sqs.order_by('-languageNameSort_exact')
            else:
                sqs = sqs.order_by('resourceNameSort_exact')
        else:
            sqs = sqs.order_by('resourceNameSort_exact')

        # collect statistics about the query
        starttime = datetime.now()
        results_count = sqs.count()
        if self.query:
            saveQueryStats(self.query, str(sorted(self.request.GET.getlist("selected_facets"))), \
                self.request.user.username, results_count, (datetime.now() - starttime).microseconds)

        return sqs
    
    def _get_selected_facets(self):
        """
        Returns the selected facets from the current GET request as a more
        structured Python dictionary.
        """
        result = {}
        for facet in self.request.GET.getlist("selected_facets"):
            if ":" in facet:
                field, value = facet.split(":", 1)
                if value:
                    if field in result:
                        result[field].append(value)
                    else:
                        result[field] = [value]
        return result
    
    def _create_filters_structure(self, facet_fields):
        """
        Creates a data structure encapsulating most of the logic which is
        required for rendering the filters/facets of the META-SHARE search.
        
        Takes the raw facet 'fields' dictionary which is (indirectly) returned
        by the `facet_counts()` method of a `SearchQuerySet`.
        """
        import re

        result = []
        # pylint: disable-msg=E1101
        filter_labels = [(name, field.label, field.facet_id, field.parent_id)
                         for name, field
                         in resourceInfoType_modelIndex.fields.iteritems()
                         if name.endswith("Filter")]
        filter_labels.sort(key=lambda f: f[2])
        sel_facets = self._get_selected_facets()
        # Step (1): if there are any selected facets, then add these first:
        if sel_facets:
            # add all top level facets (sorted by their facet IDs):
            for name, label, facet_id, _ in [f for f in filter_labels if f[3] == 0]:
                name_exact = '{0}_exact'.format(name)
                # only add selected facets in step (1)
                if name_exact in sel_facets:
                    subfacets = [f for f in filter_labels if f[3] == facet_id]
                    subfacets_exactname_list = []
                    subfacets_exactname_list.extend([u'{0}_exact'.format(subfacet[0]) for subfacet in subfacets])
                    subresults = []
                    for facet in subfacets:
                        subresults = self.show_subfilter(facet, sel_facets, facet_fields, subresults)
                    items = facet_fields.get(name)
                    if items:
                        removable = []
                        addable = []
                        # only items with a count > 0 are shown
                        for item in [i for i in items if i[1] > 0]:
                            if item[0] in sel_facets[name_exact]:
                                if item[0] != "":
                                    lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', item[0][0].capitalize()+item[0][1:]))[:-1]
                                    removable.append({'label': lab_item,
                                        'count': item[1], 'targets':
                                            [u'{0}:{1}'.format(name, value)
                                             for name, values in
                                             sel_facets.iteritems() for value in
                                             values if (name != name_exact
                                             or value != item[0]) and name not in subfacets_exactname_list]})
                            else:
                                targets = [u'{0}:{1}'.format(name, value)
                                           for name, values in
                                           sel_facets.iteritems()
                                           for value in values]
                                targets.append(u'{0}:{1}'.format(name_exact,
                                                                 item[0]))
                                if item[0] != "":
                                    lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', item[0][0].capitalize()+item[0][1:]))[:-1]
                                    addable.append({'label': lab_item,
                                                'count': item[1],
                                                'targets': targets})

                        result.append({'label': label, 'removable': removable,
                                       'addable': addable, 'subresults': subresults})                    

        # Step (2): add all top level facets without selected facet items at the
        # end (sorted by their facet IDs):
        for name, label, facet_id, _ in [f for f in filter_labels if f[3] == 0]:
            name_exact = '{0}_exact'.format(name)
            # only add facets without selected items in step (2)
            if not name_exact in sel_facets:
                items = facet_fields.get(name)
                if items:
                    addable = []
                    # only items with a count > 0 are shown
                    for item in [i for i in items if i[1] > 0]:
                        targets = [u'{0}:{1}'.format(name, value)
                                   for name, values in sel_facets.iteritems()
                                   for value in values]
                        targets.append(u'{0}:{1}'.format(name_exact, item[0]))

                        if item[0] != "":
                            lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', item[0][0].capitalize()+item[0][1:]))[:-1]
                            addable.append({'label': lab_item, 'count': item[1],
                                        'targets': targets})
                    subresults = [f for f in filter_labels if f[3] == facet_id] 
                    result.append({'label': label, 'removable': [],
                                   'addable': addable, 'subresults': subresults})

        return result

    def extra_context(self):
        extra = super(MetashareFacetedSearchView, self).extra_context()
        # add a data structure encapsulating most of the logic which is required
        # for rendering the filters/facets
        extra['filters'] = self._create_filters_structure(
                                        extra['facets']['fields'])
        return extra
    
    def show_subfilter(self, facet, sel_facets, facet_fields, results):
        import re

        name = facet[0]
        label = facet[1]

        name_exact = '{0}_exact'.format(name)

        if name_exact in sel_facets:
            items = facet_fields.get(name)
            if items:
                removable = []
                addable = []
                # only items with a count > 0 are shown
                for item in [i for i in items if i[1] > 0]:
                    if item[0] in sel_facets[name_exact]:
                        if item[0] != "":
                            lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', item[0][0].capitalize()+item[0][1:]))[:-1]
                            removable.append({'label': lab_item,
                                'count': item[1], 'targets':
                                    [u'{0}:{1}'.format(name, value)
                                     for name, values in
                                     sel_facets.iteritems() for value in
                                     values if name != name_exact
                                     or value != item[0]]})
                    else:
                        targets = [u'{0}:{1}'.format(name, value)
                                   for name, values in
                                   sel_facets.iteritems()
                                   for value in values]
                        targets.append(u'{0}:{1}'.format(name_exact,
                                                         item[0]))
                        if item[0] != "":
                            lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', item[0][0].capitalize()+item[0][1:]))[:-1]
                            addable.append({'label': lab_item,
                                        'count': item[1],
                                        'targets': targets})
                if (addable+removable):
                    results.append({'label': label, 'removable': removable,
                               'addable': addable})
        else:
            items = facet_fields.get(name)
            if items:
                addable = []
                # only items with a count > 0 are shown
                for item in [i for i in items if i[1] > 0]:
                    targets = [u'{0}:{1}'.format(name, value)
                               for name, values in sel_facets.iteritems()
                               for value in values]
                    targets.append(u'{0}:{1}'.format(name_exact, item[0]))
                    if item[0] != "":
                        lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', item[0][0].capitalize()+item[0][1:]))[:-1]
                        addable.append({'label': lab_item, 'count': item[1],
                                    'targets': targets})
                if addable:
                    results.append({'label': label, 'removable': [],
                               'addable': addable})

        return results
