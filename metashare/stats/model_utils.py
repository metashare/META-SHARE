import logging
import json
import threading
from metashare.stats.models import LRStats, QueryStats, UsageStats
from django.db.models import Count, Sum
from django.contrib.auth.models import User
from datetime import datetime
from metashare.settings import LOG_LEVEL, LOG_HANDLER
from math import trunc

USAGETHREADNAME = "usagethread"

#type of monitored actions
UPDATE_STAT = "u"
VIEW_STAT = "v"
RETRIEVE_STAT = "r"
DOWNLOAD_STAT = "d"
PUBLISH_STAT = "p"
INGEST_STAT = "i"

STAT_LABELS = {UPDATE_STAT: "update", VIEW_STAT: "view", RETRIEVE_STAT: "retrieve", DOWNLOAD_STAT: "download", PUBLISH_STAT: "publish", INGEST_STAT: "ingest"}
VISIBLE_STATS = [UPDATE_STAT, VIEW_STAT, RETRIEVE_STAT, DOWNLOAD_STAT]
    
# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.stats.model_utils')
LOGGER.addHandler(LOG_HANDLER)


def saveLRStats(resource, userid, sessid, action): 
    """
    this function saves the actions on a resource (it takes into account the session to avoid to increment more than one time the stats counter)
    """
    if not sessid:
        sessid = ""   
    lrset = LRStats.objects.filter(userid=userid, lrid=resource.storage_object.identifier, sessid=sessid, action=action)
    if (lrset.count() > 0):
        record = lrset[0]
        #record.count = record.count+1
        record.sessid = sessid
        record.lasttime = datetime.now()
        record.save(force_update=True)
        LOGGER.debug('UPDATESTATS: Saved LR {0}, {1} action={2} ({3}).'.format(resource.storage_object.identifier, sessid, action, record.lasttime))
    else:       
        record = LRStats()
        record.userid = userid
        record.lrid = resource.storage_object.identifier
        record.action = action
        record.sessid = sessid 
        record.save(force_insert=True)
        LOGGER.debug('SAVESTATS: Saved LR {0}, {1} action={2}.'.format(resource.storage_object.identifier, sessid, action))
    if action == UPDATE_STAT or action == PUBLISH_STAT:
        if (resource.storage_object.published):
            UsageStats.objects.filter(lrid=resource.id).delete()
            _update_usage_stats(resource.id, resource.export_to_elementtree())
            LOGGER.debug('STATS: Updating usage statistics: resource {0} updated'.format(resource.storage_object.identifier))
    
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
def getLRTop(action, limit):
    action_list = []
    if (action and not action == ""):
        action_list = LRStats.objects.values('lrid').filter(action=action).annotate(sum_count=Sum('count')).order_by('-sum_count')[:limit]                
    return action_list

def getLRLast(action, limit):
    action_list = []
    if (action and not action == ""):
        action_list =  LRStats.objects.values('lrid', 'action', 'lasttime').filter(action=action).order_by('-lasttime')[:limit]
    else:
        action_list =  LRStats.objects.values('lrid', 'action', 'lasttime').order_by('-lasttime')[:limit]
    return action_list

def saveQueryStats(query, facets, userid, found, exectime=0): 
    stat = QueryStats()
    stat.userid = userid
    stat.query = query
    stat.facets = facets
    stat.found = found
    stat.exectime = exectime    
    stat.save()
    LOGGER.debug('STATS: Query {0}.'.format(query))

def getTopQueries(limit):
    return QueryStats.objects.values('query', 'facets','lasttime').annotate(query_count=Count('query'), facets_count=Count('facets')).order_by('query_count','facets_count')[:limit]
 
def getLastQuery (limit):
    return QueryStats.objects.values('query', 'facets', 'lasttime', 'found').order_by('-lasttime')[:limit]
 
def statByDate(date):
    return LRStats.objects.values("action").filter(lasttime__year=date[0:4], lasttime__month=date[4:6], lasttime__day=date[6:8]).annotate(Count('action'))
    
def statDays():
    return LRStats.objects.dates('lasttime', 'day')

def _update_usage_stats(lrid, element_tree):
    if len(element_tree.getchildren()):
        for child in element_tree.getchildren():
            item = _update_usage_stats(lrid, child)
            if (item == None or item[0] == None):
                continue
            if not isinstance(item[0], basestring):
                elname = item[0][0]
                if elname != None:
                    elname = elname.encode("utf-8")
                text = item[0][1]
                if text != None:
                    text = text.encode("utf-8")
                lrset = UsageStats.objects.filter(lrid=lrid, elparent=element_tree.tag, elname=elname, text=text)
                if (lrset.count() > 1):
                    LOGGER.debug('ERROR! Saving usage stats in {}, {}'.format(element_tree.tag, elname))
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

class UsageThread(threading.Thread):
    """
    Thread updating usage statistics.
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

