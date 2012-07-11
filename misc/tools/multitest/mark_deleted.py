
try:
	import sys
	import os
	from metashare.storage.models import StorageObject
	f = os.fdopen(5, 'w')
	stos = StorageObject.objects.all()
	sto1 = stos[0]
	sto1.deleted = True
	sto1.save()
	sto1.update_storage()
	f.write(sto1.identifier)
except:
	sys.exit(1)

sys.exit(0)

