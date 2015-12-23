import logging

from datetime import datetime
from os.path import split, getsize
from urllib import urlopen
from mimetypes import guess_type

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.translation import ugettext as _

from haystack.views import FacetedSearchView

from metashare.repository.editor.resource_editor import has_edit_permission
from metashare.repository.forms import LicenseSelectionForm, \
    LicenseAgreementForm, DownloadContactForm, MORE_FROM_SAME_CREATORS, \
    MORE_FROM_SAME_PROJECTS
from metashare.repository import model_utils
from metashare.repository.models import licenceInfoType_model, \
    resourceInfoType_model
from metashare.repository.search_indexes import resourceInfoType_modelIndex, \
    update_lr_index_entry
from metashare.settings import LOG_HANDLER, MEDIA_URL, DJANGO_URL
from metashare.stats.model_utils import getLRStats, saveLRStats, \
    saveQueryStats, VIEW_STAT, DOWNLOAD_STAT
from metashare.storage.models import PUBLISHED
from metashare.recommendations.recommendations import SessionResourcesTracker, \
    get_download_recommendations, get_view_recommendations, \
    get_more_from_same_creators_qs, get_more_from_same_projects_qs


MAXIMUM_READ_BLOCK_SIZE = 4096

# Setup logging support.
LOGGER = logging.getLogger(__name__)
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
        # use pretty print name of element instead of tag; requires that 
        # element_tree is created using export_to_elementtree(pretty=True)
        return (element_tree.attrib["pretty"], values)

    # Otherwise, we return a tuple containg (key, value, required), 
    # i.e., (tag, text, <True,False>).
    # The "required" element was added to the tree, for passing 
    # information about whether a field is required or not, to correctly
    # render the single resource view.
    else:
        # use pretty print name of element instead of tag; requires that 
        # element_tree is created using export_to_elementtree(pretty=True)
        return ((element_tree.attrib["pretty"], element_tree.text),)


# a type providing an enumeration of META-SHARE member types
MEMBER_TYPES = type('MemberEnum', (), dict(GOD=100, FULL=3, ASSOCIATE=2, NON=1))


