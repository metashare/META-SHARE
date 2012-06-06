from django.http import HttpResponse
import json
from zipfile import ZipFile
from metashare import settings
from django.shortcuts import get_object_or_404
from metashare.storage.models import StorageObject, MASTER, INTERNAL

def inventory(request):
    if settings.SYNC_NEEDS_AUTHENTICATION and not request.user.has_perm('storage.can_sync'):
        return HttpResponse("Forbidden: only synchronization users can access this page.", status=403)
    response = HttpResponse(status=200, content_type='application/zip')
    response['Metashare-Version'] = settings.METASHARE_VERSION
    response['Content-Disposition'] = 'attachment; filename="inventory.zip"'
    json_inventory = []
    objects_to_sync = StorageObject.objects.filter(copy_status=MASTER).exclude(publication_status=INTERNAL)
    for obj in objects_to_sync:
        json_inventory.append({'id':str(obj.identifier), 'digest':str(obj.digest_checksum)})
    with ZipFile(response, 'w') as outzip:
        outzip.writestr('inventory.json', json.dumps(json_inventory))
    return response

def full_metadata(request, resource_uuid):
    if settings.SYNC_NEEDS_AUTHENTICATION and not request.user.has_perm('storage.can_sync'):
        return HttpResponse("Forbidden: only synchronization users can access this page.", status=403)
    storage_object = get_object_or_404(StorageObject, identifier=resource_uuid)
    if storage_object.publication_status == INTERNAL:
        return HttpResponse("Forbidden: the given resource is internal at this time.", status=403)
    response = HttpResponse(status=200, content_type='application/zip')
    response['Metashare-Version'] = settings.METASHARE_VERSION
    response['Content-Disposition'] = 'attachment; filename="full-metadata.zip"'
    if storage_object.digest_checksum is None:
        storage_object.update_storage()
    #if storage_object.digest_checksum is None: # still no digest? something is very wrong here:
    #    raise Exception("Object {0} has no digest".format(resource_uuid))
    zipfilename = "{0}/resource.zip".format(storage_object._storage_folder())
    with open(zipfilename, 'r') as inzip:
        zipfiledata = inzip.read()
        response.write(zipfiledata)
#    with ZipFile(response, 'w') as outzip:
#        outzip.writestr('storage-global.json', str(storage_object.identifier))
#        outzip.writestr('metadata.xml', storage_object.metadata.encode('utf-8'))
    return response
    