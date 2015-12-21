'''
Derived from http://djangosnippets.org/snippets/2565/
'''
from django.contrib import admin
from django.db.models.fields import related
from django.forms.widgets import SelectMultiple, HiddenInput
from django.http import HttpResponse
from django.utils.html import escape, escapejs
from django.utils.translation import ugettext as _

from metashare.repository.editor.related_widget import RelatedFieldWidgetWrapper
from metashare.repository.editor.widgets import SubclassableRelatedFieldWidgetWrapper, \
    OneToManyWidget
from selectable.forms.widgets import AutoCompleteSelectMultipleWidget
from django.db import models
from metashare.repository.models import actorInfoType_model, \
    documentationInfoType_model, \
    organizationInfoType_model, projectInfoType_model,\
    membershipInfoType_model, \
    personInfoType_model, \
    targetResourceInfoType_model, documentInfoType_model, \
    languageVarietyInfoType_model, distributionInfoType_model, \
    sizeInfoType_model, resolutionInfoType_model, audioSizeInfoType_model
from metashare.repository.editor.lookups import ActorLookup, \
    OrganizationLookup, ProjectLookup, MembershipDummyLookup, \
    PersonLookup, TargetResourceLookup, DocumentLookup, \
    DocumentationLookup, LanguageVarietyDummyLookup, SizeDummyLookup, \
    ResolutionDummyLookup, AudioSizeDummyLookup
from metashare.repository.editor.widgets import AutoCompleteSelectMultipleSubClsWidget
from metashare.repository.editor.widgets import AutoCompleteSelectMultipleEditWidget
from metashare.repository.editor.widgets import AutoCompleteSelectSingleWidget

