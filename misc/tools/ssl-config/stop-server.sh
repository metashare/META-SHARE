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


stop_django $DJANGO_PID

stop_light "$LIGHTTPD_PID"

export DJANGO_PORT
export DATABASE_FILE
export STORAGE_PATH
export SOLR_PORT

stop_solr "$SOLR_ROOT" $SOLR_PORT $SOLR_STOP_PORT "$SOLR_STOP_KEY" "$SOLR_LOG"

