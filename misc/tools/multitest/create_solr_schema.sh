#!/bin/bash

MSERV_DIR=$(dirname $0)

. ${MSERV_DIR}/_meta_dir.sh
. ${MSERV_DIR}/_python.sh
. ${MSERV_DIR}/_utils.sh
. ${MSERV_DIR}/_django.sh

CURRENT_DIR=`pwd`
SCHEMA_FILE=$MSERV_DIR/init_data/schema.xml

cp $MSERV_DIR/init_data/settings_multitest.py $METASHARE_DIR/settings.py

NODE_NAME="NodeSolr"
DJANGO_PORT=12345
STORAGE_PATH="$TEST_DIR/$NODE_NAME/storageFolder"
SOLR_PORT=54321
DATABASE_FILE=$CURRENT_DIR/init_data/metashare_test.db
CORE_NODES="()"
PROXIED_NODES="()"
SYNC_USERS="()"
export NODE_DIR="$TEST_DIR/$NODE_NAME"
mkdir -p "$TEST_DIR/$NODE_NAME/dj_settings"
create_django_settings "$NODE_NAME" $SOLR_PORT "$DATABASE_FILE" \
	"$STORAGE_PATH" $DJANGO_PORT "$CORE_NODES" \
	"$PROXIED_NODES" "$SYNC_USERS"

#cd $METASHARE_DIR
mkdir -p "$(basename $SCHEMA_FILE)"
$PYTHON manage.py build_solr_schema --filename="$SCHEMA_FILE"
#cd $CURRENT_DIR

META_LOG=`get_meta_log`
rm -r "$TEST_DIR/$NODE_NAME"

echo "Schema file " $SCHEMA_FILE " has been created/updated."
