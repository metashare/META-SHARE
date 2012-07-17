import os
import settings

fl = os.fdopen(5, 'w')
fl.write(settings.LOG_FILENAME)

