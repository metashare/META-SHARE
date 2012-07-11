#!/bin/bash

. _meta_dir.sh
. _python.sh
. _node_info.sh
. _sync.sh


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

MARK_DEL_SCR="$MSERV_DIR/mark_deleted.py"
delete_res_on_node()
{
	local NODE_NUM="$1" ; shift
	local RES_ID="$1" ; shift

	local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
	NODE_DIR="$TEST_DIR/$NODE_NAME"
	export NODE_DIR=$NODE_DIR
	PYTHON_CMD="execfile(\"$MARK_DEL_SCR\")"
	echo "NODE_DIR = $NODE_DIR"
	echo "PYTHON = $PYTHON"
	echo "PYTHON_CMD = '$PYTHON_CMD'"
	echo "RES_ID = $RES_ID"
	cd "$METASHARE_DIR"
	pwd
	echo "$PYTHON_CMD" | "$PYTHON" manage.py shell 1>/dev/null 2>/dev/null 5>"$RES_ID"
	local ret_val=$?
	return $ret_val
}

CHECK_DEL_SCR="$MSERV_DIR/check_res_deleted.py"
check_resource_deleted()
{
	local NODE_NUM="$1" ; shift
	local RES_ID="$1" ; shift

	local NODE_NAME=`get_node_info $NODE_NUM NODE_NAME`
	NODE_DIR="$TEST_DIR/$NODE_NAME"
	export NODE_DIR
	local IDENT=`cat "$RES_ID"`
	cd "$METASHARE_DIR"
	PYTHON_CMD="res_id=\"$IDENT\"; execfile(\"$CHECK_DEL_SCR\")"
	echo "$PYTHON_CMD" | "$PYTHON" manage.py shell 1>/dev/null 2>/dev/null
	local ret_val=$?
	return $ret_val
}

CURRENT_DIR=`pwd`


SERVER_NODE_NUM="$1" ; shift
CLIENT_NODE_NUM="$1" ; shift
RES_FILE="$1" ; shift

SERVER_NODE_NAME=`get_node_info $SERVER_NODE_NUM NODE_NAME`
SERVER_NODE_DIR="$TEST_DIR/$SERVER_NODE_NAME"
IMPORTS_FILE="$SERVER_NODE_DIR/imports.txt"
echo "Node name is " $SERVER_NODE_NAME
echo "Marking resource as deleted ..."
RES_ID="$NODE_DIR/rse_id.log"
echo "RES_ID = $RES_ID"

delete_res_on_node $SERVER_NODE_NUM "$RES_ID"
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Error in marking resource as deleted" >&3
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


check_resource_deleted $CLIENT_NODE_NUM "$RES_ID"
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Resource has not been deleted"
	exit 1
fi

