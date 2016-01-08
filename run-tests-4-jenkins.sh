#!/bin/bash

if [ ! -d "venv" ]; then
   ./install-dependencies.sh || exit 1
fi

./misc/test-ci/run-testsuite-4-jenkins.sh || exit 1
./misc/test-ci/multitest-4-jenkins.sh || exit 1
