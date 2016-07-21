'''
A number of utility functions and classes which do not easily fit into a single
place.

To avoid circular imports, this file must not import anything from
metashare.repository.editor. 
'''
from django import template
from django.contrib.admin.options import ModelAdmin, IncorrectLookupParameters
from django.contrib.admin.views.main import ChangeList, SEARCH_VAR, ERROR_FLAG
from django.core.exceptions import PermissionDenied,ImproperlyConfigured, \
    SuspiciousOperation
from django.core.paginator import Paginator, InvalidPage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.translation import ungettext
from django.template.response import SimpleTemplateResponse

from haystack import connections
from haystack.admin import list_max_show_all
from haystack.query import RelatedSearchQuerySet

try:
    from django.contrib.admin.options import csrf_protect_m
except ImportError:
    from haystack.utils.decorators import method_decorator
    # Do nothing on Django 1.1 and below.
    def csrf_protect(view):
        def wraps(request, *args, **kwargs):
            return view(request, *args, **kwargs)
        return wraps
    
    csrf_protect_m = method_decorator(csrf_protect)


# inline names included in fieldsets are prepended with an '_'
def encode_as_inline(name):
    return '_' + name

def decode_inline(fieldname):
    if fieldname.startswith('_'):
        name = fieldname[1:]
        return name
    else:
        return fieldname

def is_inline(fieldname):
    if fieldname.startswith('_'):
        return True
    else:
        return False
    
class AllChangeList(ChangeList):
    """
    Customized changelist for haystack search in backoffice admin of all resources. 
    """
    
    def get_results(self, request):
        if not SEARCH_VAR in request.GET:
            return super(AllChangeList, self).get_results(request)
        
        # Note that pagination is 0-based, not 1-based.
        sqs = RelatedSearchQuerySet().models(self.model).auto_query(request.GET[SEARCH_VAR]).load_all()
        if not request.user.is_superuser:
            result = self.model.objects.distinct().filter(Q(owners=request.user)
                    | Q(editor_groups__name__in=
                           request.user.groups.values_list('name', flat=True)))
        else:
            result = self.model.objects.distinct()
        if 'storage_object__publication_status__exact' in request.GET:
            result = result.filter(storage_object__publication_status__exact=request.GET["storage_object__publication_status__exact"])
        sqs = sqs.load_all_queryset(self.model, result)
        paginator = Paginator(sqs, self.list_per_page)
        # Fixed bug for pagination, count full_result_count
        full_result_count = 0
        for sq in sqs:
            full_result_count += 1
        result_count = paginator.count
        # Get the number of objects, with admin filters applied.
        
        can_show_all = result_count <= list_max_show_all(self)
        multi_page = result_count > self.list_per_page
        
        # Get the list of objects to display on this page.
        try:
            result_list = paginator.page(self.page_num+1).object_list
            # Grab just the Django models, since that's what everything else is
            # expecting.
            result_list = [result.object for result in result_list]
        except InvalidPage:
            result_list = ()
        
        self.result_count = result_count
        self.full_result_count = full_result_count
        self.result_list = result_list
        self.can_show_all = can_show_all
        self.multi_page = multi_page
        self.paginator = paginator

