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
    readonly_fields = ('identifier', 'created', 'modified', 'checksum')
    search_fields = ('metadata',)
    
    fieldsets = (
      ('Read-only Fields', {
        'fields': ('identifier', 'created', 'modified', 'checksum'),
      }),
      ('Status Fields', {
        'fields': ('revision', 'publication_status', 'deleted'),
      }),
      ('Metadata Fields', {
        'fields': ('metadata',),
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