"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import re
from datetime import datetime
from xml.etree import ElementTree as etree
from django.http import HttpResponse, HttpResponseServerError, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from metashare.storage.models import StorageObject

def get_latest_revision(request, identifier):
    """
    Returns the revision number for the instance with the given identifier.
    
    Returns 0 if the master copy attribute is not set.
    Returns -1 if there is no instance for this identifier.
    """
    storage_object = StorageObject.objects.filter(identifier=identifier)
    revision = -1
    
    if storage_object:
        storage_object = storage_object[0]
        
        if storage_object.master_copy:
            revision = storage_object.revision
        
        else:
            revision = 0
    
    return HttpResponse(str(revision), mimetype="text/plain")

def get_export_for_single_object(request, identifier):
    """
    Renders the XML representation for the instance with the given identifier.
    """
    storage_object = get_object_or_404(StorageObject, identifier=identifier)
    
    # Only export storage object instances that are local master copies and
    # have been published; otherwise raise a HTTP 404 Not Found error.
    if not storage_object.master_copy or not storage_object.published:
        raise Http404
    
    # Remove XML declaration from metadata, if present, to produce legal XML.
    _xml_declaration = re.compile(r'<\?xml.+\?>')
    metadata = _xml_declaration.sub('', storage_object.metadata).strip()
    
    dictionary = {'storage_object': storage_object, 'metadata': metadata}
    _result_xml = render_to_string('storage/single_object.xml', dictionary)
    
    # Pretty-print _result_xml :)
    _result_tree = etree.fromstring(_result_xml.encode('utf-8'))
    _result_pretty = etree.tostring(_result_tree, encoding="UTF-8") #,
      #pretty_print=True, xml_declaration=True)
    
    return HttpResponse(_result_pretty, mimetype="text/xml")

def get_export_for_all_objects(request, from_date=None):
    """
    Renders the XML representation for all storage object instances.
    
    If given, only instances created or modified after from_date are given.
    """
    storage_objects = StorageObject.objects.filter(master_copy=True)
    
    if from_date:
        try:
            year = from_date[:4]
            month = from_date[5:7]
            day = from_date[8:10]
            from_date = datetime(year=int(year), month=int(month), day=int(day))

        except ValueError:
            return HttpResponseServerError()
        
        _created_objects = storage_objects.filter(created__gt=from_date)
        _modified_objects = storage_objects.filter(modified__gt=from_date)
    
        storage_objects = list(_created_objects)
        storage_objects.extend(list(_modified_objects))
    
    # Ensure published/deleted status here!
    storage_objects = [x for x in storage_objects if x.published or x.deleted]
    storage_objects = set(storage_objects)
    
    _storage_xml = []
    for storage_object in storage_objects:
        # Remove XML declaration, if present, to produce legal embedded XML.
        _xml_declaration = re.compile(r'<\?xml.+\?>')
        metadata = _xml_declaration.sub('', storage_object.metadata).strip()

        dictionary = {'storage_object': storage_object, 'metadata': metadata}
        _result_xml = render_to_string('storage/single_object.xml', dictionary)
        _storage_xml.append(_result_xml)
    
    dictionary = {'storage_objects': _storage_xml}
    _result_xml = render_to_string('storage/all_objects.xml', dictionary)

    # Pretty-print _result_xml :)
    _result_tree = etree.fromstring(_result_xml.encode('utf-8'))
    _result_pretty = etree.tostring(_result_tree, encoding="UTF-8") #,
      #pretty_print=True, xml_declaration=True)

    return HttpResponse(_result_pretty, mimetype="text/xml")