# Get all individual unit tests together.
# Do it by hand for now;
# should we need something automatic, see here: http://djangosnippets.org/snippets/1972/

# Yes, pylint, we want wildcard imports here.
# pylint: disable-msg=W0401
from metashare.repository.seltests.test_example import *
