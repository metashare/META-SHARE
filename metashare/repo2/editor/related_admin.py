'''
From http://djangosnippets.org/snippets/2565/
'''
from django.contrib import admin
from django.db.models.fields import related
from django.forms.widgets import SelectMultiple, HiddenInput
from django.http import HttpResponse
from django.utils.html import escape, escapejs

from metashare.repo2.editor.related_widget import RelatedFieldWidgetWrapper
from metashare.repo2.editor.widgets import SingleChoiceTypeWidget, \
  MultiChoiceTypeWidget
  
# TODO: Here we are duplicating in two classes twice 99% the same code -- extract mixin?
#
# NOTE: schroed: The code for hidden fields really has nothing to do with
#                related widgets.
#
#    cfedermann: While this is true, the two SchemaModel admins defined in
#                superadmin.py sub-class the two RelatedWidgetWrapper* classes
#                which meant this was a suitable entry point for adding the
#                HiddenInput behaviour;  the whole editor class design should
#                be cleaned up and refactored at some point, though...

class RelatedWidgetWrapperAdmin(admin.ModelAdmin):

    def formfield_for_dbfield(self, db_field, **kwargs):
        _hidden_fields = getattr(self, 'hidden_fields', None)
        _hidden_fields = _hidden_fields or []
        if db_field.name in _hidden_fields:
            widget = HiddenInput()
            kwargs['widget'] = widget
            kwargs['label'] = ''
        if db_field.rel:
            _instance = db_field.rel.to()
            if hasattr(_instance, '__schema_name__') \
              and _instance.__schema_name__ == "SUBCLASSABLE":
                request = kwargs.pop('request', None)
                
                admin_site = self.admin_site
                if isinstance(db_field, related.ManyToManyField):
                    widget = MultiChoiceTypeWidget(db_field.rel, admin_site)
                else:
                    widget = SingleChoiceTypeWidget(db_field.rel, admin_site)
                
                kwargs['widget'] = widget
                return db_field.formfield(**kwargs)
        
        # OneToOne fields are rendered with a HiddenInput instead a select.
        if isinstance(db_field, related.OneToOneField):
            attrs = {'id': 'id_{}'.format(db_field.name)}
            if db_field.rel:
                _instance = db_field.rel.to()
                if _instance.id:
                    attrs['value'] = _instance.id
            
            widget = HiddenInput(attrs=attrs)
            kwargs['widget'] = widget
        
        formfield = super(RelatedWidgetWrapperAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if (formfield and
            isinstance(formfield.widget, admin.widgets.RelatedFieldWidgetWrapper) and
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
        return formfield

    def response_change(self, request, obj):
        if '_popup' in request.REQUEST:
            pk_value = obj._get_pk_val()
            return HttpResponse('<script type="text/javascript">opener.dismissEditRelatedPopup(window, "%s", "%s");</script>' % \
            # escape() calls force_unicode.
            (escape(pk_value), escapejs(obj)))
        else:
            return super(RelatedWidgetWrapperAdmin, self).response_change(request, obj)

class RelatedWidgetWrapperInline(admin.StackedInline):

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.rel:
            _instance = db_field.rel.to()
            if hasattr(_instance, '__schema_name__') \
              and _instance.__schema_name__ == "SUBCLASSABLE":
                request = kwargs.pop('request', None)
                
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

        # OneToOne fields are rendered with a HiddenInput instead a select.
        if isinstance(db_field, related.OneToOneField):
            attrs = {'id': 'id_{}'.format(db_field.name)}
            if db_field.rel:
                _instance = db_field.rel.to()
                if _instance.id:
                    attrs['value'] = _instance.id

            widget = HiddenInput(attrs=attrs)
            kwargs['widget'] = widget

        formfield = super(RelatedWidgetWrapperInline, self).formfield_for_dbfield(db_field, **kwargs)
        if (formfield and
            isinstance(formfield.widget, admin.widgets.RelatedFieldWidgetWrapper) and
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
        return formfield

    def response_change(self, request, obj):
        if '_popup' in request.REQUEST:
            pk_value = obj._get_pk_val()
            return HttpResponse('<script type="text/javascript">opener.dismissEditRelatedPopup(window, "%s", "%s");</script>' % \
            # escape() calls force_unicode.
            (escape(pk_value), escapejs(obj)))
        else:
            return super(RelatedWidgetWrapperInline, self).response_change(request, obj)

