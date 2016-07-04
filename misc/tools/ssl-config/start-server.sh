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

echo "DJANGO_PORT = $DJANGO_PORT"
export DJANGO_PORT
export DATABASE_FILE
export STORAGE_PATH
export SOLR_PORT

start_solr "$SOLR_ROOT" $SOLR_PORT $SOLR_STOP_PORT "$SOLR_STOP_KEY" "$SOLR_LOG"

sleep 5 # give SOLR time to start up before trying to verify that it is there

# Register scheduled task(s) for synchronization
cd "$METASHARE_DIR"
"$PYTHON" manage.py installtasks

# Start the Django + lighttpd server:
start_django $PYTHON_PORT "$DJANGO_PID"
#"$PYTHON" manage.py runfcgi host=localhost port=$DJANGO_PORT method=threaded pidfile=$DJANGO_PID

start_light "$LIGHT_CONF_FILE"
#lighttpd -f "$METASHARE_SW_DIR/misc/tools/ssl-config/lighttpd-ssl.conf
