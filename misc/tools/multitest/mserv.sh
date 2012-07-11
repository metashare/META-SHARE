#!/bin/bash

# Include environment variables and utility functions
. _meta_dir.sh
. _python.sh
. _solr.sh
. _node_info.sh
. _django.sh



CURRENT_DIR=`pwd`
if [[ "$TEST_DIR" == "" ]] ; then
	export TEST_DIR=$CURRENT_DIR/test_dir
fi

counter=0

CREATE_DB=1
OP=$1
if [[ "$OP" == "--nodb" ]] ; then
	CREATE_DB=0
	shift
fi

CREATE_SOLR_SCHEMA=1
OP=$1
if [[ "$OP" == "--noschema" ]] ; then
	CREATE_SOLR_SCHEMA=0
	shift
fi

OP=$1
if [[  "$OP" != "start" && "$OP" != "stop" && "$OP" != "clean" ]] ; then
	echo "usage: $0 [start|stop|clean]"
	exit 1
fi

if [[ "$OP" == "start" ]] ; then
	if [[ "$CREATE_DB" == "1" ]] ; then
		# Create a new empty database compatible with the models.py
		./create_db.sh -r
	fi

	if [[ "$CREATE_SOLR_SCHEMA" == "1" ]] ; then
		# Create a new SOLR schema compatible with the models.py
		./create_solr_schema.sh
	fi

	# Remove local_settings from metashare directory since it
	# may override the node specific one
	rm -f "$METASHARE_DIR/local_settings.py"
	rm -f "$METASHARE_DIR/local_settings.pyc"
	# Replace the original settings.py with one that imports 
	# local_settings for each specific node
	cp $MSERV_DIR/init_data/settings_test.py $METASHARE_DIR/settings.py
	sync
fi

# Loop until get_node_cfg returns an error
while get_node_info $counter NODE_NAME &> /dev/null ; do
	NODE_NAME=`get_node_info $counter NODE_NAME`
	NODE_DIR="$TEST_DIR/$NODE_NAME"
	echo "Processing " $NODE_NAME
	# Create a directory for Node
	NODE_SETTINGS_DIR=$NODE_DIR/dj_settings
	cd "$TEST_DIR"
	if [[ "$OP" == "start" ]] ; then
		mkdir "$NODE_NAME"
		mkdir "$NODE_SETTINGS_DIR"
	fi

	# Copy the solr empty tree
	if [[ "$OP" == "start" ]] ; then
		cp -R "$SOLR_DIR/solr" "$TEST_DIR/$NODE_NAME"
	fi

	SOLR_ROOT=$TEST_DIR/$NODE_NAME/solr
	SOLR_LOG=$SOLR_ROOT/solr.log
	SOLR_PORT=`get_node_info $counter SOLR_PORT`
	SOLR_STOP_PORT=`get_node_info $counter SOLR_STOP_PORT`
	SOLR_STOP_KEY=`get_node_info $counter SOLR_STOP_KEY`

	if [[ "$OP" == "start" ]] ; then
		init_solr "$SOLR_ROOT"
	
		# Start the Solr server for Node
		start_solr "$NODE_NAME" "$NODE_DIR" $SOLR_PORT $SOLR_STOP_PORT "$SOLR_STOP_KEY" "$SOLR_LOG"
		# Wait for Solr
		echo "Waiting for Solr to start and open connections ..."
		sleep 8
		# Copy an empty database
		DJANGO_PORT=`get_node_info $counter DJANGO_PORT`
		DATABASE_NAME=`get_node_info $counter DATABASE_NAME`
		DATABASE_FILE=$NODE_DIR/$DATABASE_NAME
		STORAGE_PATH=$TEST_DIR/$NODE_NAME/storageFolder
		mkdir "$STORAGE_PATH"

		CORE_NODES=`get_node_info $counter CORE_NODES`
		PROXIED_NODES=`get_node_info $counter PROXIED_NODES`
		SYNC_USERS=`get_node_info $counter SYNC_USERS`

		create_django_settings "$NODE_NAME" $SOLR_PORT \
			"$DATABASE_FILE" "$STORAGE_PATH" $DJANGO_PORT \
			"$CORE_NODES" "$PROXIED_NODES" "$SYNC_USERS"

		# run syncdb on the new node to create all synchronization user accounts
		run_syncdb "$NODE_NAME" "$DATABASE_NAME"

		# Start Django application
		start_django "$NODE_NAME" $DJANGO_PORT

	elif [[ "$OP" == "stop" ]] ; then
		stop_django "$NODE_NAME"
		stop_solr "$NODE_NAME" $SOLR_PORT $SOLR_STOP_PORT "$SOLR_STOP_KEY" "$SOLR_LOG"
	else
		rm -r "$NODE_NAME"
	fi

	cd "$CURRENT_DIR"
	let counter=counter+1
done

exit 0
