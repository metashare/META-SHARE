#!/bin/bash


CURRENT_DIR=`pwd`
METASHARE_DIR=$METASHARE_SW_DIR/metashare
SCHEMA_FILE=$CURRENT_DIR/init_data/schema.xml

cp init_data/settings_orig.py ../../metashare/settings.py
cp init_data/local_settings_test.py ../../metashare/local_settings.py

export DJANGO_PORT=12345
export STORAGE_PATH=/tmp/storageFolder
export SOLR_PORT=54321
export DATABASE_FILE=$CURRENT_DIR/init_data/metashare_test.db

# find the best Python binary to use: only use the platform default if ther is
# no custom Python installation for META-SHARE available
if [ -x "$METASHARE_SW_DIR/opt/bin/python" ] ; then
	PYTHON="$METASHARE_SW_DIR/opt/bin/python"
else
	PYTHON=`which python`
fi

cd $METASHARE_DIR
python manage.py build_solr_schema --filename="$SCHEMA_FILE"
cd $CURRENT_DIR

echo "Schema file " $SCHEMA_FILE " has been created/updated."
