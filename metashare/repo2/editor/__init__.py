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
        if not request.user.is_superuser and not request.user.has_perm('repo2.add_resourceinfotype_model'):
            raise PermissionDenied

        if request.method == 'POST':
            form = ResourceDescriptionUploadForm(request.POST, request.FILES)
            if form.is_valid():
                # Retrieve the upload resource description file.
                description = request.FILES['description']
                successes, failures = import_from_file(description, description.name, INTERNAL, request.user.id)
                
                if len(successes) == 1 and len(failures) == 0: # single resource successfully uploaded
                    resource_object = successes[0]
                    # Construct redirect URL for the new object.
                    redirect_url = reverse('editor:repo2_resourceinfotype_model_change', args=[resource_object.id])
                    messages.info(request, u'Successfully uploaded file: {}'.format(description.name))
                else:
                    # Default case: either at least one failure, or more than one success
                    # We will redirect to upload page if we have no successes at all,
                    # or to "my resources" if there is at least one success
                    redirect_url = reverse('editor:upload_xml')
                    if len(successes) > 0:
                        redirect_url = reverse('editor:repo2_resourceinfotype_model_myresources')
                        messages.info(request, u'Successfully uploaded {} resource descriptions'.format(len(successes)))
                    if len(failures) > 0:
                        _msg = u'Import failed for {} files:\n'.format(len(failures))
                        for descriptor, exception in failures:
                            _msg += u'\t{}: {}\n'.format(descriptor, ' '.join(exception.args))
                        messages.error(request, _msg)
                return HttpResponseRedirect(redirect_url)
        else: # not a POST request
            form = ResourceDescriptionUploadForm()

        context = {
          'title': _('Upload new resource description(s)'),
          'form': form,
          'form_url': request.path,
          'root_path': self.root_path,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
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