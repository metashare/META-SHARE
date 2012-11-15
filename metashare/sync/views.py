from django.http import HttpResponse
import json
from zipfile import ZipFile
from metashare import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from metashare.storage.models import StorageObject, MASTER, PROXY, INTERNAL, \
    REMOTE


def inventory(request):
    if settings.SYNC_NEEDS_AUTHENTICATION and not request.user.has_perm('storage.can_sync'):
        return HttpResponse("Forbidden: only synchronization users can access this page.", status=403)
    
    # check for compatible sync protocol version
    sync_protocol = None
    if 'sync_protocol' in request.GET:
        for _prot in request.GET.getlist('sync_protocol'):
            if _prot in  settings.SYNC_PROTOCOLS:
                sync_protocol = _prot
                break
    
    if not sync_protocol:
        # either no sync protocol parameter was send (which means the client is 
        # pre 3.0 and that synchronization protocol is no longer supported) or
        # no match was found between the client and server supported sync 
        # protocols
        return HttpResponse(status=501)
    
    response = HttpResponse(status=200, content_type='application/zip')
    response['Metashare-Version'] = settings.METASHARE_VERSION
    response['Content-Disposition'] = 'attachment; filename="inventory.zip"'
    response['Sync-Protocol'] = sync_protocol

    # collect inventory for existing resources;
    # consists of key - value pairs of resource identifiers and digest checksums
    json_response = {}
    objects_to_sync = StorageObject.objects \
        .filter(Q(copy_status=MASTER) | Q(copy_status=PROXY)) \
        .exclude(publication_status=INTERNAL)
    # 'from' parameter for restricting the inventory CAN NOT be used anymore
    # since it would break to automatic detection of deleted resources
#    if 'from' in request.GET:
#        try:
#            fromdate = dateutil.parser.parse(request.GET['from'])
#            objects_to_sync = objects_to_sync.filter(digest_modified__gte=fromdate)
#        except ValueError:
#            # If we cannot parse the date string, act as if none was provided
#            pass
    for obj in objects_to_sync:
        json_response[obj.identifier] = obj.get_digest_checksum()
    
    with ZipFile(response, 'w') as outzip:
        outzip.writestr('inventory.json', json.dumps(json_response))
    return response

def full_metadata(request, resource_uuid):
    if settings.SYNC_NEEDS_AUTHENTICATION and not request.user.has_perm('storage.can_sync'):
        return HttpResponse("Forbidden: only synchronization users can access this page.", status=403)
    storage_object = get_object_or_404(StorageObject, identifier=resource_uuid)
    if storage_object.publication_status == INTERNAL:
        return HttpResponse("Forbidden: the given resource is internal at this time.", status=403)
    if storage_object.copy_status == REMOTE:
        return HttpResponse("Forbidden: the specified resource is a `REMOTE` " \
            "resource and cannot be distributed by this node.", status=403)
    response = HttpResponse(status=200, content_type='application/zip')
    response['Metashare-Version'] = settings.METASHARE_VERSION
    response['Content-Disposition'] = 'attachment; filename="full-metadata.zip"'
    if storage_object.digest_checksum is None:
        storage_object.update_storage()
    #if storage_object.digest_checksum is None: # still no digest? something is very wrong here:
    #    raise Exception("Object {0} has no digest".format(resource_uuid))
    zipfilename = "{0}/resource.zip".format(storage_object._storage_folder())
    with open(zipfilename, 'rb') as inzip:
        zipfiledata = inzip.read()
        response.write(zipfiledata)
#    with ZipFile(response, 'w') as outzip:
#        outzip.writestr('storage-global.json', str(storage_object.identifier))
#        outzip.writestr('metadata.xml', storage_object.metadata.encode('utf-8'))
    return response
    