class RelatedAdminMixin(object):
    '''
    Group the joint logic for the related widget to be used in both
    the ModelAdmin and the Inline subclasses.
    '''
    
    kwargs = {'position':'top'}
    custom_m2m_widget_overrides = {
        # Reusable types with actual ajax search:
        actorInfoType_model: AutoCompleteSelectMultipleSubClsWidget(lookup_class=ActorLookup, **kwargs), 
        documentationInfoType_model: AutoCompleteSelectMultipleSubClsWidget(lookup_class=DocumentationLookup, **kwargs),
        documentInfoType_model: AutoCompleteSelectMultipleEditWidget(lookup_class=DocumentLookup, **kwargs),
        personInfoType_model: AutoCompleteSelectMultipleEditWidget(lookup_class=PersonLookup, **kwargs),
        organizationInfoType_model: AutoCompleteSelectMultipleEditWidget(lookup_class=OrganizationLookup, **kwargs),
        projectInfoType_model: AutoCompleteSelectMultipleEditWidget(lookup_class=ProjectLookup, **kwargs),
        targetResourceInfoType_model: AutoCompleteSelectMultipleEditWidget(lookup_class=TargetResourceLookup, **kwargs),
        # Custom one-to-many widgets needed to avoid nested inlines:
        membershipInfoType_model: OneToManyWidget(lookup_class=MembershipDummyLookup),
        languageVarietyInfoType_model: OneToManyWidget(lookup_class=LanguageVarietyDummyLookup),
        sizeInfoType_model: OneToManyWidget(lookup_class=SizeDummyLookup),
        resolutionInfoType_model: OneToManyWidget(lookup_class=ResolutionDummyLookup),
        audioSizeInfoType_model: OneToManyWidget(lookup_class=AudioSizeDummyLookup),
    }
    
    custom_m2o_widget_overrides = {
        documentationInfoType_model: AutoCompleteSelectSingleWidget(lookup_class=DocumentationLookup),
        targetResourceInfoType_model: AutoCompleteSelectSingleWidget(lookup_class=TargetResourceLookup),
    }
    
    def hide_hidden_fields(self, db_field, kwargs):
        '''
        Return True if db_field is marked as a hidden field, False otherwise.
        '''
        if db_field.name in getattr(self, 'hidden_fields', ()):
            kwargs['widget'] = HiddenInput()
            kwargs['label'] = ''

    def is_x_to_many_relation(self, db_field):
        '''
        True for ForeignKey and ManyToManyField, but false for OneToOneField
        '''
        return isinstance(db_field, (models.ForeignKey, models.ManyToManyField)) \
            and not isinstance(db_field, models.OneToOneField)

    def is_subclassable(self, db_field):
        '''
        Return True if db_field points to a subclassable type, False otherwise.
        '''
        if not db_field.rel:
            return False
        _instance = db_field.rel.to()
        return hasattr(_instance, '__schema_name__') \
              and _instance.__schema_name__ == "SUBCLASSABLE"

    def formfield_for_relation(self, db_field, **kwargs):
        # The following code (except for the wrapper) is taken from options.py:formfield_for_dbfield():

        request = kwargs.pop("request", None)
        # Combine the field kwargs with any options for formfield_overrides.
        # Make sure the passed in **kwargs override anything in
        # formfield_overrides because **kwargs is more specific, and should
        # always win.
        if db_field.__class__ in self.formfield_overrides:
            kwargs = dict(self.formfield_overrides[db_field.__class__], **kwargs)


        # Get the correct formfield.
        if isinstance(db_field, models.ForeignKey):
            # Custom default widgets for certain relation fields:
            if db_field.rel.to in self.custom_m2o_widget_overrides:
                kwargs = dict({'widget':self.custom_m2o_widget_overrides[db_field.rel.to]}, **kwargs)
            formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
        elif isinstance(db_field, models.ManyToManyField):
            # Custom default widgets for certain relation fields:
            if db_field.rel.to in self.custom_m2m_widget_overrides:
                kwargs = dict({'widget':self.custom_m2m_widget_overrides[db_field.rel.to]}, **kwargs)
                if isinstance(self.custom_m2m_widget_overrides[db_field.rel.to], AutoCompleteSelectMultipleEditWidget):
                    # For AutoComplete widgets remove the 'Hold down ...'
                    # message from the field description 
                    help_text = unicode(db_field.help_text)
                    text_index = help_text.find('Hold down "Control",')
                    if text_index > 0:
                        help_text = help_text[0:text_index]
                        db_field.help_text = help_text
            formfield = self.formfield_for_manytomany(db_field, request, **kwargs)

        # For non-raw_id fields, wrap the widget with a wrapper that adds
        # extra HTML -- the "add other" interface -- to the end of the
        # rendered output. formfield can be None if it came from a
        # OneToOneField with parent_link=True or a M2M intermediary.
        if formfield and db_field.name not in self.raw_id_fields:
            related_modeladmin = self.admin_site._registry.get(
                                                        db_field.rel.to)
            can_add_related = bool(related_modeladmin and
                        related_modeladmin.has_add_permission(request))
            wrapper_class = self.is_subclassable(db_field) and SubclassableRelatedFieldWidgetWrapper \
                or admin.widgets.RelatedFieldWidgetWrapper
            
            formfield.widget = wrapper_class(
                        formfield.widget, db_field.rel, self.admin_site,
                        can_add_related=can_add_related)

        return formfield

    def use_hidden_widget_for_one2one(self, db_field, kwargs):
        ''' OneToOne fields are rendered with a HiddenInput instead of a select. '''
        if isinstance(db_field, related.OneToOneField):
            attrs = {'id':'id_{}'.format(db_field.name)}
            if db_field.rel:
                _instance = db_field.rel.to()
                if _instance.id:
                    attrs['value'] = _instance.id
            widget = HiddenInput(attrs=attrs)
            # But don't treat it as a hidden widget, e.g. in tabular inlines:
            widget.is_hidden = False
            kwargs['widget'] = widget

    def is_related_widget_appropriate(self, kwargs, formfield):
        'Determine whether it is appropriate to use a related-widget'
        if formfield and \
                isinstance(formfield.widget, admin.widgets.RelatedFieldWidgetWrapper) and \
                not isinstance(formfield.widget.widget, SelectMultiple) and \
                not ('widget' in kwargs and isinstance(kwargs['widget'], AutoCompleteSelectMultipleWidget)) and \
                not ('widget' in kwargs and isinstance(kwargs['widget'], OneToManyWidget)):
            return True
        return False

    def use_related_widget_where_appropriate(self, db_field, kwargs, formfield):
        if self.is_related_widget_appropriate(kwargs, formfield):
            request = kwargs.pop('request', None)
            related_modeladmin = self.admin_site._registry.get(db_field.rel.to)
            can_change_related = bool(related_modeladmin and 
                related_modeladmin.has_change_permission(request))
            can_delete_related = bool(related_modeladmin and 
                related_modeladmin.has_delete_permission(request))
            # FIXME:
            # This is a hack to workaround github issue #748
            # https://github.com/metashare/META-SHARE/issues/748
            # There is probably a better way to fix it but this
            # will have to do for now until a cleaner solution is found
            if db_field.rel.to == distributionInfoType_model:
                can_delete_related = False
            # END FIXME
            widget = RelatedFieldWidgetWrapper.from_contrib_wrapper(formfield.widget, 
                can_change_related, 
                can_delete_related)
            formfield.widget = widget
            
    def save_and_continue_in_popup(self, obj, request):
        '''
        For related popups, send the javascript that triggers
        (a) reloading the popup, and
        (b) updating the parent field with the ID of the object we just edited.
        '''
        pk_value = obj._get_pk_val()
        msg = _('The %(name)s "%(obj)s" was saved successfully. You may edit ' \
            'it again below.') % {'name': obj._meta.verbose_name, 'obj': obj} 
        self.message_user(request, msg)
        post_url_continue = '../%s/?_popup=1'
        return HttpResponse('<script type="text/javascript">opener.saveAndContinuePopup(window, "%s", "%s", "%s");</script>' % \
            # escape() calls force_unicode.
            (escape(pk_value), escapejs(obj), escapejs(post_url_continue % pk_value)))

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

    def edit_response_close_popup_magic_o2m(self, obj, caller=None):
        '''
        For related popups, send the javascript that triggers
        (a) closing the popup, and
        (b) updating the parent field with the ID of the object we just edited.
        '''
        pk_value = obj._get_pk_val()
        caller = caller or 'opener'
        return HttpResponse('<script type="text/javascript">%s.dismissEditPopup(window, "%s", "%s");</script>' % \
            # escape() calls force_unicode.
            (caller, escape(pk_value), escapejs(obj)))


    def list_m2m_fields_without_custom_widget(self, model):
        'List those many-to-many fields which do not have a custom widget'
        h_fields = []
        for fld in model.get_many_to_many_fields():
            if hasattr(self.form, 'Meta') and hasattr(self.form.Meta, 'widgets') and fld in self.form.Meta.widgets:
                pass # field has custom widget, do not include
            elif model._meta.get_field(fld).rel.to in self.custom_m2m_widget_overrides:
                pass # field has custom default, do not include
            else:
                h_fields.append(fld)
        return h_fields