# a dictionary holding a URL for each download licence and a member type which
# is required at a minimum to be able to download the associated resource
# straight away; otherwise the licence requires a hard-copy signature
LICENCEINFOTYPE_URLS_LICENCE_CHOICES = {
  'AGPL': (MEDIA_URL + 'licences/AGPL.pdf', MEMBER_TYPES.NON),
  'LGPL': (MEDIA_URL + 'licences/LGPL.pdf', MEMBER_TYPES.NON),
  'CC-ZERO': (MEDIA_URL + 'licences/CC-ZERO.pdf', MEMBER_TYPES.NON),
  'CC-BY-NC-ND': (MEDIA_URL + 'licences/CC-BY-NC-ND.pdf', MEMBER_TYPES.NON),
  'CC-BY-NC-SA': (MEDIA_URL + 'licences/CC-BY-NC-SA.pdf', MEMBER_TYPES.NON),
  'CC-BY-NC': (MEDIA_URL + 'licences/CC-BY-NC.pdf', MEMBER_TYPES.NON),
  'CC-BY-ND': (MEDIA_URL + 'licences/CC-BY-ND.pdf', MEMBER_TYPES.NON),
  'CC-BY-SA': (MEDIA_URL + 'licences/CC-BY-SA.pdf', MEMBER_TYPES.NON),
  'CC-BY': (MEDIA_URL + 'licences/CC-BY.pdf', MEMBER_TYPES.NON),
  'PDDL': (MEDIA_URL + 'licences/PDDL.pdf', MEMBER_TYPES.NON),
  'ODC-BY': (MEDIA_URL + 'licences/ODC-BY.pdf', MEMBER_TYPES.NON),
  'ODbL': (MEDIA_URL + 'licences/ODbL.pdf', MEMBER_TYPES.NON),
  # 'MSCommons-BY': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BY_v1.0.htm',
  #                  MEMBER_TYPES.FULL),
  # 'MSCommons-BY-NC': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNC_v1.0.htm',
  #                     MEMBER_TYPES.FULL),
  # 'MSCommons-BY-NC-ND': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNCND_' \
  #                        'v1.0.htm', MEMBER_TYPES.FULL),
  # 'MSCommons-BY-NC-SA': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYNCSA' \
  #                        '_v1.0.htm', MEMBER_TYPES.FULL),
  # 'MSCommons-BY-ND': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYND_v1.0.htm',
  #                     MEMBER_TYPES.FULL),
  # 'MSCommons-BY-SA': (MEDIA_URL + 'licences/META-SHARE_COMMONS_BYSA_v1.0.htm',
  #                     MEMBER_TYPES.FULL),
  'MS-NoReD-FF': (MEDIA_URL + 'licences/MS-NoReD-FF.pdf', MEMBER_TYPES.GOD),
  'MS-NoReD': (MEDIA_URL + 'licences/MS-NoReD.pdf', MEMBER_TYPES.GOD),
  'MS-NoReD-ND-FF': (MEDIA_URL + 'licences/MS-NoReD-ND-FF.pdf', MEMBER_TYPES.GOD),
  'MS-NoReD-ND': (MEDIA_URL + 'licences/MS-NoReD-ND.pdf', MEMBER_TYPES.GOD),
  'MS-NC-NoReD-ND-FF': (MEDIA_URL + 'licences/MS-NC-NoReD-ND-FF.pdf', MEMBER_TYPES.GOD),
  'MS-NC-NoReD-ND': (MEDIA_URL + 'licences/MS-NC-NoReD-ND.pdf', MEMBER_TYPES.GOD),
  'MS-NC-NoReD-FF': (MEDIA_URL + 'licences/MS-NC-NoReD-FF.pdf', MEMBER_TYPES.GOD),
  'MS-NC-NoReD': (MEDIA_URL + 'licences/MS-NC-NoReD.pdf', MEMBER_TYPES.GOD),
  'ELRA_EVALUATION': (MEDIA_URL + 'licences/ELRA_EVALUATION.pdf', MEMBER_TYPES.GOD),
  'ELRA_VAR': (MEDIA_URL + 'licences/ELRA_VAR.pdf', MEMBER_TYPES.GOD),
  'ELRA_END_USER': (MEDIA_URL + 'licences/ELRA_END_USER.pdf', MEMBER_TYPES.GOD),
  'CLARIN_PUB': (MEDIA_URL + 'licences/CLARIN_PUB.pdf', MEMBER_TYPES.GOD),
  'CLARIN_ACA-NC': (MEDIA_URL + 'licences/CLARIN_ACA-NC.pdf', MEMBER_TYPES.GOD),
  'CLARIN_ACA': (MEDIA_URL + 'licences/CLARIN_ACA.pdf', MEMBER_TYPES.GOD),
  'CLARIN_RES': (MEDIA_URL + 'licences/CLARIN_RES.pdf', MEMBER_TYPES.GOD),
  'Princeton_Wordnet': (MEDIA_URL + 'licences/Princeton_Wordnet.pdf',
                        MEMBER_TYPES.NON),
  'GPL': (MEDIA_URL + 'licences/GPL.pdf', MEMBER_TYPES.NON),
  'GFDL': (MEDIA_URL + 'licences/GFDL.pdf', MEMBER_TYPES.NON),
  'ApacheLicence_2.0': (MEDIA_URL + 'licences/ApacheLicence_2.0.pdf',
                        MEMBER_TYPES.NON),
  'BSD_3-clause': (MEDIA_URL + 'licences/BSD_3-clause.pdf', MEMBER_TYPES.NON),
  'BSD_4-clause': (MEDIA_URL + 'licences/BSD_4-clause.pdf', MEMBER_TYPES.NON),
  'FreeBSD': (MEDIA_URL + 'licences/FreeBSD.pdf', MEMBER_TYPES.NON),
  'proprietary': ('', MEMBER_TYPES.GOD),
  'underNegotiation': ('', MEMBER_TYPES.GOD),
  'nonStandardLicenceTerms': ('', MEMBER_TYPES.NON),
  # 'other': ('', MEMBER_TYPES.GOD)
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
                         for l_name in l_info.licence])
    result = {}
    for name, info in all_licenses.items():
        access = LICENCEINFOTYPE_URLS_LICENCE_CHOICES.get(name, None)
        if access == None:
            LOGGER.warn("Unknown license name discovered in the database for " \
                        "object #{}: {}".format(resource.id, name))
            del all_licenses[name]
        elif user_membership >= access[1] \
                and (info.downloadLocation \
                     or resource.storage_object.get_download()):
            # the resource can be downloaded somewhere under the current license
            # terms and the user's membership allows her to immediately download
            # the resource
            result[name] = (info, True)
        else:
            # further negotiations are required with the current license
            result[name] = (info, False)
    return result


