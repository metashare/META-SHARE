from django.http import HttpResponse
from django.contrib.auth.decorators import permission_required
import json
from zipfile import ZipFile

@permission_required('storage.can_sync')
def inventory(request):
    response = HttpResponse(status=200, content_type='application/zip')
    dummy_json_structure = [
        {'id':'dummy_id', 'digest':'dummy_digest'},
        {'id':'dummy_id2', 'digest':'dummy_digest2'},
    ]
    with ZipFile(response, 'w') as outzip:
        outzip.writestr('inventory.json', json.dumps(dummy_json_structure))
    return response