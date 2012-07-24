'''
Created on 16.07.2012

@author: steffen
'''
from metashare import settings
from metashare.recommendations.models import TogetherManager
import datetime
from metashare.repository.models import resourceInfoType_model

# viewed and downloaded resources are tracked
class Resource:
    VIEW = "view"
    DOWNLOAD = "download"


class SessionResourcesTracker:
    """
    Keeps track of resources the user has viewed/downloaded within a session.
    """
    
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
        
        # set of resource ids that have been downloaded together; 
        # time intervals between downloads are not longer than MAX_DOWNLOAD_INTERVAL     
        self.downloads = set()
        
        # time of last download
        self.last_download = None
        
        # set of resource ids that have been downloaded together; 
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
            # update TogetherManager with new pairs
            man = TogetherManager.getManager(res_type)
            for _res in res_set:
                man.addResourcePair(_res, res)
            res_set.add(res)
            
            
    def _get_expiration_date(self, seconds, time):
        """
        Returns the expiration date for the given maximm age in seconds based
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
