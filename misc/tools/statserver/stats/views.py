# Create your views here.
from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import render_to_response      
from statserver.stats.models import Node, NodeStats, DATA_STATS_CHOICES
from statserver.settings import CHECKINGTIME, MEDIA_URL
from urllib2 import URLError, Request, urlopen 
import threading
from datetime import datetime, date
from threading import Timer, Thread
import time
import json

action_labels = {"updated": "u", "downloaded": "d", "viewed":"v"}

class BackgroundTimer(Thread):
    def run(self):
        while 1:
            time.sleep(CHECKINGTIME)
            Timer(0, checknodes).start()

def checknodes():
    nodes = Node.objects.all()
    print "# {0} Checking META-Share nodes: {1} found".format(datetime.now(), len(nodes))
    for node in nodes:
        updateNodeStats(node, date.today())  
    

def addnode(request):
    """
    Add a new node to Node class. If it is already exists the fields "timestamp" and "checked" are updated only.
    """
    ip_address = request.META.get("REMOTE_ADDR")
    hostname = ""
    if (request.GET.has_key('url')):
        hostname = str(request.GET['url'])
        nodestat = getNodeStats(hostname + "/stats/get")
        if (len(nodestat) == 1 and nodestat[0]['date'] is not None and nodestat[0]['lrview'] is not None):
            nodes = Node.objects.filter(hostname=hostname)
            if (nodes.count() == 0):
                node = Node()
                node.hostname = hostname
                node.ip = ip_address
            else:
                node = nodes[0]
            
            nodes = Node.objects.filter(ip__contains=ip_address).exclude(hostname=hostname)
            if (nodes.count() > 0):
                node.suspected = node.suspected + 1
                
            if (ip_address not in node.ip):
                node.ip = node.ip + " " + ip_address
            node.timestamp = datetime.now()
            node.checked = True
            node.save()
            
            #if (node.suspected == 0):
            collectnodestats(node)
            return HttpResponse({'success': True})
        else:
            print "Excluded node: " + hostname
            Node.objects.filter(hostname=hostname).delete()
            
    return HttpResponse({'fail': True})
                   

def getNodeStats (url):
    try:
        urlthread = FetchUrls(url)
        urlthread.start()
        urlthread.join()
        data = urlthread.getcontent()
        #print str(json.dumps(data)) 
        if data:
            return json.loads(data)
    except URLError, (err):
        print 'WARNING! Failed contacting statistics on {0} ({1})'.format(url, err)	
    except:
        print 'WARNING! No JSON object could be decoded from {0}'.format(url)
		
    return ""
		
class FetchUrls(threading.Thread):
    """
    Thread checking URLs.
    """
    
    def __init__(self, url):
        """
        Constructor.
        
        @param url to check
        @param output string to write url output
        """
        threading.Thread.__init__(self)
        self.url = url
        self.output = ""
        #self.lock = lock

    def getcontent(self):
        return self.output

    def run(self):
        try:
            url = self.url
            req = Request(url)
            handle = urlopen(req)
            self.output = handle.read()
        except URLError, (err):
            print 'WARNING! Failed contacting ' + url + " " + str(err)        

def updateNodeStats(node, daytime):
    url = node.hostname + "/stats/get?date=" + str(daytime)
    data = getNodeStats(url)
    if (not data):
        node.checked = False
    else: 
        node.checked = True
        node.timestamp = datetime.now()
        
        for items in data:
            if (items.has_key("date")):
                for key,val in items.items():
                    if (key != "date" and (isinstance(val, int) or isinstance(val, float))):
                        datestats = NodeStats.objects.filter(node=node, date=daytime, datakey=key)
                        updatestats = False
                        if (datestats.count() == 0):
                            nodestats = NodeStats(node = node, date=daytime, datakey=key)
                        else:
                            nodestats = datestats[0]
                            updatestats = True
                        nodestats.dataval = int(val)
                        nodestats.save(force_update=updatestats)        
    node.save(force_update=True)
    return 
 

