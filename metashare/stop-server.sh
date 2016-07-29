#!/bin/bash
# META-SHARE Django website

PROJECT_ROOT=$(dirname "$0")
DJANGO_PID="$PROJECT_ROOT/django.pid"
LIGHTTPD_PID="$PROJECT_ROOT/lighttpd.pid"

if [ -f $DJANGO_PID ]; then
    kill -9 `cat $DJANGO_PID`
    rm -f $DJANGO_PID
fi

if [ -f $LIGHTTPD_PID ]; then
    kill -9 `cat $LIGHTTPD_PID`
    rm -f $LIGHTTPD_PID
fi

source "${PROJECT_ROOT}/../venv/bin/activate"

# Unregister scheduled tasks for synchronization, session cleanup, etc.
(cd "$PROJECT_ROOT/../" && python2.7 manage.py uninstalltasks )

deactivate

$PROJECT_ROOT/stop-solr.sh
