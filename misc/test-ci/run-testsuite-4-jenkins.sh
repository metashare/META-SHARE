#!/bin/bash

# Copy test configuration
mkdir -p "storage"
echo $(pwd)

cp misc/test-ci/local_settings.test_local metashare/local_settings.py
cp misc/test-ci/initial_data.test.json metashare/initial_data.json

# Initialize database
rm -f metashare/testing.db
source venv/bin/activate
pip install coverage

if [ "x$PYTHONWARNINGS" = "x" ]; then
    export PYTHONWARNINGS="d"
fi

python manage.py syncdb --noinput
#python manage.py dumpdata > metashare/django-dump.json
rm metashare/initial_data.json

# Run testsuite:
metashare/start-solr.sh
sleep 10
python manage.py jenkins repository
deactivate
metashare/stop-solr.sh
