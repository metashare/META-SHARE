# Get all individual unit tests together.
# Do it by hand for now;
# should we need something automatic, see here: http://djangosnippets.org/snippets/1972/

# Yes, pylint, we want wildcard imports here.
# pylint: disable-msg=W0401
from metashare.repository.seltests.test_editor import *
from metashare.repository.seltests.test_filter import *
from metashare.repository.seltests.test_example import *

import os
if 'METASHARE_NIGHTLY_BUILD' in os.environ.keys() \
      and os.environ['METASHARE_NIGHTLY_BUILD'] == 'true':
    from metashare.repository.seltests.test_editor_nightly import *
