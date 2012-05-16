"""
Project: META-SHARE 
Author: Christian Girardi <cgirardi@fbk.eu>
"""

from metashare.settings import DJANGO_URL, STATS_SERVER_URL
from metashare.stats.models import LRStats, QueryStats, UsageStats
# pylint: disable-msg=W0611, W0401
from metashare.stats.model_utils import *

# pylint: disable-msg=W0611, W0401
from metashare.repository.models import *

from django.utils.importlib import import_module
import django.utils.encoding
from django.shortcuts import render_to_response     
from django.db.models import Count, Max, Min, Avg
from django.http import HttpResponse
from django.template import RequestContext

from json import JSONEncoder
from datetime import datetime, date
import urllib, urllib2
from threading import Timer
import base64
import collections
import logging 
from metashare.settings import LOG_LEVEL, LOG_HANDLER, MEDIA_URL

try:
    import cPickle as pickle
except:
    import pickle

#no accessable fields
NOACCESS_FIELDS = ["downloadLocation", "executionLocation"]

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.stats.views')
LOGGER.addHandler(LOG_HANDLER)


def callServerStats():
    url = urllib.urlencode({'url': DJANGO_URL})
    try:
        req = urllib2.Request("{0}stats/addnode?{1}".format(STATS_SERVER_URL, url))
        urllib2.urlopen(req)
    except:
        LOGGER.debug('WARNING! Failed contacting statistics server on %s' % STATS_SERVER_URL)
                  
thread = Timer(2.0, callServerStats)
thread.start()
    
def mystats (request):
    data = []
    entry_list = getMyResources(request.user.username)
    for resource in entry_list:
        data.append([resource.id, resource.get_absolute_url, resource, \
            getLRStats(resource.storage_object.identifier), getUserStats(resource.storage_object.identifier)]) 
    return render_to_response('stats/mystats.html', {"data": data},
         context_instance=RequestContext(request))
 
def getMyResources(username):
    return resourceInfoType_model.objects.filter(owners__username=username)
    

def isOwner(username):
    entry_list = getMyResources(username)
    if (len(entry_list) > 0):
        return True
    return False
    
    
def usagestats (request):
    """  Get usage of fields LR """
    import sys
    _models = [x for x in dir(sys.modules['metashare.repository.models']) if x.endswith('_model')]
    mod = import_module("metashare.repository.models")
    _fields = {}
    _classes = {}
    errors = None
    for _model in _models:
        # get info about classes
        dbfields = getattr(mod, _model).__schema_classes__
        for _class in dbfields:
            _classes[_class] = dbfields[_class].replace("Type_model","")
            
        # get info about fields
        dbfields = getattr(mod, _model).__schema_fields__
        for _not_used, _field, _required in dbfields:
            model_name = _model.replace("Type_model","")
            if not _field.endswith('_set') and not model_name+" " + _field in _fields:
                verbose_name = eval(u'{0}._meta.get_field("{1}").verbose_name'.format(_model, _field))
                _fields[model_name+" " + _field] = [model_name, _field, verbose_name, _required, 0, 0]
                
    lrset = resourceInfoType_model.objects.all()
    usageset = UsageStats.objects.values('elname', 'elparent').annotate(Count('lrid', distinct=True), \
        Sum('count')).order_by('elparent', '-lrid__count', 'elname')        
    if len(lrset) > 0:
        if len(usageset) == 0:
            usagethread = updateUsageStats(lrset, True)
        else:
            usagethread = updateUsageStats(lrset)
        if usagethread != None:
            errors = "Usage statistics updating is in progress... "+ str(usagethread.getProgress()) +"% completed"

    if (len(usageset) > 0):
        for item in usageset:
            class_name = str(item["elparent"])
            if class_name in _classes:
                class_name = _classes[class_name]
            key = str(class_name) + " " + str(item["elname"])
            if key in _fields:
                _fields[key][4] = item["lrid__count"]
                _fields[key][5] = item["count__sum"]
            #else:
             #   errors = "Unexpected error occured during usage statistics execution"
                
    selected_filters = request.POST.getlist('filter')
    fields_count = 0
    usage_fields = {}
    usage_filter = {"required": 0, "recommended": 0, "optional": 0, "never used": 0}
    for key in _fields:
        value = _fields[key]
        _filters = []
        if value[3] == 1:
            _filters.append("required")
        elif value[3] == 2:
            _filters.append("optional")
        elif value[3] == 3:
            _filters.append("recommended")
        
        if value[5] == 0:
            _filters.append("never used")
        
        #filter
        for ifilter in _filters:
            usage_filter[ifilter] += 1
            
        if len(selected_filters) > 0:
            usedfilters = 0
            for ifilter in selected_filters:
                if ifilter in _filters:
                    usedfilters += 1
            if len(_filters) != usedfilters:
                continue 
            
        if not value[0] in usage_fields:
            usage_fields[value[0]] = [value]
        else:
            usage_fields[value[0]].append(value)
        fields_count += 1
        
    
    selected_class = request.POST.get('class')
    selected_field = request.POST.get('field')
    result = []
    resultset = UsageStats.objects.values('text').filter(elparent=selected_class, \
        elname=selected_field).annotate(Count('elname'), Sum('count')).order_by('-elname__count')
    if len(resultset) > 0:
        for item in resultset:
            text = item["text"]
            if selected_field in NOACCESS_FIELDS:
                text = "<HIDDEN VALUE>"   
            result.append([text, item["elname__count"], item["count__sum"]])
         
    return render_to_response('stats/usagestats.html',
        {'usage_fields': usage_fields,
        'usage_filter': usage_filter,
        'fields_count': fields_count,
        'lr_count': len(lrset),
        'selected_filters': selected_filters,
        'selected_class': selected_class,
        'selected_field': selected_field,
        'result': result,
        'errors': errors,
        'myres': isOwner(request.user.username)},
        context_instance=RequestContext(request))

    
