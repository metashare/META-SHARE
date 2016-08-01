from haystack import connection_router, connections
from haystack.exceptions import NotHandled
from haystack.query import SearchQuerySet

ignored_pk_list = []

def __len__(self):
    if not self._result_count:
        self._result_count = self.query.get_count()
        # Some backends give weird, false-y values here. Convert to zero.
        if not self._result_count:
            self._result_count = 0

    # This needs to return the actual number of hits, not what's in the
    # cache.
    return max(0, self._result_count - self._ignored_result_count)

def _determine_backend(self):
    global ignored_pk_list
    ignored_pk_list = []
    from haystack import connections
    # A backend has been manually selected. Use it instead.
    if self._using is not None:
        self.query = connections[self._using].get_query()
        return

    # No backend, so rely on the routers to figure out what's right.
    hints = {}

    if self.query:
        hints['models'] = self.query.models

    backend_alias = connection_router.for_read(**hints)

    if isinstance(backend_alias, (list, tuple)) and len(backend_alias):
        # We can only effectively read from one engine.
        backend_alias = backend_alias[0]

    # The ``SearchQuery`` might swap itself out for a different variant
    # here.
    if self.query:
        self.query = self.query.using(backend_alias)
    else:
        self.query = connections[backend_alias].get_query()
            
def post_process_results(self, results):
    to_cache = []
    global ignored_pk_list

    # Check if we wish to load all objects.
    if self._load_all:
        models_pks = {}
        loaded_objects = {}

        # Remember the search position for each result so we don't have to resort later.
        for result in results:
            models_pks.setdefault(result.model, []).append(result.pk)

        # Load the objects for each model in turn.
        for model in models_pks:
            try:
                ui = connections[self.query._using].get_unified_index()
                index = ui.get_index(model)
                objects = index.read_queryset(using=self.query._using)
                loaded_objects[model] = objects.in_bulk(models_pks[model])
            except NotHandled:
                self.log.warning("Model '%s' not handled by the routers", model)
                # Revert to old behaviour
                loaded_objects[model] = model._default_manager.in_bulk(models_pks[model])

    for result in results:
        if self._load_all:
            # We have to deal with integer keys being cast from strings
            model_objects = loaded_objects.get(result.model, {})
            if result.pk not in model_objects:
                try:
                    result.pk = int(result.pk)
                except ValueError:
                    pass
            try:
                result._object = model_objects[result.pk]
            except KeyError:
                # The object was either deleted since we indexed or should
                # be ignored; fail silently.
                
                if not result.pk in ignored_pk_list:
                    ignored_pk_list.append(result.pk)
                    self._ignored_result_count += 1
                continue

        to_cache.append(result)

    return to_cache

SearchQuerySet._determine_backend = _determine_backend
SearchQuerySet.post_process_results = post_process_results
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
