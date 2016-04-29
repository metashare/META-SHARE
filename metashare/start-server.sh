#!/bin/bash
# META-SHARE Django website

PROJECT_ROOT=`cd $(dirname "$0"); pwd`
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

source "${PROJECT_ROOT}/../venv/bin/activate"

# Register scheduled tasks for synchronization, session cleanup, etc.
(cd "$PROJECT_ROOT/../"; python manage.py installtasks)

# Start the Django + lighttpd server:
(cd "$PROJECT_ROOT/../"; python manage.py runfcgi host=localhost port=9190 method=threaded pidfile=$DJANGO_PID)
lighttpd -f "$PROJECT_ROOT/lighttpd.conf"

deactivate

