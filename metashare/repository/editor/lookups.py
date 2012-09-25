'''
This file contains the lookup logic for ajax-based editor search widgets.
'''
from django.utils.translation import ungettext

from selectable.base import ModelLookup
from selectable.registry import registry
from metashare.repository.models import personInfoType_model, \
    actorInfoType_model, documentInfoType_model, documentationInfoType_model,\
    projectInfoType_model, organizationInfoType_model,\
    membershipInfoType_model, \
    targetResourceInfoType_model, languageVarietyInfoType_model, \
    sizeInfoType_model, annotationInfoType_model, videoFormatInfoType_model, \
    imageFormatInfoType_model, resolutionInfoType_model, \
    audioSizeInfoType_model
from metashare.storage.models import MASTER
import logging
from metashare.settings import LOG_HANDLER
from metashare.repository.model_utils import get_root_resources

# Setup logging support.
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(LOG_HANDLER)


_AUTO_SUGGEST_SG_TPL = u'%(label)s (used %(count)d time)'
_AUTO_SUGGEST_PL_TPL = u'%(label)s (used %(count)d times)'


def print_query_results(results):
    if LOGGER.isEnabledFor(logging.DEBUG):
        if results is not None:
            LOGGER.debug(u'{0} results'.format(results.__len__()))
        else:
            LOGGER.debug(u'No results')
    return

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
        persons = self.get_queryset().filter(copy_status = MASTER)
        if term == '*':
            results = persons
        else:
            results = [p for p in persons if matches(p)]
        print_query_results(results)
        return results

    def format_item(self, item):
        fmt_item = super(PersonLookup, self).format_item(item)
        count = get_root_resources(item).__len__()
        lab = fmt_item['label']
        fmt_item['label'] = ungettext(_AUTO_SUGGEST_SG_TPL,
            _AUTO_SUGGEST_PL_TPL, count) % {'label': lab, 'count': count}
        return fmt_item

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
            if hasattr(item, 'as_subclass'):
                if hasattr(item.as_subclass(), 'copy_status'):
                    if item.as_subclass().copy_status != MASTER:
                        return False 
            return lcterm in unicode(item).lower()
        
        items = self.get_queryset()
        if term == '*':
            results = items
        else:
            results = [p for p in items if matches(p)]
        results = self.filter_results(results)
        print_query_results(results)
        return results
    
    def format_item(self, item):
        fmt_item = super(GenericUnicodeLookup, self).format_item(item)
        count = get_root_resources(item).__len__()
        lab = fmt_item['label']
        fmt_item['label'] = ungettext(_AUTO_SUGGEST_SG_TPL,
            _AUTO_SUGGEST_PL_TPL, count) % {'label': lab, 'count': count}
        if hasattr(item, 'as_subclass'):
            fmt_item['cls'] = item.as_subclass().__class__.__name__.lower()
        return fmt_item
    
    def filter_results(self, results):
        return results

class ActorLookup(GenericUnicodeLookup):
    model = actorInfoType_model
    
class DocumentationLookup(GenericUnicodeLookup):
    '''
    A special lookup which can represent values of both
    the (structured) documentInfo type and the documentUnstructured text-only type,
    but which performes lookup only on the structured entries.
    '''
    model = documentationInfoType_model

    def filter_results(self, results):
        filtered_results = [p for p in results if p.as_subclass().__class__ == documentInfoType_model]
        return filtered_results

class MembershipDummyLookup(ModelLookup):
    '''
        Dummy class for use with OneToOneWidget.
        Should be removed when unnecessary dependencies are
        removed from OneToOneWidget
    '''
    model = membershipInfoType_model

class AnnotationLookup(ModelLookup):
    '''
        Dummy class for use with OneToOneWidget.
        Should be removed when unnecessary dependencies are
        removed from OneToOneWidget
    '''
    model = annotationInfoType_model

