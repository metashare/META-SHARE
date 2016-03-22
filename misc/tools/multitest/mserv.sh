#!/bin/bash

# Include environment variables and utility functions
MSERV_DIR=$(dirname "$0")
. "${MSERV_DIR}/_meta_dir.sh"
. "${MSERV_DIR}/_python.sh"
. "${MSERV_DIR}/_solr.sh"
. "${MSERV_DIR}/_node_info.sh"
. "${MSERV_DIR}/_django.sh"



CURRENT_DIR=`pwd`
if [[ "$TEST_DIR" == "" ]] ; then
	export TEST_DIR=$CURRENT_DIR/test_dir
fi

RESULT=0

counter=0

DET_FILE=""
OP=$1
if [[ "$OP" == "--det-file" ]] ; then
	shift
	DET_FILE="$1"
	shift
fi

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

	# Copy settings.py and local_settings.sample
	$MSERV_DIR/create_settings_files.sh

	if [[ "$CREATE_DB" == "1" ]] ; then
		# Create a new empty database compatible with the models.py
		$MSERV_DIR/create_db.sh -r
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot create empty DB" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
	fi
        
	if [[ "$CREATE_SOLR_SCHEMA" == "1" ]] ; then
		# Create a new SOLR schema compatible with the models.py
		$MSERV_DIR/create_solr_schema.sh
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot create SOLR schema" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
	fi
	# Replace the original settings.py with one that imports 
	# local_settings for each specific node
	cp $MSERV_DIR/init_data/settings_multitest.py $METASHARE_DIR/settings.py
	ret_val=$?
	if [[ $ret_val -ne 0 ]] ; then
		if [[ "$DET_FILE" != "" ]] ; then
			echo -n "Cannot copy settings.py" >> "$DET_FILE"
		fi
		exit $ret_val
	fi
	sync
fi

# Loop until get_node_cfg returns an error
while get_node_info $counter NODE_NAME &> /dev/null ; do
	NODE_NAME=`get_node_info $counter NODE_NAME`
	NODE_DIR="$TEST_DIR/$NODE_NAME"
	echo "Processing " $NODE_NAME
	# Create a directory for Node
	NODE_SETTINGS_DIR=$NODE_DIR/dj_settings
	#cd "$TEST_DIR"
	if [[ "$OP" == "start" ]] ; then
		mkdir -p "$TEST_DIR/$NODE_NAME"
		mkdir -p "$TEST_DIR/$NODE_SETTINGS_DIR"
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot create directories for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
	fi

	# Copy the solr empty tree
	if [[ "$OP" == "start" ]] ; then
		cp -R "$SOLR_DIR/solr" "$TEST_DIR/$NODE_NAME"
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot copy SOLR files for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
	fi

	SOLR_ROOT=$TEST_DIR/$NODE_NAME/solr
	SOLR_LOG=$SOLR_ROOT/solr.log
	SOLR_PORT=`get_node_info $counter SOLR_PORT`
	SOLR_STOP_PORT=`get_node_info $counter SOLR_STOP_PORT`
	SOLR_STOP_KEY=`get_node_info $counter SOLR_STOP_KEY`

	if [[ "$OP" == "start" ]] ; then
		init_solr "$SOLR_ROOT"
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot init SOLR for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
	
		# Start the Solr server for Node
		start_solr "$NODE_NAME" "$NODE_DIR" $SOLR_PORT $SOLR_STOP_PORT "$SOLR_STOP_KEY" "$SOLR_LOG"
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot start SOLR for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
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
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot create Django local settings for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi

		# run syncdb on the new node to create all synchronization user accounts
		run_syncdb "$NODE_NAME" "$DATABASE_NAME"
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot create synchronization users for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi

		# Start Django application
		start_django "$NODE_NAME" $DJANGO_PORT
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot start Django for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi

	elif [[ "$OP" == "stop" ]] ; then
		stop_django "$NODE_NAME"
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot stop Django for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
		stop_solr "$NODE_NAME" $SOLR_PORT $SOLR_STOP_PORT "$SOLR_STOP_KEY" "$SOLR_LOG"
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot stop SOLR for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
	else
		# Restore the original settings.py
		cp $MSERV_DIR/init_data/settings_original.py $METASHARE_DIR/settings.py
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot restore settings.py" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
		rm -r "$TEST_DIR/$NODE_NAME"
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			if [[ "$DET_FILE" != "" ]] ; then
				echo -n "Cannot remove directory for node $NODE_NAME" >> "$DET_FILE"
			fi
			exit $ret_val
		fi
	fi

	cd "$CURRENT_DIR"
	let counter=counter+1
done

exit 0