def download(request, object_id):
    """
    Renders the resource download/purchase view including license selection,
    etc.
    """
    user_membership = _get_user_membership(request.user)

    # here we are only interested in licenses (or their names) of the specified
    # resource that allow the current user a download/purchase
    resource = get_object_or_404(resourceInfoType_model,
                                 storage_object__identifier=object_id,
                                 storage_object__publication_status=PUBLISHED)
    licences = _get_licences(resource, user_membership)

    # Check whether the resource is from the current node, or whether it must be
    # redirected to the master copy
    if not resource.storage_object.master_copy:
        return render_to_response('repository/redirect.html',
                { 'resource': resource,
                  'redirection_url': model_utils.get_lr_master_url(resource) },
                context_instance=RequestContext(request))

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
                      'licence_name': licence_choice, 'licence_path': \
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
              'resource': resource, 'licence_name': licence_choice, 
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
    dl_path = resource.storage_object.get_download()
    if dl_path:
        try:
            def dl_stream_generator():
                with open(dl_path, 'rb') as _local_data:
                    _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)
                    while _chunk:
                        yield _chunk
                        _chunk = _local_data.read(MAXIMUM_READ_BLOCK_SIZE)

            # build HTTP response with a guessed mime type; the response
            # content is a stream of the download file
            filemimetype = guess_type(dl_path)[0] or "application/octet-stream"
            response = HttpResponse(dl_stream_generator(),
                                    mimetype=filemimetype)
            response['Content-Length'] = getsize(dl_path) 
            response['Content-Disposition'] = 'attachment; filename={0}' \
                                                .format(split(dl_path)[1])
            _update_download_stats(resource, request)
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
                _update_download_stats(resource, request)
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


def _update_download_stats(resource, request):
    """
    Updates all relevant statistics counters for a the given successful resource
    download request.
    """
    # maintain general download statistics
    if saveLRStats(resource, DOWNLOAD_STAT, request):
        # update download count in the search index, too
        update_lr_index_entry(resource)
    # update download tracker
    tracker = SessionResourcesTracker.getTracker(request)
    tracker.add_download(resource, datetime.now())
    request.session['tracker'] = tracker


@login_required
def download_contact(request, object_id):
    """
    Renders the download contact view to request information regarding a resource
    """
    resource = get_object_or_404(resourceInfoType_model,
                                 storage_object__identifier=object_id,
                                 storage_object__publication_status=PUBLISHED)

    default_message = "We are interested in using the above mentioned " \
        "resource. Please provide us with all the relevant information (e.g.," \
        " licensing provisions and restrictions, any fees required etc.) " \
        "which is necessary for concluding a deal for getting a license. We " \
        "are happy to provide any more information on our request and our " \
        "envisaged usage of your resource.\n\n" \
        "[Please include here any other request you may have regarding this " \
        "resource or change this message altogether]\n\n" \
        "Please kindly use the above mentioned e-mail address for any " \
        "further communication."

    # Find out the relevant resource contact emails and names
    resource_emails = []
    resource_contacts = []
    for person in resource.contactPerson.all():
        resource_emails.append(person.communicationInfo.email[0])
        if person.givenName:
            _name = u'{} '.format(person.get_default_givenName())
        else:
            _name = u''
        resource_contacts.append(_name + person.get_default_surname())

    # Check if the edit form has been submitted.
    if request.method == "POST":
        # If so, bind the creation form to HTTP POST values.
        form = DownloadContactForm(initial={'userEmail': request.user.email,
                                            'message': default_message},
                                   data=request.POST)
        # Check if the form has validated successfully.
        if form.is_valid():
            message = form.cleaned_data['message']
            user_email = form.cleaned_data['userEmail']

            # Render notification email template with correct values.
            data = {'message': message, 'resource': resource,
                'resourceContactName': resource_contacts, 'user': request.user,
                'user_email': user_email, 'node_url': DJANGO_URL}
            try:
                # Send out email to the resource contacts
                send_mail('Request for information regarding a resource',
                    render_to_string('repository/' \
                      'resource_download_information.email', data),
                    user_email, resource_emails, fail_silently=False)
            except: #SMTPException:
                # If the email could not be sent successfully, tell the user
                # about it.
                messages.error(request,
                  _("There was an error sending out the request email."))
            else:
                messages.success(request, _('You have successfully ' \
                    'sent a message to the resource contact person.'))

            # Redirect the user to the resource page.
            return redirect(resource.get_absolute_url())

    # Otherwise, render a new DownloadContactForm instance
    else:
        form = DownloadContactForm(initial={'userEmail': request.user.email,
                                            'message': default_message})

    dictionary = { 'username': request.user,
      'resource': resource,
      'resourceContactName': resource_contacts,
      'resourceContactEmail': resource_emails,
      'form': form }
    return render_to_response('repository/download_contact_form.html',
                        dictionary, context_instance=RequestContext(request))


