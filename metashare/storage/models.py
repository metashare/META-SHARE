"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from Crypto import Random
from Crypto.PublicKey import RSA
from base64 import b64encode
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
# pylint: disable-msg=E0611
from hashlib import md5
from httplib import HTTPConnection
from metashare.settings import LOG_LEVEL, LOG_HANDLER
from metashare import settings
from os import mkdir
from os.path import exists
import os.path
from urllib import urlencode
from uuid import uuid1, uuid4
from xml.etree import ElementTree as etree
from datetime import datetime
from time import mktime
import logging
import re
from metashare.xml_utils import pretty_xml
from xml.etree.ElementTree import tostring
from json import dumps, loads
from django.core.serializers.json import DjangoJSONEncoder
import zipfile
from zipfile import ZIP_DEFLATED
import json

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.storage.models')
LOGGER.addHandler(LOG_HANDLER)

ALLOWED_ARCHIVE_EXTENSIONS = ('zip', 'tar.gz', 'gz', 'tgz', 'tar', 'bzip2')
MAXIMUM_MD5_BLOCK_SIZE = 1024
XML_DECL = re.compile(r'\s*<\?xml version=".+" encoding=".+"\?>\s*\n?',
  re.I|re.S|re.U)

# Publication status constants and choice:
INTERNAL = 'i'
INGESTED = 'g'
PUBLISHED = 'p'
STATUS_CHOICES = (
    (INTERNAL, 'internal'),
    (INGESTED, 'ingested'),
    (PUBLISHED, 'published'),
)

# Copy status constants and choice:
MASTER = 'm'
REMOTE = 'r'
PROXY = 'p'
COPY_CHOICES = (
    (MASTER, 'master copy'),
    (REMOTE, 'remote copy'),
    (PROXY, 'proxy copy'))

# attributes to by serialized in the global JSON of the storage object
GLOBAL_STORAGE_ATTS = ['source_url', 'identifier', 'created', 'modified', 
  'revision', 'publication_status', 'metashare_version']

# attributes to be serialized in the local JSON of the storage object
LOCAL_STORAGE_ATTS = ['digest_checksum', 'digest_modified', 'copy_status']


def _validate_valid_xml(value):
    """
    Checks whether the given value is well-formed and valid XML.
    """
    try:
        # Try to create an XML tree from the given String value.
        _value = XML_DECL.sub(u'', value)
        _ = etree.fromstring(_value.encode('utf-8'))
        return True
    
    except etree.ParseError, parse_error:
        # In case of an exception, we raise a ValidationError.
        raise ValidationError(parse_error)
    
    # cfedermann: in case of other exceptions, raise a ValidationError with
    #   the corresponding error message.  This will prevent the exception
    #   page handler to be shown and is hence more acceptable for end users.
    except Exception, error:
        raise ValidationError(error)

def _create_uuid():
    """
    Creates a unique id from a UUID-1 and a UUID-4, checks for collisions.
    """
    # Create new identifier based on a UUID-1 and a UUID-4.
    new_id = '{0}{1}'.format(uuid1().hex, uuid4().hex)
    
    # Check for collisions; in case of a collision, create new identifier.
    while StorageObject.objects.filter(identifier=new_id):
        new_id = '{0}{1}'.format(uuid1().hex, uuid4().hex)
    
    return new_id

