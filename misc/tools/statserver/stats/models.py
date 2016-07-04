from django.db import models
from datetime import datetime

DATA_STATS_CHOICES = (
    ('lrcount', ['Available resources', 'global']),
    ('lrmastercount', ['Master copy', 'global']),
    ('user', ['Users', 'incremental']),
    ('lrupdate', ['Updated actions', 'incremental']),
    ('lrdown', ['Downloaded actions', 'incremental']),
    ('lrview', ['Viewed actions', 'incremental']),
    ('queries', ['Made queries', 'incremental']),
    ('qexec_time_avg', ['Average query execution time (ms)', 'incremental']),
    ('qlt_avg', ['Queries < average time', 'incremental']),
)

class Node(models.Model):
    hostname = models.TextField(blank=False)
    ip = models.TextField(blank=False)
    timestamp = models.DateTimeField(auto_now_add=False, default=datetime.now())
    checked = models.BooleanField(default=False)
    suspected = models.IntegerField(blank=False, default=0)
    
class NodeStats(models.Model):
    node = models.ForeignKey( Node )
    date = models.DateField(default=datetime.now())
    datakey = models.CharField(max_length=30, choices=DATA_STATS_CHOICES)
    dataval = models.IntegerField(blank=False, default=0)