def view(request, resource_name=None, object_id=None):
    """
    Render browse or detail view for the repository application.
    """
    # only published resources may be viewed
    resource = get_object_or_404(resourceInfoType_model,
                                 storage_object__identifier=object_id,
                                 storage_object__publication_status=PUBLISHED)
    if request.path_info != resource.get_absolute_url():
        return redirect(resource.get_absolute_url())

    # Convert resource to ElementTree and then to template tuples.
    lr_content = _convert_to_template_tuples(
        resource.export_to_elementtree(pretty=True))

    # get the 'best' language version of a "DictField" and all other versions
    resource_name = resource.identificationInfo.get_default_resourceName()
    res_short_names = resource.identificationInfo.resourceShortName.values()
    description = resource.identificationInfo.get_default_description()
    other_res_names = [name for name in resource.identificationInfo \
            .resourceName.itervalues() if name != resource_name]
    other_descriptions = [name for name in resource.identificationInfo \
            .description.itervalues() if name != description]

    # Create fields lists
    url = resource.identificationInfo.url
    metashare_id = resource.identificationInfo.metaShareId
    identifier = resource.identificationInfo.identifier
    resource_type = resource.resourceComponentType.as_subclass().resourceType
    media_types = set(model_utils.get_resource_media_types(resource))
    linguality_infos = set(model_utils.get_resource_linguality_infos(resource))
    license_types = set(model_utils.get_resource_license_types(resource))
    attribution_details = model_utils.get_resource_attribution_texts(resource)

    
    distribution_info_tuple = None
    contact_person_tuples = []
    metadata_info_tuple = None
    version_info_tuple = None
    validation_info_tuples = []
    usage_info_tuple = None
    documentation_info_tuple = None
    resource_creation_info_tuple = None
    relation_info_tuples = []
    resource_component_tuple = None
    for _tuple in lr_content[1]:
        if _tuple[0] == "Distribution":
            distribution_info_tuple = _tuple
        elif _tuple[0] == "Contact person":
            contact_person_tuples.append(_tuple)
        elif _tuple[0] == "Metadata":
            metadata_info_tuple = _tuple
        elif _tuple[0] == "Version":
            version_info_tuple = _tuple
        elif _tuple[0] == "Validation":
            validation_info_tuples.append(_tuple)
        elif _tuple[0] == "Usage":
            usage_info_tuple = _tuple
        elif _tuple[0] == "Resource documentation":
            documentation_info_tuple = _tuple            
        elif _tuple[0] == "Resource creation":
            resource_creation_info_tuple = _tuple
        elif _tuple[0] == "Relation":
            relation_info_tuples.append(_tuple)
        elif _tuple[0] == "Resource component type":
            resource_component_tuple = _tuple[1]
    
    # Convert resource_component_tuple to nested dictionaries
    resource_component_dicts = {}
    validation_dicts = []
    relation_dicts = []    
    
    # Convert several tuples to dictionaries to facilitate rendering
    # the templates.
    contact_person_dicts = []
    for item in contact_person_tuples:
        contact_person_dicts.append(tuple2dict([item]))
    distribution_dict = tuple2dict([distribution_info_tuple])
    resource_component_dict = tuple2dict(resource_component_tuple)
    resource_creation_dict = tuple2dict([resource_creation_info_tuple])
    metadata_dict = tuple2dict([metadata_info_tuple])
    usage_dict = tuple2dict([usage_info_tuple])
    version_dict = tuple2dict([version_info_tuple])
    documentation_dict = tuple2dict([documentation_info_tuple])
    for item in validation_info_tuples:
        validation_dicts.append(tuple2dict([item]))
    for item in relation_info_tuples:
        relation_dicts.append(tuple2dict([item]))

    # Count individual media resource components
    text_counts = []
    video_counts = []

    if resource_type == "corpus":
        for key, value in resource_component_dict['Resource_component_type']['Media_type_component_of_corpus'].items():
            if "Corpus_text" in key and not "numerical" in key and not "ngram" in key:
                text_counts.append(value)
            elif "Corpus_video" in key:
                video_counts.append(value)
              
    # Create a list of resource components dictionaries
    if resource_type == "corpus":
        for media_type in media_types:
            if media_type == "text":
                resource_component_dicts['text'] = \
                  resource_component_dict['Resource_component_type'] \
                    ['Media_type_component_of_corpus']['Corpus_text']
            if media_type == "audio":
                resource_component_dicts['audio'] = \
                  resource_component_dict['Resource_component_type'] \
                    ['Media_type_component_of_corpus']['Corpus_audio_component']
            if media_type == "video":
                resource_component_dicts['video'] = \
                  resource_component_dict['Resource_component_type'] \
                    ['Media_type_component_of_corpus']['Corpus_video']
            if media_type == "image":
                resource_component_dicts['image'] = \
                  resource_component_dict['Resource_component_type'] \
                    ['Media_type_component_of_corpus']['Corpus_image_component']
            if media_type == "textNgram":
                resource_component_dicts['textNgram'] = \
                  resource_component_dict['Resource_component_type'] \
                     ['Media_type_component_of_corpus']['Corpus_textNgram']
            if media_type == "textNumerical":
                resource_component_dicts['textNumerical'] = \
                  resource_component_dict['Resource_component_type'] \
                     ['Media_type_component_of_corpus']['Corpus_textNumerical']


    elif resource_type == "languageDescription":
        for media_type in media_types:
            if media_type == "text":
                resource_component_dicts['text'] = \
                  resource_component_dict['Resource_component_type'] \
                    ['Media_type_component_of_language_description']['Language_description_text_component']
            if media_type == "image":
                resource_component_dicts['image'] = \
                  resource_component_dict['Resource_component_type'] \
                    ['Media_type_component_of_language_description']['Language_description_image_component']
            if media_type == "video":
                resource_component_dicts['video'] = \
                  resource_component_dict['Resource_component_type'] \
                    ['Media_type_component_of_language_description']['Language_description_video_component']


    elif resource_type == "lexicalConceptualResource":
        for media_type in media_types:

            if media_type == "text":
                resource_component_dicts['text'] = \
                  resource_component_dict['Resource_component_type'] \
                    ['Media_type_component_of_lexical___conceptual_resource'] \
                    ['Lexical___Conceptual_resource_text_component']
            if media_type == "audio":
                resource_component_dicts['audio'] = \
                  resource_component_dict['Resource_component_type'] \
                  ['Media_type_component_of_lexical___conceptual_resource'] \
                  ['Lexical___Conceptual_resource_audio_component']
            if media_type == "video":
                resource_component_dicts['video'] = \
                  resource_component_dict['Resource_component_type'] \
                  ['Media_type_component_of_lexical___conceptual_resource'] \
                  ['Lexical___Conceptual_resource_video_component']
            if media_type == "image":
                resource_component_dicts['image'] = \
                  resource_component_dict['Resource_component_type'] \
                  ['Media_type_component_of_lexical___conceptual_resource'] \
                  ['Lexical___Conceptual_resource_image_component']

    elif resource_type == "toolService":
        resource_component_dicts['toolService'] = \
          resource_component_dict['Resource_component_type']
   
    # Define context for template rendering.
    context = {
                'contact_person_dicts': contact_person_dicts,
                'description': description,
                'distribution_dict': distribution_dict,
                'documentation_dict': documentation_dict,
                'license_types': license_types,
                'linguality_infos': linguality_infos,
                'mediaTypes': media_types,
                'metadata_dict': metadata_dict,
                'metaShareId': metashare_id,
                'identifier': identifier,
                'other_res_names': other_res_names,
                'other_descriptions': other_descriptions,
                'relation_dicts': relation_dicts,
                'res_short_names': res_short_names,
                'resource': resource,
                'resource_component_dicts': resource_component_dicts,
                'resource_component_dict': resource_component_dict,
                'resourceName': resource_name,
                'attribution_details': attribution_details,
                'resourceType': resource_type,
                'resource_creation_dict': resource_creation_dict,
                'url': url,
                'usage_dict': usage_dict,
                'validation_dicts': validation_dicts,                
                'version_dict': version_dict,
                'text_counts': text_counts,
                'video_counts': video_counts,
              }
    template = 'repository/resource_view/lr_view.html'

    # For users who have edit permission for this resource, we have to add 
    # LR_EDIT which contains the URL of the Django admin backend page 
    # for this resource.
    if has_edit_permission(request, resource):
        context['LR_EDIT'] = reverse(
            'admin:repository_resourceinfotype_model_change', \
              args=(resource.id,))

    # Update statistics:
    if saveLRStats(resource, VIEW_STAT, request):
        # update view count in the search index, too
        update_lr_index_entry(resource)
    # update view tracker
    tracker = SessionResourcesTracker.getTracker(request)
    tracker.add_view(resource, datetime.now())
    request.session['tracker'] = tracker

    # Add download/view/last updated statistics to the template context.
    context['LR_STATS'] = getLRStats(resource.storage_object.identifier)
            
    # Add recommendations for 'also viewed' resources
    context['also_viewed'] = \
        _format_recommendations(get_view_recommendations(resource))
    # Add recommendations for 'also downloaded' resources
    context['also_downloaded'] = \
        _format_recommendations(get_download_recommendations(resource))
    # Add 'more from same' links
    if get_more_from_same_projects_qs(resource).count():
        context['search_rel_projects'] = '{}/repository/search?q={}:{}'.format(
            DJANGO_URL, MORE_FROM_SAME_PROJECTS,
            resource.storage_object.identifier)
    if get_more_from_same_creators_qs(resource).count():
        context['search_rel_creators'] = '{}/repository/search?q={}:{}'.format(
            DJANGO_URL, MORE_FROM_SAME_CREATORS,
            resource.storage_object.identifier)

    # Render and return template with the defined context.
    ctx = RequestContext(request)
    return render_to_response(template, context, context_instance=ctx)

