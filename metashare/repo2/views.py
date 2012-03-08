"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""

import types
import operator
import re
    
from collections import defaultdict, OrderedDict
from urllib import urlopen
from os.path import split
from urlparse import urlparse
import base64
try:
    import cPickle as pickle
except:
    import pickle
                        
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, Http404
from datetime import datetime

from haystack.views import FacetedSearchView

from metashare.repo2.forms import SimpleSearchForm
# pylint: disable-msg=W0401, W0614
from metashare.repo2.models import *

from metashare.settings import DJANGO_URL
from metashare.stats.model_utils import getLRStats, saveLRStats, saveQueryStats, \
  VIEW_STAT, DOWNLOAD_STAT


MAXIMUM_READ_BLOCK_SIZE = 4096

# Used for the group_keywords method
GET_TERMS_RE = re.compile(r'"([^"]+)"|(\S+)').findall
GROUPING_RE = re.compile(r'\s{2,}').sub

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
LICENCEINFOTYPE_URLS_LICENCE_CHOICES = {'AGPL': ['/site_media/licences/GNU_agpl-3.0.htm', ''],
  'LGPL': ['/site_media/licences/GNU_lgpl-2.0.htm',''],
  'LGPLv3': ['/site_media/licences/GNU_lgpl-3.0.htm',''],
  'CC': ['/site_media/licences/CC0v1.0.htm',''],
  'CC_BY-SA_3.0': ['/site_media/licences/CC-BYSAv3.0.htm',''],
  'CC_BY-NC-ND': ['/site_media/licences/CC-BYNCNDv3.0.htm',''],
  'CC_BY-NC-SA': ['/site_media/licences/CC-BYNCSAv2.5.pdf',''],
  'CC_BY-NC': ['/site_media/licences/CC-BYNCv3.0.htm',''],
  'CC_BY-ND': ['/site_media/licences/CC-BYNDv3.0.htm',''],
  'CC_BY-SA': ['/site_media/licences/CC-BYSAv2.5.pdf',''],
  'CC_BY': ['/site_media/licences/CC-BYv3.0.htm',''],
  'CC_BY-NC-SA_3.0': ['/site_media/licences/CC-BYNCSAv3.0.htm',''],
  'MSCommons_BY': ['/site_media/licences/META-SHARE_COMMONS_BY_v1.0.htm',''],
  'MSCommons_BY-NC': ['/site_media/licences/META-SHARE_COMMONS_BYNC_v1.0.htm',''],
  'MSCommons_BY-NC-ND': ['/site_media/licences/META-SHARE_COMMONS_BYNCND_v1.0.htm',''],
  'MSCommons_BY-NC-SA': ['/site_media/licences/META-SHARE_COMMONS_BYNCSA_v1.0.htm',''],
  'MSCommons_BY-ND': ['/site_media/licences/META-SHARE_COMMONS_BYND_v1.0.htm',''],
  'MSCommons_BY-SA': ['/site_media/licences/META-SHARE_COMMONS_BYSA_v1.0.htm',''],
  'MSCommons_COM-NR-FF': ['/site_media/licences/META-SHARE_Commercial_NoRedistribution_For-a-Fee_v0.7.htm','SignatureRequired'], 
  'MSCommons_COM-NR': ['/site_media/licences/META-SHARE_Commercial_NoRedistribution_v0.7.htm',''],
  'MSCommons_COM-NR-ND-FF': ['/site_media/licences/META-SHARE_Commercial_NoRedistribution_NoDerivatives_For-a-fee-v1.0.htm','SignatureRequired'],
  'MSCommons_COM-NR-ND': ['/site_media/licences/META-SHARE_Commercial_NoRedistribution_NoDerivatives-v1.0.htm',''],
  'MSCommons_NoCOM-NC-NR-ND-FF': ['/site_media/licences/META-SHARE_NonCommercial_NoRedistribution_NoDerivatives_For-a-fee-v1.0.htm','SignatureRequired'],
  'MSCommons_NoCOM-NC-NR-ND': ['/site_media/licences/META-SHARE_Commercial_NoRedistribution_NoDerivatives-v1.0.htm',''],
  'MSCommons_NoCOM-NC-NR-FF': ['/site_media/licences/META-SHARE_NonCommercial_NoRedistribution_For-a-Fee-v1.0.htm','SignatureRequired'],
  'MSCommons_NoCOM-NC-NR': ['/site_media/licences/META-SHARE_NonCommercial_NoRedistribution-v1.0.htm',''],
  'ELRA_EVALUATION': ['/site_media/licences/EVALUATION.pdf','SignatureRequired'],
  'ELRA_VAR': ['/site_media/licences/VAR-v3_2007.pdf','SignatureRequired'],
  'ELRA_END_USER': ['/site_media/licences/ENDUSER-v3_2007.pdf','SignatureRequired'],
  'ELRA_LIMITED': ['/site_media/licences/Var-E-v2.pdf','SignatureRequired'],
  'proprietary': ['','SignatureRequired'],
  'CLARIN_PUB': ['','SignatureRequired'],
  'CLARIN_ACA-NC': ['','SignatureRequired'],
  'CLARIN_ACA': ['','SignatureRequired'],
  'CLARIN_RES': ['','SignatureRequired'],
  'Princeton_Wordnet': ['/site_media/licences/WordNet-3.0.pdf',''],
  'GPL': ['/site_media/licences/GNU_gpl-3.0.pdf',''],
  'GeneralLicenceGrant': ['','SignatureRequired'],
  'GFDL': ['/site_media/licences/GNU_fdl-1.3.pdf',''],
  'ApacheLicence_V2.0': ['/site_media/licences/Apache-2.0.htm',''],
  'BSD-style': ['/site_media/licences/BSD_license.pdf',''],
  'underNegotiation': ['','SignatureRequired'],
  'other': ['','SignatureRequired']
}






