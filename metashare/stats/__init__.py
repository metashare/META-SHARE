import urllib2, urllib
from metashare.settings import DJANGO_URL, STATS_SERVER_URL

def callServerStats(url):
    try:
        req = urllib2.Request("{0}stats/{1}".format(STATS_SERVER_URL, url))
        urllib2.urlopen(req)
    except urllib2.URLError:
        print 'WARNING! Failed contacting statistics server on %s' % STATS_SERVER_URL
               
params = urllib.urlencode({'url': DJANGO_URL})
callServerStats("addnode?%s" % params)

