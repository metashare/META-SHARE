from haystack.query import SearchQuerySet

def __len__(self):
    if not self._result_count:
        self._result_count = self.query.get_count()
        # Some backends give weird, false-y values here. Convert to zero.
        if not self._result_count:
            self._result_count = 0

    # This needs to return the actual number of hits, not what's in the
    # cache.
    return max(0, self._result_count - self._ignored_result_count)

SearchQuerySet.__len__ = __len__

def verify_at_startup():
    """
    A generic verification method called for certain commands directly from our custom manage.py.
    The purpose of this method is to check that things seem set up properly,
    and to throw an Exception if they don't.
    
    Thus, this method serves as a "hook" for a fail-early strategy -- we only allow the server
    to start if we have reasons to believe it can run properly.
    """
    
    check_solr_running()
    check_settings()


def check_solr_running():
    try:
        import socket
        from pysolr import SolrError
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

def check_settings():
    def fail(msg):
        raise Exception(u'Error in settings: {}'.format(msg))
    from metashare.settings import DJANGO_BASE, DJANGO_URL
    if DJANGO_URL.endswith('/'):
        fail('DJANGO_URL must not end in a slash')
    if not (DJANGO_BASE.endswith('/') or DJANGO_BASE == ''):
        fail('DJANGO_BASE must end in a slash or be the empty string')
    # from base, remove the trailing slash:
    base_path = DJANGO_BASE[:-1]
    # From url, remove the protocol if present:
    url_path = '://' in DJANGO_URL and DJANGO_URL[DJANGO_URL.find('://')+3:] or DJANGO_URL
    # and then the host/port:
    url_path = '/' in url_path and url_path[url_path.find('/')+1:] or ''
    if base_path != url_path:
        fail(u"Based on DJANGO_URL '{}', expected DJANGO_BASE '{}/', but was '{}'".format(DJANGO_URL, url_path, DJANGO_BASE))



