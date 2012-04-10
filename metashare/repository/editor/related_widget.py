'''
From http://djangosnippets.org/snippets/2562/
'''
from django.conf import settings
from django.contrib.admin import widgets
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

class RelatedFieldWidgetWrapper(widgets.RelatedFieldWidgetWrapper):
    
    class Media:
        js = (settings.MEDIA_URL + "js/related-widget-wrapper.js",)
    
    def __init__(self, *args, **kwargs):
        self.can_change_related = kwargs.pop('can_change_related', None)
        self.can_delete_related = kwargs.pop('can_delete_related', None)
        self.can_delete_related = False
        super(RelatedFieldWidgetWrapper, self).__init__(*args, **kwargs)
    
    @classmethod
    def from_contrib_wrapper(cls, wrapper, can_change_related, can_delete_related):
        return cls(wrapper.widget, wrapper.rel, wrapper.admin_site,
                   can_add_related=wrapper.can_add_related,
                   can_change_related=can_change_related,
                   can_delete_related=can_delete_related)
    
    def get_related_url(self, rel_to, info, action, args=None):
        if not args:
            args = []
        return reverse("admin:%s_%s_%s" % (info + (action,)), current_app=self.admin_site.name, args=args)
    
    def render(self, name, value, attrs=None, *args, **kwargs):
        if not attrs:
            attrs = {}
        
        # We may have inherited a faulty 'id' attribute in self.attrs from the RelatedWidgetMixin code,
        # which does not take any inline prefixes into account. If so, update it to the proper value:
        if 'id' in self.widget.attrs:
            self.widget.attrs['id'] = u'id_{}'.format(name)
        
        rel_to = self.rel.to
        info = (rel_to._meta.app_label, rel_to._meta.object_name.lower())
        self.widget.choices = self.choices
        attrs['class'] = ' '.join((attrs.get('class', ''), 'related-widget-wrapper'))
        context = {'widget': self.widget.render(name, value, attrs, *args, **kwargs),
                   'name': name,
                   'media_prefix': settings.ADMIN_MEDIA_PREFIX,
                   'can_change_related': self.can_change_related,
                   'can_add_related': self.can_add_related,
                   'can_delete_related': self.can_delete_related}
        if self.can_change_related:
            if value:
                context['change_url'] = self.get_related_url(rel_to, info, 'change', [value])
            template = self.get_related_url(rel_to, info, 'change', ['%s'])
            # pylint: disable-msg=E1102
            context.update({
                            'change_url_template': template,
                            'change_help_text': _('Edit related model')
                            })
        if self.can_add_related:
            # pylint: disable-msg=E1102
            context.update({
                            'add_url': self.get_related_url(rel_to, info, 'add'),
                            'add_help_text': _('Add information')
                            })
        if self.can_delete_related:
            if value:
                context['delete_url'] = self.get_related_url(rel_to, info, 'delete', [value])
            template = self.get_related_url(rel_to, info, 'delete', ['%s'])
            # pylint: disable-msg=E1102
            context.update({
                            'delete_url_template': template,
                            'delete_help_text': _('Delete related model')
                            })
        
        return mark_safe(render_to_string('repository/related_widget_wrapper.html', context))
