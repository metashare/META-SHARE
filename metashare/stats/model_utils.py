import logging
import json
import threading
import itertools 
from metashare.stats.models import LRStats, QueryStats, UsageStats
from metashare.stats.geoip import getcountry_code, getcountry_name
from django.db.models import Count, Sum
from django.contrib.auth.models import User
from datetime import datetime
from metashare.settings import LOG_HANDLER
from math import trunc

USAGETHREADNAME = "usagethread"

#type of monitored actions
UPDATE_STAT = "u"
VIEW_STAT = "v"
RETRIEVE_STAT = "r"
DOWNLOAD_STAT = "d"
PUBLISH_STAT = "p"
INGEST_STAT = "i"
DELETE_STAT = "e"

STAT_LABELS = {UPDATE_STAT: "update", VIEW_STAT: "view", RETRIEVE_STAT: "retrieve", \
    DOWNLOAD_STAT: "download", PUBLISH_STAT: "publish", INGEST_STAT: "ingest", DELETE_STAT: "delete"}
VISIBLE_STATS = [UPDATE_STAT, VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT]
    
# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)


def saveLRStats(resource, action, request=None): 
    """
    Saves the actions on a resource.
    
    Takes into account the session to avoid to increment more than one time the
    stats counter. Returns whether the stats counter was incremented or not.
    """
    if not hasattr(resource, 'storage_object') or resource.storage_object is None:
        return
        
    result = False
    lrid = resource.storage_object.identifier
    if action == INGEST_STAT or action == DELETE_STAT:
        UsageStats.objects.filter(lrid=lrid).delete()
        LRStats.objects.filter(lrid=lrid).delete()
        return
    
    userid = _get_userid(request)
    sessid = _get_sessionid(request)
    lrset = LRStats.objects.filter(userid=userid, lrid=lrid, sessid=sessid, action=action)

    if (lrset.count() > 0):
        record = lrset[0]
        #record.count = record.count+1
        #record.sessid = sessid
        record.lasttime = datetime.now()
        record.save(force_update=True)
        LOGGER.debug('UPDATESTATS: Saved LR {0}, {1} action={2} ({3}).'.format(lrid, sessid, action, record.lasttime))
    else:       
        record = LRStats()
        record.userid = userid
        record.lrid = lrid
        record.action = action
        record.sessid = sessid
        record.geoinfo = getcountry_code(_get_ipaddress(request))
        record.save(force_insert=True)
        LOGGER.debug('SAVESTATS: Saved LR {0}, {1} action={2}.'.format(lrid, sessid, action))
        result = True
    if action == UPDATE_STAT:
        if (resource.storage_object.published):
            UsageStats.objects.filter(lrid=resource.id).delete()
            _update_usage_stats(resource.id, resource.export_to_elementtree())
            LOGGER.debug('STATS: Updating usage statistics: resource {0} updated'.format(lrid))
    return result

def saveQueryStats(query, facets, found, exectime=0, request=None): 
    stat = QueryStats()
    stat.userid = _get_userid(request)
    stat.geoinfo = getcountry_code(_get_ipaddress(request))    
    stat.query = query
    stat.facets = facets
    stat.found = found
    stat.exectime = exectime    
    stat.save()
    LOGGER.debug(u'STATS: Query {0}.'.format(query))

def getLRStats(lrid):
    data = ""
    action_list = LRStats.objects.values('lrid', 'action').filter(lrid=lrid).annotate(Count('action'), Sum('count')).order_by('-action')
    if (action_list.count() > 0):
        for key in action_list:
            sets = LRStats.objects.values('lasttime').filter(lrid=lrid, action=str(key['action'])).order_by('-lasttime')[:1]
            for key2 in sets:
                if str(key['action']) in VISIBLE_STATS:
                    if (len(data) > 0):
                        data += ", "
                    data += "{\"action\":\""+ STAT_LABELS[str(key['action'])] +"\",\"count\":\""+ \
                        str(key['count__sum']) +"\",\"last\":\""+str(key2['lasttime'])[:10]+"\"}"
                    break    
    return json.loads("["+data+"]")

    