@login_required
def getlicence(request, object_id):
    """ Renders the resource licence. """
    content = "<p>No license terms have been released for this resource.<br/>"
    licences = licenceInfoType_model.objects.values("licence").filter(back_to_distributioninfotype_model__id=object_id)
    #licenceinfo = licenceInfoType_model.objects.get(back_to_distributioninfotype_model__id=object_id)
    if (len(licences) > 0):
        licencelabel = LICENCEINFOTYPE_LICENCE_CHOICES['choices'][int(licences[0]['licence'])][1]
        url = LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licencelabel][0]
        if url != "":
            urlparser = urlparse(url)
            if urlparser[1] == "":
                url =  '{0}{1}'.format(DJANGO_URL, url)
            if ".pdf" in url:
                content = '<object data="{0}" type="application/pdf" id=pdf width="700" height="80%"><a href="{0}">View PDF licence</a></object>'.format(url) 
            else:
                # cfedermann: it is NOT a good idea to use urlopen to read in
                #   a media file served by the same Django instance.  I fix
                #   this by adding an <object> containing the license to get
                #   the v2.0 release done...  This has to be checked/cleaned
                #   up somewhen later!
                content = '<object data="{0}" type="text/html" id=pdf width="700" height="80%"><a href="{0}">View PDF licence</a></object>'.format(url) 
#                handle = urlopen(url)
#                content = handle.read()
#                handle.close()    
    return HttpResponse(content)
    

