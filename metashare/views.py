"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging

from django.contrib.auth.views import login as LOGIN, logout as LOGOUT
from django.shortcuts import render_to_response
from django.template import RequestContext

from metashare.repository.models import resourceInfoType_model
from metashare.settings import LOG_LEVEL, LOG_HANDLER
from metashare.storage.models import PUBLISHED


# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.views')
LOGGER.addHandler(LOG_HANDLER)


def frontpage(request):
    """Renders the front page view."""
    LOGGER.info('Rendering frontpage view for user "{0}".'
                .format(request.user.username or "Anonymous"))
    lr_count = resourceInfoType_model.objects.filter(
        storage_object__publication_status=PUBLISHED,
        storage_object__deleted=False).count()
    dictionary = {'title': 'Welcome to META-SHARE!', 'resources': lr_count,
      'uuid': request.session.get('METASHARE_UUID', None)}
    return render_to_response('frontpage.html', dictionary,
      context_instance=RequestContext(request))


def login(request, template_name):
    """Renders login view by connecting to django.contrib.auth.views."""
    LOGGER.info('Rendering login view for user "{0}".'.format(
      request.user.username or "Anonymous"))
    
    return LOGIN(request, template_name)


def logout(request, next_page):
    """Renders logout view by connecting to django.contrib.auth.views."""
    LOGGER.info('Logging out user "{0}", redirecting to "{1}".'.format(
      request.user.username or "Anonymous", next_page)) 
    
    return LOGOUT(request, next_page)
