# coding=utf-8
# pylint:

"""
    OAI-PMH module.

    @author: jm (UFAL, Charles University in Prague)
    @www: http://ufal-point.mff.cuni.cz
    @version: 0.2
"""

import sys
import os
import logging
import re
import codecs
from zipfile import ZipFile
from _utils import *
from collections import OrderedDict
from datetime import datetime
import oaipmh.error
from oai_pmh.oaipmh import common


# ensure local libs get loaded
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# setup logging support
#noinspection PyBroadException
try:
    _logger = logging.getLogger(__name__)
    from metashare.settings import LOG_HANDLER
    _logger.addHandler(LOG_HANDLER)
except:
    pass


#noinspection PyUnresolvedReferences
def check_system():
    """
        Check the system for support of oai-pmh.
    """
    try:
        from lxml import etree
    except ImportError:
        _logger.warning(u"Install lxml")
        return False, u"Please, install lxml"

    try:
        from oaipmh.client import Client
    except ImportError:
        _logger.warning(u"Install pyoai")
        return False, u"Please, install pyoai"

    return True, None


#==========================
# Interface helpers to pyoai
#==========================

def _client( url_str, registry=None ):
    """
    """
    from oaipmh.client import Client
    client = Client(url_str, registry)
    return client


def _reader( metadata_str ):
    """

    """
    from oaipmh.metadata import MetadataRegistry
    registry = MetadataRegistry()

    if "dc" in metadata_str:
        from oaipmh.metadata import oai_dc_reader
        registry.registerReader(metadata_str, oai_dc_reader)

    elif "metashare" in metadata_str:
        from _metadatareader import metashare_schema_reader
        registry.registerReader(metadata_str, metashare_schema_reader())

    elif "ore" in metadata_str:
        from _metadatareader import metashare_schema_reader
        registry.registerReader(metadata_str, metashare_schema_reader())

    else:
        raise NotImplementedError("Metadata reading not implemented for [%s]" % metadata_str)

    return registry


#==========================
# The actual work
#==========================

def list_records( kwargs ):
    """
        List all records.
        @required: url, metadata_str
        @return: dict of displayable items
    """
    #noinspection PyUnresolvedReferences
    from lxml import etree
    import cgi

    url_str, metadata_str = params(kwargs, ("url", "metadata_str"))
    client = _client(url_str, _reader(metadata_str))
    d = {}
    for header, metadata, _1 in client.listRecords(metadataPrefix=metadata_str):
        data_str = prehtmlify(metadata.getMap() if not metadata is None else {},
                              add_pre=False)
        data_str = data_str.replace(u"\\n", u"\n").splitlines()
        data_str = [cgi.escape(x) for x in data_str if not 0 == len(x.strip())]
        d[header.identifier()] = u"<br>".join(data_str)
    return d


def list_sets( kwargs ):
    """
        List all sets.
        @required: url
        @return: dict of displayable items
    """
    url_str = params(kwargs, ("url",))
    client = _client(url_str)
    d = {}
    for spec, name, description in client.listSets():
        d[spec] = prehtmlify((
            u"name: %s" % name,
            u"spec: %s" % spec,
            u"description: %s" % description,
        ))
    return d


def list_formats( kwargs ):
    """
        List all metadata formats.
        @required: url
        @return: dict of displayable items
    """
    url_str = params(kwargs, ("url",))
    client = _client(url_str)
    d = {}
    for prefix, schema, ns in client.listMetadataFormats():
        d[prefix] = prehtmlify((
            u"prefix: %s" % prefix,
            u"schema: %s" % schema,
            u"ns: %s" % ns,
        ))
    return d


def list_identifiers( kwargs ):
    """
        List all metadata identifiers.
        @required: url, metadata_str
        @return: dict of displayable items
    """
    url_str, metadata_str = params(kwargs, ("url", "metadata_str"))
    client = _client(url_str)
    d = {}
    for id_ in client.listIdentifiers(metadataPrefix=metadata_str):
        id_str = id_.setSpec()
        if isinstance(id_str, (tuple, list)):
            id_str = id_str[0]
        d[id_.identifier()] = id_str
    return d


def identify( kwargs ):
    """
        List server identification.
        @required: url, metadata_str
        @return: dict of displayable items
    """
    url_str = params(kwargs, ("url",))
    client = _client(url_str)
    d = {}
    id_ = client.identify()
    d["Name"] = id_.repositoryName()
    d["Url"] = id_.baseURL()
    d["Protocol ver."] = id_.protocolVersion()
    d["Admin emails"] = id_.adminEmails()
    return d


