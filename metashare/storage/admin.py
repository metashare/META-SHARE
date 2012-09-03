from django.contrib import admin
from metashare.storage.models import StorageObject, RemovedObject

class StorageObjectAdmin(admin.ModelAdmin):
    """
    Model admin class for stored object instances.
    """
    list_filter = ('copy_status', 'publication_status', 'deleted')
    readonly_fields = ('source_url', 'identifier', 'created', 'modified', 
      'checksum', 'digest_checksum', 'digest_modified', 'digest_last_checked', 
      'metashare_version', 'copy_status')
    search_fields = ('metadata', 'global_storage', 'local_storage')
    
    fieldsets = (
      ('Read-only Fields', {
        'fields': ('source_url', 'identifier', 'created', 'modified', 
          'checksum', 'digest_checksum', 'digest_modified', 'digest_last_checked',
          'metashare_version', 'copy_status'),
      }),
      ('Status Fields', {
        'fields': ('revision', 'publication_status', 'deleted'),
      }),
      ('Metadata Fields', {
        'fields': ('metadata', 'global_storage', 'local_storage'),
      }),
    )


class RemovedObjectAdmin(admin.ModelAdmin):
    """
    Model admin class for removed object instances.
    """
    readonly_fields = ('identifier', 'removed')
    
    fieldsets = (
      ('Read-only Fields', {
        'fields': ('identifier', 'removed'),
      }),
    )

admin.site.register(StorageObject, StorageObjectAdmin)
admin.site.register(RemovedObject, RemovedObjectAdmin)
