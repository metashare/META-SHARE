#! /usr/bin/env python
"""
Call the external program xdiff to compare two XML files

"""

from subprocess import call, STDOUT
import sys
import os
import logging
from metashare.settings import LOG_LEVEL, LOG_HANDLER, XDIFF_LOCATION

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('metashare.xml_utils')
LOGGER.addHandler(LOG_HANDLER)

CONSOLE = "/dev/null"

def xml_compare(file1, file2, outfile=None):
    """
    Compare two XML files with the external program xdiff.

    Return True, if they are equal, False otherwise.

    """
    if not os.access(XDIFF_LOCATION, os.X_OK):
        LOGGER.error("no executable xdiff binary: {0}".format(XDIFF_LOCATION))
        return False

    if not outfile:
        outfile = "{0}.diff".format(file1)
    
    # If diff-file exists, remove it so that there is no diff after a clean run:
    if os.access(outfile, os.F_OK):
        os.remove(outfile)
        
    for __f in [file1, file2]:
        if not os.path.isfile(__f):
            LOGGER.warning("file {0} does not exist".format(__f))
    
    with open(CONSOLE, "w+") as out:
        retval = call([XDIFF_LOCATION, file1, file2, outfile],
                      stdout=out, stderr=STDOUT)

    return (retval == 0)

if __name__ == "__main__":
    if xml_compare(sys.argv[1], sys.argv[2]):
        print "equal"
    else :
        print "not equal"

