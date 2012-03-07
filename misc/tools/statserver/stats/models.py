from django.db import models
from datetime import datetime

class NodeStats(models.Model):
    hostname = models.TextField(blank=False)
    date = models.DateField(default=datetime.now())
    user = models.IntegerField(blank=False, default=0)
    lrupdate = models.IntegerField(blank=False, default=0)
    lrdown = models.IntegerField(blank=False, default=0)
    lrview = models.IntegerField(blank=False, default=0)
    queries = models.IntegerField(blank=False, default=0)
    qexec_time_avg = models.IntegerField(blank=False, default=0)
    qlt_avg = models.IntegerField(blank=False, default=0)

class Node(models.Model):
    hostname = models.TextField(blank=False)
    ip = models.TextField(blank=False)
    timestamp = models.DateTimeField(auto_now_add=False, default=datetime.now())
    checked = models.BooleanField()

