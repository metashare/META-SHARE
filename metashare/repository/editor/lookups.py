'''
This file contains the lookup logic for ajax-based editor search widgets.
'''

from selectable.base import ModelLookup
from selectable.registry import registry
from metashare.repository.models import personInfoType_model, \
    actorInfoType_model, documentInfoType_model, documentationInfoType_model,\
    targetResourceInfoType_model

class PersonLookup(ModelLookup):
    model = personInfoType_model

    def get_query(self, request, term):
        #results = super(PersonLookup, self).get_query(request, term)
        # Since MultiTextFields cannot be searched using query sets (they are base64-encoded and pickled),
        # we must do the searching by hand.
        # Note: this is inefficient, but in practice fast enough it seems (tested with >1000 resources)
        lcterm = term.lower()
        def matches(person):
            'Helper function to group the search code for a person'
            for multifield in (person.surname, person.givenName):
                for field in multifield.itervalues():
                    if lcterm in field.lower():
                        return True
            return False
        persons = self.get_queryset()
        if term == '*':
            results = persons
        else:
            results = [p for p in persons if matches(p)]
        if results is not None:
            print u'{} results'.format(results.__len__())
        else:
            print u'No results'
        return results


class GenericUnicodeLookup(ModelLookup):
    '''
    A reusable base class for lookups that have to be carried out by hand
    (rather than using querysets to do an efficient database search),
    doing string matching on the unicode string representing a database item.
    '''
    def get_query(self, request, term):
        # Since Subclassables and some other classes cannot be searched using query sets,
        # we must do the searching by hand.
        # Note: this is inefficient, but in practice fast enough it seems (tested with >1000 resources)
        lcterm = term.lower()
        def matches(item):
            'Helper function to group the search code for a database item'
            return lcterm in unicode(item).lower()
        items = self.get_queryset()
        if term == '*':
            results = items
        else:
            results = [p for p in items if matches(p)]
        if results is not None:
            print u'{} results'.format(results.__len__())
        else:
            print u'No results'
        return results

class ActorLookup(GenericUnicodeLookup):
    model = actorInfoType_model

class DocumentationLookup(ModelLookup):
    '''
    A special lookup which can represent values of both
    the (structured) documentInfo type and the documentUnstructured text-only type,
    but which performes lookup only on the structured entries.
    '''
    model = documentationInfoType_model

    def get_query(self, request, term):
        # Since Subclassables and some other classes cannot be searched using query sets,
        # we must do the searching by hand.
        # Note: this is inefficient, but in practice fast enough it seems (tested with >1000 resources)
        lcterm = term.lower()
        def matches(item):
            'Helper function to group the search code for a database item'
            return lcterm in unicode(item).lower()
        items = documentInfoType_model.objects.get_query_set()
        if term == '*':
            results = items
        else:
            results = [p for p in items if matches(p)]
        if results is not None:
            print u'{} results'.format(results.__len__())
        else:
            print u'No results'
        return results

class DocumentLookup(GenericUnicodeLookup):
    model = documentInfoType_model
    
class TargetResourceLookup(GenericUnicodeLookup):
    model = targetResourceInfoType_model

registry.register(PersonLookup)
registry.register(ActorLookup)
registry.register(DocumentationLookup)
registry.register(DocumentLookup)
registry.register(TargetResourceLookup)

