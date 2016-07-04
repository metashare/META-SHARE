#!/bin/bash
# META-SHARE statistics server

PROJECT_ROOT=$(pwd)
DJANGO_PID="$PROJECT_ROOT/metastats.pid"

if [ -f $DJANGO_PID ]; then
    kill -9 `cat -- $DJANGO_PID`
    rm -f -- $DJANGO_PID
fi


python manage.py runfcgi host=localhost port=9191 method=threaded pidfile=$DJANGO_PID

