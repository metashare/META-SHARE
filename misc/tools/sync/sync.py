#!/usr/bin/env python
'''
A command-line enabled tool implementing the client end of the META-SHARE 
client-server protocol for synchronizing metadata.  
'''

import sys
import urllib
import urllib2
import contextlib
import json
from zipfile import ZipFile
from StringIO import StringIO

# Taken from 
# http://stackoverflow.com/questions/5082128/how-do-i-authenticate-a-urllib2-script-in-order-to-access-https-web-services-fro
def login(login_url, username, password):
    """
    Login to django site.
    Returns an opener with which logged-in requests can be sent.
    Raises URLError if HTTP response status is in the 400-599 range.
    """
    cookies = urllib2.HTTPCookieProcessor()
    opener = urllib2.build_opener(cookies)
    urllib2.install_opener(opener)

    opener.open(login_url)

    try:
        token = [x.value for x in cookies.cookiejar if x.name == 'csrftoken'][0]
    except IndexError:
        raise Exception("no csrftoken")

    params = dict(username=username, password=password,
        this_is_the_login_form=True,
        csrfmiddlewaretoken=token,
    )
    encoded_params = urllib.urlencode(params)

    with contextlib.closing(opener.open(login_url, encoded_params)) as response:
        html = response.read()
        if not 'Logout' in html:
            raise Exception("Expected html page with a Logout button but got:\n{0}".format(html))

    return opener


def get_inventory(opener, inventory_url):
    '''
    Obtain the inventory from a logged-in opener and fill it into a JSON structure.
    Returns the JSON structure.
    '''
    with contextlib.closing(opener.open(inventory_url)) as response:
        data = response.read()
        with ZipFile(StringIO(data), 'r') as inzip:
            json_inventory = json.load(inzip.open('inventory.json'))
            # TODO: add error handling and verification of json structure
            return json_inventory

def get_full_metadata(opener, full_metadata_url):
    '''
    Obtain the full metadata record for one resource.
    Returns a pair of storage_json, resource_xml_string.
    '''
    with contextlib.closing(opener.open(full_metadata_url)) as response:
        data = response.read()
        with ZipFile(StringIO(data), 'r') as inzip:
            with inzip.open('storage-global.json') as storage_file:
                storage_json = storage_file.read()
            with inzip.open('metadata.xml') as resource_xml:
                resource_xml_string = resource_xml.read()
            return storage_json, resource_xml_string

if __name__ == "__main__":
    base_url = "http://localhost:8000/metashare"
    user = "marc"
    password = "blabla7"
    opener = login("{0}/login/".format(base_url), user, password)
    
    if len(sys.argv) < 2:
        print "Usage: sync.py (inventory | metadata <uuid>)"
        sys.exit(1)
        
    if sys.argv[1] == 'inventory':
        inventory = get_inventory(opener, "{0}/sync/".format(base_url))
        print inventory
    elif sys.argv[1] == 'metadata':
        uuid = sys.argv[2]
        storage_json, resource_xml_string = get_full_metadata(opener, "{0}/sync/{1}/metadata/".format(base_url, uuid))
        print storage_json
        print resource_xml_string
