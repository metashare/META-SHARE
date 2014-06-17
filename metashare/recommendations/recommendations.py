from metashare import settings
from metashare.recommendations.models import TogetherManager, ResourceCountDict, \
    ResourceCountPair
from metashare.repository.models import resourceInfoType_model
from metashare.settings import LOG_HANDLER
from metashare.storage.models import StorageObject
import datetime
import logging
import threading

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)


# viewed and downloaded resources are tracked
class Resource:
    VIEW = "view"
    DOWNLOAD = "download"


class SessionResourcesTracker:
    """
    Keeps track of resources the user has viewed/downloaded within a session.
    """
    # a lock used for the thread-safe updating of TogetherManager with new pairs 
    lock = threading.RLock()

    @staticmethod
    def getTracker(request):
        """
        get tracker for the given request; creates new tracker if required
        """
        tracker = request.session.get('tracker')
        if not tracker:
            tracker = SessionResourcesTracker()
            request.session['tracker'] = tracker
        return tracker
    
    def __init__(self):
        
        # set of resources that have been downloaded together; 
        # time intervals between downloads are not longer than MAX_DOWNLOAD_INTERVAL     
        self.downloads = set()
        
        # time of last download
        self.last_download = None
        
        # set of resources that have been viewed together; 
        # time intervals between downloads are not longer than MAX_VIEW_INTERVAL
        self.views = set()
        
        # time of last view
        self.last_view = None


    def add_view(self, resource, time):
        """
        Tells the tracker that the given resource has been viewed 
        at the given time.
        """
        
        # check if this view is still considered 'together' with 
        # the previous views
        _expiration_date = \
          self._get_expiration_date(settings.MAX_VIEW_INTERVAL, self.last_view)
        if time > _expiration_date:
            # init new 'together' set
            self.views = set()
            self.views.add(resource)
        else:
            # update TogetherManager
            self._add_resource_to_set(self.views, resource, Resource.VIEW)
        self.last_view = time


    def add_download(self, resource, time):
        """
        Tells the tracker that the given resource has been downloaded 
        at the given time.
        """

        # check if this download is still considered 'together' with
        # the previous downloads
        _expiration_date = \
          self._get_expiration_date(
            settings.MAX_DOWNLOAD_INTERVAL, self.last_download)
        if time > _expiration_date:
            # init new 'together' set
            self.downloads = set()
            self.downloads.add(resource)
        else:
            # update TogetherManager
            self._add_resource_to_set(self.downloads, resource, Resource.DOWNLOAD)
        self.last_download = time

        
    def _add_resource_to_set(self, res_set, res, res_type):  
        """
        Adds the given resource to the given resource set; 
        resource is of the given resource type, 
        either Resource.VIEW or Resource.DOWNLOAD.
        """  
        if not res in res_set:
            # update TogetherManager with new pairs but make sure that only one
            # thread updates the TogetherManager at a time 
            with SessionResourcesTracker.lock:
                man = TogetherManager.getManager(res_type)
                for _res in res_set:
                    man.addResourcePair(_res, res)
                res_set.add(res)
            
            
    def _get_expiration_date(self, seconds, time):
        """
        Returns the expiration date for the given maximum age in seconds based
        on the given time.
        """
        if not time:
            return datetime.datetime(1970, 1, 1, 0, 0, 0)
        _td = datetime.timedelta(seconds=seconds)
        _expiration_date = time + _td
        return _expiration_date
    

def get_view_recommendations(resource):
    """
    Returns a list of ranked view recommendations for the given resource.
    """
    # TODO: decide what threshold to use; may restrict recommendation to top X resources of the list
    return TogetherManager.getManager(Resource.VIEW)\
      .getTogetherList(resource, 0)
    

def get_download_recommendations(resource):
    """
    Returns a list of ranked download recommendations for the given resource.
    """
    # TODO: decide what threshold to use; may restrict recommendation to top X resources of the list 
    return TogetherManager.getManager(Resource.DOWNLOAD)\
      .getTogetherList(resource, 0)


def get_more_from_same_creators(resource):
    """
    Returns all resources where at least one of the creators of the given
    resource is also an assigned creator.
    """
    # get all creators of the resource; this includes persons and organizations
    creation_info = resource.resourceCreationInfo
    if creation_info:
        return tuple(get_more_from_same_creators_qs(resource))
    return ()


def get_more_from_same_creators_qs(resource):
    """
    Returns a query set of all resources where at least one of the creators of
    the given resource is also an assigned creator.
    """
    # get all creators of the resource; this includes persons and organizations
    creation_info = resource.resourceCreationInfo
    if creation_info:
        return resourceInfoType_model.objects.exclude(pk=resource.pk) \
                    .filter(resourceCreationInfo__resourceCreator__in=
                                creation_info.resourceCreator.all()) \
                    .distinct()
    return resourceInfoType_model.objects.none()


def get_more_from_same_projects(resource):
    """
    Returns all resources where at least one of the projects of the given
    resource is also an assigned project.
    """
    # get all projects of the resource
    creation_info = resource.resourceCreationInfo
    if creation_info:
        return tuple(get_more_from_same_projects_qs(resource))
    return ()


def get_more_from_same_projects_qs(resource):
    """
    Returns a query set of all resources where at least one of the projects of
    the given resource is also an assigned project.
    """
    # get all projects of the resource
    creation_info = resource.resourceCreationInfo
    if creation_info:
        return resourceInfoType_model.objects.exclude(pk=resource.pk) \
                    .filter(resourceCreationInfo__fundingProject__in=
                                creation_info.fundingProject.all()) \
                    .distinct()
    return resourceInfoType_model.objects.none()
    

def repair_recommendations():
    """
    Checks if the recommendations contain links to documents no longer
    available. Removes those links when found.
    """
    from django.contrib.sessions.models import Session
    from django.contrib.sessions.backends.db import SessionStore
    for session in Session.objects.all():
        session_dict = session.get_decoded()
        if 'tracker' in session_dict:
            LOGGER.info("removing tracker for session '{}'"
                .format(session.session_key))
            del session_dict['tracker']
            session.session_data = SessionStore().encode(session_dict)
            session.save()
    for _dict in ResourceCountDict.objects.all():
        try:
            StorageObject.objects.get(identifier=_dict.lrid)
        except StorageObject.DoesNotExist:
            # remove recommendation
            LOGGER.info("removing recommendations dictionary for {}".format(_dict.lrid))
            _dict.delete()
    for _pair in ResourceCountPair.objects.all():
        try:
            StorageObject.objects.get(identifier=_pair.lrid)
        except StorageObject.DoesNotExist:
            # remove recommendation
            LOGGER.info("removing recommendations entry for {}".format(_pair.lrid))
            _pair.delete()
