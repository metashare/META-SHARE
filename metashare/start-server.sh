#!/bin/bash
# META-SHARE Django website

PROJECT_ROOT=$(dirname "$0")
DJANGO_PID="$PROJECT_ROOT/django.pid"
LIGHTTPD_PID="$PROJECT_ROOT/lighttpd.pid"

if [ -f $DJANGO_PID ]; then
    kill -9 `cat -- $DJANGO_PID`
    rm -f -- $DJANGO_PID
fi

if [ -f $LIGHTTPD_PID ]; then
    kill -9 `cat -- $LIGHTTPD_PID`
    rm -f -- $LIGHTTPD_PID
fi

$PROJECT_ROOT/start-solr.sh

sleep 5 # give SOLR time to start up before trying to verify that it is there

# Start the Django + lighttpd server:
python2.7 manage.py runfcgi host=localhost port=9190 method=threaded pidfile=$DJANGO_PID
lighttpd -f /opt/metashare_git/META-SHARE-Software/metashare/lighttpd/metashare.conf
