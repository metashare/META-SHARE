import sys
import logging 
from metashare.settings import DJANGO_URL, STATS_SERVER_URL, METASHARE_VERSION
from metashare.repository.models import resourceInfoType_model
from metashare.storage.models import PUBLISHED
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
from django.core.paginator import Paginator

from json import JSONEncoder
import datetime
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import urllib, urllib2
from threading import Timer
from metashare.settings import LOG_HANDLER, MEDIA_URL
from metashare.stats.geoip import getcountry_name

try:
    import cPickle as pickle
except:
    import pickle

#no accessable fields
NOACCESS_FIELDS = ["downloadLocation", "executionLocation"]

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)

from django.db.models.sql import aggregates

class CountIf(aggregates.Count):
    """ 
    Hack Count() to get a conditional count working.
    """
    is_ordinal = True
    sql_function = 'COUNT'
    sql_template = '%(function)s(IF(%(condition)s,TRUE,NULL))'

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
        lastaccess = LRStats.objects.values('lasttime').filter(lrid=resource.storage_object.identifier).order_by('-lasttime')[:1]
        data.append([resource.id, resource.get_absolute_url, resource, resource.storage_object.publication_status, \
            getLRStats(resource.storage_object.identifier), getUserCount(resource.storage_object.identifier), \
            lastaccess[0]["lasttime"].strftime("%Y/%m/%d - %I:%M:%S")])
    return render_to_response('stats/mystats.html', 
        {"data": data},
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
        for _component, _field, _required in dbfields:
            verbose_name = None
            if ("/" in _component):
                verbose_name = _component
                _component = _field    #_component[_component.index('/')+1:]
            model_name = _model.replace("Type_model","")
            component_name = eval(u'{0}._meta.verbose_name'.format(_model))
            
            if (_component in _classes):
                if (not model_name+" "+_component in _fields):
                    if (not verbose_name):
                        if (not "_set" in _field):
                            verbose_name = eval(u'{0}._meta.get_field("{1}").verbose_name'.format(_model, _field))
                            class_name = eval(u'{0}Type_model._meta.verbose_name'.format(_classes[_component]))
                            if (verbose_name != class_name):
                                verbose_name = verbose_name + " [" + class_name + "]"
                        else:
                            verbose_name = eval(u'{0}Type_model._meta.verbose_name'.format(_classes[_component]))
                    _fields[model_name+" "+_component] = [component_name, _classes[_component], verbose_name, _required, 0, 0, "component", model_name]
            else:
                if (not model_name+" "+_component in _fields):
                    if (not verbose_name):
                        verbose_name = eval(u'{0}._meta.get_field("{1}").verbose_name'.format(_model, _field))
                    _fields[model_name+" "+_component] = [component_name, _field, verbose_name, _required, 0, 0, "field", model_name]            
             
    lrset = resourceInfoType_model.objects.filter(
        storage_object__publication_status=PUBLISHED,
        storage_object__deleted=False)
    lr_count = len(lrset)

    try: 
        usageset = UsageStats.objects.values('elname', 'elparent').annotate(Count('lrid', distinct=True), \
            Sum('count')).order_by('elparent', '-lrid__count', 'elname')        
        if (len(usageset) > 0):
            for item in usageset:
                class_name = str(item["elparent"])
                if class_name in _classes:
                    class_name = _classes[class_name]
                key = str(class_name) + " " + str(item["elname"])
                if key in _fields:
                    _fields[key][4] += item["lrid__count"]
                    _fields[key][5] += item["count__sum"]
                    
        selected_filters = request.POST.getlist('filter')
        fields_count = 0
        usage_fields = {}
        usage_filter = {"required": 0, "recommended": 0, "optional": 0, "never used": 0, "at least one": 0}
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
            else:
                _filters.append("at least one")
                
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
            
        
        expand_all = request.POST.get('expandall')    
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
                    
        # update usage stats according with published resources
        lr_usage = UsageStats.objects.filter(elname="resourceName").count()
        if (lrset.count() != lr_usage):
            usagethread = updateUsageStats(lrset, True)
            if usagethread != None:
                errors = "Usage statistics updating is in progress... "+ str(usagethread.getProgress()) +"% completed"
    except Exception:
        errors = "Usage statistics updating is in progress... "
    return render_to_response('stats/usagestats.html',
        {'usage_fields': sorted(usage_fields.iteritems()),
        'usage_filter': usage_filter,
        'fields_count': fields_count,
        'lr_count': lr_count,
        'selected_filters': selected_filters,
        'selected_class': selected_class,
        'selected_field': selected_field,
        'expand_all': expand_all,
        'result': result,
        'errors': errors,
        'myres': isOwner(request.user.username)},
        context_instance=RequestContext(request))

    
def topstats (request):
    """ viewing statistics about the top LR and latest queries. """    
    topdata = []
    view = request.GET.get('view', 'topviewed')
    last = request.GET.get('last', '')
    limit = int(request.GET.get('limit', '2'))
    offset = int(request.GET.get('offset', '0'))
    since = None
    if (last == "day"):
        since = date.today() + relativedelta(days = -1)
    elif (last == "week"):
        since = date.today() + relativedelta(days = -7)
    elif (last == "month"):
        since = date.today() + relativedelta(months = -1)
    elif (last == "year"):
        since = date.today() + relativedelta(years = -1)
        
    countrycode = request.GET.get('country', '')
    countryname = ""
    if (countrycode != ''):
        countryname = getcountry_name(countrycode)
    if view == "topviewed":
        geovisits = getCountryActions(VIEW_STAT)
        visitstitle = "viewing resources"
        data = getLRTop(VIEW_STAT, limit, countrycode, since, offset)
        for item in data:
            try:
                res_info =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
                topdata.append([res_info,""])
            except: 
                LOGGER.debug("Warning! The object "+item['lrid']+ " has not been found.")               
    elif (view == "latestupdated"):
        geovisits = getCountryActions(UPDATE_STAT)
        visitstitle = "updating resources"
        data = getLRLast(UPDATE_STAT, limit, countrycode, offset)
        for item in data:
            try:
                res_info =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
                topdata.append([res_info, pretty_timeago(item['lasttime'])])
            except: 
                LOGGER.debug("Warning! The object "+item['lrid']+ " has not been found.")
    elif (view == "topdownloaded"):
        geovisits = getCountryActions(DOWNLOAD_STAT)
        visitstitle = "downloading resources"
        data = getLRTop(DOWNLOAD_STAT, limit, countrycode, since, offset)
        for item in data:
            try:
                res_info =  resourceInfoType_model.objects.get(storage_object__identifier=item['lrid'])
                topdata.append([res_info,""])
            except: 
                LOGGER.debug("Warning! The object "+item['lrid']+ " has not been found.")
    elif view == "topqueries":
        geovisits = getCountryQueries()
        visitstitle = "queries"
        data = getTopQueries(limit, countrycode, since, offset)
        for item in data:
            url = "q=" + item['query']
            query = urllib.unquote(item['query'])
            facets = ""
            if (item['facets'] != ""):
                facetlist = eval(item['facets'])
                for face in facetlist:
                    url += "&selected_facets=" + face
                    facets += ", " + face.replace("Filter_exact:",": ")
                facets = facets.replace(", ", "", 1)     
            topdata.append([query, facets, "", item['query_count'], url])         
    elif view == "latestqueries":
        geovisits = getCountryQueries()
        visitstitle = "queries"
        data = getLastQuery(limit, countrycode, offset)
        for item in data:
            url = "q=" + item['query']
            query = urllib.unquote(item['query'])
            facets = ""
            if (item['facets'] != ""):
                facetlist = eval(item['facets'])
                for face in facetlist:
                    url += "&selected_facets=" + face
                    facets += ", " + face.replace("Filter_exact:",": ")
                facets = facets.replace(", ", "", 1) 
            topdata.append([query, facets, pretty_timeago(item['lasttime']), item['found'], url])       
    
    return render_to_response('stats/topstats.html',
        {'user': request.user, 
        'topdata': topdata[:limit], 
        'view': view,
        'geovisits': geovisits,
        'countrycode': countrycode,
        'countryname': countryname,
        'visitstitle': visitstitle,
        'last' : last,
        'offset': offset,
        'limit': limit,
        'myres': isOwner(request.user.username)},
        context_instance=RequestContext(request))
    
def statdays (request):
    """ get dates where there are some statistics """
    dates = []
    for day in statDays():
        dates.append(day.strftime("%Y-%m-%d"))
    return HttpResponse(JSONEncoder().encode(dates), mimetype="application/json")

def getstats (request):
    """ get statistics for a date in terms of user action made """
    data = {}
    currdate = request.GET.get('date',"")
    if (not currdate):
        currdate = date.today()
    
    data['date'] = str(currdate)    
    data['metashare_version'] = METASHARE_VERSION  
    data['user'] = LRStats.objects.filter(lasttime__startswith=currdate).values('sessid').annotate(Count('sessid')).count()
    data['lrcount'] = resourceInfoType_model.objects.filter(
        storage_object__publication_status=PUBLISHED,
        storage_object__deleted=False).count()
    data['lrupdate'] = LRStats.objects.filter(lasttime__startswith=currdate, action=UPDATE_STAT).count()
    data['lrview'] = LRStats.objects.filter(lasttime__startswith=currdate, action=VIEW_STAT).count()
    data['lrdown'] = LRStats.objects.filter(lasttime__startswith=currdate, action=DOWNLOAD_STAT).count()
    data['queries'] = QueryStats.objects.filter(lasttime__startswith=currdate).count()
    extimes = QueryStats.objects.filter(lasttime__startswith=currdate).aggregate(Avg('exectime'), Max('exectime'), Min('exectime'))
    
    qltavg = 0
    if (extimes["exectime__avg"]):
        qltavg = QueryStats.objects.filter(lasttime__startswith=currdate, exectime__lt = int(extimes["exectime__avg"])).count()
    else:
        extimes["exectime__avg"] = 0
    
    data['qexec_time_avg'] = extimes["exectime__avg"]
    data['qlt_avg'] = qltavg
    
    ###get usage statistics
    _models = [x for x in dir(sys.modules['metashare.repository.models']) if x.endswith('_model')]
    mod = import_module("metashare.repository.models")
    _fields = {}
    for _model in _models:
        # get info about fields
        dbfields = getattr(mod, _model).__schema_fields__
        for _not_used, _field, _required in dbfields:
            model_name = _model.replace("Type_model","")
            if not _field.endswith('_set') and not model_name+" " + _field in _fields:
                verbose_name = eval(u'{0}._meta.get_field("{1}").verbose_name'.format(_model, _field))
                _fields[model_name+" " + _field] = [model_name, _field, verbose_name, _required, 0, 0]
   
    usageset = UsageStats.objects.values('elname', 'elparent').annotate(Count('lrid', distinct=True), \
        Sum('count')).order_by('elparent', '-lrid__count', 'elname')        
    if (len(usageset) > 0):
        usagedata = {}
        currclass = {}
        for item in usageset:
            verbose = item["elname"]
            if item["elparent"]+" "+item["elname"] in _fields:
                verbose = _fields[item["elparent"]+" "+item["elname"]][2]
            if not item["elparent"] in currclass:
                usagedata[item["elparent"]] = [{"field": item["elname"], "label": verbose, "counters": [int(item["lrid__count"]), int(item["count__sum"])]}]
            else:
                usagedata[item["elparent"]].append({"field": item["elname"], "label": verbose, "counters": [int(item["lrid__count"]), int(item["count__sum"])]})
        data["usagestats"] = usagedata
    return HttpResponse("["+json.dumps(data)+"]", mimetype="application/json")
    

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
    if day_diff < 14:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"
    
