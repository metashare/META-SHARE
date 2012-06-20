#!/bin/bash

# Import several files in each node of the inner circle.
# Trigger synchronization on each node.
# Then verify that every published resource from each master node
# has been copied to every other node.
# Also verify that non-published resource are not copied to other nodes.

import_file_on_node()
{
	NODE_NUM="$1"
	IMP_FILE="$2"
	NODE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NODE_NUM NODE_NAME`
	IMPORTS_LOG=$TEST_DIR/imp.log
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	echo "Import file $IMP_FILE on node $NODE_NAME"
	cd "$METASHARE_DIR"
	"$PYTHON" import_xml.py "$IMP_FILE" > $IMPORTS_LOG
	cd "$CURRENT_DIR"
}

synchronize_node()
{
	NODE_NUM="$1"
	REMOTE_DATA_FILE=$TEST_DIR/rem.log
	NODE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NODE_NUM NODE_NAME`
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	echo "Synchronizing $NODE_NAME"
	cd "$METASHARE_DIR"
	"$PYTHON" manage.py synchronize > $REMOTE_DATA_FILE
	cd "$CURRENT_DIR"
}

get_node_resource_list()
{
	NODE_NUM="$1"
	NODE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NODE_NUM NODE_NAME`
	#echo "NODE_NUM = $NODE_NUM , NODE_NAME = $NODE_NAME"
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	#echo "Get resource list for node $NODE_NAME"
	cd "$METASHARE_DIR"
	"$PYTHON" manage.py get_resource_list | sort
	cd "$CURRENT_DIR"
}

get_digest()
{
	FILENAME="$1"
	DIG=`get_key_value "$FILENAME" digest_checksum`
	echo $DIG
}

get_publ_status()
{
	FILENAME="$1"
	PUB_ST=`get_key_value "$FILENAME" publication_status`
	echo $PUB_ST
}

get_key_value()
{
	FILENAME="$1"
	KEY="$2"
	VAL=`cat "$FILENAME" | sed -e "s/\(.*\)\(\"$KEY\":\)\(\"\)\([a-z0-9]*\)\(\"\)\(.*\)/\4/"`
	echo $VAL
}

# The following function performs the check by using
# the folders in the storageFolder.
# It seems to not work appropriately: maybe if a resource
# is imported more than once it uses a new storage directory
# and the old one is not deleted.
# Needs more checking.
check_resources()
{
	echo "Checking that all nodes contain the same set of published resources"
	echo " and the corresponding resources have the same digest"
	for NODE_NUM in $NODES
	do
		NODE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NODE_NUM NODE_NAME`
		echo "Get list of resources from node $NODE_NAME"
		DIR=$TEST_DIR/$NODE_NAME/storageFolder
		ls "$DIR" | while read LINE
		do
			echo "--> " $LINE
			G_JSON=$DIR/$LINE/storage-global.json
			L_JSON=$DIR/$LINE/storage-local.json
			DIG=`get_digest "$L_JSON"`
			PUB_ST=`get_publ_status "$G_JSON"`
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
	echo "Checking that all nodes contain the same set of published resources"
	echo " and the corresponding resources have the same digest"
	CHECK_OK=1
	PREVIOUS_RES=""
	for NODE_NUM in $NODES
	do
		NODE_NAME=`"$PYTHON" "$CURRENT_DIR/get_node_cfg.py" $NODE_NUM NODE_NAME`
		RES_FILE=$TEST_DIR/stat-$NODE_NAME.res
		get_node_resource_list $NODE_NUM > "$RES_FILE"
		if [[ "$PREVIOUS_RES" != "" ]] ; then
			C=`diff "$RES_FILE" "$PREVIOUS_RES" | wc -l`
			if [[ "$C" != "0" ]] ; then
				CHECK_OK=0
			fi
		fi
		PREVIOUS_RES=$RES_FILE
	done
	if [[ "$CHECK_OK" == "1" ]] ; then
		echo "Synchronization successful"
	else
		echo "Synchronization failed"
	fi
}


CURRENT_DIR=`pwd`
METASHARE_DIR=$METASHARE_SW_DIR/metashare
RES_DIR="$METASHARE_SW_DIR/misc/testdata/v2.1"

# find the best Python binary to use: only use the platform default if ther is
# no custom Python installation for META-SHARE available
if [ -x "$METASHARE_SW_DIR/opt/bin/python" ] ; then
	PYTHON="$METASHARE_SW_DIR/opt/bin/python"
else
	PYTHON=`which python`
fi

DO_IMPORT_FILES=1
DO_SYNCHRONIZE=1
DO_CHECK_RESOURCES=1

if [[ $DO_IMPORT_FILES -eq 1 ]] ; then
  NODE_NUMBER=0

  RES_FILE="$RES_DIR/ELRAResources/elra20.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/ELRAResources/elra30.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/ELRAResources/elra40.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"


  NODE_NUMBER=1

  RES_FILE="$RES_DIR/ELRAResources/elra21.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/ELRAResources/elra31.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/ELRAResources/elra41.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/ELRAResources/elra51.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/ELRAResources/elra61.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"


  NODE_NUMBER=3

  RES_FILE="$RES_DIR/METASHAREResources/ILSP/ILSP12.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/METASHAREResources/ILSP/ILSP16.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/METASHAREResources/ILSP/ILSP18.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

  RES_FILE="$RES_DIR/METASHAREResources/ILSP/ILSP25.xml"
  import_file_on_node $NODE_NUMBER "$RES_FILE"

fi

if [[ $DO_SYNCHRONIZE -eq 1 ]] ; then
  synchronize_node 0

  synchronize_node 1

  synchronize_node 3
fi


if [[ $DO_CHECK_RESOURCES -eq 1 ]] ; then
  NODES="0 1 3"
  check_resources_2 $NODES
fi

