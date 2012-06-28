from django.db import models
from datetime import datetime

DATA_STATS_CHOICES = (
    ('user', 'Users'),
    ('lrpublish', 'Published resources'),
    ('lrupdate', 'Updated resources'),
    ('lrdown', 'Downloaded resources'),
    ('lrview', 'Viewed resources'),
    ('queries', 'Made queries'),
    ('qexec_time_avg', 'Average query execution time'),
    ('qlt_avg', 'Queries < average time'),
)

class Node(models.Model):
    hostname = models.TextField(blank=False)
    ip = models.TextField(blank=False)
    timestamp = models.DateTimeField(auto_now_add=False, default=datetime.now())
    checked = models.BooleanField()
    
class NodeStats(models.Model):
    node = models.ForeignKey( Node )
    date = models.DateField(default=datetime.now())
    datakey = models.CharField(max_length=30, choices=DATA_STATS_CHOICES)
    dataval = models.IntegerField(blank=False, default=0)
    
    """
    hostname = models.TextField(blank=False)
    user = models.IntegerField(blank=False, default=0)
    lrupdate = models.IntegerField(blank=False, default=0)
    lrdown = models.IntegerField(blank=False, default=0)
    lrview = models.IntegerField(blank=False, default=0)
    queries = models.IntegerField(blank=False, default=0)
    qexec_time_avg = models.IntegerField(blank=False, default=0)
    qlt_avg = models.IntegerField(blank=False, default=0)
    """
