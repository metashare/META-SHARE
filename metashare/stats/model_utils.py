import logging
import json
from metashare.stats.models import LRStats, QueryStats
from django.db.models import Count, Sum
from django.contrib.auth.models import User
from datetime import datetime
from metashare.settings import LOG_LEVEL, LOG_HANDLER

#type of monitored actions
UPDATE_STAT = "u"
VIEW_STAT = "v"
RETRIEVE_STAT = "r"
DOWNLOAD_STAT = "d"
PUBLISH_STAT = "p"
INGEST_STAT = "i"

STAT_LABELS = {UPDATE_STAT: "update", VIEW_STAT: "view", RETRIEVE_STAT: "retrieve", DOWNLOAD_STAT: "download", PUBLISH_STAT: "publish", INGEST_STAT: "ingest"}

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.stats.model_utils')
LOGGER.addHandler(LOG_HANDLER)

def saveLRStats(userid, lrid, sessid, action): 
    """
    this function saves the actions on a resource (it takes into account the session to avoid to increment more than one time the stats counter)
    """
    if not sessid:
        sessid = ""
    
    lrset = LRStats.objects.filter(userid=userid, lrid=lrid, sessid=sessid, action=action)
    if (lrset.count() > 0):
        record = lrset[0]
        #record.count = record.count+1
        record.sessid = sessid
        record.lasttime = datetime.now()
        record.save(force_update=True)
        LOGGER.debug('UPDATESTATS: Saved LR {0}, {1} action={2} ({3}).'.format(lrid, sessid, action, record.lasttime))
    else:       
        record = LRStats()
        record.userid = userid
        record.lrid = lrid
        record.action = action
        record.sessid = sessid 
        record.save(force_insert=True)
        LOGGER.debug('SAVESTATS: Saved LR {0}, {1} action={2}.'.format(lrid, sessid, action))

def getLRStats(lrid):
    data = ""
    action_list = LRStats.objects.values('lrid', 'action').filter(lrid=lrid).annotate(Count('action'), Sum('count')).order_by('-action')
    if (action_list.count() > 0):
        for key in action_list:
            sets = LRStats.objects.values('lasttime').filter(lrid=lrid, action=str(key['action'])).order_by('-lasttime')[:1]
            for key2 in sets:
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

def saveQueryStats(userid, facets, query, found, exectime=0): 
    stat = QueryStats()
    stat.userid = userid
    stat.query = query
    stat.facets = facets
    stat.found = found
    stat.exectime = exectime    
    stat.save()
    LOGGER.debug('STATS: Query {0}.'.format(query))

def getLastQuery (limit):
    return QueryStats.objects.values('query', 'facets', 'lasttime', 'found').filter(found__gt=0).order_by('-lasttime')[:limit]
 
def statByDate(date):
    return LRStats.objects.values("action").filter(lasttime__year=date[0:4], lasttime__month=date[4:6], lasttime__day=date[6:8]).annotate(Count('action'))
    
def statDays():
    return LRStats.objects.dates('lasttime', 'day')


