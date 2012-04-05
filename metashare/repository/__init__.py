"""
Project: META-SHARE prototype implementation
 Author: Christian Federmann <cfedermann@dfki.de>
"""

def verify_at_startup():
    """
    A generic verification method called for certain commands directly from our custom manage.py.
    The purpose of this method is to check that things seem set up properly,
    and to throw an Exception if they don't.
    
    Thus, this method serves as a "hook" for a fail-early strategy -- we only allow the server
    to start if we have reasons to believe it can run properly.
    """
    
    check_solr_running()


def check_solr_running():
    try:
        import socket
        from pysolr import SolrError
        from haystack.query import SearchQuerySet
        SearchQuerySet().count()
    except (SolrError, socket.error) as solr_error:
        _msg = """
**************************************************************************
Problem contacting SOLR search index server.
Make sure you have executed start-solr.sh!
Caused by: {}
**************************************************************************
""".format(solr_error)
        raise Exception(_msg)