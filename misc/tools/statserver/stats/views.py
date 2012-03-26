# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response      
from statserver.stats.models import Node, NodeStats
from statserver.settings import CHECKINGTIME, MEDIA_URL
from urllib2 import URLError, Request, urlopen 
import urllib
import threading
from datetime import datetime, date
from threading import Timer
import json
import time

action_labels = {"updated": "u", "downloaded": "d", "viewed":"v"}

def addnode(request):
    ip_address = request.META.get("REMOTE_ADDR")
    hostname = ""
    if (request.GET.has_key('url')):
        hostname = str(request.GET['url'])
        nodestat = getNodeStats(hostname + "/stats/get")
        if (nodestat is not ""):
            nodes = Node.objects.filter(hostname=hostname)
            if (nodes.count() == 0):
                node = Node()
                node.hostname = hostname
                node.ip = ip_address
            else:
                node = nodes[0]
            
            node.timestamp = datetime.now()
            node.checked = True
            node.save()
            collectnodestats(node)
            return HttpResponse({'success': True})
            
    return HttpResponse({'fail': True})
                   

def getNodeStats (url):
    try:
        urlthread = FetchUrls(url)
        urlthread.start()
        urlthread.join()
        data = urlthread.getcontent()
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
        
        datestats = NodeStats.objects.filter(hostname=node.hostname, date=daytime)
        updatestats = False
        if (datestats.count() == 0):
            nodestats = NodeStats(hostname = node.hostname, date=daytime)
        else:
            nodestats = datestats[0]
            updatestats = True
        
        for item in data:
            if (item.has_key("date")):
                nodestats.date = item["date"]
            if (item.has_key("user")):
                nodestats.user = int(item["user"])
            if (item.has_key("lrupdate")):
                nodestats.lrupdate = int(item["lrupdate"])
            if (item.has_key("lrdown")):
                nodestats.lrdown = int(item["lrdown"])
            if (item.has_key("lrview")):
                nodestats.lrview = int(item["lrview"])
            if (item.has_key("queries")):
                nodestats.queries = int(item["queries"])
            if (item.has_key("qexec_time_avg")):
                nodestats.qexec_time_avg = int(item["qexec_time_avg"])         
            if (item.has_key("qlt_avg")):
                nodestats.qlt_avg = int(item["qlt_avg"])         
 
        nodestats.save(force_update=updatestats)
        
    node.save(force_update=True)
    return 
 
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
    

def checknodes():
    nodes = Node.objects.all()
    print "# {0} Checking META-Share nodes: {1} found".format(datetime.now(), len(nodes))
    for node in nodes:
        updateNodeStats(node, date.today())  
    thread = Timer(CHECKINGTIME, checknodes)
    thread.start()
     
thread = Timer(CHECKINGTIME, checknodes)
thread.start()
thread2 = Timer(5.0, collectnodestats)
thread2.start()

  
# create a view about actions made on all METASHARE nodes	
def browse(request):
    hosts = {}
    total_counter = [0, "", 0, 0, 0, 0, 0, 0, 0]
    actions = {}
    actions_byhost = {}
    actions_bydate = {}

    currdate=date.today()
    if (request.GET.has_key('date')):
        currdate=str(request.GET['date'])
        if (currdate.find(",") != -1):
            year, month, day = currdate.split(",")
            month=str(int(month)+1)
            if (int(month) < 10):
                month="0"+month
            currdate=year+"-"+month+"-"+day
        
        
    days = NodeStats.objects.values('date').order_by('-date').distinct('date')
    traffic = Node.objects.values('hostname', 'checked', 'timestamp')
    upnodes = 0
    for node in traffic:
        datestats = NodeStats.objects.filter(hostname=node['hostname'], date=currdate)
        #hostname = re.sub(r'metashare/*$', "", str(node['hostname']))
        hostname = str(node['hostname'])
        if (not datestats):
            hosts[hostname] = [int(node['checked']), pretty_timeago(node['timestamp']), 0, 0, 0, 0, 0, 0, 0]
        else:
            upnodes += 1
            hosts[hostname] = [int(node['checked']), pretty_timeago(node['timestamp']), int(datestats[0].user), int(datestats[0].lrview), int(datestats[0].lrupdate), int(datestats[0].lrdown), int(datestats[0].queries), "%0.0f" % int(datestats[0].qexec_time_avg), int(datestats[0].qlt_avg)]
            total_counter[2] += int(datestats[0].user)
            total_counter[3] += int(datestats[0].lrview)
            total_counter[4] += int(datestats[0].lrupdate)
            total_counter[5] += int(datestats[0].lrdown)
            total_counter[6] += int(datestats[0].queries)
            total_counter[7] += int(datestats[0].qexec_time_avg)
            total_counter[8] += int(datestats[0].qlt_avg)
    if (total_counter[7] > 0):
        total_counter[7] = "%0.0f" % (total_counter[7] / upnodes)
                   
    hosts["#TOTAL"] = total_counter
            

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
          
        for node in Node.objects.all():
            action_list = NodeStats.objects.values('hostname', afield)
            if (action_list):
                actions_byhost[alabel].append(int(action_list[0][afield]))
            else:
                actions_byhost[alabel].append(0)
            actions[alabel] = sum(actions_byhost[alabel])

        actions_list = NodeStats.objects.values('date', afield)
        dates = {}

        for key in actions_list:
            day = str(key['date'])  
            labeldate = day[0:4] +","+str(int(day[5:7])-1)+","+day[8:10]
            dates[labeldate] = int(key[afield])
        actions_bydate[alabel] = dates
    
    return render_to_response('templates/metastats.html', {'actions': actions, 'actionlabels': action_labels, 'traffic': hosts, 'actions_byhost': actions_byhost, 'actions_bydate': actions_bydate, 'media_prefix': MEDIA_URL, 'date': days, 'currdate': currdate})
  
def pretty_timeago(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time 
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
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
