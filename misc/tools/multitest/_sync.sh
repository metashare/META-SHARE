#!/bin/bash

# Env vars required:
# - METASHARE_DIR
# - TEST_DIR
# - PYTHON

get_node_count()
{
	local NODE_COUNT=`$PYTHON "$MSERV_DIR/get_node_count.py"`
	echo $NODE_COUNT
}

import_file_on_node()
{
	local NODE_NUM="$1" ; shift
	local IMP_FILE="$1" ; shift
	local ID_FILE="$1" ; shift

	local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
	local IMPORTS_LOG=$TEST_DIR/imp.log
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	local ret_val
	echo "Import file $IMP_FILE on node $NODE_NAME"
	#cd "$METASHARE_DIR"
	if [[ "$ID_FILE" == "" ]] ; then
		$PYTHON metashare/import_xml.py "$IMP_FILE" > "$IMPORTS_LOG"
		ret_val=$?
	else
		$PYTHON metashare/import_xml.py --id-file="$ID_FILE" "$IMP_FILE" > "$IMPORTS_LOG"
		ret_val=$?
	fi
	rm -f "$IMPORTS_LOG"
	#cd "$CURRENT_DIR"
	return $ret_val
}

import_fileset_on_node()
{
	local NODE_NUM="$1" ; shift
	local FSET_NAME="$1" ; shift

	get_fileset $FSET_NAME $NODE_NUM | while read LINE
	do
		import_file_on_node $NODE_NUM "$LINE"
	done
}

# The import_files accept a parameter 'type' that can have the following values:
#   inner : import files only on META-SHARE Managing Nodes (aka. inner nodes)
#   outer : import files only on normal META-SHARE Nodes (aka. outer nodes)
#   all (default): import files on all nodes
import_files()
{
	local FSET_NAME="$1" ; shift
	local TARGET_TYPE="${1:-all}"

	local NODE_COUNT=`get_node_count`
	echo "Importing files on $TARGET_TYPE nodes"
	for (( j=0; j<$NODE_COUNT; j++ ))
	do
		local DO_IMPORT=0
		if [[ "$TARGET_TYPE" == "all" ]] ; then
			DO_IMPORT=1
		else
			local NODE_TYPE=`get_node_info $j NODE_TYPE`
			if [[ "$NODE_TYPE" == "$TARGET_TYPE" ]] ; then
				DO_IMPORT=1
			fi
		fi
		if [[ $DO_IMPORT -eq 1 ]] ; then
			import_fileset_on_node $j "${FSET_NAME}"
		fi
	done
}

synchronize_node()
{
	local NODE_NUM="$1"

	local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
	local REMOTE_DATA_FILE=$TEST_DIR/rem_$NODE_NAME
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	echo "Synchronizing $NODE_NAME"
	#cd "$METASHARE_DIR"
	$PYTHON manage.py synchronize > "$REMOTE_DATA_FILE"
	local ret_val=$?
	if [[ $ret_val -ne 0 ]] ; then
		echo -n "Error in synchronizing $NODE_NAME" >&3
		return $ret_val
	fi
	rm -f "$REMOTE_DATA_FILE"
	local ret_val=$?
	#cd "$CURRENT_DIR"
	return $ret_val
}

synchronize_node_idf()
{
	local NODE_NUM="$1" ; shift
	local ID_FILE="$1" ; shift

	local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
	local REMOTE_DATA_FILE=$TEST_DIR/$NODE_NAME/rem.log
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	echo "Synchronizing $NODE_NAME"
	#cd "$METASHARE_DIR"
	$PYTHON manage.py synchronize --id-file=$ID_FILE > $REMOTE_DATA_FILE
	local ret_val=$?
	#cd "$CURRENT_DIR"
	return $ret_val
}

synchronize_nodes()
{
	local NODE_COUNT=`get_node_count`
	local ret_val=0
	local last_ret_val
	for (( j=0; j<$NODE_COUNT; j++ ))
	do
		synchronize_node $j
		last_ret_val=$?
		if [[ $ret_val -eq 0 ]] ; then
			ret_val=$last_ret_val
		fi
	done
	return $ret_val
}

get_node_resource_list()
{
	local NODE_NUM="$1" ; shift
	local EXT="$1" ; shift

	local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
	#echo "NODE_NUM = $NODE_NUM , NODE_NAME = $NODE_NAME"
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	#echo "Get resource list for node $NODE_NAME"
	local EXTRA_INFO=""
	if [ "$EXT" == "ext" ] ; then
		EXTRA_INFO="--extended"
	fi
	#cd "$METASHARE_DIR"
	$PYTHON manage.py get_resource_list "$EXTRA_INFO" | sort
	#cd "$CURRENT_DIR"
}

