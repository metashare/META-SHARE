#!/bin/bash


CURRENT_DIR=`pwd`
METASHARE_DIR=$METASHARE_SW_DIR/metashare
SCHEMA_FILE=$CURRENT_DIR/init_data/schema.xml

export DJANGO_PORT=12345
export STORAGE_PATH=/tmp/storageFolder
export SOLR_PORT=54321
export DATABASE_FILE=$CURRENT_DIR/init_data/metashare_test.db

cd $METASHARE_DIR
python manage.py build_solr_schema --filename="$SCHEMA_FILE"
cd $CURRENT_DIR

echo "Schema file " $SCHEMA_FILE " has been created/updated."