class VideoFormatLookup(ModelLookup):
    '''
        Dummy class for use with OneToOneWidget.
        Should be removed when unnecessary dependencies are
        removed from OneToOneWidget
    '''
    model = videoFormatInfoType_model

class ImageFormatLookup(ModelLookup):
    '''
        Dummy class for use with OneToOneWidget.
        Should be removed when unnecessary dependencies are
        removed from OneToOneWidget
    '''
    model = imageFormatInfoType_model

class ResolutionDummyLookup(ModelLookup):
    '''
        Dummy class for use with OneToOneWidget.
        Should be removed when unnecessary dependencies are
        removed from OneToOneWidget
    '''
    model = resolutionInfoType_model

class LanguageVarietyDummyLookup(ModelLookup):
    '''
        Dummy class for use with OneToOneWidget.
        Should be removed when unnecessary dependencies are
        removed from OneToOneWidget
    '''
    model = languageVarietyInfoType_model

class SizeDummyLookup(ModelLookup):
    '''
        Dummy class for use with OneToOneWidget.
        Should be removed when unnecessary dependencies are
        removed from OneToOneWidget
    '''
    model = sizeInfoType_model

class AudioSizeDummyLookup(ModelLookup):
    model = audioSizeInfoType_model


class ProjectLookup(ModelLookup):
    model = projectInfoType_model
    search_fields = ('projectName__contains', )
    filters = {}
    
    def get_query(self, request, term):
        lcterm = term.lower()
        
        def matches(project):
            'Helper function to group the search code for a project'
            for multifield in (project.projectName, project.projectShortName):
                for field in multifield.itervalues():
                    if lcterm in field.lower():
                        return True
            return False
        
        projects = self.get_queryset().filter(copy_status = MASTER)
        if term == '*':
            results = projects
        else:
            results = [p for p in projects if matches(p)]
        print_query_results(results)
        return results
    
    def get_item_label(self, item):
        short_names = ''.join(item.projectShortName.itervalues())
        names = ''.join(item.projectName.itervalues())
        res = u'%s: %s' % (short_names, names)
        return res
    
    def get_item_id(self, item):
        return item.id

    def format_item(self, item):
        fmt_item = super(ProjectLookup, self).format_item(item)
        count = get_root_resources(item).__len__()
        lab = fmt_item['label']
        fmt_item['label'] = ungettext(_AUTO_SUGGEST_SG_TPL,
            _AUTO_SUGGEST_PL_TPL, count) % {'label': lab, 'count': count}
        return fmt_item
    
class OrganizationLookup(ModelLookup):
    model = organizationInfoType_model
    
    def get_query(self, request, term):
        # Since MultiTextFields cannot be searched using query sets (they are base64-encoded and pickled),
        # we must do the searching by hand.
        # Note: this is inefficient, but in practice fast enough it seems (tested with >1000 resources)
        lcterm = term.lower()
        def matches(org):
            'Helper function to group the search code for a person'
            for multifield in (org.organizationShortName, org.organizationName):
                for field in multifield.itervalues():
                    if lcterm in field.lower():
                        return True
            return False
        orgs = self.get_queryset().filter(copy_status = MASTER)
        if term == '*':
            results = orgs
        else:
            results = [p for p in orgs if matches(p)]
        print_query_results(results)
        return results

    def get_item_label(self, item):
        short_names = ''.join(item.organizationShortName.itervalues())
        names = ''.join(item.organizationName.itervalues())
        res = u'%s: %s' % (short_names, names)
        return res
    

class DocumentLookup(GenericUnicodeLookup):
    model = documentInfoType_model
    
class TargetResourceLookup(GenericUnicodeLookup):
    model = targetResourceInfoType_model

registry.register(PersonLookup)
registry.register(ActorLookup)
registry.register(DocumentationLookup)
registry.register(DocumentLookup)
registry.register(ProjectLookup)
registry.register(OrganizationLookup)
registry.register(TargetResourceLookup)

