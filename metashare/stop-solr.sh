#!/bin/bash

export METASHAREDIR=$(dirname "$0")
export SOLR_ROOT=$(cd "$METASHAREDIR/../solr" ; pwd)
export SOLR_STOP_PORT=8079
export SOLR_STOP_KEY=stopkey

echo "Trying to stop SOLR server"

# Stop SOLR search index
java -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY="$SOLR_STOP_KEY" -jar "$SOLR_ROOT/start.jar" --stop


