"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""

import logging

from datetime import datetime
from os.path import split
from urllib import urlopen
from urlparse import urlparse

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _

from haystack.views import FacetedSearchView

from metashare.repo2.models import licenceInfoType_model, \
    resourceInfoType_model, LICENCEINFOTYPE_LICENCE_CHOICES
from metashare.settings import DJANGO_URL, LOG_LEVEL, LOG_HANDLER
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



# The following most be kept here, rather than in models.py,
# because models.py is automatically generated from the XML Schema.
LICENCEINFOTYPE_URLS_LICENCE_CHOICES = {
  'AGPL': ('/site_media/licences/GNU_agpl-3.0.htm', False),
  'LGPL': ('/site_media/licences/GNU_lgpl-2.0.htm', False),
  'LGPLv3': ('/site_media/licences/GNU_lgpl-3.0.htm', False),
  'CC': ('/site_media/licences/CC0v1.0.htm', False),
  'CC_BY-SA_3.0': ('/site_media/licences/CC-BYSAv3.0.htm', False),
  'CC_BY-NC-ND': ('/site_media/licences/CC-BYNCNDv3.0.htm', False),
  'CC_BY-NC-SA': ('/site_media/licences/CC-BYNCSAv2.5.pdf', False),
  'CC_BY-NC': ('/site_media/licences/CC-BYNCv3.0.htm', False),
  'CC_BY-ND': ('/site_media/licences/CC-BYNDv3.0.htm', False),
  'CC_BY-SA': ('/site_media/licences/CC-BYSAv2.5.pdf', False),
  'CC_BY': ('/site_media/licences/CC-BYv3.0.htm', False),
  'CC_BY-NC-SA_3.0': ('/site_media/licences/CC-BYNCSAv3.0.htm', False),
  'MSCommons_BY': \
    ('/site_media/licences/META-SHARE_COMMONS_BY_v1.0.htm', False),
  'MSCommons_BY-NC': \
    ('/site_media/licences/META-SHARE_COMMONS_BYNC_v1.0.htm', False),
  'MSCommons_BY-NC-ND': \
    ('/site_media/licences/META-SHARE_COMMONS_BYNCND_v1.0.htm', False),
  'MSCommons_BY-NC-SA': \
    ('/site_media/licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm', False),
  'MSCommons_BY-ND': \
    ('/site_media/licences/META-SHARE_COMMONS_BYND_v1.0.htm', False),
  'MSCommons_BY-SA': \
    ('/site_media/licences/META-SHARE_COMMONS_BYSA_v1.0.htm', False),
  'MSCommons_COM-NR-FF': \
    ('/site_media/licences/META-SHARE_Commercial_NoRedistribution_For-a-Fee' \
     '_v0.7.htm', True),
  'MSCommons_COM-NR': \
    ('/site_media/licences/META-SHARE_Commercial_NoRedistribution_v0.7.htm',
     False),
  'MSCommons_COM-NR-ND-FF': \
    ('/site_media/licences/META-SHARE_Commercial_NoRedistribution_' \
     'NoDerivatives_For-a-fee-v1.0.htm', True),
  'MSCommons_COM-NR-ND': \
    ('/site_media/licences/META-SHARE_Commercial_NoRedistribution_' \
     'NoDerivatives-v1.0.htm', False),
  'MSCommons_NoCOM-NC-NR-ND-FF': \
    ('/site_media/licences/META-SHARE_NonCommercial_NoRedistribution_' \
     'NoDerivatives_For-a-fee-v1.0.htm', True),
  'MSCommons_NoCOM-NC-NR-ND': \
    ('/site_media/licences/META-SHARE_Commercial_NoRedistribution_' \
     'NoDerivatives-v1.0.htm', False),
  'MSCommons_NoCOM-NC-NR-FF': \
    ('/site_media/licences/META-SHARE_NonCommercial_NoRedistribution_' \
     'For-a-Fee-v1.0.htm', True),
  'MSCommons_NoCOM-NC-NR': \
    ('/site_media/licences/META-SHARE_NonCommercial_NoRedistribution-v1.0.htm',
     False),
  'ELRA_EVALUATION': \
    ('/site_media/licences/EVALUATION.pdf', True),
  'ELRA_VAR': ('/site_media/licences/VAR-v3_2007.pdf', True),
  'ELRA_END_USER': \
    ('/site_media/licences/ENDUSER-v3_2007.pdf', True),
  'ELRA_LIMITED': ('/site_media/licences/Var-E-v2.pdf', True),
  'proprietary': ('', True),
  'CLARIN_PUB': ('', True),
  'CLARIN_ACA-NC': ('', True),
  'CLARIN_ACA': ('', True),
  'CLARIN_RES': ('', True),
  'Princeton_Wordnet': ('/site_media/licences/WordNet-3.0.pdf', False),
  'GPL': ('/site_media/licences/GNU_gpl-3.0.pdf', False),
  'GeneralLicenceGrant': ('', True),
  'GFDL': ('/site_media/licences/GNU_fdl-1.3.pdf', False),
  'ApacheLicence_V2.0': ('/site_media/licences/Apache-2.0.htm', False),
  'BSD-style': ('/site_media/licences/BSD_license.pdf', False),
  'underNegotiation': ('', True),
  'other': ('', True)
}



