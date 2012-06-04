from django.http import HttpResponse
import json
from zipfile import ZipFile
from metashare import settings
from django.shortcuts import get_object_or_404
from metashare.storage.models import StorageObject, MASTER

def inventory(request):
    if settings.SYNC_NEEDS_AUTHENTICATION and not request.user.has_perm('storage.can_sync'):
        return HttpResponse("Forbidden: only synchronization users can access this page.", status=403)
    response = HttpResponse(status=200, content_type='application/zip')
    response['Metashare-Version'] = '2.2-SNAPSHOT'
    response['Content-Disposition'] = 'attachment; filename="inventory.zip"'
    json_inventory = [
        {'id':'dummy_id', 'digest':'dummy_digest'},
        {'id':'dummy_id2', 'digest':'dummy_digest2'},
    ]
    qs = StorageObject.objects.filter(copy_status=MASTER)
    for obj in qs:
        json_inventory.append({'id':str(obj.identifier), 'digest':str(obj.digest_checksum)})
    with ZipFile(response, 'w') as outzip:
        outzip.writestr('inventory.json', json.dumps(json_inventory))
    return response

def full_metadata(request, resource_uuid):
    if settings.SYNC_NEEDS_AUTHENTICATION and not request.user.has_perm('storage.can_sync'):
        return HttpResponse("Forbidden: only synchronization users can access this page.", status=403)
    storage_object = get_object_or_404(StorageObject, identifier=resource_uuid)
    response = HttpResponse(status=200, content_type='application/zip')
    response['Metashare-Version'] = '2.2-SNAPSHOT'
    response['Content-Disposition'] = 'attachment; filename="full-metadata.zip"'
    with ZipFile(response, 'w') as outzip:
        outzip.writestr('storage.txt', str(storage_object.identifier))
        outzip.writestr('resource.xml', storage_object.metadata.encode('utf-8'))
    return response
    