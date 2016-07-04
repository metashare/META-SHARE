import logging
import json
import itertools 
import threading
import re
from django.db.models import Count, Sum
from django.contrib.auth.models import User
from math import trunc
from metashare.stats.models import LRStats, QueryStats, UsageStats
from metashare.stats.geoip import getcountry_code, getcountry_name
from metashare.storage.models import PUBLISHED
from metashare.settings import LOG_HANDLER

USAGETHREADNAME = "usagethread"
BOT_AGENT_RE = re.compile(r".*(bot|spider|spyder|crawler|archiver|seek|\
    scooter|wget|misesajour|slurp|agent|gazz|onetszukaj|perl|web|lab|\
    scrubby|asterias|ip3000|knowledge|rambler|search|link|zmeu|hat|appie|\
    yandex|iron33|nazilla|kototoi).*", re.IGNORECASE)

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
    result = False
    LOGGER.debug("saveLRStats action=%s lrid=%s", action,
                 resource.storage_object.identifier)
    if not hasattr(resource, 'storage_object') or resource.storage_object is None:
        return result
        
    # Manage statistics according with the resource status
    lrid = resource.storage_object.identifier
    ignored = False
    if action == INGEST_STAT:
        ignored = True
        LRStats.objects.filter(lrid=lrid).update(ignored=ignored)
        UsageStats.objects.filter(lrid=lrid).delete()
    if action == DELETE_STAT:
        UsageStats.objects.filter(lrid=lrid).delete()
        LRStats.objects.filter(lrid=lrid).delete()
        return result
    if (resource.storage_object.publication_status != PUBLISHED):
        return result
        
    userid = _get_userid(request)
    sessid = _get_sessionid(request)
    lrset = LRStats.objects.filter(userid=userid, lrid=lrid, sessid=sessid, action=action)
    if (lrset.count() > 0):
        record = lrset[0]
        record.ignored = ignored
        record.save(force_update=True)
        #LOGGER.debug('UPDATESTATS: Saved LR {0}, {1} action={2} ({3}).'.format(lrid, sessid, action, record.lasttime))
    else:       
        record = LRStats()
        record.userid = userid
        record.lrid = lrid
        record.action = action
        record.sessid = sessid    
        record.geoinfo = getcountry_code(_get_ipaddress(request))
        record.ignored = ignored
        record.save(force_insert=True)
        #LOGGER.debug('SAVESTATS: Saved LR {0}, {1} action={2}.'.format(lrid, sessid, action))
        result = True
    if action == UPDATE_STAT:
        if (resource.storage_object.published):
            UsageStats.objects.filter(lrid=lrid).delete()
            update_usage_stats(lrid, resource.export_to_elementtree())
            #LOGGER.debug('STATS: Updating usage statistics: resource {0} updated'.format(lrid))
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
    LOGGER.debug(u'saveQueryStats q={0}.'.format(query))

def getLRStats(lrid):
    data = ""
    action_list = LRStats.objects.values('lrid', 'action').filter(lrid=lrid, ignored=False).annotate(Count('action'), Sum('count')).order_by('-action')
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

    
def getUserCount(lrid, user = None):
    if user != None:
        users = LRStats.objects.values('userid').filter(lrid=lrid).exclude(userid=user).annotate(Count('userid'))
    else:
        users = LRStats.objects.values('userid').filter(lrid=lrid).annotate(Count('userid'))
    for key in users:
        return key['userid__count']
    return 0
    
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
                        if (not userobj.email in user):
                            user = user + " (" +str(userobj.email)+")" #userobj.last_activity_ip
                        last_login = str(userobj.last_login.strftime("%Y/%m/%d - %I:%M:%S"))
                data += "{\"action\":\""+ STAT_LABELS[str(key['action'])] +"\",\"count\":\""+ \
                    str(key['count__sum']) +"\",\"last\":\""+str(key2['lasttime'])[:10]+"\",\"user\":\""+ user + "\",\"lastaccess\":\""+ last_login +"\"}"
                break    
    return json.loads("["+data+"]")

    
## get the top data (limited by a number) 
def getLRTop(action, limit, geoinfo=None, since=None, offset=0):
    action_list = []
    if (action and not action == ""):
        if (geoinfo != None and geoinfo != ''):
            if (since):
                action_list = LRStats.objects.values('lrid') \
                    .filter(ignored=False, action=action, geoinfo=geoinfo, lasttime__gte=since) \
                    .annotate(sum_count=Sum('count')).order_by('-sum_count')[offset:offset+limit]
            else:
                action_list = LRStats.objects.values('lrid') \
                    .filter(ignored=False, action=action, geoinfo=geoinfo) \
                    .annotate(sum_count=Sum('count')).order_by('-sum_count')[offset:offset+limit]
        else:
            if (since):
                action_list = LRStats.objects.values('lrid') \
                    .filter(ignored=False, action=action, lasttime__gte=since) \
                    .annotate(sum_count=Sum('count')).order_by('-sum_count')[offset:offset+limit]
            else:
                action_list = LRStats.objects.values('lrid') \
                    .filter(ignored=False, action=action) \
                    .annotate(sum_count=Sum('count')).order_by('-sum_count')[offset:offset+limit]
    return action_list

