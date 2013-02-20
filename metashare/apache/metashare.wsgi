import os
import sys

path = '/opt/META-SHARE'
if path not in sys.path:
	sys.path.insert(0, '/opt/META-SHARE')

sys.path.append('/opt/META-SHARE/lib/python2.7/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = 'metashare.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

#def application(environ, start_response):
#    if environ['wsgi.url_scheme'] == 'https':
#        environ['HTTPS'] = 'on'
#    return _application(environ, start_response)
