
# Functions to start and stop SOLR server
#
# Env vars required:
#  - METASHARE_SW_DIR
#  - MSERV_DIR
#  - PYTHON
#  


init_solr()
{
	local SOLR_ROOT="$1" ; shift

	# Copy schema files
	local MAIN_SCHEMA_FILE="$SOLR_ROOT/main/conf/schema.xml"
	local TESTING_SCHEMA_FILE="$SOLR_ROOT/testing/conf/schema.xml"
	local METASHARE_DIR=$METASHARE_SW_DIR/metashare
	cd "$METASHARE_DIR"
	%PYTHON% manage.py build_solr_schema --filename="$MAIN_SCHEMA_FILE"
	cp "$MAIN_SCHEMA_FILE" "$TESTING_SCHEMA_FILE"
}

start_solr()
{
	local SOLR_ROOT="$1" ; shift
	local SOLR_PORT="$1" ; shift
	local SOLR_STOP_PORT="$1" ; shift
	local SOLR_STOP_KEY="$1" ; shift
	local SOLR_LOG="$1" ; shift

	echo "Starting Solr server"
	local SOLR_DIR=$SOLR_ROOT/solr
	cd "$SOLR_ROOT"
	java -Djetty.port=$SOLR_PORT -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY=$SOLR_STOP_KEY "-Dsolr.solr.home=$SOLR_DIR" -jar start.jar &> "$SOLR_LOG" &
	cd $CURRENT_DIR
}

stop_solr()
{
	local SOLR_ROOT="$1" ; shift
	local SOLR_PORT="$1" ; shift
	local SOLR_STOP_PORT="$1" ; shift
	local SOLR_STOP_KEY="$1" ; shift
	local SOLR_LOG="$1" ; shift

	echo "Stopping Solr server"
	local SOLR_DIR=$SOLR_ROOT/solr
	cd "$SOLR_ROOT"
	nohup java -Djetty.port=$SOLR_PORT -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY=$SOLR_STOP_KEY -jar start.jar --stop &> $SOLR_LOG &
	cd $CURRENT_DIR
}

