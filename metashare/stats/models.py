from django.db import models
from datetime import datetime
        
class LRStats(models.Model):
    # the storage object identifier of the language resource,
    # NOT the pk of the resource!
    lrid = models.CharField(blank=False, max_length=64)    

    userid = models.CharField(blank=False, max_length=64)
    geoinfo = models.CharField(blank=True, max_length=2)
    sessid = models.CharField(blank=False, max_length=64)
    lasttime = models.DateTimeField(blank=False)
    action = models.CharField(blank=False, max_length=1)
    count = models.IntegerField(blank=False, default=1)
    ignored = models.BooleanField(blank=False, default=False)

    def save(self, **kwargs):
        # automatically set the `lasttime` value if it is not given; we are not
        # using Django's `auto_now_add` on purpose, as we'd like to be able to
        # override the timestamp upon object creation (e.g., during node
        # migration)
        if self.lasttime is None:
            self.lasttime = datetime.now()
        super(LRStats, self).save(**kwargs)

    #def __unicode__(self):
    #   return "L>> " +  self.userid + "," +self.lrid  + "," + self.action  + "," \
    #        + str(self.lasttime) + "," + self.sessid+ "," + str(self.count)+ "," \
    #        + str(self.ignored)
        
class QueryStats(models.Model):
    userid = models.CharField(blank=False, max_length=64)
    geoinfo = models.CharField(blank=True, max_length=2)
    query = models.TextField(blank=False)
    facets = models.TextField(blank=False)
    lasttime = models.DateTimeField(blank=False)
    found = models.IntegerField(blank=False, default=0)
    exectime = models.IntegerField(blank=False, default=0)

    def save(self, **kwargs):
        # automatically set the `lasttime` value if it is not given; we are not
        # using Django's `auto_now_add` on purpose, as we'd like to be able to
        # override the timestamp upon object creation (e.g., during node
        # migration)
        if self.lasttime is None:
            self.lasttime = datetime.now()
        super(QueryStats, self).save(**kwargs)

    #def __unicode__(self):
    #    return "Q>> " +self.userid + "," + self.query + "," + str(self.lasttime)

class UsageStats(models.Model):
    # the storage object identifier of the language resource,
    # NOT the pk of the resource!
    lrid = models.CharField(blank=False, max_length=64)    

    elname = models.CharField(blank=False, max_length=64)
    elparent = models.CharField(blank=True, max_length=64)
    text = models.TextField(blank=True)
    count = models.IntegerField(blank=False, default=1)
    
    #def __unicode__(self):
    #    return "U>> " +str(self.lrid) + "," + str(self.elname) + "," + str(self.elparent) + "," +str(self.text)+ "," + str(self.count)
