from haystack.routers import DefaultRouter
from metashare.settings import TEST_MODE_NAME


class MetashareRouter(DefaultRouter):
    """
    A custom router which can be dynamically switched to a test mode.
    """
    # static variable denoting whether we are in test mode or not; change it to
    # switch between test mode and default mode
    in_test_mode = False
    
    def __init__(self):
        super(MetashareRouter, self).__init__()

    def for_read(self, **hints):
        if MetashareRouter.in_test_mode:
            return TEST_MODE_NAME
        return super(MetashareRouter, self).for_read(**hints)

    def for_write(self, **hints):
        if MetashareRouter.in_test_mode:
            return TEST_MODE_NAME
        return super(MetashareRouter, self).for_write(**hints)