def tuple2dict(_tuple):
    '''
    Recursively converts a tuple into a dictionary for ease of use 
    in templates.
    '''
    _dict = {}
    count_dict = {}
    for item in _tuple:
        if isinstance(item, tuple) or isinstance(item, list):
            if isinstance(item[0], basestring):
                # Replace spaces by underscores for component names.
                if item[0].find(" "):
                    _key = item[0].replace(" ", "_").replace("/","_")
                else: 
                    _key = item[0]
                if _key in _dict:
                    # If a repeatable component is found, a customized 
                    # dictionary is added, since no duplicate key names
                    # are allowed. We keep a dictionary with counts and
                    # add a new entry in the original dictionary in the 
                    # form <component>_<no_of_occurences>
                    if not _key in count_dict:
                        count_dict[_key] = 1
                    else:
                        count_dict[_key] += 1
                    new_key = "_".join([_key, str(count_dict[_key])])
                    _dict[new_key] = tuple2dict(item[1])
                else:
                    _dict[_key] = tuple2dict(item[1])
            else:
                if isinstance(item[0], tuple):
                    # Replace spaces by underscores for element names.
                    if item[0][0].find(" "):
                        _key = item[0][0].replace(" ", "_").replace('(',"").replace(")","").replace("/","_").replace("-","_")
                    else: _key = item[0][0]

                    # If the item is a date, convert it to real datetime
                    if _key.find("_date") != -1:
                        new_item = datetime.strptime(item[0][1], "%Y-%m-%d")
                    else:
                        new_item = item[0][1]
                    # If a repeatable element is found, the old value is
                    # concatenated with the new one, adding a space in between.
                    if _key in _dict:
                        _dict[_key] = ", ".join([_dict[_key], new_item])
                    else:
                        _dict[_key] = new_item
    return _dict