# create a view about actions made on all METASHARE nodes	
def browse(request):
    hosts = []
    total_counter = {}
    
    actions_byhost = {}
    actions_bydate = {}
    host_labels = []
    currdate = None
    hosts_with_qexec = 0
    try:
        showupnodes = ""
        if (request.GET.has_key('showupnodes')):
            showupnodes = request.GET['showupnodes']
        if (request.GET.has_key('date')):
            currdate = str(request.GET['date'])
            if (currdate.find(",") != -1):
                year, month, day = currdate.split(",")
                month = str(int(month)+1)
                if (int(month) < 10):
                    month = "0"+month
                currdate = year+"-"+month+"-"+day
    except:
        currdate = None
    
    days = NodeStats.objects.values('date').order_by('-date').distinct('date')
    if (showupnodes == ""):
        traffic = Node.objects.values('hostname', 'checked', 'suspected', 'timestamp').distinct('hostname').order_by('-checked')
    else:    
        traffic = Node.objects.values('hostname', 'checked', 'suspected', 'timestamp').filter(checked=True).distinct('hostname')
        
    for node in traffic:
        hostname = str(node['hostname'])
        host_labels.append(hostname)
        host_info = []
        host_info.append(int(node['checked']))
        host_info.append(hostname)
        host_info.append(int(node['suspected']))
        host_info.append(pretty_timeago(node['timestamp']))
        for datakey, datalabel in DATA_STATS_CHOICES:
            if (currdate):
                datastats = NodeStats.objects.values('node__hostname') \
                    .filter(node__hostname=hostname, date=currdate, datakey=datakey) \
                    .annotate(Sum('dataval'))
            else:
                if (datalabel[1] == "global"):
                    datastats = NodeStats.objects.values('node__hostname') \
                        .filter(node__hostname=hostname, datakey=datakey) \
                        .order_by("-date")[:1].annotate(Sum('dataval'))
                else:
                    datastats = NodeStats.objects.values('node__hostname') \
                        .filter(node__hostname=hostname, datakey=datakey) \
                        .annotate(Sum('dataval'))
                    
            if (datastats):
                if (datakey not in total_counter):
                    total_counter[datakey] = 0
                if (datakey == "qexec_time_avg"):
                    host_info.append(int(datastats[0]["dataval__sum"])/1000)
                    total_counter[datakey] += int(datastats[0]["dataval__sum"]/1000)
                    hosts_with_qexec += 1
                else:
                    host_info.append(int(datastats[0]["dataval__sum"]))
                    if (datalabel[1] == "global"):
                        total_counter[datakey] = ""
                    else:
                        total_counter[datakey] += int(datastats[0]["dataval__sum"])
            else:
                host_info.append("N/A")
        hosts.append(host_info) 
            
    if ("qexec_time_avg" in total_counter):
        total_counter["qexec_time_avg"] = "%0.0f" % (total_counter["qexec_time_avg"] / hosts_with_qexec)               
            
    host_info = []
    host_info.append("")
    host_info.append("TOTAL")
    host_info.append("")
    host_info.append("")
    for datakey, datalabel in DATA_STATS_CHOICES:
        if (datakey in total_counter):
            host_info.append(total_counter[datakey])
        else:
            host_info.append("")
    hosts.append(host_info)
        
    for alabel, aid in action_labels.items():
        if (not actions_byhost.has_key(alabel)):
            actions_byhost[alabel] = []
        if (aid=="v"):
            afield = 'lrview'
        elif (aid=="u"):
            afield = 'lrupdate'
        elif (aid=="d"):
            afield = 'lrdown'
        else:
            continue
          
        for node in traffic:
            host_action = NodeStats.objects.values('node__hostname') \
                .filter(node__hostname=node['hostname'], datakey=afield) \
                .annotate(Sum("dataval"))
            for action in host_action:
                actions_byhost[alabel].append(int(action["dataval__sum"]))
        
        dates = {}       
       
        actions_list = NodeStats.objects.values('date').filter(datakey=afield).annotate(Sum("dataval"))
        for key in actions_list:
            day = str(key['date'])  
            labeldate = day[0:4] +","+str(int(day[5:7])-1)+","+day[8:10]
            dates[labeldate] = int(key["dataval__sum"])
        actions_bydate[alabel] = dates
    return render_to_response('templates/metastats.html',
        {'host_labels': host_labels,
        'stats_fields': DATA_STATS_CHOICES,
        'traffic': hosts, 
        'actions_byhost': actions_byhost,
        'actions_bydate': actions_bydate,
        'media_prefix': MEDIA_URL, 
        'date': days, 
        'currdate': currdate, 
        'showupnodes': showupnodes})


def collectnodestats(node=None):
    if (node == None):
        nodes = Node.objects.all()
    else:
        nodes = []
        nodes.append(node)
    for node in nodes:
        #get days with some statistic 
        days = getNodeStats(node.hostname+ "/stats/days")
        for day in days:  
            updateNodeStats(node, str(day))
 
collectnodes = Timer(5.0, collectnodestats)
collectnodes.start()
checktimer = BackgroundTimer()
checktimer.start()


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
    
