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

misc/tools/multitest/unit_tests_1.sh || exit 1
misc/tools/multitest/unit_tests_2.sh || exit 1
misc/tools/multitest/unit_tests_3.sh || exit 1
misc/tools/multitest/unit_tests_4.sh || exit 1

deactivate
