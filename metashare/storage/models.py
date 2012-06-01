"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from Crypto import Random
from Crypto.PublicKey import RSA
from base64 import b64encode
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
# pylint: disable-msg=E0611
from hashlib import md5
from httplib import HTTPConnection
from metashare.settings import LOG_LEVEL, LOG_HANDLER
from metashare import settings
from os import mkdir, rename, rmdir
from os.path import exists
from urllib import urlencode
from uuid import uuid1, uuid4
from xml.etree import ElementTree as etree
from datetime import datetime
from time import mktime
import logging
import re
from metashare.xml_utils import pretty_xml
from xml.etree.ElementTree import tostring

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

class StorageObject(models.Model):
    """
    Models an object inside the persistent storage layer.
    """
    __schema_name__ = "STORAGEOJBECT"
    
    class Meta:
        permissions = (
            ('can_sync', 'Can synchronize'),
        )
    
    source = models.ForeignKey(StorageServer, blank=True, null=True,
      editable=False, help_text="(Read-only) source for this storage " \
      "object instance.")
    
    identifier = models.CharField(max_length=64, default=_create_uuid,
      editable=False, unique=True, help_text="(Read-only) unique " \
      "identifier for this storage object instance.")
    
    created = models.DateTimeField(auto_now_add=True, editable=False,
      help_text="(Read-only) creation date for this storage object instance.")
    
    modified = models.DateTimeField(auto_now=True, editable=False,
      help_text="(Read-only) last modification date for this storage " \
      "object instance.")
    
    checksum = models.CharField(blank=True, null=True, max_length=32,
      help_text="(Read-only) MD5 checksum of the binary data for this " \
      "storage object instance.")
    
    revision = models.PositiveIntegerField(default=1, help_text="Revision " \
      "or version information for this storage object instance.")
    
    master_copy = models.BooleanField(default=True, help_text="Master copy " \
      "status flag for this storage object instance.")
    
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
    
    def __unicode__(self):
        """
        Returns the Unicode representation for this storage object instance.
        """
        return u'<StorageObject id="{0}">'.format(self.id)
    
    def _storage_folder(self):
        """
        Returns the path to the local folder for this storage object instance.
        
        Returns None if the master copy attribute of the instance is not set.
        """
        if self.master_copy:
            return '{0}/{1}'.format(settings.STORAGE_PATH, self.identifier)
        
        return None
    
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
    
    def save(self, *args, **kwargs):
        """
        Overwrites the predefined save() method to ensure that STORAGE_PATH
        contains a folder for this storage object instance.  We also check
        that the object validates.
        """
        # Perform a full validation for this storage object instance.
        self.full_clean()
        
        # Check if the storage folder for this storage object instance exists.
        if self._storage_folder() and not exists(self._storage_folder()):
            # If not, create the storage folder.
            mkdir(self._storage_folder())
        
        # Update the checksum, if a downloadable file exists.
        if self.master_copy:
            self._compute_checksum()
        
        # Call save() method from super class with all arguments.
        super(StorageObject, self).save(*args, **kwargs)
        
        # save metadata XML to storage folder
        if self.publication_status in (INGESTED, PUBLISHED):
            with open('{0}/metadata.xml'.format(self._storage_folder()), 'w') as _out:
                _out.write(self.metadata.encode('utf-8'))
    
    def update_metadata(self):
        """
        Updates the metadata XML of this storage object. Use only after the initial
        language resource and storage object have been saved.
        """
        _metadata = pretty_xml(tostring(
          # pylint: disable-msg=E1101
          self.resourceinfotype_model_set.all()[0].export_to_elementtree()))
        self.metadata = _metadata
    
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

@receiver(pre_delete, sender=StorageObject)
def _delete_storage_folder(sender, instance, **kwargs):
    """Deletes to storage folder for the sender instance, if possible."""
    # We can safely remove the storage folder if no binary data is present.
    if not instance._storage_folder():
        return
    
    if not instance.has_download():
        if exists(instance._storage_folder()):
            rmdir(instance._storage_folder())
    
    # Otherwise, we can only rename the storage folder for later inspection.
    else:
        _old_name = instance._storage_folder()
        _new_name = '{0}/DELETED-{1}'.format(settings.STORAGE_PATH,
          instance.identifier)
        rename(_old_name, _new_name)
