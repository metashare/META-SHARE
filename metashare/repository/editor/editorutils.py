'''
A number of utility functions and classes which do not easily fit into a single place.
To avoid circular imports, this file must not import anything from metashare.repository.editor. 
'''
from django.db import models
from django.contrib.admin.views.main import ChangeList
from django.core.urlresolvers import reverse

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

class FilteredChangeList(ChangeList):
    """
    A FilteredChangeList filters the result_list for request.user objects.
    This implementation always filters; use the superclass ChangeList for
    unfiltered views.
    """
    def __init__(self, request, model, list_display, list_display_links,
      list_filter, date_hierarchy, search_fields, list_select_related,
      list_per_page, list_editable, model_admin):
        # Call super constructor to initialise object instance.
        super(FilteredChangeList, self).__init__(request, model, list_display,
          list_display_links, list_filter, date_hierarchy, search_fields,
          list_select_related, list_per_page, list_editable, model_admin)
        # Check if the current model has an "owners" ManyToManyField.
        _has_owners_field = False
        if 'owners' in self.opts.get_all_field_names():
            _field = self.opts.get_field_by_name('owners')[0]
            _has_owners_field = isinstance(_field, models.ManyToManyField)

        # If "owners" are available, we
        # have to constrain the QuerySet using an additional filter...
        if _has_owners_field:
            _user = request.user
            self.root_query_set = self.root_query_set.filter(owners=_user)

        self.query_set = self.get_query_set()
        self.get_results(request)

    def url_for_result(self, result):
        return reverse("editor:{}_{}_change".format(self.opts.app_label, self.opts.module_name), args=(getattr(result, self.pk_attname),))