def getUserStats(lrid):
    data = ""
    action_list = LRStats.objects.values('userid', 'action').filter(lrid=lrid).annotate(Count('action'), Sum('count')).order_by('-action')
    if (action_list.count() > 0):
        for key in action_list:
            sets = LRStats.objects.values('lasttime').filter(lrid=lrid, userid=str(key['userid']), action=str(key['action'])).order_by('-lasttime')[:1]
            for key2 in sets:
                if (len(data) > 0):
                    data += ", "
                user = ""
                last_login = ""
                if key['userid']:
                    userobj = User.objects.get(username=str(key['userid']))
                    if userobj:
                        if userobj.first_name and userobj.last_name:
                            user = str(userobj.first_name) + " " +str(userobj.last_name)
                        else:
                            user = str(userobj.username)
                        user =  user + " (" +str(userobj.email)+")" #userobj.last_activity_ip
                        last_login = str(userobj.last_login.strftime("%Y/%m/%d - %I:%M:%S"))
                data += "{\"action\":\""+ STAT_LABELS[str(key['action'])] +"\",\"count\":\""+ \
                    str(key['count__sum']) +"\",\"last\":\""+str(key2['lasttime'])[:10]+"\",\"user\":\""+ user + "\",\"lastaccess\":\""+ last_login +"\"}"
                break    
    return json.loads("["+data+"]")

    
## get the top data (limited by a number) 
def getLRTop(action, limit, geoinfo=None, since=None):
    action_list = []
    if (action and not action == ""):
        if (geoinfo != None and geoinfo is not ""):
            if (since):
                action_list = LRStats.objects.values('lrid').filter(action=action, geoinfo=geoinfo, \
                    lasttime__gte=since).annotate(sum_count=Sum('count')).order_by('-sum_count')[:limit]
            else:
                action_list = LRStats.objects.values('lrid').filter(action=action, geoinfo=geoinfo).annotate(sum_count=Sum('count')).order_by('-sum_count')[:limit]
        else:
            if (since):
                action_list = LRStats.objects.values('lrid').filter(action=action, \
                    lasttime__gte=since).annotate(sum_count=Sum('count')).order_by('-sum_count')[:limit]
            else:
                action_list = LRStats.objects.values('lrid').filter(action=action).annotate(sum_count=Sum('count')).order_by('-sum_count')[:limit]
    return action_list

def getLRLast(action, limit, geoinfo=None):
    action_list = []
    if (action and not action == ""):
        if (geoinfo != None and geoinfo is not ""):
            action_list =  LRStats.objects.values('lrid', 'action', 'lasttime').filter(action=action, \
                geoinfo=geoinfo).order_by('-lasttime')[:limit]
        else:
            action_list =  LRStats.objects.values('lrid', 'action', 'lasttime').filter(action=action).order_by('-lasttime')[:limit]    
    else:
        action_list =  LRStats.objects.values('lrid', 'action', 'lasttime').order_by('-lasttime')[:limit]
    return action_list

def getTopQueries(limit, geoinfo=None, since=None):
    if (geoinfo != None and geoinfo is not ""):
        if (since):
            topqueries = QueryStats.objects.values('query', 'facets').filter(lasttime__gte=since, \
                geoinfo=geoinfo).annotate(query_count=Count('query'), facets_count=Count('facets')).order_by('-query_count','-facets_count')[:limit]
        else:
            topqueries = QueryStats.objects.values('query', 'facets').filter(geoinfo=geoinfo).annotate(query_count=Count('query'), \
                facets_count=Count('facets')).order_by('-query_count','-facets_count')[:limit] 
    else:
        if (since):
            topqueries = QueryStats.objects.values('query', 'facets').filter(lasttime__gte=since).annotate(query_count=Count('query'), \
                facets_count=Count('facets')).order_by('-query_count','-facets_count')[:limit]
        else:
            topqueries = QueryStats.objects.values('query', 'facets').annotate(query_count=Count('query'), \
                facets_count=Count('facets')).order_by('-query_count','-facets_count')[:limit]
    return topqueries
    
def getLastQuery (limit, geoinfo=None):
    if (geoinfo != None and geoinfo is not ""):
        lastquery = QueryStats.objects.values('query', 'facets', 'lasttime', 'found').filter(geoinfo=geoinfo).order_by('-lasttime')[:limit]
    else:
        lastquery = QueryStats.objects.values('query', 'facets', 'lasttime', 'found').order_by('-lasttime')[:limit]
    return lastquery

def statByDate(date):
    return LRStats.objects.values("action").filter(lasttime__year=date[0:4], lasttime__month=date[4:6], \
        lasttime__day=date[6:8]).annotate(Count('action'))
    
def statDays():
    days = itertools.chain(LRStats.objects.dates('lasttime', 'day'), QueryStats.objects.dates('lasttime', 'day'))
    return reduce(lambda x, y: x if y in x else x + [y], days, [])