class StorageServer(models.Model):
    """
    Models a remote storage server hosting storage objects.
    """
    shortname = models.CharField(max_length=50, unique=True,
      help_text="Human-readable name for this storage server instance.")
    
    hostname = models.URLField(verify_exists=False, help_text="The URL " \
      "for this storage server instance. Use http://localhost/ for your " \
      "local node.")
    
    updated = models.DateTimeField(null=True, editable=False,
      help_text="(Read-only) last update date for this storage server " \
      "instance.")
    
    public_key = models.TextField(help_text="Base64 Format. Used to " \
      "encrypt data sent to this metadata server." )
    
    def __unicode__(self):
        """
        Returns the Unicode representation for this storage server instance.
        """
        return u'<StorageServer id="{0}">'.format(self.id)
    
    def synchronise(self):
        """
        Syncs local django with this storage server instance.
        """
        # Compose export URL for this storage server.
        _sync_url = "{0}storage/export/".format(self.hostname)
        if self.updated:
            # Add from_date if appropriate.
            _sync_url += "{0}/".format(self.updated.strftime('%Y-%m-%d'))
        
        return _sync_url
    
    def is_local_server(self):
        """Checks if this StorageServer instance is the local server."""
        return str(self.hostname).strip() == 'http://localhost/'
    
    def create_sso_token(self, uuid, timestamp=None):
        """Creates new SSO token for non-managing nodes."""
        if self.is_local_server():
            LOGGER.info('Cannot send message to local server.')
            return None
        
        # If no timestamp is given, we use the current time.
        if not timestamp:
            # Convert time tuple to timestamp String.
            timestamp = str(int(mktime(datetime.now().timetuple())))
        
        _public_key = RSA.importKey(self.public_key)
        _random_bytes = Random.get_random_bytes(16)
        _message = '{0}{1}'.format(uuid, timestamp)
        token = b64encode(_public_key.encrypt(_message, _random_bytes)[0])
        return (uuid, timestamp, token)
    
    def send_message(self, msg, action):
        """Send an encrypted message to this StorageServer."""
        if self.is_local_server():
            LOGGER.info('Cannot send message to local server.')
            return False
        
        _public_key = RSA.importKey(self.public_key)
        _random_bytes = Random.get_random_bytes(16)
        _chunk_size = _public_key.size() / 8
        _chunks = len(msg) / _chunk_size
        
        _encrypted = []
        for offset in range(_chunks):
            _offset = offset * _chunk_size
            _chunk = msg[_offset:_offset+_chunk_size]
            _encrypted.append(_public_key.encrypt(_chunk, _random_bytes))
        
        if len(msg) % _chunk_size:
            _chunk = msg[_chunks * _chunk_size:]
            _encrypted.append(_public_key.encrypt(_chunk, _random_bytes))
        
        params = urlencode({'message': _encrypted})
        headers = {"Content-type": "application/x-www-form-urlencoded",
          "Accept": "text/plain"}
        _urls = str(self.hostname).strip('http://').strip('/').split('/')
        if len(_urls) > 1:
            _url = _urls[0]
            _prefix = '/'.join(_urls[1:])
            action = '/{0}{1}'.format(_prefix, action)
        
        else:
            _url = _urls[0]

        _conn = HTTPConnection(_url)
        _conn.request("POST", action, params, headers)
        response = _conn.getresponse()
        
        # cfedermann: for the moment, we are ignoring the HTTP response text.
        #             It could be accessed using: data = response.read()
        _conn.close()
        
        return response.status == 200

