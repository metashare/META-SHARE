#!/bin/bash


import_data()
{
	echo "Importing data"
	echo '$METASHARE_DIR =' $METASHARE_DIR
	cd "$METASHARE_DIR"
	IMPORTS_FILE="$NODE_DIR/imports.txt"
	# The output of import_xml should contain lines with 
	# storage identifier of imported resources.
	"$PYTHON" import_xml.py "$RES_FILE" > $IMPORTS_FILE
}

synchronize()
{
	CLIENT_NODE_NAME="$1"
	export NODE_DIR="$TEST_DIR/$CLIENT_NODE_NAME"
	cd "$METASHARE_DIR"
	echo "NODE_DIR = $NODE_DIR"
	echo "Synchronizing ..."
	REMOTE_DATA_FILE="$NODE_DIR/remote_data.txt"
	# The output of synchronize should contain lines with
	# storage identifier of new/udpated resources
	"$PYTHON" manage.py synchronize > $REMOTE_DATA_FILE
	cd "$CURRENT_DIR"
}

check_results()
{
	ST1=`cat "$IMPORTS_FILE" | grep -e "--->" | sed -e "s/--->//"`
	echo "ST1 = $ST1"
	RES_ID1=`echo $ST1 | sed -e "s/RESOURCE_ID://" | sed -e "s/;.*$//"`
	echo "RES_ID1 = $RES_ID1"
	STO_ID1=`echo $ST1 | sed -e "s/.*STORAGE_IDENTIFIER://"`
	echo "STO_ID1 = $STO_ID1"
	RES=`cat "$REMOTE_DATA_FILE" | grep -e "STORAGE_IDENTIFIER:$STO_ID1" | wc -l`
	echo "RES = $RES"
	if [[ "$RES" == "1" ]] ; then
		echo "Update received"
	else
		echo "Update not received"
	fi
	CLIENT_STO_DIR="$TEST_DIR/$CLIENT_NODE_NAME/storageFolder/$STO_ID1"
	CLIENT_JSON="$CLIENT_STO_DIR/storage-local.json"
	SERVER_STO_DIR="$TEST_DIR/$SERVER_NODE_NAME/storageFolder/$STO_ID1"
	SERVER_JSON="$SERVER_STO_DIR/storage-local.json"
	echo "Checking if $CLIENT_STO_DIR is present"
	if [[ -d "$CLIENT_STO_DIR" ]] ; then 
		if [[ -f "$SERVER_JSON" ]] ; then
			if [[ -f "$CLIENT_JSON" ]] ; then
				# Extract the value of "digest_checksum"
				CLIENT_DIG=`cat "$CLIENT_JSON" | sed -e "s/\(.*\)\(\"digest_checksum\":\)\(\"\)\([a-z0-9]*\)\(\"\)\(.*\)/\4/"`
				SERVER_DIG=`cat "$SERVER_JSON" | sed -e "s/\(.*\)\(\"digest_checksum\":\)\(\"\)\([a-z0-9]*\)\(\"\)\(.*\)/\4/"`
				if [[ "$CLIENT_DIG" -eq "$SERVER_DIG" ]] ; then
					echo "Synchronization successful"
				else
					echo "Synchronization failed: checksums differ"
				fi
			else
				echo "Synchronization failed: missing $CLIENT_JSON"
			fi
		else
			echo "Synchronization failed: missing $SERVER_JSON"
		fi
	else
		echo "Synchronization failed: missing storage directory $CLIENT_STO_DIR"
        fi
}

# Check it the environment variable is set and points
# to a valid directory
if [[ "$METASHARE_SW_DIR" == "" ]] ; then
	echo "The environment variable METASHARE_SW_DIR must be defined"
	echo "and contain the directory with Metashare software."
	exit 1
fi

# Remove trailing slash if present
METASHARE_SW_DIR=`echo $METASHARE_SW_DIR | sed -e "s/\/$//"`

# Verify METASHARE_SW_DIR is a valid directory
if [ ! -d "$METASHARE_SW_DIR" ] ; then
	echo $METASHARE_SW_DIR " is not a valid directory."
	exit 1
fi

# find the best Python binary to use: only use the platform default if ther is
# no custom Python installation for META-SHARE available
if [ -x "$METASHARE_SW_DIR/opt/bin/python" ] ; then
	PYTHON="$METASHARE_SW_DIR/opt/bin/python"
else
	PYTHON=`which python`
fi

CURRENT_DIR=`pwd`
export METASHARE_DIR="$METASHARE_SW_DIR/metashare"
if [[ "$TEST_DIR" == "" ]] ; then
	export TEST_DIR=$CURRENT_DIR/test_dir
fi

NUM=1
NODE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NUM NODE_NAME`
echo "Node name is " $NODE_NAME
export DJANGO_PORT=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NUM DJANGO_PORT`
export STORAGE_PATH=$TEST_DIR/$NODE_NAME/storageFolder
DATABASE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NUM DATABASE_NAME`
export DATABASE_FILE=$TEST_DIR/$NODE_NAME/$DATABASE_NAME
echo "DATABASE_NAME = " $DATABASE_NAME
export SOLR_PORT=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NUM SOLR_PORT`
echo "SOLR_PORT = " $SOLR_PORT
RES_FILE="$METASHARE_SW_DIR/misc/testdata/v2.1/ELRAResources/elra20.xml"
export NODE_DIR=$TEST_DIR/$NODE_NAME
echo "Starting import..."
import_data

SERVER_NODE_NUM=$NUM
CLIENT_NODE_NUM=3
CLIENT_NODE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $CLIENT_NODE_NUM NODE_NAME`
SERVER_NODE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $SERVER_NODE_NUM NODE_NAME`
synchronize $CLIENT_NODE_NAME

check_results

