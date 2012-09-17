
from django.conf import settings
from metashare.repository.model_utils import get_root_resources

def find_related_objects(inst):
    inst_model = inst.__class__
    inst_attrs = dir(inst_model)
    rel_attrs = []
    for attr in inst_attrs:
        if attr.endswith('_related'):
            rel_attrs.append(attr)
    
    related_objects = []
    for attr in rel_attrs:
        man = inst.__getattribute__(attr)
        objs = man.get_query_set()
        related_objects.extend(objs)
    return related_objects

class AdminRelatedInfo(object):

    show_component_type = False
    
    def build_objects_list(self, objs):
        option_elems = u''
        base_url = u'{0}'.format(settings.DJANGO_URL)
        for obj in objs:
            if self.show_component_type:
                comp_type = obj.__class__.__name__
                comp_type = comp_type.replace('InfoType_model', '')
                comp_type = comp_type.capitalize()
                separator = ':'
            else:
                comp_type = ''
                separator = ''
            url = u'{0}/editor/repository/{1}/{2}'\
                .format(base_url, obj.__class__.__name__.lower(), obj.id)
            option_elem = u'<li><a href="{2}">{0}{3} {1}</a></li>'\
                .format(comp_type, obj.__unicode__(), url, separator)
            option_elems = option_elems + option_elem
        sel = u'<div style="overflow: auto;"><ul class="related_resources">{0}</ul></div>'.format(option_elems)
        return sel

    def related_objects(self, obj):
        rel_objects = find_related_objects(obj)
        values = []
        count = rel_objects.__len__()
        val = '<span>{0} objects</span>'.format(count)
        values.append(val)
        val = self.build_objects_list(rel_objects)
        values.append(val)
        return '  '.join(values)
    related_objects.allow_tags = True
    
    def related_resources(self, obj):
        rel_objects = get_root_resources(obj)
        values = []
        val = self.build_objects_list(rel_objects)
        values.append(val)
        return '  '.join(values)
    related_resources.allow_tags = True
    
    def num_related_resources(self, obj):
        rel_objects = get_root_resources(obj)
        count = rel_objects.__len__()
        return count
    
    