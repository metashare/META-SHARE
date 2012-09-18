from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
# pylint: disable-msg=E0611
from hashlib import md5
from metashare.settings import LOG_HANDLER
from metashare import settings
from os import mkdir
from os.path import exists
import os.path
from uuid import uuid1, uuid4
from xml.etree import ElementTree as etree
from datetime import datetime, timedelta
import logging
import re
from json import dumps, loads
from django.core.serializers.json import DjangoJSONEncoder
import zipfile
from zipfile import ZIP_DEFLATED
from django.db.models.query_utils import Q
import glob

# Setup logging support.
LOGGER = logging.getLogger(__name__)
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
  'revision', 'publication_status', 'metashare_version', 'deleted']

# attributes to be serialized in the local JSON of the storage object
LOCAL_STORAGE_ATTS = ['digest_checksum', 'digest_modified', 
  'digest_last_checked', 'copy_status', 'source_node']


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
      help_text="(Read-only) MD5 checksum of the digest zip file containing the " \
      "global serialized storage object and the metadata XML for this " \
      "storage object instance.")
      
    digest_modified = models.DateTimeField(editable=False, null=True, blank=True,
      help_text="(Read-only) last modification date of digest zip " \
      "for this storage object instance.")
    
    digest_last_checked = models.DateTimeField(editable=False, null=True, blank=True,
      help_text="(Read-only) last update check date of digest zip " \
      "for this storage object instance.")
    
    revision = models.PositiveIntegerField(default=1, help_text="Revision " \
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
    
    source_node = models.CharField(blank=True, null=True, max_length=32, editable=False, 
      help_text="(Read-only) id of source node from which the resource " \
        "originally stems as set in local_settings.py in CORE_NODES and " \
        "PROXIED_NODES; empty if resource stems from this local node")
    
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
    
    def get_digest_checksum(self):
        """
        Checks if the current digest is till up-to-date, recreates it if
        required, and return the up-to-date digest checksum.
        """
        _expiration_date = _get_expiration_date()
        if _expiration_date > self.digest_modified \
          and _expiration_date > self.digest_last_checked: 
            self.update_storage()
        return self.digest_checksum
    
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
        
        self.checksum = compute_checksum(self.get_download())


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
        # And check if the local checksum matches the master copy's checksum.
        return self.checksum == compute_checksum(_binary_data)
    
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
        
        self.digest_last_checked = datetime.now()        

        # flag to indicate if rebuilding of metadata.xml is required
        update_xml = False
        
        # create current version of metadata XML
        from metashare.xml_utils import to_xml_string
        _metadata = to_xml_string(
          # pylint: disable-msg=E1101
          self.resourceinfotype_model_set.all()[0].export_to_elementtree(),
          # use ASCII encoding to convert non-ASCII chars to entities
          encoding="ASCII")
        
        if self.metadata != _metadata:
            self.metadata = _metadata
            self.modified = datetime.now()
            # increase revision for ingested and published resources whenever 
            # the metadata XML changes
            if self.publication_status in (INGESTED, PUBLISHED):
                self.revision += 1
                update_xml = True
            LOGGER.debug(u"\nMETADATA: {0}\n".format(self.metadata))
            
        # check if there exists a metadata XML file; this is not the case if
        # the publication status just changed from internal to ingested
        # or if the resource was received when syncing
        if self.publication_status in (INGESTED, PUBLISHED) \
          and not os.path.isfile(
          '{0}/metadata-{1:04d}.xml'.format(self._storage_folder(), self.revision)):
            update_xml = True

        # flag to indicate if rebuilding of resource.zip is required
        update_zip = False
          
        if update_xml:
            # serialize metadata
            with open('{0}/metadata-{1:04d}.xml'.format(
              self._storage_folder(), self.revision), 'wb') as _out:
                _out.write(unicode(self.metadata).encode('ASCII'))
            update_zip = True
        
        # check if global storage object serialization has changed; if yes,
        # save it to storage folder
        _dict_global = { }
        for item in GLOBAL_STORAGE_ATTS:
            _dict_global[item] = getattr(self, item)
        _global_storage = \
          dumps(_dict_global, cls=DjangoJSONEncoder, sort_keys=True, separators=(',',':'))
        if self.global_storage != _global_storage:
            self.global_storage = _global_storage
            if self.publication_status in (INGESTED, PUBLISHED):
                with open('{0}/storage-global.json'.format(
                  self._storage_folder()), 'wb') as _out:
                    _out.write(unicode(self.global_storage).encode('utf-8'))
                update_zip = True
        
        # create new digest zip if required, but only for master and proxy copies
        if update_zip and self.copy_status in (MASTER, PROXY):
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
            self.digest_checksum = \
              compute_digest_checksum(self.metadata, self.global_storage)
            # update last modified timestamp
            self.digest_modified = datetime.now()
            
        # check if local storage object serialization has changed; if yes,
        # save it to storage folder
        _dict_local = { }
        for item in LOCAL_STORAGE_ATTS:
            _dict_local[item] = getattr(self, item)
        _local_storage = \
          dumps(_dict_local, cls=DjangoJSONEncoder, sort_keys=True, separators=(',',':'))
        if self.local_storage != _local_storage:
            self.local_storage = _local_storage
            if self.publication_status in (INGESTED, PUBLISHED):
                with open('{0}/storage-local.json'.format(
                  self._storage_folder()), 'wb') as _out:
                    _out.write(unicode(self.local_storage).encode('utf-8'))
        
        # save storage object if required; this is always required since at 
        # least self.digest_last_checked has changed
        self.save()

def restore_from_folder(storage_id, copy_status=MASTER, storage_digest=None, source_node=None):
    """
    Restores the storage object and the associated resource for the given
    storage object identifier and makes it persistent in the database. 
    
    storage_id: the storage object identifier; it is assumed that this is the
        folder name in the storage folder folder where serialized storage object
        and metadata XML are located
    
    copy_status (optional): one of MASTER, REMOTE, PROXY; if present, used as
        copy status for the restored resource
    
    storage_digest (optional): the digest_checksum to set in the restored
        storage object

    source_node (optional): the source node if to set in the restored
        storage object
            
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
    LOGGER.info("restoring from {0}/{1}".format(storage_folder, _metadata_files[0]))
    _metadata_file = open('{0}/{1}'.format(storage_folder, _metadata_files[0]), 'rb')
    _xml_string = _metadata_file.read()
    _metadata_file.close()
    result = resourceInfoType_model.import_from_string(_xml_string, copy_status=copy_status)
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
    
    # If object is synchronized, retain the storage digest
    if storage_digest:
        _storage_object.digest_checksum = storage_digest
    # If object is non-local, set its source node id
    if source_node:
        _storage_object.source_node = source_node

    _storage_object.save()
    _storage_object.update_storage()
        
    return resource


def add_or_update_resource(storage_json, resource_xml_string, storage_digest,
                    copy_status=REMOTE, source_node=None):
    '''
    For the resource described by storage_json and resource_xml_string,
    do the following:

    - if it does not exist, import it with the given copy status and
        digest_checksum;
    - if it exists, delete it from the database, then import it with the given
        copy status and digest_checksum.
    
    Raises 'IllegalAccessException' if an attempt is made to overwrite
    an existing master-copy resource with a non-master-copy one.
    '''
    # Local helper functions first:
    def write_to_disk(storage_id):
        folder = os.path.join(settings.STORAGE_PATH, storage_id)
        if not os.path.exists(folder):
            os.mkdir(folder)
        with open(os.path.join(folder, 'storage-global.json'), 'wb') as out:
            out.write(
              unicode(
                dumps(storage_json, cls=DjangoJSONEncoder, sort_keys=True, separators=(',',':')))
                .encode('utf-8'))
        with open(os.path.join(folder, 'metadata.xml'), 'wb') as out:
            out.write(unicode(resource_xml_string).encode('utf-8'))

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
        # we have to keep the statistics and recommendations for this resource
        # since it is only updated
        resource.delete_deep(keep_stats=True)
        storage_object.delete()

    # Now the actual update_resource():
    storage_id = storage_json['identifier']
    if storage_object_exists(storage_id):
        if copy_status != MASTER and StorageObject.objects.get(identifier=storage_id).copy_status == MASTER:
            raise IllegalAccessException("Attempt to overwrite a master copy with a non-master-copy record; refusing")
        remove_files_from_disk(storage_id)
        remove_database_entries(storage_id)
    write_to_disk(storage_id)
    # if the resource was marked for deletion, remove that mark
    try:
        RemovedObject.objects.get(identifier=storage_id).delete()
    except ObjectDoesNotExist:
        pass
    return restore_from_folder(storage_id, copy_status=copy_status,
                        storage_digest=storage_digest, source_node=source_node)


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


def update_digests():
    """
    Re-creates a digest if it is older than MAX_DIGEST_AGE / 2.
    This assumes that this method is called in MAX_DIGEST_AGE / 2 intervals to
    guarantee a maximum digest age of MAX_DIGEST_AGE.
    """
    
    _expiration_date = _get_expiration_date()
    
    # get all master copy storage object of ingested and published resources
    for _so in StorageObject.objects.filter(
      Q(copy_status=MASTER),
      Q(publication_status=INGESTED) | Q(publication_status=PUBLISHED)):
        if _expiration_date > _so.digest_modified \
          and _expiration_date > _so.digest_last_checked: 
            LOGGER.info('updating {}'.format(_so.identifier))
            _so.update_storage()
        else:
            LOGGER.info('{} is up to date'.format(_so.identifier))

def repair_storage_folder():
    """
    Repairs the storage folder by forcing the recreation of all files.
    Superfluous files are deleted."
    """
    for _so in StorageObject.objects.all():
        if _so.publication_status == INTERNAL:
            # if storage folder is found, delete all files except a possible
            # binary
            folder = os.path.join(settings.STORAGE_PATH, _so.identifier)
            for _file in ('storage-local.json', 'storage-global.json', 
              'resource.zip', 'metadata.xml', 'metadata-*.xml'):
                path = os.path.join(folder, _file)
                for _path in glob.glob(path):
                    if os.path.exists(_path):
                        os.remove(_path)
        else:
            _so.metadata = None
            _so.global_storage = None
            _so.local_storage = None
            _so.update_storage()

def compute_checksum(infile):
    """
    Compute the MD5 checksum of infile, and return it as a hexadecimal string.
    infile: either a file-like object instance with a read() method, or
            a file path which can be opened using open(infile, 'rb').
    """
    checksum = md5()
    try:
        if hasattr(infile, 'read'):
            instream = infile
        else:
            instream = open(infile, 'rb')
        chunk = instream.read(MAXIMUM_MD5_BLOCK_SIZE)
        while chunk:
            checksum.update(chunk)
            chunk = instream.read(MAXIMUM_MD5_BLOCK_SIZE)
    finally:
        instream.close()
    return checksum.hexdigest()


def compute_digest_checksum(metadata, global_storage):
    """
    Computes the digest checksum for the given metadata and global storage objects.
    """
    _cs = md5() 
    _cs.update(metadata)
    _cs.update(global_storage)
    return _cs.hexdigest()

class IllegalAccessException(Exception):
    pass        

def _get_expiration_date():
    """
    Returns the expiration date of a digest based on the maximum age.
    """
    _half_time = settings.MAX_DIGEST_AGE / 2
    _td = timedelta(seconds=_half_time)
    _expiration_date = datetime.now() - _td
    return _expiration_date


class RemovedObject(models.Model):
    """
    Models a language resource that was completely removed from the storage layer.
    """
    
    identifier = models.CharField(max_length=64, blank=False,
      editable=False, unique=True, help_text="(Read-only) unique " \
      "identifier holding the identifier of the removed language resource.")
    
    removed = models.DateTimeField(editable=False, default=datetime.now(),
      help_text="(Read-only) removal date of the metadata XML " \
        "for this removed object instance.")
    
    def __unicode__(self):
        """
        Returns the Unicode representation for this reomved object instance.
        """
        return u'<RemovedObject id="{0}">'.format(self.id)
