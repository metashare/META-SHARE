from django.db import models
from datetime import datetime

        
class LRStats(models.Model):
    userid = models.CharField(blank=False, max_length=64)
    lrid = models.CharField(blank=False, max_length=64)
    sessid = models.CharField(blank=False, max_length=64)
    lasttime = models.DateTimeField(blank=False, default=datetime.now())
    action = models.CharField(blank=False, max_length=1)
    count = models.IntegerField(blank=False, default=1)

    #def __unicode__(self):
    #   return "L>> " +  self.userid + "," +self.lrid  + "," + self.action + "," + str(self.count) + "," + str(self.lasttime) + "," + self.sessid
    

class QueryStats(models.Model):
    userid = models.CharField(blank=False, max_length=64)
    field = models.CharField(blank=False, max_length=32)
    query = models.TextField(blank=False)
    lasttime = models.DateTimeField(blank=False, default=datetime.now())
    found = models.IntegerField(blank=False, default=0)
    exectime = models.IntegerField(blank=False, default=0)
    
    #def __unicode__(self):
    #    return "Q>> " +self.userid + "," + self.query + "," + str(self.lasttime)

    