def _update_usage_stats(lrid, element_tree):
    if len(element_tree.getchildren()):
        for child in element_tree.getchildren():
            item = _update_usage_stats(lrid, child)
            if (item == None or item[0] == None):
                lrset = UsageStats.objects.filter(lrid=lrid, elparent=element_tree.tag, elname=child.tag)
                if (lrset.count() > 1):
                    LOGGER.debug('ERROR! Saving usage stats in {}, {}'.format(element_tree.tag, child.tag))
                    continue
                if (lrset.count() > 0):
                    record = lrset[0]
                    record.count = record.count+1
                    record.save(force_update=True)
                else:
                    record = UsageStats()
                    record.lrid = lrid
                    record.elname = child.tag
                    record.elparent = element_tree.tag
                    record.save(force_insert=True)
                continue
            if not isinstance(item[0], basestring):
                elname = item[0][0].encode("utf-8") if item[0][0] != None else ""
                text = item[0][1].encode("utf-8") if item[0][1] != None else ""
                lrset = UsageStats.objects.filter(lrid=lrid, elparent=element_tree.tag, elname=elname, text=text)
                if (lrset.count() > 1):
                    LOGGER.debug('ERROR! Saving usage stats in {}, {}'.format(element_tree.tag, elname))
                    continue
                if (lrset.count() > 0):
                    record = lrset[0]
                    record.count = record.count+1
                    record.save(force_update=True)
                else:
                    record = UsageStats()
                    record.lrid = lrid
                    record.elname = elname
                    record.elparent = element_tree.tag
                    record.text = text
                    record.save(force_insert=True)
        return None
    # Otherwise, we return a tuple containg (key, value), i.e., (tag, text).
    else:
        return ((element_tree.tag, element_tree.text),)
        
      
def updateUsageStats(resources, create=False):   
    #check if it is already running an usage stats thread
    for current_thread in threading.enumerate():
        if current_thread.getName() == USAGETHREADNAME:
            return current_thread

    #create one
    if create:
        usagethread = UsageThread(USAGETHREADNAME, resources)
        usagethread.setName(USAGETHREADNAME)
        usagethread.start()
        return usagethread    
    return None
    
    
def getCountryActions(action):
    result = []
    sets = None
    if (action != None):
        sets = LRStats.objects.values('geoinfo').exclude(geoinfo=u'').filter(action=action).annotate(Count('action')).order_by('-action__count')
    else:
        sets = LRStats.objects.values('geoinfo').annotate(Count('action')).order_by('-action__count')
    
    for key in sets:
        result.append([key['geoinfo'], key['action__count'], getcountry_name(key['geoinfo'])])
    return result
        
        
def getCountryQueries():
    result = []
    sets = QueryStats.objects.values('geoinfo').exclude(geoinfo=u'').annotate(Count('geoinfo')).order_by('-geoinfo__count')
    for key in sets:
        result.append([key['geoinfo'], key['geoinfo__count'], getcountry_name(key['geoinfo'])])
    return result

def _get_sessionid(request):
    """
    Returns the session ID stored in the cookies of the given request.
    
    The empty string is returned, if there is no session ID available.
    """
    if request != None and request.COOKIES:
        return request.COOKIES.get('sessionid', '')
    return ''

def _get_userid(request):
    """
    Returns the username in the user of the given request.
    """
    if request != None and request.user and hasattr(request.user,'username'):
        return request.user.username
    return ''


def _get_ipaddress(request):
    """
    Returns the IP address store in META request.
    """
    if request != None and request.META.has_key('REMOTE_ADDR'):
        return request.META['REMOTE_ADDR']
    return ''


class UsageThread(threading.Thread):
    """
    Thread updating usage statistics from scratch.
    """
    resources = None
    done = 0

    def __init__(self, threadname, resources):
        """
        Constructor.

        @param thread name
        @param resources to check
        """
        threading.Thread.__init__(self)
        self.resources = resources

    def getProgress(self):
        if self.resources != None and len(self.resources) > 0:
            return trunc(self.done * 100 / len(self.resources))
        return 0
        
    def run(self):       
        self.done = 0
        for resource in self.resources:
            if (resource.storage_object.published):
                try:
                    _update_usage_stats(resource.id, resource.export_to_elementtree())
                    self.done += 1
                # pylint: disable-msg=W0703
                except Exception, e:
                    LOGGER.debug('ERROR! Usage statistics updating failed on resource {}: {}'.format(resource.id, e))