def topstats (request):
    """ viewing statistics about the top LR and latest queries. """    
    topdata = []
    view = request.GET.get('view', 'topviewed')
    if view == "topviewed":
        data = getLRTop(VIEW_STAT, 10)
        for item in data:
            try:
                res_info =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
                topdata.append([res_info.id, res_info.get_absolute_url, item['sum_count'], res_info])
            except: 
                LOGGER.debug("Warning! The object "+item['lrid']+ " has not been found.")
                
    if (view == "latestupdated"):
        data = getLRLast(UPDATE_STAT, 10)
        for item in data:
            try:
                res_info =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
                topdata.append([res_info.id,  res_info.get_absolute_url, pretty_timeago(item['lasttime']), res_info])
            except: 
                LOGGER.debug("Warning! The object "+item['lrid']+ " has not been found.")
    if (view == "topdownloaded"):
        data = getLRTop(DOWNLOAD_STAT, 10)
        for item in data:
            try:
                res_info =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
                topdata.append([res_info.id, res_info.get_absolute_url, item['sum_count'], res_info])
            except: 
                LOGGER.debug("Warning! The object "+item['lrid']+ " has not been found.")

    if view == "topqueries":
        data = getTopQueries(10)
        for item in data:
            url = "q=" + item['query']
            query = urllib.unquote(item['query'])
            facets = ""
            if (item['facets'] != ""):
                facetlist = eval(item['facets'])
                for face in facetlist:
                    url += "&selected_facets=" + face
                    facets += ", " + face.replace("Filter_exact:",": ")
            topdata.append([query, facets, pretty_timeago(item['lasttime']), item['query_count'], url])       
             
    
    if view == "latestqueries":
        data = getLastQuery(10)
        for item in data:
            url = "q=" + item['query']
            query = urllib.unquote(item['query'])
            facets = ""
            if (item['facets'] != ""):
                facetlist = eval(item['facets'])
                for face in facetlist:
                    url += "&selected_facets=" + face
                    facets += ", " + face.replace("Filter_exact:",": ")
            topdata.append([query, facets, pretty_timeago(item['lasttime']), item['found'], url])       
             
    return render_to_response('stats/topstats.html',
        {'user': request.user, 
        'topdata': topdata[:10], 
        'view': view,
        'myres': isOwner(request.user.username)},
        context_instance=RequestContext(request))

def statdays (request):
    """ get dates where there are some statistics """
    dates = []
    for day in statDays():
        dates.append(day.strftime("%Y-%m-%d"))
    return HttpResponse(JSONEncoder().encode(dates))

def getstats (request):
    """ get statistics for a date in terms of user action made """
    currdate = request.GET.get('date',"")
    if (not currdate):
        currdate = date.today()
        
    user = LRStats.objects.filter(lasttime__startswith=currdate).values('sessid').annotate(Count('sessid')).count()
    ##optimize these calls just using one (model_utils.statByDate)
    lrpublish_stat = LRStats.objects.values('lrid' , 'lasttime').filter(action=PUBLISH_STAT).order_by('lasttime')
    lrpublish = 0
    for stat in lrpublish_stat:
        lringest = LRStats.objects.filter(lrid=stat["lrid"], action=INGEST_STAT, lasttime__gt=stat["lasttime"]).count()
        if (lringest == 0):
            lrpublish += 1
    lrupdate = LRStats.objects.filter(lasttime__startswith=currdate, action=UPDATE_STAT).count()
    lrview = LRStats.objects.filter(lasttime__startswith=currdate, action=VIEW_STAT).count()
    lrdown = LRStats.objects.filter(lasttime__startswith=currdate, action=DOWNLOAD_STAT).count()
    queries = QueryStats.objects.filter(lasttime__startswith=currdate).count()
    extimes = QueryStats.objects.filter(lasttime__startswith=currdate).aggregate(Avg('exectime'), Max('exectime'), Min('exectime'))
    
    qltavg = 0
    if (extimes["exectime__avg"]):
        qltavg = QueryStats.objects.filter(lasttime__startswith=currdate, exectime__lt = int(extimes["exectime__avg"])).count()
    else:
        extimes["exectime__avg"] = 0
     
    return HttpResponse("["+JSONEncoder().encode({"date": str(currdate), "lrpublish": lrpublish, "user": \
        user, "lrupdate": lrupdate, "lrview": lrview, "lrdown": lrdown, "queries": queries, \
        "qexec_time_avg": extimes["exectime__avg"], "qlt_avg": qltavg})+"]")
  

# pylint: disable-msg=R0911
def pretty_timeago(timein=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.now()
    if type(timein) is int:
        diff = now - datetime.fromtimestamp(timein)    
    elif isinstance(timein, datetime):
        diff = now - timein 
    elif not timein:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days
    
    if day_diff < 0:
        return ""

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"
    
