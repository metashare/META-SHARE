"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.contrib import admin
from metashare.storage.models import StorageObject, StorageServer


class StorageObjectAdmin(admin.ModelAdmin):
    """
    Model admin class for stored object instances.
    """
    list_filter = ('copy_status', 'publication_status', 'deleted')
    readonly_fields = ('source_url', 'identifier', 'created', 'modified', 
      'checksum', 'digest_checksum', 'digest_modified', 'metashare_version',
      'copy_status')
    search_fields = ('metadata', 'global_storage', 'local_storage')
    
    fieldsets = (
      ('Read-only Fields', {
        'fields': ('source_url', 'identifier', 'created', 'modified', 
          'checksum', 'digest_checksum', 'digest_modified', 
          'metashare_version', 'copy_status'),
      }),
      ('Status Fields', {
        'fields': ('revision', 'publication_status', 'deleted'),
      }),
      ('Metadata Fields', {
        'fields': ('metadata', 'global_storage', 'local_storage'),
      }),
    )


class StorageServerAdmin(admin.ModelAdmin):
    """
    Model admin class for storage server instances.
    """
    readonly_fields = ('updated',)
    search_fields = ('shortname',)


admin.site.register(StorageObject, StorageObjectAdmin)
admin.site.register(StorageServer, StorageServerAdmin)