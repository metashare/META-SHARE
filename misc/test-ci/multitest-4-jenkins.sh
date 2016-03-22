#!/bin/bash
#Run this from the top META-SHARE directory
# misc/test-ci/multitest.sh

export METASHARE_SW_DIR="$PWD"
export TEST_DIR="$PWD/tmp-multitest"
source venv/bin/activate
export PYTHON="coverage run -a "

if [ "x$PYTHONWARNINGS" = "x" ]; then
    export PYTHONWARNINGS="d"
fi

misc/tools/multitest/unit_tests_1.sh
misc/tools/multitest/unit_tests_2.sh
misc/tools/multitest/unit_tests_3.sh
misc/tools/multitest/unit_tests_4.sh

deactivate
