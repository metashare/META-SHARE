# coding=utf-8
# pylint:

"""
    OAI-PMH metashare scheme (specific) reader.

    @author: jm (UFAL, Charles University in Prague)
    @www: http://ufal-point.mff.cuni.cz
    @version: 0.1
"""

from oaipmh import common
from lxml import etree


class metashare_schema_reader( object ):
    """
        An implementation of a reader.
    """
    def __init__(self):
        pass

    def __call__( self, lxml_elem ):
        xml = etree.tostring( lxml_elem, pretty_print=True )
        return common.Metadata( { "raw_xml": xml } )
