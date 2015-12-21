#!/bin/bash

if [ ! -d "venv" ]; then
   ./install-dependencies.sh || exit 1
fi

source venv/bin/activate || exit 1
pip install coveralls || exit 1
deactivate || exit 1

./misc/test-ci/run-testsuite.sh || exit 1
./misc/test-ci/run-testsuite.sh --selenium-only || exit 1
./misc/test-ci/multitest.sh || exit 1

source venv/bin/activate || exit 1
coveralls || exit 1
deactivate || exit 1


