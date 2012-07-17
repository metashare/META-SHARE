
# Functions to start and stop SOLR server
#
# Env vars required:
#  - METASHARE_SW_DIR
#  - MSERV_DIR
#  

SOLR_DIR="$METASHARE_SW_DIR/solr"

init_solr()
{
	local SOLR_ROOT="$1"

	# Copy schema files
	local MAIN_SCHEMA_FILE="$SOLR_ROOT/main/conf/schema.xml"
	local TESTING_SCHEMA_FILE="$SOLR_ROOT/testing/conf/schema.xml"
	local ret_val
	cp "$MSERV_DIR/init_data/schema.xml" "$MAIN_SCHEMA_FILE"
	ret_val=$?
	if [[ $ret_val -ne 0 ]] ; then
		return $ret_val
	fi
	cp "$MSERV_DIR/init_data/schema.xml" "$TESTING_SCHEMA_FILE"
	ret_val=$?
	return $ret_val
}

start_solr()
{
	local NODE_NAME="$1" ; shift
	local NODE_DIR="$1" ; shift
	local SOLR_PORT="$1" ; shift
	local SOLR_STOP_PORT="$1" ; shift
	local SOLR_STOP_KEY="$1" ; shift
	local SOLR_LOG="$1" ; shift

	echo "Starting Solr server for node " $NODE_NAME
	local CURRENT_DIR=`pwd`
	cd "$METASHARE_SW_DIR/solr"
	java -Djetty.port=$SOLR_PORT -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY=$SOLR_STOP_KEY "-Dsolr.solr.home=$TEST_DIR/$NODE_NAME/solr" -jar start.jar &> "$SOLR_LOG" &
	ret_val=$?
	cd $CURRENT_DIR
	return $ret_val
}

stop_solr()
{
	local NODE_NAME="$1" ; shift
	local SOLR_PORT="$1" ; shift
	local SOLR_STOP_PORT="$1" ; shift
	local SOLR_STOP_KEY="$1" ; shift
	local SOLR_LOG="$1" ; shift

	echo "Stopping Solr server for node " $NODE_NAME
	local CURRENT_DIR=`pwd`
	cd "$METASHARE_SW_DIR/solr"
	echo
	java -Djetty.port=$SOLR_PORT -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY=$SOLR_STOP_KEY -jar start.jar --stop &> $SOLR_LOG &
	cd $CURRENT_DIR
}

