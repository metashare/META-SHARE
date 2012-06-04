from django.http import HttpResponse
from django.contrib.auth.decorators import permission_required
import json
from zipfile import ZipFile

def inventory(request):
    if not request.user.has_perm('storage.can_sync'):
        return HttpResponse("Forbidden: only synchronization users can access this page.", status=403)
    response = HttpResponse(status=200, content_type='application/zip')
    response['Metashare-Version'] = '2.2-SNAPSHOT'
    dummy_json_structure = [
        {'id':'dummy_id', 'digest':'dummy_digest'},
        {'id':'dummy_id2', 'digest':'dummy_digest2'},
    ]
    with ZipFile(response, 'w') as outzip:
        outzip.writestr('inventory.json', json.dumps(dummy_json_structure))
    return response