get_digest()
{
	local FILENAME="$1"

	local DIG=`get_key_value "$FILENAME" digest_checksum`
	echo $DIG
}

get_publ_status()
{
	local FILENAME="$1"

	local PUB_ST=`get_key_value "$FILENAME" publication_status`
	echo $PUB_ST
}

get_key_value()
{
	local FILENAME="$1"

	local KEY="$2"
	local VAL=`cat "$FILENAME" | sed -e "s/\(.*\)\(\"$KEY\":\)\(\"\)\([a-z0-9]*\)\(\"\)\(.*\)/\4/"`
	echo $VAL
}

update_digests_on_node()
{
	local NODE_NUM="$1"

	local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	echo "Updating digests on node $NODE_NAME"
	#cd "$METASHARE_DIR"
	$PYTHON manage.py update_digests
	local ret_val=$?
	#cd "$CURRENT_DIR"
	return $ret_val
}

update_digests()
{
	local NODE_COUNT=`get_node_count`

	for (( j=0; j<$NODE_COUNT; j++ ))
	do
		update_digests_on_node $j
	done
}

# The following function performs the check by using
# the folders in the storageFolder.
# It seems to not work appropriately: maybe if a resource
# is imported more than once it uses a new storage directory
# and the old one is not deleted.
# Needs more checking.
check_resources()
{
	local NODES="$1" ; shift

	echo "Checking that all nodes contain the same set of published resources"
	echo " and the corresponding resources have the same digest"
	for NODE_NUM in $NODES
	do
		local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
		echo "Get list of resources from node $NODE_NAME"
		local DIR=$TEST_DIR/$NODE_NAME/storageFolder
		ls "$DIR" | while read LINE
		do
			echo "--> " $LINE
			local G_JSON=$DIR/$LINE/storage-global.json
			local L_JSON=$DIR/$LINE/storage-local.json
			local DIG=`get_digest "$L_JSON"`
			local PUB_ST=`get_publ_status "$G_JSON"`
			echo " pub status = $PUB_ST"
			echo " digest = $DIG"
			if [[ "$PUB_ST" == "p" ]] ; then
				echo "$LINE:$DIG" >> $TEST_DIR/stat-$NODE_NAME.res
			fi
		done
	done
}

# This function gets the list of resource for a given node
# by querying the database and listing all the
# published resources.
check_resources_2()
{
	local NODES="$1" ; shift

	echo "Checking that all nodes contain the same set of published resources"
	echo " and the corresponding resources have the same digest"
	local CHECK_OK=1
	local PREVIOUS_RES=""
	local PREVIOUS_NODE_NAME=""
	local RES_DETAILS=$TEST_DIR/res-details.log
	touch "$RES_DETAILS"
	for NODE_NUM in $NODES
	do
		local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
		local RES_FILE=$TEST_DIR/stat-$NODE_NAME.res
		get_node_resource_list $NODE_NUM "ext" > "$RES_FILE"
		echo "Resources on node $NODE_NAME: (id:digest:source_url)" >> "$RES_DETAILS"
		cat "$RES_FILE" >> "$RES_DETAILS"
		get_node_resource_list $NODE_NUM > "$RES_FILE"
		if [[ "$PREVIOUS_RES" != "" ]] ; then
			echo "Comparing $RES_FILE and $PREVIOUS_RES."
			C=`diff "$RES_FILE" "$PREVIOUS_RES" | wc -l`
			if [[ "$C" != "0" ]] ; then
				echo "FAILED"
				CHECK_OK=0
				echo "Resource list for node $NODE_NAME:"
				cat "$RES_FILE"
				echo "Resource list for node $PREVIOUS_NODE_NAME:"
				cat "$PREVIOUS_RES"
			fi
		fi
		rm -f "$PREVIOUS_RES"
		PREVIOUS_RES=$RES_FILE
		PREVIOUS_NODE_NAME=$NODE_NAME
	done
	rm -f $PREVIOUS_RES
	if [[ "$CHECK_OK" == "1" ]] ; then
		echo "Synchronization successful"
		rm -f "$RES_DETAILS"
	else
		echo "Synchronization failed"
		echo -n "Synchronization failed" >&3
		echo "Dumping details"
		cat "$RES_DETAILS"
		rm -f "$RES_DETAILS"
		return 1
	fi
}

check_resources_on_inner_nodes()
{
	local NODE_COUNT=`get_node_count`
	local NODES=""
	for (( j=0; j<$NODE_COUNT; j++ ))
	do
		local NODE_TYPE=`get_node_info $j NODE_TYPE`
		if [[ "$NODE_TYPE" == "inner" ]] ; then
			NODES="$NODES $j"
		fi
	done
	echo "Checking resources on nodes $NODES"
	check_resources_2 "$NODES"
	local ret_val=$?
	return $ret_val
}