def import_id( kwargs ):
    """
        Import selected set id.

        What it does?
        1) get the settings of what we want
        2) get xml string of metashare metadata
        3) do the metadata import
        4) get ORE files
        5) copy the file to the proper place and update metashare node


        @required: url, metadata_str, itemid
        @return: dict of displayable items

    """
    from metashare.xml_utils import import_from_string
    from metashare.storage.models import PUBLISHED, MASTER
    import metashare.storage_admin

    ##
    # 1. settings
    #
    save_to_dir = None
    # noinspection PyBroadException
    try:
        # noinspection PyUnresolvedReferences
        from metashare.settings import OAI_PMH_IMPORT_SAVE_DIR
        save_to_dir = OAI_PMH_IMPORT_SAVE_DIR
        if not os.path.exists(save_to_dir):
            os.makedirs(save_to_dir)
    except:
        pass

    ##
    # 2. get metashare metadata
    #
    OK_MSG = u"OK"
    url_str, metadata_str, itemid, import_from_dir = \
        params(kwargs, ("url", "metadata_str", "itemid", "import_from_dir"))
    if 0 == len(itemid.strip()):
        itemid = None
    else:
        itemid = u"/".join(itemid.split(u"/")[-2:])

    # what else than specific metashare?
    if not "metashare" in metadata_str:
        return {"Error": "how shall i import? (you need specific metashare metadata profile)"}

    ret_d = OrderedDict()
    # make metashare friendly
    re_subs = ( re.compile(u"^<metadata [^>]+>", re.M | re.U),
                re.compile(u"</metadata>$", re.M | re.U) )

    # <identificationInfo>
    #  <identifier>
    re_id = re.compile(u"<identificationInfo>.*<identifier>([^<]+)</identifier>.*</identificationInfo>",
                       re.MULTILINE | re.DOTALL | re.UNICODE)
    re_sub_id = re.compile(u"(<metaShareId>).*(</metaShareId>)", re.UNICODE)

    # Metashare glitch
    def _id_from_meta( raw_xml_record ):
        m = re_id.search(raw_xml_record)
        return m.group(1) if m else None

    from metashare.storage.models import StorageObject

    storage_objects = StorageObject.objects.all()
    so_map = {}
    for so in storage_objects:
        so_map[_id_from_meta(so.metadata)] = so

    def _find_id_in_current_db( raw_xml_record ):
        id_str = _id_from_meta(raw_xml_record)
        return so_map[id_str] if id_str in so_map else None

    pos = 0
    client = _client(url_str, _reader(metadata_str))
    for header, metadata, _2 in client.listRecords(metadataPrefix=metadata_str):
        pos += 1
        try:
            if header.isDeleted():
                ret_d[header.identifier()] = html_mark_warning(u"This record is deleted - delete it manually!!!"), \
                                                header.identifier(), \
                                                None
                continue

            # try to publish it on this node
            raw_xml_record = metadata.getField("raw_xml")
            for re_sub in re_subs:
                raw_xml_record = re_sub.sub(u"", raw_xml_record)

            if not itemid is None and not itemid in header.identifier():
                _logger.info(u"Skipping [%s]", header.identifier())
                continue

            # e.g., for debugging
            if not save_to_dir is None:
                with codecs.open(os.path.join(save_to_dir, "UFAL-metashare-%s.xml" % pos),
                                 mode="w+", encoding="utf-8") as fout:
                    fout.write(raw_xml_record)

            # 3. do the import
            #
            # 2.5 find the id and check if we already have it
            obj = _find_id_in_current_db(raw_xml_record)
            if obj:
                raw_xml_record = re_sub_id.sub(u"<metaShareId>%s</metaShareId>" % obj.identifier,
                                               raw_xml_record, count=1)
                _logger.info(u"Item [%s]->[%s] found in database",
                             _id_from_meta(raw_xml_record), obj.identifier)

            resource = import_from_string(raw_xml_record, PUBLISHED, MASTER)
            ret_d[header.identifier()] = OK_MSG, \
                                            repr(resource), \
                                            resource.storage_object._storage_folder()
        except Exception, e:
            ret_d[header.identifier()] = html_mark_error(u"Failed!"), \
                                            html_mark_error(repr(e)), \
                                            None

    # 4. get ORE
    #
    only_in_ore = u"Found item in ORE but not in metadata format"
    ret_d[only_in_ore] = []

    metadata_str = "ore"
    client = _client(url_str, _reader(metadata_str))
    if import_from_dir:
        for header, metadata, _2 in client.listRecords(metadataPrefix=metadata_str):

            if not header.identifier() in ret_d or metadata is None:
                ret_d[only_in_ore].append(header.identifier())
                continue

            # noinspection PyBroadException,PyUnusedLocal
            try:
                raw_xml_record = metadata.getField("raw_xml")
                info, resource, import_to_path = ret_d[header.identifier()]

                if OK_MSG != info:
                    continue

                # find the path
                imported_storage_files = re.compile(u"<dcterms:identifier>([^<]+)</dcterms:identifier>") \
                    .findall(raw_xml_record)
                imported_storage_files = [os.path.join(import_from_dir, x) for x in imported_storage_files]
                for imported_storage_file in imported_storage_files:
                    if not os.path.exists(imported_storage_file):
                        warn_msg = u" | Could not find imported file [%s]" % imported_storage_file
                        ret_d[header.identifier()] = info + warn_msg, \
                                                        resource + raw_xml_record, \
                                                        import_to_path
                imported_storage_files = [x for x in imported_storage_files if os.path.exists(x)]

                # hardcoded in storage/models.py
                new_zip_path = os.path.join(import_to_path, 'archive.zip')
                # we know where, we know from where
                if os.path.exists(new_zip_path):
                    warn_msg = u" | Removed existing zip file"
                    ret_d[header.identifier()] = info + warn_msg, \
                                                    resource + raw_xml_record, \
                                                    import_to_path
                    safe_remove(new_zip_path)

                # 5. copy and update
                #
                with ZipFile(new_zip_path, 'w') as new_zip:
                    for f in imported_storage_files:
                        new_zip.write(f, arcname=os.path.basename(f))

                # all is where it should be and now update
                object_id = os.path.basename(os.path.dirname(new_zip_path))
                # Metashare glitch
                #noinspection PyUnresolvedReferences
                metashare.storage_admin.StorageObject = StorageObject
                #noinspection PyUnresolvedReferences
                metashare.storage_admin.checksum(object_id)
            except Exception, e:
                _logger.exception( u"Got exception while importing" )

    # make html friendly
    for k, v in ret_d.iteritems():
        ret_d[k] = prehtmlify(v)

    return ret_d


