from django.db import models
from datetime import datetime

        
class LRStats(models.Model):
    userid = models.CharField(blank=False, max_length=64)
    geoinfo = models.CharField(blank=True, max_length=2)
    lrid = models.CharField(blank=False, max_length=64)
    sessid = models.CharField(blank=False, max_length=64)
    lasttime = models.DateTimeField(blank=False, auto_now_add=True, default=datetime.now())
    action = models.CharField(blank=False, max_length=1)
    count = models.IntegerField(blank=False, default=1)

    #def __unicode__(self):
    #   return "L>> " +  self.userid + "," +self.lrid  + "," + self.action + "," + str(self.count) + "," + str(self.lasttime) + "," + self.sessid
    

class QueryStats(models.Model):
    userid = models.CharField(blank=False, max_length=64)
    geoinfo = models.CharField(blank=True, max_length=2)
    query = models.TextField(blank=False)
    facets = models.TextField(blank=False)
    lasttime = models.DateTimeField(blank=False, auto_now_add=True, default=datetime.now())
    found = models.IntegerField(blank=False, default=0)
    exectime = models.IntegerField(blank=False, default=0)
    
    #def __unicode__(self):
    #    return "Q>> " +self.userid + "," + self.query + "," + str(self.lasttime)

class UsageStats(models.Model):
    lrid = models.CharField(blank=False, max_length=64)
    elname = models.CharField(blank=False, max_length=64)
    elparent = models.CharField(blank=True, max_length=64)
    text = models.TextField(blank=True)
    count = models.IntegerField(blank=False, default=1)
    
    #def __unicode__(self):
    #    return "U>> " +str(self.lrid) + "," + str(self.elname) + "," + str(self.elparent) + "," +str(self.text)+ "," + str(self.count)


# the following code is based on http://djangosnippets.org/snippets/2451/

class TogetherManager(models.Model):
    """
    a data structure keeping track of resources that have been view are downloaded together
    """
    name = models.CharField(max_length=255)
    
    @staticmethod
    def getManager(name):
        """
        get the TogetherMaanger with the given name or creates a it if required
        """
        man = TogetherManager.objects.select_related().get_or_create(name=name)[0]
        return man
        
    def addResourcePair(self, res_id_1, res_id_2):
        """
        tells the manager that the resources with the given ids have appeared
        together
        """
        res_count_dict_1 = self.resourcecountdict_set.get_or_create(identifier = res_id_1)[0]
        res_count_dict_1.addResource(res_id_2)
        res_count_dict_2 = self.resourcecountdict_set.get_or_create(identifier = res_id_2)[0]
        res_count_dict_2.addResource(res_id_1)
        
    def getTogetherCount(self, res_id_1, res_id_2):
        """
        returns how often the resources with the given ids have appeared together
        """
        try:
            res_count_dict = self.resourcecountdict_set.get(identifier = res_id_1)
        except ResourceCountDict.DoesNotExist:
            return 0
        try:
            res_count_pair = res_count_dict.resourcecountpair_set.get(identifier = res_id_2)
        except ResourceCountPair.DoesNotExist:
            return 0
        return res_count_pair.count
    
    def __unicode__(self):
        """
        returns the Unicode representation for this manager
        """
        unicode_list = []
        unicode_list.append('{}:\n'.format(self.name))
        for rcd in self.resourcecountdict_set.all():
            unicode_list.append(unicode(rcd))
        return ''.join(unicode_list)
    
class ResourceCountDict(models.Model):
    """
    mapping of resource ids to key-value pairs of resource ids and counts,
    realized as ResourceCountPairs; contains a pointer to the TogetherManager 
    that owns it
    """
    container = models.ForeignKey(TogetherManager, db_index=True)
    identifier = models.CharField(max_length=64, editable=False, db_index=True)

    def addResource(self, res_id):
        """
        increases the count for the resource with the given id by 1
        """
        resCountPair = self.resourcecountpair_set.get_or_create(identifier = res_id)[0]
        resCountPair.increaseCount()
        
    def __unicode__(self):
        """
        returns the Unicode representation for this mapping
        """
        unicode_list = []
        unicode_list.append('{}:\n'.format(self.identifier))
        for pair in self.resourcecountpair_set.all():
            unicode_list.append('  {}\n'.format(unicode(pair)))
        return ''.join(unicode_list)


class ResourceCountPair(models.Model):
    """
    key-value pair holding a resource identifier as key and a counter as value; 
    contains a pointer to the ResourceCountDict that owns it
    """
    container = models.ForeignKey(ResourceCountDict, db_index=True)
    identifier = models.CharField(max_length=64, editable=False, db_index=True)
    count = models.PositiveIntegerField(default=0)

    def increaseCount(self, inc=1):
        """
        increases the count and save the model
        """
        self.count += inc
        self.save()
        
    def __unicode__(self):
        """
        returns the Unicode representation for this pair
        """
        return u'{0}: {1}'.format(self.identifier, self.count)
