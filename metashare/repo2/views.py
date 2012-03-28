"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""

import logging

from datetime import datetime
from os.path import split
from urllib import urlopen

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext

from haystack.views import FacetedSearchView

from metashare.repo2.forms import LicenseSelectionForm, LicenseAgreementForm
from metashare.repo2.models import licenceInfoType_model, resourceInfoType_model
from metashare.settings import LOG_LEVEL, LOG_HANDLER, MEDIA_URL
from metashare.stats.model_utils import getLRStats, saveLRStats, \
    saveQueryStats, VIEW_STAT, DOWNLOAD_STAT


MAXIMUM_READ_BLOCK_SIZE = 4096

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.repo2.views')
LOGGER.addHandler(LOG_HANDLER)


def _convert_to_template_tuples(element_tree):
    """
    Converts the given ElementTree instance to template tuples.

    A template tuple contains:
    - a two-tuple (component, values) for complex nodes, and
    - a one-tuple ((key, value),) for simple tags.

    The length distinction allows for recursive rendering in the template.
    See repo2/detail.html and repo2/detail_view.html for more information.

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

    # Otherwise, we return a tuple containg (key, value), i.e., (tag, text).
    else:
        return ((element_tree.tag, element_tree.text),)


# a dictionary holding a URL for each download licence and a boolean marking
# whether the licence requires an hard-copy signature or not
LICENCEINFOTYPE_URLS_LICENCE_CHOICES = {
  'AGPL': (MEDIA_URL + 'licences/GNU_agpl-3.0.htm', False),
  'LGPL': (MEDIA_URL + 'licences/GNU_lgpl-2.0.htm', False),
  'LGPLv3': (MEDIA_URL + 'licences/GNU_lgpl-3.0.htm', False),
  'CC': (MEDIA_URL + 'licences/CC0v1.0.htm', False),
  'CC_BY-SA_3.0': (MEDIA_URL + 'licences/CC-BYSAv3.0.htm', False),
  'CC_BY-NC-ND': (MEDIA_URL + 'licences/CC-BYNCNDv3.0.htm', False),
  'CC_BY-NC-SA': (MEDIA_URL + 'licences/CC-BYNCSAv2.5.htm', False),
  'CC_BY-NC': (MEDIA_URL + 'licences/CC-BYNCv3.0.htm', False),
  'CC_BY-ND': (MEDIA_URL + 'licences/CC-BYNDv3.0.htm', False),
  'CC_BY-SA': (MEDIA_URL + 'licences/CC-BYSAv2.5.htm', False),
  'CC_BY': (MEDIA_URL + 'licences/CC-BYv3.0.htm', False),
  'CC_BY-NC-SA_3.0': (MEDIA_URL + 'licences/CC-BYNCSAv3.0.htm', False),
  'MSCommons_BY': \
    (MEDIA_URL + 'licences/META-SHARE_COMMONS_BY_v1.0.htm', False),
  'MSCommons_BY-NC': \
    (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNC_v1.0.htm', False),
  'MSCommons_BY-NC-ND': \
    (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNCND_v1.0.htm', False),
  'MSCommons_BY-NC-SA': \
    (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm', False),
  'MSCommons_BY-ND': \
    (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYND_v1.0.htm', False),
  'MSCommons_BY-SA': \
    (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYSA_v1.0.htm', False),
  'MSCommons_COM-NR-FF': \
    (MEDIA_URL + 'licences/META-SHARE_Commercial_NoRedistribution_For-a-Fee' \
     '_v0.7.htm', True),
  'MSCommons_COM-NR': \
    (MEDIA_URL + 'licences/META-SHARE_Commercial_NoRedistribution_v0.7.htm',
     False),
  'MSCommons_COM-NR-ND-FF': \
    (MEDIA_URL + 'licences/META-SHARE_Commercial_NoRedistribution_' \
     'NoDerivatives_For-a-fee-v1.0.htm', True),
  'MSCommons_COM-NR-ND': \
    (MEDIA_URL + 'licences/META-SHARE_Commercial_NoRedistribution_' \
     'NoDerivatives-v1.0.htm', False),
  'MSCommons_NoCOM-NC-NR-ND-FF': \
    (MEDIA_URL + 'licences/META-SHARE_NonCommercial_NoRedistribution_' \
     'NoDerivatives_For-a-fee-v1.0.htm', True),
  'MSCommons_NoCOM-NC-NR-ND': \
    (MEDIA_URL + 'licences/META-SHARE_Commercial_NoRedistribution_' \
     'NoDerivatives-v1.0.htm', False),
  'MSCommons_NoCOM-NC-NR-FF': \
    (MEDIA_URL + 'licences/META-SHARE_NonCommercial_NoRedistribution_' \
     'For-a-Fee-v1.0.htm', True),
  'MSCommons_NoCOM-NC-NR': \
    (MEDIA_URL + 'licences/META-SHARE_NonCommercial_NoRedistribution-v1.0.htm',
     False),
  'ELRA_EVALUATION': (MEDIA_URL + 'licences/EVALUATION.htm', True),
  'ELRA_VAR': (MEDIA_URL + 'licences/VAR-v3_2007.htm', True),
  'ELRA_END_USER': (MEDIA_URL + 'licences/ENDUSER-v3_2007.htm', True),
  'ELRA_LIMITED': (MEDIA_URL + 'licences/Var-E-v2.htm', True),
  'proprietary': ('', True),
  'CLARIN_PUB': ('', True),
  'CLARIN_ACA-NC': ('', True),
  'CLARIN_ACA': ('', True),
  'CLARIN_RES': ('', True),
  'Princeton_Wordnet': (MEDIA_URL + 'licences/WordNet-3.0.txt', False),
  'GPL': (MEDIA_URL + 'licences/GNU_gpl-3.0.htm', False),
  'GeneralLicenceGrant': ('', True),
  'GFDL': (MEDIA_URL + 'licences/GNU_fdl-1.3.htm', False),
  'ApacheLicence_V2.0': (MEDIA_URL + 'licences/Apache-2.0.htm', False),
  'BSD-style': (MEDIA_URL + 'licences/BSD_licence.htm', False),
  'underNegotiation': ('', True),
  'other': ('', True)
}


def _get_download_licences(object_id):
    """
    Returns the licences under which a download of the resource with the given
    ID is possible.
    
    The result is a dictionary mapping from licence names to corresponding
    `licenceInfoType_model`s.
    """
    licence_infos = tuple(licenceInfoType_model.objects \
        .filter(back_to_distributioninfotype_model__id=object_id))
    result = dict([(l_name, l_info) for l_info in licence_infos
        if u'downloadable' in l_info.get_distributionAccessMedium_display_list()
        for l_name in l_info.get_licence_display_list()])
    return result


@login_required
def download(request, object_id):
    """
    Renders the resource download view including license selection, etc.
    """
    if not request.user.is_active:
        return HttpResponseForbidden()

    # here we are only interested in licenses (or their names) of the specified
    # resource that allow a download
    resource = get_object_or_404(resourceInfoType_model, pk=object_id)
    licences = _get_download_licences(object_id)

    licence_choice = None
    if request.method == "POST":
        licence_choice = request.POST.get('licence', None)
        if licence_choice and 'in_licence_agree_form' in request.POST:
            la_form = LicenseAgreementForm(licence_choice, data=request.POST)
            if la_form.is_valid():
                return _provide_download(request, resource,
                                    licences[licence_choice].downloadLocation)
            else:
                return render_to_response('repo2/licence_agreement.html',
                    { 'form': la_form, 'resource': resource,
                      'licence_path': \
                      LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licence_choice][0],
                      'requires_sig': \
                      LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licence_choice][1] },
                    context_instance=RequestContext(request))
        elif licence_choice and not licence_choice in licences:
            licence_choice = None

    if len(licences) == 1:
        # no need to manually choose amongst 1 license ...
        licence_choice = licences.iterkeys().next()

    if licence_choice:
        return render_to_response('repo2/licence_agreement.html',
            { 'form': LicenseAgreementForm(licence_choice),
              'resource': resource,
              'licence_path': \
                LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licence_choice][0],
              'requires_sig': \
                LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licence_choice][1] },
            context_instance=RequestContext(request))
    elif len(licences) > 1:
        return render_to_response('repo2/licence_selection.html',
            { 'form': LicenseSelectionForm(licences), 'resource': resource },
            context_instance=RequestContext(request))
    else:
        return render_to_response('repo2/lr_not_downloadable.html',
                                  { 'resource': resource },
                                  context_instance=RequestContext(request))


def _provide_download(request, resource, download_urls):
    """
    Returns an HTTP response with a download of the given resource.
    """
    if resource.storage_object.has_local_download_copy():
        try:
            dl_path = resource.storage_object.get_download()

            # build HTTP response with a generic, binary mime type
            response = HttpResponse(mimetype="application/octet-stream")
            response['Content-Disposition'] = 'attachment; filename={0}' \
                                                .format(split(dl_path)[1])
            with open(dl_path, 'rb') as _local_data:
                _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)
                while _chunk:
                    response.write(_chunk)
                    _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)

            # maintain download statistics and return the response for download
            saveLRStats(request.user.username,
                        resource.storage_object.identifier,
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
                saveLRStats(request.user.username,
                            resource.storage_object.identifier,
                            _get_sessionid(request), DOWNLOAD_STAT)
                LOGGER.info("Redirecting to {0} for the download of resource " \
                            "#{1}.".format(url, resource.id))
                return redirect(url)
        LOGGER.warn("No download could be offered for resource #{0}. These " \
                    "URLs were tried: {1}".format(resource.id, download_urls))
    else:
        LOGGER.warn("No download could be offered for resource #{0} with " \
                    "storage object identifier #{1} although it is marked as " \
                    "downloadable!".format(resource.id,
                                           resource.storage_object.identifier))

    # no download could be provided
    return render_to_response('repo2/lr_not_downloadable.html',
                              { 'resource': resource },
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
    return redirect(reverse('admin:repo2_resourceinfotype_model_add'))


def view(request, object_id=None):
    """
    Render browse or detail view for the repo2 application.
    """
    # If an object id is given, try to look up the corresponding resource in
    # the Django database, raising HTTP 404 if it cannot be found.
    if object_id:

        resource = get_object_or_404(resourceInfoType_model, pk=object_id)

        # Convert resource to ElementTree and then to template tuples.
        resource_tree = resource.export_to_elementtree()
        lr_content = _convert_to_template_tuples(resource_tree)

        # we need to know if the resource is published or not
        resource_published = resource.storage_object.published

        # Define context for template rendering.
        context = {'resource': resource, 'lr_content': lr_content,
                   'RESOURCE_PUBLISHED': resource_published}
        template = 'repo2/lr_view.html'

        # For staff users, we have to add LR_EDIT which contains the URL of
        # the Django admin backend page for this resource.
        if request.user.is_staff:
            context['LR_EDIT'] = reverse(
                'admin:repo2_resourceinfotype_model_change', args=(object_id,))

        context['LR_DOWNLOAD'] = ""
        try:
            # only show the download button if the resource has a local download
            # copy or if there is a download license with an external download
            # location 
            if resource.storage_object.has_local_download_copy() \
                    or any(l_info.downloadLocation for l_info
                           in _get_download_licences(object_id).viewvalues()):
                context['LR_DOWNLOAD'] = reverse(download, args=(object_id,))
                if (not request.user.is_active):
                    context['LR_DOWNLOAD'] = "restricted"
        except ObjectDoesNotExist:
            print "ERROR! Info about licence doesn't exist."

        # Update statistics and create a report about the user actions on LR
        if hasattr(resource.storage_object, 'identifier'):
            sessionid = ""
            if request.COOKIES:
                sessionid = request.COOKIES.get('sessionid', '')
            saveLRStats(request.user.username,
              resource.storage_object.identifier, sessionid, VIEW_STAT)
            context['LR_STATS'] = getLRStats(resource.storage_object.identifier)

    # Otherwise, we just collect all resources from the Django database.
    else:
        resources = resourceInfoType_model.objects.all()

        # Define context for template rendering.
        context = {'resources': resources}
        template = 'repo2/resources.html'

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
        if results_count and self.query:
            saveQueryStats(self.request.user.username, '', self.query,
                results_count, (datetime.now() - starttime).microseconds)

        return sqs