# pylint: disable-msg=R0902
class StorageObject(models.Model):
    """
    Models an object inside the persistent storage layer.
    """
    __schema_name__ = "STORAGEOJBECT"
    
    class Meta:
        permissions = (
            ('can_sync', 'Can synchronize'),
        )
    
    #jsteffen: to be removed in later versions, replaced by source_url
    source = models.ForeignKey(StorageServer, blank=True, null=True,
      editable=False, help_text="(Read-only) source for this storage " \
      "object instance.")
      
    source_url = models.URLField(verify_exists=False, editable=False,
      default=settings.DJANGO_URL,
      help_text="(Read-only) base URL for the server where the master copy of " \
      "the associated language resource is located.")
    
    identifier = models.CharField(max_length=64, default=_create_uuid,
      editable=False, unique=True, help_text="(Read-only) unique " \
      "identifier for this storage object instance.")
    
    created = models.DateTimeField(auto_now_add=True, editable=False,
      help_text="(Read-only) creation date for this storage object instance.")
    
    modified = models.DateTimeField(editable=False, default=datetime.now(),
      help_text="(Read-only) last modification date of the metadata XML " \
      "for this storage object instance.")
    
    checksum = models.CharField(blank=True, null=True, max_length=32,
      help_text="(Read-only) MD5 checksum of the binary data for this " \
      "storage object instance.")
    
    digest_checksum = models.CharField(blank=True, null=True, max_length=32,
      help_text="(Read-only) MD5 checksum of the digest zip file containing the" \
      "global serialized storage object and the metadata XML for this " \
      "storage object instance.")
      
    digest_modified = models.DateTimeField(editable=False, null=True, blank=True,
      help_text="(Read-only) last modification date of digest zip " \
      "for this storage object instance.")
      
    revision = models.PositiveIntegerField(default=0, help_text="Revision " \
      "or version information for this storage object instance.")
      
    metashare_version = models.CharField(max_length=32, editable=False, 
      default=settings.METASHARE_VERSION,
      help_text="(Read-only) META-SHARE version used with the storage object instance.")
    
    def _get_master_copy(self):
        return self.copy_status == MASTER
    
    def _set_master_copy(self, value):
        if value == True:
            self.copy_status = MASTER
        else:
            self.copy_status = REMOTE
    
    master_copy = property(_get_master_copy, _set_master_copy)
    
    copy_status = models.CharField(default=MASTER, max_length=1, editable=False, choices=COPY_CHOICES,
        help_text="Generalized copy status flag for this storage object instance.")
    
    def _get_published(self):
        return self.publication_status == PUBLISHED
    
    def _set_published(self, value):
        if value == True:
            self.publication_status = PUBLISHED
        else:
            # request to unpublish depends on current state:
            # if we are currently published, set to ingested;
            # else don't change
            if self.publication_status == PUBLISHED:
                self.publication_status = INGESTED
    
    published = property(_get_published, _set_published)
    
    publication_status = models.CharField(default=INTERNAL, max_length=1, choices=STATUS_CHOICES,
        help_text="Generalized publication status flag for this " \
        "storage object instance.")
    
    deleted = models.BooleanField(default=False, help_text="Deletion " \
      "status flag for this storage object instance.")
    
    metadata = models.TextField(validators=[_validate_valid_xml],
      help_text="XML containing the metadata description for this storage " \
      "object instance.")
      
    global_storage = models.TextField(default='not set yet',
      help_text="text containing the JSON serialization of global attributes " \
      "for this storage object instance.")
    
    local_storage = models.TextField(default='not set yet',
      help_text="text containing the JSON serialization of local attributes " \
      "for this storage object instance.")
    
    
    def __unicode__(self):
        """
        Returns the Unicode representation for this storage object instance.
        """
        return u'<StorageObject id="{0}">'.format(self.id)
    
    def _storage_folder(self):
        """
        Returns the path to the local folder for this storage object instance.
        """
        return '{0}/{1}'.format(settings.STORAGE_PATH, self.identifier)
    
    def _compute_checksum(self):
        """
        Computes the MD5 hash checksum for this storage object instance.
        
        Reads in the downloadable data in blocks of MAXIMUM_MD5_BLOCK_SIZE
        bytes which is possible as MD5 allows incremental hash computation.
        """
        if not self.master_copy or not self.get_download():
            return
        
        _checksum = md5()
        
        # Compute the MD5 hash from chunks of the downloadable data.
        with open(self.get_download(), 'rb') as _downloadable_data:
            _chunk = _downloadable_data.read(MAXIMUM_MD5_BLOCK_SIZE)
            while _chunk:
                _checksum.update(_chunk)
                _chunk = _downloadable_data.read(MAXIMUM_MD5_BLOCK_SIZE)
        
        self.checksum = _checksum.hexdigest()
    
    def has_local_download_copy(self):
        """
        Checks if this instance has a local copy of the downloadable data.
        """
        if not self.has_download():
            return False
        
        # Check if there is a local file inside the storage folder.
        _binary_data = self.get_download()        
        if not _binary_data:
            return False
        
        # If this is the master copy, we don't know that the checksum is OK.
        if self.master_copy:
            return True
        
        # Otherwise, we compute the MD5 hash from chunks of the local data.
        _checksum = md5()
        with open(_binary_data, 'rb') as _downloadable_data:
            _chunk = _downloadable_data.read(MAXIMUM_MD5_BLOCK_SIZE)
            while _chunk:
                _checksum.update(_chunk)
                _chunk = _downloadable_data.read(MAXIMUM_MD5_BLOCK_SIZE)
        
        # And check if the local checksum matches the master copy's checksum.
        return self.checksum == _checksum.hexdigest()
    
    def has_download(self):
        """
        Checks if this storage object instance contains downloadable data.
        """
        return self.checksum != None
    
    def get_download(self):
        """
        Returns the local path to the downloadable data.
        """
        _path = '{0}/archive'.format(self._storage_folder())
        for _ext in ALLOWED_ARCHIVE_EXTENSIONS:
            _binary_data = '{0}.{1}'.format(_path, _ext)
            if exists(_binary_data):
                return _binary_data

        return None
    
    def save(self, *args, **kwargs):
        """
        Overwrites the predefined save() method to ensure that STORAGE_PATH
        contains a folder for this storage object instance.  We also check
        that the object validates.
        """
        # Perform a full validation for this storage object instance.
        self.full_clean()
        
        # Call save() method from super class with all arguments.
        super(StorageObject, self).save(*args, **kwargs)
    
    def update_storage(self):
        """
        Updates the metadata XML if required and serializes it and this storage
        object to the storage folder.
        """
        # for internal resources, no serialization is done
        if self.publication_status is INTERNAL:
            return
        
        # check if the storage folder for this storage object instance exists
        if self._storage_folder() and not exists(self._storage_folder()):
            # If not, create the storage folder.
            mkdir(self._storage_folder())
        
        # update the checksum, if a downloadable file exists
        if self.master_copy:
            self._compute_checksum()
        
        # flag to indicate if rebuilding of resource.zip is required
        update_zip = False
        
        # flag to indicate if saving is required
        update_obj = False
        
        # create current version of metadata XML
        _metadata = pretty_xml(tostring(
          # pylint: disable-msg=E1101
          self.resourceinfotype_model_set.all()[0].export_to_elementtree()))
        
        # check if there exists a metadata XML file; this is not the case if
        # the publication status just changed from internal to ingested
        _xml_exists = os.path.isfile(
          '{0}/metadata-{1:04d}.xml'.format(self._storage_folder(), self.revision))
          
        # check if metadata has changed; if yes, increase revision for ingested
        # and published resources and save metadata to storage folder
        if self.metadata != _metadata or not _xml_exists:
            if self.metadata != _metadata:
                self.metadata = _metadata
                self.modified = datetime.now()
                update_obj = True
            if self.publication_status in (INGESTED, PUBLISHED):
                self.revision += 1
                update_obj = True
                # serialize metadata
                with open('{0}/metadata-{1:04d}.xml'.format(
                  self._storage_folder(), self.revision), 'wb') as _out:
                    _out.write(unicode(self.metadata).encode('utf-8'))
                update_zip = True
            LOGGER.debug(u"\nMETADATA: {0}\n".format(self.metadata))
        
        # check if global storage object serialization has changed; if yes,
        # save it to storage folder
        _dict_global = { }
        for item in GLOBAL_STORAGE_ATTS:
            _dict_global[item] = getattr(self, item)
        _global_storage = \
          dumps(_dict_global, cls=DjangoJSONEncoder, sort_keys=True, separators=(',',':'))
        if self.global_storage != _global_storage:
            self.global_storage = _global_storage
            update_obj = True
            if self.publication_status in (INGESTED, PUBLISHED):
                with open('{0}/storage-global.json'.format(
                  self._storage_folder()), 'wb') as _out:
                    _out.write(unicode(self.global_storage).encode('utf-8'))
                update_zip = True
        
        # create new digest zip if required, but only for master copies
        if update_zip and self.copy_status == MASTER:
            _zf_name = '{0}/resource.zip'.format(self._storage_folder())
            _zf = zipfile.ZipFile(_zf_name, mode='w', compression=ZIP_DEFLATED)
            try:
                _zf.write(
                  '{0}/metadata-{1:04d}.xml'.format(self._storage_folder(), self.revision),
                  arcname='metadata.xml')
                _zf.write(
                  '{0}/storage-global.json'.format(self._storage_folder()),
                  arcname='storage-global.json')
            finally:
                _zf.close()
            # update zip digest checksum
            _checksum = md5()
            with open(_zf_name, 'rb') as _zf_reader:
                _chunk = _zf_reader.read(MAXIMUM_MD5_BLOCK_SIZE)
                while _chunk:
                    _checksum.update(_chunk)
                    _chunk = _zf_reader.read(MAXIMUM_MD5_BLOCK_SIZE)
            self.digest_checksum = _checksum.hexdigest()
            # update last modified timestamp
            self.digest_modified = datetime.now()
            update_obj = True
            
        # check if local storage object serialization has changed; if yes,
        # save it to storage folder
        _dict_local = { }
        for item in LOCAL_STORAGE_ATTS:
            _dict_local[item] = getattr(self, item)
        _local_storage = \
          dumps(_dict_local, cls=DjangoJSONEncoder, sort_keys=True, separators=(',',':'))
        if self.local_storage != _local_storage:
            self.local_storage = _local_storage
            update_obj = True
            if self.publication_status in (INGESTED, PUBLISHED):
                with open('{0}/storage-local.json'.format(
                  self._storage_folder()), 'wb') as _out:
                    _out.write(unicode(self.local_storage).encode('utf-8'))
        
        # save storage object if required
        if update_obj:
            self.save()

