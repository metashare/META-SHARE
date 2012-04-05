'''
Derived from http://djangosnippets.org/snippets/2565/
'''
from django.contrib import admin
from django.db.models.fields import related
from django.forms.widgets import SelectMultiple, HiddenInput
from django.http import HttpResponse
from django.utils.html import escape, escapejs

from metashare.repository.editor.related_widget import RelatedFieldWidgetWrapper
from metashare.repository.editor.widgets import SingleChoiceTypeWidget, \
  MultiChoiceTypeWidget

class RelatedAdminMixin(object):
    '''
    Group the joint logic for the related widget to be used in both
    the ModelAdmin and the Inline subclasses.
    '''
    def hide_hidden_fields(self, db_field, kwargs):
        '''
        Return True if db_field is marked as a hidden field, False otherwise.
        '''
        _hidden_fields = getattr(self, 'hidden_fields', None)
        _hidden_fields = _hidden_fields or []
        if db_field.name in _hidden_fields:
            kwargs['widget'] = HiddenInput()
            kwargs['label'] = ''

    def is_subclassable(self, db_field):
        '''
        Return True if db_field points to a subclassable type, False otherwise.
        '''
        if not db_field.rel:
            return False
        _instance = db_field.rel.to()
        return hasattr(_instance, '__schema_name__') \
              and _instance.__schema_name__ == "SUBCLASSABLE"

    def formfield_for_subclassable(self, db_field, **kwargs):
        kwargs.pop('request', None)
        admin_site = self.admin_site
        if isinstance(db_field, related.ManyToManyField):
            widget = MultiChoiceTypeWidget(db_field.rel, admin_site)
        else:
            widget = SingleChoiceTypeWidget(db_field.rel, admin_site)
        kwargs['widget'] = widget
        formfield = db_field.formfield(**kwargs)
        # Ugly trick from http://ionelmc.wordpress.com/2012/01/19/tweaks-for-making-django-admin-faster/
        # to reuse the same database query result for more than one inline of the same type.
        # We benefit from this for the 'validator' field:
        if db_field.name == 'validator':
            formfield.choices = formfield.choices
        return formfield

    def use_hidden_widget_for_one2one(self, db_field, kwargs):
        ''' OneToOne fields are rendered with a HiddenInput instead a select. '''
        if isinstance(db_field, related.OneToOneField):
            attrs = {'id':'id_{}'.format(db_field.name)}
            if db_field.rel:
                _instance = db_field.rel.to()
                if _instance.id:
                    attrs['value'] = _instance.id
            widget = HiddenInput(attrs=attrs)
            kwargs['widget'] = widget

    def use_related_widget_where_appropriate(self, db_field, kwargs, formfield):
        if (formfield and isinstance(formfield.widget, admin.widgets.RelatedFieldWidgetWrapper) and 
            not isinstance(formfield.widget.widget, SelectMultiple)):
            request = kwargs.pop('request', None)
            related_modeladmin = self.admin_site._registry.get(db_field.rel.to)
            can_change_related = bool(related_modeladmin and 
                related_modeladmin.has_change_permission(request))
            can_delete_related = bool(related_modeladmin and 
                related_modeladmin.has_delete_permission(request))
            widget = RelatedFieldWidgetWrapper.from_contrib_wrapper(formfield.widget, 
                can_change_related, 
                can_delete_related)
            formfield.widget = widget

    def edit_response_close_popup_magic(self, obj):
        '''
        For related popups, send the javascript that triggers
        (a) closing the popup, and
        (b) updating the parent field with the ID of the object we just edited.
        '''
        pk_value = obj._get_pk_val()
        return HttpResponse('<script type="text/javascript">opener.dismissEditRelatedPopup(window, "%s", "%s");</script>' % \
            # escape() calls force_unicode.
            (escape(pk_value), escapejs(obj)))



