import logging

from django_selenium.selenium_runner import SeleniumTestRunner

from haystack.management.commands import clear_index

from metashare import settings
from metashare.haystack_routers import MetashareRouter

# set up logging support
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(settings.LOG_HANDLER)


def _run_custom_test_db_setup():
    """
    Runs the custom test DB setup logic which is required in META-SHARE.
    """
    # from now on, redirect any search index access to the test index
    MetashareRouter.in_test_mode = True
    # clear the test index
    clear_index.Command().handle(interactive=False,
                                 using=[settings.TEST_MODE_NAME,])

class MetashareTestRunner(SeleniumTestRunner):
    """
    A custom Django test runner which inherits from `SeleniumTestRunner`
    which in turn inherits from `DjangoTestSuiteRunner`.
    
    The added value of this test runner on top of the default functionality
    provided by Django/Selenium is that the runner automatically sets up
    Haystack so that it uses a dedicated search backend for testing.
    """
    def setup_databases(self, **kwargs):
        _run_custom_test_db_setup()
        # run the normal Django test setup
        return super(MetashareTestRunner, self).setup_databases(**kwargs)
