#!/bin/bash

MSERV_DIR=$(dirname "$0")
. "${MSERV_DIR}/_meta_dir.sh"
. "${MSERV_DIR}/_python.sh"
. "${MSERV_DIR}/_node_info.sh"
. "${MSERV_DIR}/_sync.sh"


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
	#cd "$METASHARE_DIR"
	#pwd
        echo $PWD
	echo "$PYTHON_CMD" | $PYTHON manage.py shell 1>/dev/null 2>/dev/null 5>"$RES_ID"
        echo $PWD
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
	#cd "$METASHARE_DIR"
	PYTHON_CMD="res_id=\"$IDENT\"; execfile(\"$CHECK_DEL_SCR\")"
	echo "$PYTHON_CMD" | $PYTHON manage.py shell 1>/dev/null 2>/dev/null
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
RES_ID="$SERVER_NODE_DIR/res_id.log"
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