@login_required
def getlicence(request, object_id):
    """ Renders the resource licence. """
    content = "<p>No license terms have been released for this resource.<br/>"
    licences = licenceInfoType_model.objects.values("licence").filter(
                            back_to_distributioninfotype_model__id=object_id)
    #licenceinfo = licenceInfoType_model.objects.get(
    #                        back_to_distributioninfotype_model__id=object_id)
    if (len(licences) > 0):
        licencelabel = LICENCEINFOTYPE_LICENCE_CHOICES['choices'] \
                                            [int(licences[0]['licence'])][1]
        url = LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licencelabel][0]
        if url != "":
            urlparser = urlparse(url)
            if urlparser[1] == "":
                url =  '{0}{1}'.format(DJANGO_URL, url)
            if ".pdf" in url:
                content = '<object data="{0}" type="application/pdf" id=pdf ' \
                    'width="700" height="80%"><a href="{0}">View PDF licence' \
                    '</a></object>'.format(url)
            else:
                # cfedermann: it is NOT a good idea to use urlopen to read in
                #   a media file served by the same Django instance.  I fix
                #   this by adding an <object> containing the license to get
                #   the v2.0 release done...  This has to be checked/cleaned
                #   up somewhen later!
                content = '<object data="{0}" type="text/html" id=pdf ' \
                    'width="700" height="80%"><a href="{0}">View PDF licence' \
                    '</a></object>'.format(url)
#                handle = urlopen(url)
#                content = handle.read()
#                handle.close()
    return HttpResponse(content)


@login_required
def download(request, object_id):
    """ Renders the repository download view. """
    resource = get_object_or_404(resourceInfoType_model, pk=object_id)
    licences = tuple(licenceInfoType_model.objects \
        .filter(back_to_distributioninfotype_model__id=object_id))

    if request.user.is_active:
        agreement = False
        if request.method == "POST":
            la_val = request.POST.get('license_agree', '0')
            agreement = la_val == '1'
        elif request.method == "GET":
            la_val = request.GET.get('license_agree', '0')
            agreement = la_val == '1'
        if agreement:
            provide_download(request, resource, licences)

    signature_req = True
    for licence in [name for licence_info in licences if u'downloadable' in
                    licence_info.get_distributionAccessMedium_display_list()
                    for name in licence_info.get_licence_display_list()]:
        if not LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licence][1]:
            signature_req = False
            # for now we break as soon as we have found the first download
            # licence for which there is no signature required
            break
    if resource.identificationInfo.resourceName:
        title = resource.identificationInfo.resourceName[0]
    else:
        title = _('Unnamed Resource')
    dictionary = { 'title': title,
                   'object_id': object_id,
                   'signature_req': signature_req }
    return render_to_response('repo2/download.html', dictionary,
                              context_instance=RequestContext(request))


def provide_download(request, resource, licences):
    sessionid = ""
    if request.COOKIES:
        sessionid = request.COOKIES.get('sessionid', '')

    if resource.storage_object.has_local_download_copy():
        try:
            _binary_data = resource.storage_object.get_download()

            # We use a generic, binary mime type here for version v1.
            response = HttpResponse(mimetype="application/octet-stream")
            response['Content-Disposition'] = 'attachment; filename={0}' \
                                                .format(split(_binary_data)[1])
            with open(_binary_data, 'rb') as _local_data:
                _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)
                while _chunk:
                    response.write(_chunk)
                    _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)

            saveLRStats(request.user.username,
                        resource.storage_object.identifier, sessionid,
                        DOWNLOAD_STAT)
            return response
        except:
            raise Http404
    # redirect to download location, if available
    else:
        for url in [loc for licence_info in licences
                    if u'downloadable' in licence_info \
                        .get_distributionAccessMedium_display_list()
                    for loc in licence_info.downloadLocation]:
            if (urlopen(url).code / 100 < 4):
                saveLRStats(request.user.username,
                            resource.storage_object.identifier,
                            sessionid, DOWNLOAD_STAT)
                return redirect(url)
        LOGGER.info("No download could be offered for resource #{0}." \
                    .format(resource.id))
    raise Http404


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
            licences = licenceInfoType_model.objects \
                .values("downloadLocation") \
                .filter(back_to_distributioninfotype_model__id=object_id)
            if resource.storage_object.has_download() \
                    or resource.storage_object.has_local_download_copy() \
                    or len(licences) > 0:
                context['LR_DOWNLOAD'] = reverse(download, args=(object_id,))
                if (not request.user.is_active):
                    context['LR_DOWNLOAD'] = "restricted"
        except ObjectDoesNotExist:
            print "Info about licence doesn't exist."

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

        # collect statistics about the query
        starttime = datetime.now()
        results_count = sqs.count()
        if results_count and self.query:
            saveQueryStats(self.request.user.username, '', self.query,
                results_count, (datetime.now() - starttime).microseconds)

        return sqs