def _format_recommendations(recommended_resources):
    '''
    Returns the given resource recommendations list formatted as a list of
    dictionaries with the two keys "name" and "url" (for use in the single
    resource view).
    
    The number of returned recommendations is restricted to at most 4.
    '''
    result = []
    for res in recommended_resources[:4]:
        res_item = {}
        res_item['name'] = res.__unicode__()
        res_item['url'] = res.get_absolute_url()
        result.append(res_item)
    return result


class MetashareFacetedSearchView(FacetedSearchView):
    """
    A modified `FacetedSearchView` which makes sure that only such results will
    be returned that are accessible by the current user.
    """
    def get_results(self):
        sqs = super(MetashareFacetedSearchView, self).get_results()

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
            elif sort_list[0] == 'dl_count_desc':
                sqs = sqs.order_by('-dl_count', 'resourceNameSort_exact')
            elif sort_list[0] == 'view_count_desc':
                sqs = sqs.order_by('-view_count', 'resourceNameSort_exact')
            else:
                sqs = sqs.order_by('resourceNameSort_exact')

        # collect statistics about the query
        starttime = datetime.now()
        results_count = sqs.count()
        if self.query:
            saveQueryStats(self.query, \
                str(sorted(self.request.GET.getlist("selected_facets"))), \
                results_count, \
                (datetime.now() - starttime).microseconds, self.request)

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
            for name, label, facet_id, _dummy in \
              [f for f in filter_labels if f[3] == 0]:
                name_exact = '{0}_exact'.format(name)
                # only add selected facets in step (1)
                if name_exact in sel_facets:
                    items = facet_fields.get(name)
                    if items:
                        removable = []
                        addable = []
                        # only items with a count > 0 are shown
                        for item in [i for i in items if i[1] > 0]:
                            subfacets = [f for f in filter_labels if (f[3] == \
                              facet_id and item[0] in f[0]) ]
                            subfacets_exactname_list = []
                            subfacets_exactname_list.extend( \
                              [u'{0}_exact'.format(subfacet[0]) \
                              for subfacet in subfacets])
                            subresults = []
                            for facet in subfacets:
                                subresults = self.show_subfilter( \
                                  facet, sel_facets, facet_fields, subresults)
                            if item[0] in sel_facets[name_exact]:
                                if item[0] != "":
                                    lab_item = " ".join(re.findall( \
                                      '[A-Z\_]*[^A-Z]*', \
                                      item[0][0].capitalize()+item[0][1:]))[:-1]
                                    removable.append({'label': lab_item,
                                        'count': item[1], 'targets':
                                            [u'{0}:{1}'.format(name, value)
                                             for name, values in
                                             sel_facets.iteritems() for value in
                                             values if (name != name_exact
                                             or value != item[0]) and name \
                                               not in subfacets_exactname_list], \
                                               'subresults': subresults})
                            else:
                                targets = [u'{0}:{1}'.format(name, value)
                                           for name, values in
                                           sel_facets.iteritems()
                                           for value in values]
                                targets.append(u'{0}:{1}'.format(name_exact,
                                                                 item[0]))
                                if item[0] != "":
                                    lab_item = " ".join(re.findall( \
                                      '[A-Z\_]*[^A-Z]*', \
                                      item[0][0].capitalize()+item[0][1:]))[:-1]
                                    addable.append({'label': lab_item,
                                                'count': item[1],
                                                'targets': targets,
                                                'subresults': subresults})

                        result.append({'label': label, 'removable': removable,
                                       'addable': addable})                    

        # Step (2): add all top level facets without selected facet items at the
        # end (sorted by their facet IDs):
        for name, label, facet_id, _dummy in \
          [f for f in filter_labels if f[3] == 0]:
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
                            lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', 
                              item[0][0].capitalize()+item[0][1:]))[:-1]
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
        if 'fields' in extra['facets']:
            extra['filters'] = self._create_filters_structure(
                                        extra['facets']['fields'])
        else:
            # in case of forced empty search results, the fields entry is not set;
            # this can happen with recommendations when using the
            # get_more_from_same_... methods
            extra['filters'] = []
        return extra
    
    def show_subfilter(self, facet, sel_facets, facet_fields, results):
        """
        Creates a second level for faceting. 
        Sub filters are included after the parent filters.
        """
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
                            lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', 
                              item[0][0].capitalize()+item[0][1:]))[:-1]
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
                            lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', 
                              item[0][0].capitalize()+item[0][1:]))[:-1]
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
                        lab_item = " ".join(re.findall('[A-Z\_]*[^A-Z]*', 
                          item[0][0].capitalize()+item[0][1:]))[:-1]
                        addable.append({'label': lab_item, 'count': item[1],
                                    'targets': targets})
                if addable:
                    results.append({'label': label, 'removable': [],
                               'addable': addable})

        return results
