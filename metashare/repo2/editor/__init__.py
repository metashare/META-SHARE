import sys

from xml.etree.ElementTree import fromstring

from django import template
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.admin.sites import AdminSite
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.decorators import method_decorator
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect

from metashare.repo2.editor.forms import ResourceDescriptionUploadForm
from metashare.storage.models import INTERNAL
from metashare.xml_utils import import_from_file

csrf_protect_m = method_decorator(csrf_protect)

# Custom admin site

class MetashareBackendSite(AdminSite):
    index_template = 'repo2/editor/index.html'
    logout_template = 'repo2/editor/logged_out.html'

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url

        urls = super(MetashareBackendSite, self).get_urls()
        urls = patterns('',
            url(r'^upload_xml/$', self.admin_view(self.upload_xml), name='upload_xml'),
            url(r'^community/$', self.admin_view(self.community), name='community'),
            url(r'^doc/$', self.admin_view(self.documentation), name='documentation'),
            url(r'^about/$', self.admin_view(self.about), name='about'),
        ) + urls
        return urls

    @csrf_protect_m
    def upload_xml(self, request, extra_context=None):
        """
        Allows to upload a resource description into the Django database.
        """
        # Check if the current user is actually allowed to upload...
        _perm = 'repo2.add_resourceinfotype_model'
        if not request.user.is_superuser and not request.user.has_perm(_perm):
            raise PermissionDenied

        if request.method == 'POST':
            form = ResourceDescriptionUploadForm(request.POST, request.FILES)
            form_validated = form.is_valid()

            if form_validated:
                # Retrieve the upload resource description file.
                description = request.FILES['description']

                successes, failures = import_from_file(description, description.name, INTERNAL, request.user.id)
                
                
                if len(successes) == 1 and len(failures) == 0: # single resource successfully uploaded
                    resource_object = successes[0]
                    # Construct redirect URL for the new object.
                    redirect_url = reverse('editor:repo2_resourceinfotype_model_change',
                      args=[resource_object.id])
                    
                    # Create log ADDITION message for the new object.
                    LogEntry.objects.log_action(
                      user_id         = request.user.pk,
                      content_type_id = ContentType.objects.get_for_model(
                        resource_object).pk,
                      object_id       = resource_object.pk,
                      object_repr     = force_unicode(resource_object),
                      action_flag     = ADDITION
                    )
                    
                    _msg = u'Successfully uploaded file: {}'.format(description.name)
                    messages.info(request, _msg)
                    return HttpResponseRedirect(redirect_url)

                else:
                    # Default case: either at least one failure, or more than one success
                    # We will redirect to upload page if we have no successes at all,
                    # or to "my resources" if there is at least one success
                    redirect_url = reverse('editor:upload_xml')
                    if len(successes) > 0:
                        redirect_url = reverse('editor:repo2_resourceinfotype_model_myresources')
                        _msg = u'Successfully uploaded {} resource descriptions'.format(len(successes))
                        messages.info(request, _msg)
                    if len(failures) > 0:
                        _msg = u'Import failed for {} files:\n'.format(len(failures))
                        for entry in failures:
                            _msg += u'\t{}\n'.format(entry)
                        messages.error(request, _msg)
                    return HttpResponseRedirect(redirect_url)
                
#                # Extract the raw XML String and create an ElementTree for it.
#                _xml_raw = ''
#                for _chunk in description.chunks():
#                    _xml_raw += _chunk
#                
#                # We can assume that this will work as the form validated.
#                _xml_tree = fromstring(_xml_raw)
#                
#                # Try to import the created ElementTree into the Django DB.
#                _factory = getattr(sys.modules['metashare.repo2.models'],
#                  'resourceInfoType_model', None)
#                
#                if _factory is not None:
#                    result = _factory.import_from_elementtree(_xml_tree)
#                    
#                    # If the import has failed, result[0] will be set to None.
#                    if not result[0]:
#                        _msg = u'An error occured for: {}'.format(
#                          description.name)
#                        
#                        # Try to append the error message from result[2].
#                        if len(result) > 2:
#                            _msg += u' - {}'.format(result[2])
#                        
#                        # Generate an error message for the current user.
#                        messages.error(request, _msg)
#                    
#                    else:
#                        # The new resource object is available in result[0].
#                        resource_object = result[0]
#                        
#                        # Add current user to list of owners for this object.
#                        resource_object.owners.add(request.user.id)
#                        resource_object.save()
#                        
#                        # Make sure that the new object is INTERNAL!
#                        storage_object = resource_object.storage_object
#                        storage_object.published = INTERNAL
#                        storage_object.save()
#                        
#                        # Construct redirect URL for the new object.
#                        redirect_url = reverse('editor:{}_{}_change'.format(
#                          'repo2', 'resourceinfotype_model'),
#                          args=[resource_object.id])
#                        
#                        # Create log ADDITION message for the new object.
#                        LogEntry.objects.log_action(
#                          user_id         = request.user.pk,
#                          content_type_id = ContentType.objects.get_for_model(
#                            resource_object).pk,
#                          object_id       = resource_object.pk,
#                          object_repr     = force_unicode(resource_object),
#                          action_flag     = ADDITION
#                        )
#                        
#                        _msg = u'Sucessfully uploaded file: {}'.format(
#                          description.name)
#                        messages.info(request, _msg)
#                        return HttpResponseRedirect(redirect_url)

        else:
            form = ResourceDescriptionUploadForm()

        context = {
          'title': _('Upload new resource description'),
          'form': form,
          'form_url': request.path,
          'root_path': self.root_path,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request,
          current_app=self.name)
        return render_to_response(
          ['admin/repo2/resourceinfotype_model/upload_description.html'],
          context, context_instance)

    def community(self, extra_context=None):
        _msg = "This view should be implemented in an upcoming Sprint."
        raise NotImplementedError, _msg

    def documentation(self, extra_context=None):
        _msg = "This view should be implemented in an upcoming Sprint."
        raise NotImplementedError, _msg

    def about(self, extra_context=None):
        _msg = "This view should be implemented in an upcoming Sprint."
        raise NotImplementedError, _msg

admin_site = MetashareBackendSite('editor')