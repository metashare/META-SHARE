#!/usr/bin/env python
'''
A command-line enabled tool implementing the client end of the META-SHARE 
client-server protocol for synchronizing metadata.  
'''

import urllib
import urllib2
import contextlib
import json
from zipfile import ZipFile
from StringIO import StringIO
from metashare.storage.models import compute_checksum
from traceback import format_exc

# Idea taken from 
# http://stackoverflow.com/questions/5082128/how-do-i-authenticate-a-urllib2-script-in-order-to-access-https-web-services-fro
def login(login_url, username, password):
    """
    Login to django site.
    Returns an opener with which logged-in requests can be sent.
    Raises URLError if HTTP response status is in the 400-599 range.
    """
    cookie_proc = urllib2.HTTPCookieProcessor()
    opener = urllib2.build_opener(cookie_proc)
    urllib2.install_opener(opener)
    opener.open(login_url)

    csrftoken = None
    for cookie in cookie_proc.cookiejar:
        if cookie.name == 'csrftoken':
            csrftoken = cookie.value
            break
    if csrftoken is None:
        raise Exception("Response does not contain a csrftoken, cannot continue")
    
    post_data = urllib.urlencode({
        'username':username,
        'password':password,
        'this_is_the_login_form':1,
        'csrfmiddlewaretoken':csrftoken,
    })

    try:
        response = opener.open(login_url, post_data)
        html = response.read()
        if not 'Logout' in html:
            raise Exception("Expected html page with a Logout button but got:\n{0}".format(html))
    finally:
        response.close()
    return opener


def get_inventory(opener, inventory_url):
    '''
    Obtain the inventory from a logged-in opener and fill it into a JSON structure.
    Returns the JSON structure.
    '''
    try:
        with contextlib.closing(opener.open(inventory_url)) as response:
            data = response.read()
            with ZipFile(StringIO(data), 'r') as inzip:
                json_inventory = json.load(inzip.open('inventory.json'))
                # TODO: add error handling and verification of json structure
                return json_inventory
    except:
        raise ConnectionException("Problem getting inventory from {0}: {1}".format(inventory_url, format_exc()))


def get_full_metadata(opener, full_metadata_url, expected_digest):
    '''
    Obtain the full metadata record for one resource.
    Returns a pair of storage_json_string, resource_xml_string.
    
    Raises CorruptDataException if the zip data received from full_metadata_url
    does not have an md5 digest identical to expected_digest.
    '''
    with contextlib.closing(opener.open(full_metadata_url)) as response:
        data = response.read()
        if not expected_digest == compute_checksum(StringIO(data)):
            raise CorruptDataException("Checksum error for resource '{0}'.".format(full_metadata_url))
        with ZipFile(StringIO(data), 'r') as inzip:
            with inzip.open('storage-global.json') as storage_file:
                # should be a json object, not string
                storage_json = json.loads(storage_file.read())
            with inzip.open('metadata.xml') as resource_xml:
                resource_xml_string = resource_xml.read()
            return storage_json, resource_xml_string


class ConnectionException(Exception):
    pass

class CorruptDataException(Exception):
    pass
