#!/bin/bash

if [ ! -d "venv" ]; then
   ./install-dependencies.sh || exit 1
fi

# Determine whether or not the test is run locally:
LOCAL_TEST="no"
if [ "x$TRAVIS_JOB_NUMBER" = "x" ]; then 
  LOCAL_TEST="yes"
fi

if [ "$LOCAL_TEST" = "no" ]; then
  source venv/bin/activate || exit 1
  pip install coveralls || exit 1
  deactivate || exit 1
fi

./misc/test-ci/run-testsuite.sh || exit 1
if [ "$LOCAL_TEST" = "no" ]; then
  ./misc/test-ci/run-testsuite.sh --selenium-only || exit 1
fi
./misc/test-ci/multitest.sh || exit 1

if [ "$LOCAL_TEST" = "no" ]; then
  source venv/bin/activate || exit 1
  coveralls || exit 1
  deactivate || exit 1
fi
