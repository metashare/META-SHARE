#!/bin/bash

export METASHAREDIR=$(dirname "$0")
export SOLR_ROOT=$(cd "$METASHAREDIR/../solr" ; pwd)
export SOLR_LOG=$SOLR_ROOT/solr.log
export SOLR_STOP_PORT=8079
export SOLR_STOP_KEY=stopkey

export MAINSCHEMAFILE=$SOLR_ROOT/solr/main/conf/schema.xml
export TESTINGSCHEMAFILE=$SOLR_ROOT/solr/testing/conf/schema.xml

# If any solr server is currently running, stop it first:
echo "Checking for a previous running SOLR server..."
"$METASHAREDIR/stop-solr.sh"


# Update schema.xml files, just in case:
python $METASHAREDIR/manage.py build_solr_schema --filename="$MAINSCHEMAFILE"
cp "$MAINSCHEMAFILE" "$TESTINGSCHEMAFILE" 

echo "Trying to start SOLR server"

# Actually start solr
(cd "$SOLR_ROOT"
nohup java -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY="$SOLR_STOP_KEY" -jar start.jar > "$SOLR_LOG" &
)