class MetashareOaiServer(object):
    """
        The metashare implementation of the OAI verbs.

        This is the first shot on a real implementation which is left for
        the original authors; however, the basics and the api usage
        is shown below.
    """

    def __init__( self, env ):
        """
            Settings, required arguments are `name`, `url`, `adminEmails`.
        """
        self.env = env

    def identify(self):
        """
            OAI-PMH ?verb=identify.
            See http://www.openarchives.org/OAI/openarchivesprotocol.html#Identify
        """
        return common.Identify(
            repositoryName=self.env["name"],
            baseURL=self.env["url"],
            protocolVersion="2.0",
            adminEmails=self.env["adminEmails"],
            earliestDatestamp=datetime(2004, 1, 1),
            deletedRecord='no',
            granularity='YYYY-MM-DDThh:mm:ssZ',
            compression=['identity'])

    def getRecord(self, metadataPrefix, identifier):
        """
            TODO! one item is composed of
              (common.Header(str(i), datestamp, '', False),
               common.Metadata({'title': ['Title %s' % i]}),
               None) # about

        """
        try:
            return []
        except IndexError:
            raise oaipmh.error.IdDoesNotExistError, "Id does not exist: %s" % identifier

    def listIdentifiers(self, metadataPrefix=None, from_=None, until=None, set=None):
        """
            TODO! check metadataPrefix
        """
        from metashare.storage.models import StorageObject

        # get all objects according to id
        re_id = re.compile(u"<identificationInfo>.*<identifier>([^<]+)</identifier>.*</identificationInfo>",
                           re.MULTILINE | re.DOTALL | re.UNICODE)

        def _id_from_meta( raw_xml_record ):
            m = re_id.search(raw_xml_record)
            return m.group(1) if m else None

        storage_objects = StorageObject.objects.all()
        so_map = {}
        result = []
        for so in storage_objects:
            i = _id_from_meta(so.metadata)
            so_map[i] = so
            result.append(
                common.Header(str(i), so.created, '', False) )
        return result

    def listRecords(self, metadataPrefix=None, from_=None, until=None, set=None):
        """
            TODO!
                resource = get_object_or_404(resourceInfoType_model,
                                storage_object__identifier=object_id,
                                storage_object__publication_status=PUBLISHED)
        """
        result = []
        return result


#==========================
# Supported commands
#==========================

key_list_ids_for_import = u"list identifiers (use for import)"
key_import = u"Import the resource(s)"
key_list_metadata_format = u"list formats"

supported_commands = OrderedDict()
supported_commands[key_import] = import_id
supported_commands[key_list_ids_for_import] = list_identifiers

# available as separate buttons
supported_commands.update({
    u"list records": list_records,
    u"identify server": identify,
    u"list sets": list_sets,
    key_list_metadata_format: list_formats,
})


#
#
if __name__ == "__main__":
    pass
