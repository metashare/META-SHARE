from django.db import models
from metashare.repository.models import resourceInfoType_model


# the following code is based on http://djangosnippets.org/snippets/2451/

class TogetherManager(models.Model):
    """
    a data structure keeping track of resources that have been view are downloaded together
    """
    name = models.CharField(max_length=255)
    
    @staticmethod
    def getManager(name):
        """
        get the TogetherManager with the given name or creates a it if required
        """
        man = TogetherManager.objects.select_related().get_or_create(name=name)[0]
        return man
        
    def addResourcePair(self, res_1, res_2):
        """
        tells the manager that the given resources have appeared together
        """
        # pylint: disable-msg=E1101
        res_count_dict_1 = self.resourcecountdict_set.get_or_create(resource=res_1)[0]
        res_count_dict_1.addResource(res_2)
        # pylint: disable-msg=E1101
        res_count_dict_2 = self.resourcecountdict_set.get_or_create(resource=res_2)[0]
        res_count_dict_2.addResource(res_1)
        
    def getTogetherCount(self, res_1, res_2):
        """
        returns how often the given resources have appeared together
        """
        try:
            # pylint: disable-msg=E1101
            res_count_dict = self.resourcecountdict_set.get(resource=res_1)
        except ResourceCountDict.DoesNotExist:
            return 0
        try:
            res_count_pair = res_count_dict.resourcecountpair_set.get(resource=res_2)
        except ResourceCountPair.DoesNotExist:
            return 0
        return res_count_pair.count
    
    def getTogetherList(self, res, threshold):
        """
        returns a sorted list of resources that have appeared together with the
        given resource; appearance count must have at least the given threshold;
        filters deleted and non-published resources
        """
        from metashare.storage.models import PUBLISHED   
        pairs = ResourceCountPair.objects\
          .filter(container__container__name=self.name)\
          .filter(container__resource=res)\
          .filter(resource__storage_object__publication_status=PUBLISHED)\
          .filter(resource__storage_object__deleted=False)\
          .filter(count__gte=threshold).order_by('-count')
        return [p.resource for p in pairs]
              
    def __unicode__(self):
        """
        returns the Unicode representation for this manager
        """
        unicode_list = []
        unicode_list.append('{}:\n'.format(self.name))
        # pylint: disable-msg=E1101
        for rcd in self.resourcecountdict_set.all():
            unicode_list.append(unicode(rcd))
        return ''.join(unicode_list)


class ResourceCountDict(models.Model):
    """
    mapping of resources to key-value pairs of resources and counts, realized as
    ResourceCountPairs; contains a pointer to the TogetherManager that owns it
    """
    container = models.ForeignKey(TogetherManager, db_index=True)
    resource = models.ForeignKey(resourceInfoType_model, editable=False, db_index=True)

    def items(self):
        """
        Get a list of tuples of key, value for the items in this dictionary.
        This is modeled after dict.items().
        """
        # pylint: disable-msg=E1101
        return [(kvp.resource, kvp.count) for kvp in self.resourcecountpair_set.all()]

    def addResource(self, res):
        """
        increases the count for the given resource by 1
        """
        # pylint: disable-msg=E1101
        res_count_pair = self.resourcecountpair_set.get_or_create(resource = res)[0]
        res_count_pair.increaseCount()
        
    def __unicode__(self):
        """
        returns the Unicode representation for this mapping
        """
        unicode_list = []
        unicode_list.append('{}:\n'.format(self.resource.storage_object.identifier))
        # pylint: disable-msg=E1101
        for pair in self.resourcecountpair_set.all():
            unicode_list.append('  {}\n'.format(unicode(pair)))
        return ''.join(unicode_list)


class ResourceCountPair(models.Model):
    """
    key-value pair holding a resource as key and a counter as value;
    contains a pointer to the ResourceCountDict that owns it
    """
    container = models.ForeignKey(ResourceCountDict, db_index=True)
    resource = models.ForeignKey(resourceInfoType_model, editable=False, db_index=True)
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
        return u'{0}: {1}'.format(self.resource.storage_object.identifier, self.count)