@login_required   
def download(request, object_id):
    """ Renders the repository download view. """
    if object_id and request.user.is_active:       
        resource = get_object_or_404(resourceInfoType_model, pk=object_id)
        
        agreement = 0
        if request.method == "POST":
            if request.POST.get('license_agree', False):
                agreement = 1

        elif request.method == "GET":
            agreement = int(request.GET.get('license_agree', '0'))

        licences = licenceInfoType_model.objects.values("licence","downloadLocation").filter(back_to_distributioninfotype_model__id=object_id)
        if agreement == 1:
            sessionid = ""
            if request.COOKIES:
                sessionid = request.COOKIES.get('sessionid', '')
                    
            if resource.storage_object.has_local_download_copy():
                try:
                    #return HttpResponse(resource.storage_object.get_download())
                    _binary_data = resource.storage_object.get_download()
                    
                    # We use a generic, binary mime type here for version v1.
                    response = HttpResponse(mimetype="application/octet-stream")
                    response['Content-Disposition'] = 'attachment; ' \
                      'filename={0}'.format(split(_binary_data)[1])
                    
                    with open(_binary_data, 'rb') as _local_data:
                        _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)
                        while _chunk:
                            response.write(_chunk)
                            _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)
                    
                    saveLRStats(request.user.username, resource.storage_object.identifier, sessionid, DOWNLOAD_STAT)
                    return response
                
                except:
                    raise Http404
            #redirect on download location
            else:
                try:
                    if (len(licences) >0 ):
                        for licenceinfo in licences:
                            urldown = pickle.loads(base64.b64decode(str(licenceinfo['downloadLocation'])))
                            if isinstance(urldown, list) and len(urldown) > 0:
                                code = urlopen(urldown[0]).code
                                if (code / 100 < 4):
                                    saveLRStats(request.user.username, resource.storage_object.identifier, sessionid, DOWNLOAD_STAT)
                                    return redirect(urldown[0])
                except ObjectDoesNotExist:
                    LOGGER.debug("Warning! Info about licence or downloadLocation is wrong.")
            
            raise Http404
    
    signature_req = 0
    for licenceinfo in licences:
        licencelabel = LICENCEINFOTYPE_LICENCE_CHOICES['choices'][int(licenceinfo['licence'])][1]
        if LICENCEINFOTYPE_URLS_LICENCE_CHOICES[licencelabel][1] == "SignatureRequired":
            signature_req = 1

    title = resource.identificationInfo.resourceName
    dictionary = {'title': title, 'object_id': object_id, 'signature_req': signature_req }
    return render_to_response('repo2/download.html', dictionary,
            context_instance=RequestContext(request))


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
            lr_edit_url = '/{}admin/repo2/resourceinfotype_model/{}/'.format(
              DJANGO_BASE, object_id)
            context['LR_EDIT'] = lr_edit_url
            
        context['LR_DOWNLOAD'] = ""                
        try:
            licences = licenceInfoType_model.objects.values("downloadLocation").filter(back_to_distributioninfotype_model__id=object_id)
            if resource.storage_object.has_download() or resource.storage_object.has_local_download_copy() or len(licences) > 0:
                context['LR_DOWNLOAD'] = '/{0}repo2/download/{1}/'.format(DJANGO_BASE, object_id)
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


def __save_search_keywords_in_session(session, form_data):
    """
    Saves the search keywords of the given form data in the given session.
    
    After returning, the given session will only contain `search_kws` if the
    form data is valid and there were any keywords available.
    
    Returns a `SimpleSearchForm` which is bound with the given form data.
    """
    form = SimpleSearchForm(form_data)
    if form.is_valid() and form.cleaned_data['keywords']:
        # Save search parameters in the current session object.
        session['search_kws'] = form.cleaned_data['keywords']
    # Otherwise reset the search keywords inside the current session.
    elif 'search_kws' in session:
        del session['search_kws']
    return form


def __save_or_get_filter_from_session(filter_name, filter_val, session):
    """
    Saves the given filter in the given session object.
    
    If the `filter_val` is None and there is another value for the filter in the
    given session, then the filter value is taken from the session. Returns the
    filter value which is eventually saved in the session (may be None).
    """
    if filter_val != None:
        session[filter_name] = filter_val
    elif filter_name in session:
        filter_val = session[filter_name]
    return filter_val


def _get_resource_ids_from_filter_class(filter_name, 
                                        filter_class, 
                                        resourceinfotypemodel_objs_ids):
    """
    Retrieve the ids of the resources from a complex filter (i.e. with variation
    of the filter type), with the intersection of an original list of ids.
    
    The variation of the filter type is managed with two sub part of the filter type
    
    If the filter is not None, then return the updated list of ids
    Else return the original list of ids.
    """
    if filter_name != "None" and filter_name != None:
        resourceinfotypemodel_objs_tmp = []
        for filter_type in filter_class:
            kwargs = { filter_type: filter_name }
            new_object_ids = resourceInfoType_model.objects.filter(**kwargs)
            resourceinfotypemodel_objs_tmp.extend(
                new_object_ids.values_list('pk', flat=True))
        resourceinfotypemodel_objs_ids = list(
          set(resourceinfotypemodel_objs_tmp)
            & set(resourceinfotypemodel_objs_ids))
    
    return resourceinfotypemodel_objs_ids

