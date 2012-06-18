"""
Project: META-SHARE prototype implementation
 Author: Christian Spurk <cspurk@dfki.de>
"""
import logging

from django_selenium.selenium_runner import SeleniumTestRunner
from django.core.management import call_command
from metashare import settings

from metashare.haystack_routers import MetashareRouter

# set up logging support
logging.basicConfig(level=settings.LOG_LEVEL)
LOGGER = logging.getLogger('metashare.test_runner')
LOGGER.addHandler(settings.LOG_HANDLER)


def _run_custom_test_db_setup():
    """
    Runs the custom test DB setup logic which is required in META-SHARE.
    """
    # from now on, redirect any search index access to the test index
    MetashareRouter.in_test_mode = True
    # clear the test index
    call_command('clear_index', interactive=False,
                 using=settings.TEST_MODE_NAME)


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


# if we're in a Jenkins test environment, then we also create a test runner for
# Jenkins
try:
    from django_selenium.jenkins_runner import JenkinsTestRunner
    class MetashareJenkinsTestRunner(JenkinsTestRunner):
        """
        A custom Django Jenkins test runner which inherits from Selenium's
        `JenkinsTestRunner` which in turn inherits from `CITestSuiteRunner`.
        
        The added value of this test runner on top of the default functionality
        provided by Django/Selenium Jenkins is that the runner automatically
        sets up Haystack so that it uses a dedicated search backend for testing.
        """
        def setup_databases(self, **kwargs):
            _run_custom_test_db_setup()
            # run the normal Django test setup
            return super(MetashareJenkinsTestRunner, self).setup_databases(
                                                                    **kwargs)
except ImportError:
    pass
