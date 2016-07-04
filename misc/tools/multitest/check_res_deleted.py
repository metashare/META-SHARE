
try:
	import sys
	import os
	from metashare.storage.models import StorageObject
	# res_id must be set in python before calling this script
	sto = StorageObject.objects.get(identifier=res_id)
	deleted = sto.deleted
	if not deleted:
		sys.exit(2)
except:
	sys.exit(1)

sys.exit(0)
