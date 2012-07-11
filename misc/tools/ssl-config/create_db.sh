#!/bin/bash
# META-SHARE Django website

. _meta_dir.sh
. _python.sh
METASHARE_DIR=$METASHARE_SW_DIR/metashare
SOLR_ROOT=$METASHARE_SW_DIR/solr
. _conf.sh
. _solr.sh
. _django.sh
. _light.sh



export DJANGO_PORT
export DATABASE_FILE
export STORAGE_PATH
export SOLR_PORT

start_solr "$SOLR_ROOT" $SOLR_PORT $SOLR_STOP_PORT "$SOLR_STOP_KEY" "$SOLR_LOG"

sleep 5 # give SOLR time to start up before trying to verify that it is there

# Register scheduled task(s) for synchronization
cd "$METASHARE_DIR"
"$PYTHON" manage.py syncdb

