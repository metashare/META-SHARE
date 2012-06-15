#!/bin/bash


import_data()
{
	echo "Importing data"
	echo '$METASHARE_DIR =' $METASHARE_DIR
	cd "$METASHARE_DIR"
	"$PYTHON" import_xml.py "$RES_FILE"
}

test_sync()
{
	"$PYTHON" test_sync.py
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
#test_sync