def getLRLast(action, limit, geoinfo=None, offset=0):
    action_list = []
    if (action and not action == ""):
        if (geoinfo != None and geoinfo != ''):
            action_list = LRStats.objects.values('lrid', 'action', 'lasttime') \
                .filter(ignored=False, action=action, geoinfo=geoinfo) \
                .order_by('-lasttime')[offset:offset+limit]
        else:
            action_list = LRStats.objects.values('lrid', 'action', 'lasttime') \
                .filter(ignored=False, action=action) \
                .order_by('-lasttime')[offset:offset+limit]    
    else:
        action_list = LRStats.objects.values('lrid', 'action', 'lasttime') \
            .filter(ignored=False) \
            .order_by('-lasttime')[offset:offset+limit]
    return action_list

def getTopQueries(limit, geoinfo=None, since=None, offset=0):
    if (geoinfo != None and geoinfo != ''):
        if (since):
            topqueries = QueryStats.objects.values('query', 'facets') \
                .exclude(query__startswith="mfs") \
                .filter(lasttime__gte=since, geoinfo=geoinfo) \
                .annotate(query_count=Count('query'),
                          facets_count=Count('facets')) \
                .order_by('-query_count','-facets_count')[offset:offset+limit]
        else:
            topqueries = QueryStats.objects.values('query', 'facets') \
                .exclude(query__startswith="mfs") \
                .filter(geoinfo=geoinfo) \
                .annotate(query_count=Count('query'), 
                    facets_count=Count('facets')) \
                .order_by('-query_count','-facets_count')[offset:offset+limit] 
    else:
        if (since):
            topqueries = QueryStats.objects.values('query', 'facets') \
                .exclude(query__startswith="mfs") \
                .filter(lasttime__gte=since) \
                .annotate(query_count=Count('query'), 
                    facets_count=Count('facets')) \
                .order_by('-query_count','-facets_count')[offset:offset+limit]
        else:
            topqueries = QueryStats.objects.values('query', 'facets') \
                .exclude(query__startswith="mfs") \
                .annotate(query_count=Count('query'), 
                    facets_count=Count('facets')) \
                .order_by('-query_count','-facets_count')[offset:offset+limit]
    return topqueries
    
def getLastQuery(limit, geoinfo=None, offset=0):
    if (geoinfo != None and geoinfo != ''):
        lastquery = QueryStats.objects.values('query', 'facets', 'lasttime', 'found') \
            .exclude(query__startswith="mfs") \
            .filter(geoinfo=geoinfo) \
            .order_by('-lasttime')[offset:offset+limit]
    else:
        lastquery = QueryStats.objects \
            .values('query', 'facets', 'lasttime', 'found') \
            .exclude(query__startswith="mfs") \
            .order_by('-lasttime')[offset:offset+limit]
    return lastquery

def statByDate(date):
    return LRStats.objects.values("action").filter(lasttime__year=date[0:4], lasttime__month=date[4:6], \
        lasttime__day=date[6:8]).annotate(Count('action'))
    
def statDays():
    days = itertools.chain(LRStats.objects.dates('lasttime', 'day'), QueryStats.objects.dates('lasttime', 'day'))
    return reduce(lambda x, y: x if y in x else x + [y], days, [])

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
    Returns the IP address store in META request. Check if the request 
    comes from some automatic programm (bot, spider, ..) removing the IP address
    (in this way the statistics will not be distorted)
    """    
    if request != None:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR') or ''
        # the X-Forwarded-For header may contain multiple IP addresses; use only
        # the first one (i.e., the original client's address)
        if ',' in ip_address:
            ip_address = ip_address.partition(',')[0]
        user_agent = request.META.get('HTTP_USER_AGENT') or ''
        if user_agent != '':
            if not BOT_AGENT_RE.match(user_agent):
                return ip_address
        else:
            return ip_address
    return ''


def update_usage_stats(lrid, element_tree):
    element_children = list(element_tree)
    if len(element_children):
        for child in element_children:
            item = update_usage_stats(lrid, child)
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
    

def updateUsageStats(resources):   
    #check if it is already running an UsageThread process
    for current_thread in threading.enumerate():
        if current_thread.getName() == USAGETHREADNAME:
            return current_thread

    usagethread = UsageThread(USAGETHREADNAME, resources)
    usagethread.setName(USAGETHREADNAME)
    usagethread.start()
    return usagethread    
    

class UsageThread(threading.Thread):
    """
    Thread for updating usage statistics.
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
        usagelrids = UsageStats.objects.values_list('lrid', flat=True).distinct()
        available_lrids = []
        for resource in self.resources:
            try:
                # add statistics for new resources
                if not resource.storage_object.identifier in usagelrids:
                    update_usage_stats(resource.storage_object.identifier, resource.export_to_elementtree())
                else: 
                    available_lrids.append(resource.storage_object.identifier)
            # pylint: disable-msg=W0703
            except Exception, e:
                LOGGER.debug('ERROR! Usage statistics updating failed on resource {}: {}'.format(resource.id, e))
            self.done += 1
        #remove statistics for no longer available resources
        if (len(usagelrids) != len(available_lrids)):
            self.done = self.done - 1
            for lrid in usagelrids:
                if not lrid in available_lrids:
                    UsageStats.objects.filter(lrid=str(lrid)).delete()
                    LRStats.objects.filter(lrid=str(lrid)).delete()
            
