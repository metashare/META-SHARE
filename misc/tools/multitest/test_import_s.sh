#!/bin/bash

MSERV_DIR=$(dirname "$0")
. "${MSERV_DIR}/_meta_dir.sh"
. "${MSERV_DIR}/_python.sh"
. "${MSERV_DIR}/_node_info.sh"
. "${MSERV_DIR}/_sync.sh"


check_results()
{
	local CLIENT_NODE_NUM="$1" ; shift
	local SERVER_NODE_NUM="$1" ; shift
	local IMPORTS_FILE="$1" ; shift
	local REMOTE_DATA_FILE="$1" ; shift

	local CLIENT_NODE_NAME=`get_node_info $CLIENT_NODE_NUM NODE_NAME`
	local SERVER_NODE_NAME=`get_node_info $SERVER_NODE_NUM NODE_NAME`
	local ST1=`cat "$IMPORTS_FILE" | grep -e "--->" | sed -e "s/--->//"`
	echo "ST1 = $ST1"
	local RES_ID1=`echo $ST1 | sed -e "s/RESOURCE_ID://" | sed -e "s/;.*$//"`
	echo "RES_ID1 = $RES_ID1"
	local STO_ID1=`echo $ST1 | sed -e "s/.*STORAGE_IDENTIFIER://"`
	echo "STO_ID1 = $STO_ID1"
	local RES=`cat "$REMOTE_DATA_FILE" | grep -e "STORAGE_IDENTIFIER:$STO_ID1" | wc -l`
	echo "RES = $RES"
	if [[ "$RES" == "1" ]] ; then
		echo "Update received"
	else
		echo "Update not received"
	fi
	local CLIENT_STO_DIR="$TEST_DIR/$CLIENT_NODE_NAME/storageFolder/$STO_ID1"
	local CLIENT_JSON="$CLIENT_STO_DIR/storage-local.json"
	local SERVER_STO_DIR="$TEST_DIR/$SERVER_NODE_NAME/storageFolder/$STO_ID1"
	local SERVER_JSON="$SERVER_STO_DIR/storage-local.json"
	echo "Checking if $CLIENT_STO_DIR is present"
	if [[ -d "$CLIENT_STO_DIR" ]] ; then 
		if [[ -f "$SERVER_JSON" ]] ; then
			if [[ -f "$CLIENT_JSON" ]] ; then
				# Extract the value of "digest_checksum"
				local CLIENT_DIG=`get_digest "$CLIENT_JSON"`
				local SERVER_DIG=`get_digest "$SERVER_JSON"`
				if [[ "$CLIENT_DIG" == "$SERVER_DIG" ]] ; then
					echo "Synchronization successful"
				else
					echo "Synchronization failed: checksums differ" >&3
					echo "Synchronization failed: checksums differ" >&2
					echo "   Checksum on node $SERVER_NODE_NAME is $SERVER_DIG" >&2
					echo "   Checksum on node $CLIENT_NODE_NAME is $CLIENT_DIG" >&2
					exit 1
				fi
			else
				echo "Synchronization failed: missing $CLIENT_JSON" >&3
				echo "Synchronization failed: missing $CLIENT_JSON" >&2
				exit 1
			fi
		else
			echo "Synchronization failed: missing $SERVER_JSON" >&3
			echo "Synchronization failed: missing $SERVER_JSON" >&2
			exit 1
		fi
	else
		echo "Synchronization failed: missing storage directory $CLIENT_STO_DIR" >&3
		echo "Synchronization failed: missing storage directory $CLIENT_STO_DIR" >&2
		exit 1
        fi
}

CURRENT_DIR=`pwd`


SERVER_NODE_NUM="$1" ; shift
CLIENT_NODE_NUM="$1" ; shift
RES_FILE="$1" ; shift

SERVER_NODE_NAME=`get_node_info $SERVER_NODE_NUM NODE_NAME`
SERVER_NODE_DIR="$TEST_DIR/$SERVER_NODE_NAME"
IMPORTS_FILE="$SERVER_NODE_DIR/imports.txt"
echo "Node name is " $SERVER_NODE_NAME
echo "Starting import..."
import_file_on_node $SERVER_NODE_NUM "$RES_FILE" "$IMPORTS_FILE"
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Error in importing file $RES_FILE" >&3
	exit 1
fi

CLIENT_NODE_NAME=`get_node_info $CLIENT_NODE_NUM NODE_NAME`
CLIENT_NODE_DIR="$TEST_DIR/$CLIENT_NODE_NAME"
REMOTE_ID_FILE="$CLIENT_NODE_DIR/remote_data.txt"
synchronize_node_idf $CLIENT_NODE_NUM "$REMOTE_ID_FILE"
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Error in synchronization procedure" >&3
	exit 1
fi


check_results $CLIENT_NODE_NUM $SERVER_NODE_NUM "$IMPORTS_FILE" "$REMOTE_ID_FILE"
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	exit 1
fi

