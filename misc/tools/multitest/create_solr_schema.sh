#!/bin/bash

. _meta_dir.sh
. _python.sh
. _utils.sh

CURRENT_DIR=`pwd`
SCHEMA_FILE=$CURRENT_DIR/init_data/schema.xml

cp init_data/settings_orig.py $METASHARE_DIR/settings.py
cp init_data/local_settings_test.py $METASHARE_DIR/local_settings.py

export DJANGO_PORT=12345
export STORAGE_PATH=/tmp/storageFolder
export SOLR_PORT=54321
export DATABASE_FILE=$CURRENT_DIR/init_data/metashare_test.db

cd $METASHARE_DIR
python manage.py build_solr_schema --filename="$SCHEMA_FILE"
cd $CURRENT_DIR

META_LOG=`get_meta_log`
rm -f "$META_LOG"
rmdir "$STORAGE_PATH"

echo "Schema file " $SCHEMA_FILE " has been created/updated."
