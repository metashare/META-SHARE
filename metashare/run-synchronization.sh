#!/bin/bash

PROJECT_ROOT=`cd $(dirname "$0"); pwd`
LOCKFILE="$PROJECT_ROOT/.synchronizing"

if [ -f $LOCKFILE ]; then
  if ps -p `cat -- $LOCKFILE` &> /dev/null; then
    echo "ERROR: The synchronization process is already running." >&2
    exit 1
  else
    rm -f -- $LOCKFILE
  fi
fi

echo $$ > $LOCKFILE
python2.7 $PROJECT_ROOT/manage.py runtask run_synchronization --settings=metashare.settings
rm $LOCKFILE