class FilteredChangeList(ChangeList):
    """
    A FilteredChangeList filters the result_list for request.user objects.
    
    This implementation always filters; use the superclass ChangeList for
    unfiltered views. 
    Customized for haystack search in backoffice admin of your own resources. 
    """
    
    def get_queryset(self, request):
        # First, we collect all the declared list filters.
        (self.filter_specs, self.has_filters, remaining_lookup_params,
         filters_use_distinct) = self.get_filters(request)

        # Then, we let every list filter modify the queryset to its liking.
        qs = self.root_queryset
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(request, qs)
            if new_qs is not None:
                qs = new_qs

        try:
            # Finally, we apply the remaining lookup parameters from the query
            # string (i.e. those that haven't already been processed by the
            # filters).
            qs = qs.filter(**remaining_lookup_params)
        except (SuspiciousOperation, ImproperlyConfigured):
            # Allow certain types of errors to be re-raised as-is so that the
            # caller can treat them in a special way.
            raise
        except Exception as e:
            # Every other error is caught with a naked except, because we don't
            # have any other way of validating lookup parameters. They might be
            # invalid if the keyword arguments are incorrect, or if the values
            # are not in the correct type, so we might get FieldError,
            # ValueError, ValidationError, or ?.
            raise IncorrectLookupParameters(e)

        if not qs.query.select_related:
            qs = self.apply_select_related(qs)

        # Set ordering.
        ordering = self.get_ordering(request, qs)
        qs = qs.order_by(*ordering)

        # Apply search results
        qs, search_use_distinct = self.model_admin.get_search_results(
            request, qs, self.query)

        _has_owners_field = False
        if 'owners' in self.opts.get_all_field_names():
            _field = self.opts.get_field_by_name('owners')[0]
            _has_owners_field = isinstance(_field, models.ManyToManyField)
        if _has_owners_field:
            _user = request.user
            qs = qs.filter(owners=_user)
        
        # Remove duplicates from results, if necessary
        if filters_use_distinct | search_use_distinct:
            return qs.distinct()
        else:
            return qs
    
    def url_for_result(self, result):
        return reverse("editor:{}_{}_change".format(self.opts.app_label, self.opts.model_name), args=(getattr(result, self.pk_attname),))
    
    def get_results(self, request):
        """
        Use RelatedSearchQuerySet to get the filtered results for user.
        """
        if not SEARCH_VAR in request.GET:
            return super(FilteredChangeList, self).get_results(request)
        
        # Note that pagination is 0-based, not 1-based.
        
        sqs = RelatedSearchQuerySet().models(self.model).auto_query(request.GET[SEARCH_VAR]).load_all()
        result = self.model.objects.distinct().filter(owners=request.user)
        if 'storage_object__publication_status__exact' in request.GET:
            result = result.filter(storage_object__publication_status__exact=request.GET["storage_object__publication_status__exact"])
        sqs = sqs.load_all_queryset(self.model, result)
        
        paginator = Paginator(sqs, self.list_per_page)
        # Fixed bug for pagination, count full_result_count
        full_result_count = 0
        for sq in sqs:
            full_result_count += 1
        result_count = paginator.count
        # Get the number of objects, with admin filters applied.
        
        can_show_all = result_count <= list_max_show_all(self)
        multi_page = result_count > self.list_per_page
        
        # Get the list of objects to display on this page.
        try:
            result_list = paginator.page(self.page_num+1).object_list
            # Grab just the Django models, since that's what everything else is
            # expecting.
            result_list = [result.object for result in result_list]
        except InvalidPage:
            result_list = ()
        
        self.result_count = result_count
        self.full_result_count = full_result_count
        self.result_list = result_list
        self.can_show_all = can_show_all
        self.multi_page = multi_page
        self.paginator = paginator
        
class MetaShareSearchModelAdmin(ModelAdmin):
    """
    MetaShareSearchModelAdmin hooks up the Haystack search engine in the resources manager dashboard: 
    "Manage your own resources" & "Manage all resources" resources can be filtered by status.
    The searched results can be also filtered by status.
    """
    
    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        if not self.has_change_permission(request, None):
            raise PermissionDenied
        
        if not SEARCH_VAR in request.GET or "action" in request.POST:
            # Do the usual song and dance.
            return super(MetaShareSearchModelAdmin, self).changelist_view(request, extra_context)
        # Do a search of just this model and populate a Changelist with the
        # returned bits.
        if not self.model in connections['default'].get_unified_index().get_indexed_models():
            # Oops. That model isn't being indexed. Return the usual
            # behavior instead.
            return super(MetaShareSearchModelAdmin, self).changelist_view(request, extra_context)
        
        # So. Much. Boilerplate.
        # Why copy-paste a few lines when you can copy-paste TONS of lines?
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)
        search_fields = self.get_search_fields(request)
        
        ChangeListClass = self.get_changelist(request)
        try:
            changelist = ChangeListClass(request, self.model, list_display,
                list_display_links, list_filter, self.date_hierarchy,
                search_fields, self.list_select_related, self.list_per_page,
                self.list_max_show_all, self.list_editable, self)

        except IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if ERROR_FLAG in request.GET.keys():
                return SimpleTemplateResponse('admin/invalid_setup.html', {
                    'title': _('Database error'),
                })
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')
        formset = changelist.formset = None
        media = self.media
        
        # Build the action form and populate it with available actions.
        # Check actions to see if any are available on this changelist
        actions = self.get_actions(request)
        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields['action'].choices = self.get_action_choices(request)
        else:
            action_form = None
        
        selection_note = ungettext('0 of %(count)d selected',
            'of %(count)d selected', len(changelist.result_list))
        selection_note_all = ungettext('%(total_count)s selected',
            'All %(total_count)s selected', changelist.result_count)
        
        context = {
            'module_name': force_unicode(self.model._meta.verbose_name_plural),
            'selection_note': selection_note % {'count': len(changelist.result_list)},
            'selection_note_all': selection_note_all % {'total_count': changelist.result_count},
            'title': changelist.title,
            'is_popup': changelist.is_popup,
            'cl': changelist,
            'media': media,
            'has_add_permission': self.has_add_permission(request),
            'app_label': self.model._meta.app_label,
            'action_form': action_form,
            'actions_on_top': self.actions_on_top,
            'actions_on_bottom': self.actions_on_bottom,
            'actions_selection_counter': getattr(self, 'actions_selection_counter', 0),
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response(self.change_list_template or [
            'admin/%s/%s/change_list.html' % (self.model._meta.app_label, self.model._meta.object_name.lower()),
            'admin/%s/change_list.html' % self.model._meta.app_label,
            'admin/change_list.html'
        ], context, context_instance=context_instance)
        
    
    
    