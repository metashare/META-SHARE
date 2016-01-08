#!/bin/bash

export METASHARETOPDIR=$(readlink -f $(dirname "$0")/..)
export METASHAREDIR=$(dirname "$0")
export SOLR_ROOT=$(cd "$METASHAREDIR/../solr" ; pwd)
export SOLR_LOG=$SOLR_ROOT/solr.log
export SOLR_PORT=8983
export SOLR_STOP_PORT=8079
export SOLR_STOP_KEY=stopkey

export MAINSCHEMAFILE=$SOLR_ROOT/solr/main/conf/schema.xml
export TESTINGSCHEMAFILE=$SOLR_ROOT/solr/testing/conf/schema.xml

# If any solr server is currently running, stop it first:
echo "Checking for a previous running SOLR server..."
"$METASHAREDIR/stop-solr.sh"

sleep 5

# Update schema.xml files, just in case:
source "${METASHAREDIR}/../venv/bin/activate"

python "$METASHARETOPDIR/manage.py" build_solr_schema --filename="$MAINSCHEMAFILE"

deactivate

cp "$MAINSCHEMAFILE" "$TESTINGSCHEMAFILE"

echo "Trying to start SOLR server"

# Actually start solr
(cd "$SOLR_ROOT"
nohup java -Djetty.port=$SOLR_PORT -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY="$SOLR_STOP_KEY" -jar start.jar > "$SOLR_LOG" 2>&1 &
)