def restore_from_folder(storage_id, copy_status=None):
    """
    Restores the storage object and the associated resource for the given
    storage object identifier and makes it persistent in the database. 
    
    storage_id: the storage object identifier; it is assumed that this is the
    folder name in the storage folder folder where serialized storage object
    and metadata XML are located
    
    copy_status (optional): one of MASTER, REMOTE, PROXY; if present, used as
        copy status for the restored resource
        
    Returns the restored resource with its storage object set.
    """
    from metashare.repository.models import resourceInfoType_model
    
    # if a storage object with this id already exists, delete it
    try:
        _so = StorageObject.objects.get(identifier=storage_id)
        _so.delete()
    except ObjectDoesNotExist:
        _so = None
    
    storage_folder = os.path.join(settings.STORAGE_PATH, storage_id)

    # get most current metadata.xml
    _files = os.listdir(storage_folder)
    _metadata_files = \
      sorted(
        [f for f in _files if f.startswith('metadata')],
        reverse=True)
    if not _metadata_files:
        raise Exception('no metadata.xml found')
    # restore resource from metadata.xml
    _metadata_file = open('{0}/{1}'.format(storage_folder, _metadata_files[0]), 'rb')
    _xml_string = _metadata_file.read()
    _metadata_file.close()
    result = resourceInfoType_model.import_from_string(_xml_string)
    if not result[0]:
        msg = u''
        if len(result) > 2:
            msg = u'{}'.format(result[2])
        raise Exception(msg)
    resource = result[0]
    # at this point, a storage object is already created at the resource, so update it 
    _storage_object = resource.storage_object
    _storage_object.metadata = _xml_string
    
    # add global storage object attributes if available
    if os.path.isfile('{0}/storage-global.json'.format(storage_folder)):
        _global_json = \
          _fill_storage_object(_storage_object, '{0}/storage-global.json'.format(storage_folder))
        _storage_object.global_storage = _global_json
    else:
        LOGGER.warn('missing storage-global.json, importing resource as new')
        _storage_object.identifier = storage_id
    # add local storage object attributes if available 
    if os.path.isfile('{0}/storage-local.json'.format(storage_folder)):
        _local_json = \
          _fill_storage_object(_storage_object, '{0}/storage-local.json'.format(storage_folder))
        _storage_object.local_storage = _local_json
        # always use the provided copy status, even if its different from the
        # one in the local storage object
        if copy_status:
            if _storage_object.copy_status != copy_status:
                LOGGER.warn('overwriting copy status from storage-local.json with "{}"'.format(copy_status))
            _storage_object.copy_status = copy_status
    else:
        if copy_status:
            _storage_object.copy_status = copy_status
        else:
            # no copy status and no local storage object is provided, so use
            # a default
            LOGGER.warn('no copy status provided, using default copy status MASTER')
            _storage_object.copy_status = MASTER

    _storage_object.save()
    _storage_object.update_storage()
        
    return resource