def _get_dictionary_from_filter_class(filter_type_class, 
                                      resourceinfotype_model_objects,
                                      filter_choices):
    """
    Build the dictionary of filter names on the resources
    that are already in the database
    
    filter_choices can be None if there is no choice list to describe 
    the name of the resource type (see for instance languageName)
    
    Return a sorted list of results
    """
    type_info = []
    for filter_type in filter_type_class:
        for object_ids in resourceInfoType_model.objects.values_list(
                                                   filter_type, flat = True).distinct():
            type_info.append(object_ids)
    # Remove duplicates
    type_info = list(set(type_info))
    
    dictionary = []
    for result in type_info:
        if (result != None) and (result != ''):
            resourceinfotypemodel_objs_tmp = []
            for filter_type in filter_type_class:
                kwargs = { filter_type: result }
                new_object_ids = \
                    resourceinfotype_model_objects.filter(**kwargs).distinct()
                resourceinfotypemodel_objs_tmp.extend(
                  new_object_ids.values_list('pk', flat=True))
            result_lr_count = len(resourceinfotypemodel_objs_tmp)
        
            if filter_choices == None:
                text_result = result
            else:
                text_result = filter_choices['choices'][int(result)][1]
            if result_lr_count != 0:
                dictionary.append((result, result_lr_count, text_result))

    dictionary_sorted = sorted(dictionary, reverse=True,
      key=operator.itemgetter(1))

    return dictionary_sorted
    
    
def simple_search(request):
    """
    Google-like search in LR.
    TODO: Make results appear sorted by a field
    """
    LOGGER.info('Rendering simple search view for user "{0}".'.format(
      request.user.username or "Anonymous"))
    
    
    context = {'title': 'Metadata search interface',
                  'mode' : 'browse',
                  'form': 'ModelFormTemplate',
#                  'results': paginated_results,
#                  'total_results': len(patched_results),
                  'keywords': ' ',
                  # The following items in the dictionary are used
                  # by filtering.
                 }
    return render_to_response('repo2/search2.html', context,
      context_instance=RequestContext(request))

   
      
def _create_flat_tuple_list(items):
    """
    Takes a list of items and returns a list of (key, value) items.

    This will recursively descend for lists and dictionary typed values.
    In a sense, this will create a "flat" representation of items.  Keys
    named "id" will be skipped as they are not needed for visualization.

    """
    _tuples = []

    if not type(items) in (types.ListType, types.DictType, OrderedDict):
        return _tuples

    if type(items) == types.ListType:
        for item in items:
            _tuples.extend(_create_flat_tuple_list(item))

    if type(items) in (types.DictType, OrderedDict):
        for key, value in items.items():
            if type(value) in (types.ListType, types.DictType, OrderedDict):
                _tuples.extend(_create_flat_tuple_list(value))

            elif key != 'id' and value:
                _tuples.append((key, value))

    return _tuples


### Added by D. Mavroeidis ###
def get_items_and_counts(all_items):
    """
    Returns a list of unique items with their respective counts.
    """

    items_dic = defaultdict(int)
    for item in all_items:
        if item:
            items_dic[item] += 1

    return items_dic


### Added by D. Mavroeidis ###
def group_keywords(keywords, get_terms=GET_TERMS_RE, grouping=GROUPING_RE):
    """
    Removes whitespace and treats strings in double quotes as a unity.
    Returns a list of keywords.
    Usage:
    group_keywords('my search string "with double quotes"')
    returns
    ['my', 'search', 'string', 'with double quotes']
    """

    return [grouping(' ', (s[0] or s[1]).strip()) for s in get_terms(keywords)]


class MetashareFacetedSearchView(FacetedSearchView):
    """
    A modified `FacetedSearchView` which makes sure that only such results will
    be returned that are accessible by the current user. 
    """
    def get_results(self):
        starttime = datetime.now()
        sqs = super(MetashareFacetedSearchView, self).get_results()
        if not self.request.user.is_staff:
            sqs = sqs.filter(published=True)
        if (len(sqs) > 0 and len(self.query) > 0):
            saveQueryStats(self.request.user.username, '', self.query, len(sqs), (datetime.now() - starttime).microseconds)
        return sqs