def update_resource(storage_json, resource_xml_string, copy_status=REMOTE):
    '''
    For the resource described by storage_json and resource_xml_string,
    do the following:

    - if it does not exist, import it with the given copy status;
    - if it exists, delete it from the database, then import it with the given copy status.
    
    Raises 'IllegalAccessException' if an attempt is made to overwrite
    an existing master-copy resource with a non-master-copy one.
    '''
    # Local helper functions first:
    def write_to_disk(storage_id):
        folder = os.path.join(settings.STORAGE_PATH, storage_id)
        if not os.path.exists(folder):
            os.mkdir(folder)
        with open(os.path.join(folder, 'storage-global.json'), 'wb') as out:
            json.dump(storage_json, out)
        with open(os.path.join(folder, 'metadata.xml'), 'wb') as out:
            out.write(resource_xml_string)

    def storage_object_exists(storage_id):
        return bool(StorageObject.objects.filter(identifier=storage_id).count() > 0)

    def remove_files_from_disk(storage_id):
        folder = os.path.join(settings.STORAGE_PATH, storage_id)
        for _file in ('storage-local.json', 'storage-global.json', 'metadata.xml'):
            path = os.path.join(folder, _file)
            if os.path.exists(path):
                os.remove(path)

    def remove_database_entries(storage_id):
        storage_object = StorageObject.objects.get(identifier=storage_id)
        resource = storage_object.resourceinfotype_model_set.all()[0]
        resource.delete_deep()
        storage_object.delete()

    # Now the actual update_resource():
    storage_id = storage_json['identifier']
    if storage_object_exists(storage_id):
        if copy_status != MASTER and StorageObject.objects.get(identifier=storage_id).copy_status == MASTER:
            raise IllegalAccessException("Attempt to overwrite a master copy with a non-master-copy record; refusing")
        remove_files_from_disk(storage_id)
        remove_database_entries(storage_id)
    write_to_disk(storage_id)
    restore_from_folder(storage_id, copy_status=copy_status)




def _fill_storage_object(storage_obj, json_file_name):
    """
    Fills the given storage object with the entries of the given JSON file.
    The JSON file contains the serialization of dictionary where it is assumed 
    the dictionary keys are valid attributes of the storage object.
    Returns the content of the JSON file.
    """
    with open(json_file_name, 'rb') as _in:
        json_string = _in.read()
        _dict = loads(json_string)
        for _att in _dict.keys():
            setattr(storage_obj, _att, _dict[_att])
        return json_string

class IllegalAccessException(Exception):
    pass        
