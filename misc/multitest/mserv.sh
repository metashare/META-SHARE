#!/bin/bash

start_solr()
{
	echo "Starting Solr server for node " $NODE_NAME
	cd $METASHARE_DIR/../solr
	java -Djetty.port=$SOLR_PORT -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY=$SOLR_STOP_KEY -Dsolr.solr.home=$TEST_DIR/$NODE_NAME/solr -jar start.jar &> $SOLR_LOG &
	cd $CURRENT_DIR
}

stop_solr()
{
	echo "Stopping Solr server for node " $NODE_NAME
	cd $METASHARE_DIR/../solr
	echo
	java -Djetty.port=$SOLR_PORT -DSTOP.PORT=$SOLR_STOP_PORT -DSTOP.KEY=$SOLR_STOP_KEY -jar start.jar --stop &> $SOLR_LOG &
	cd $CURRENT_DIR
}

start_django()
{
	echo "Starting Django server"
	cd $METASHARE_DIR
	python manage.py runserver 0.0.0.0:$DJANGO_PORT --noreload &> $TEST_DIR/$NODE_NAME/metashare.log &
	echo $! > $DJANGO_PID
	cd $CURRENT_DIR
}

stop_django()
{
	echo "Stopping Django server"
	kill -9 `cat -- $DJANGO_PID`
	rm -f -- $DJANGO_PID
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

CURRENT_DIR=`pwd`
export METASHARE_DIR="$METASHARE_SW_DIR/metashare"
export TEST_DIR=$CURRENT_DIR/test_dir
counter=0

# Verify METASHARE_SW_DIR is a valid directory
if [ ! -d "$METASHARE_SW_DIR" ] ; then
	echo $METASHARE_SW_DIR " is not a valid directory."
	exit 1
fi

OP=$1
if [[  "$OP" != "start" && "$OP" != "stop" && "$OP" != "clean" ]] ; then
	echo "usage: $0 [start|stop|clean]"
	exit 1
fi

# Loop until get_node_cfg returns an error
while python get_node_cfg.py $counter NODE_NAME &> /dev/null ; do
	export NODE_NAME=`python $CURRENT_DIR/get_node_cfg.py $counter NODE_NAME`
	echo "Processing " $NODE_NAME
	# Create a directory for Node
	cd $TEST_DIR
	if [[ "$OP" == "start" ]] ; then
		mkdir $NODE_NAME
	fi

	# Copy the solr empty tree
	if [[ "$OP" == "start" ]] ; then
		cp -R $METASHARE_DIR/../solr/solr $TEST_DIR/$NODE_NAME
	fi

	SOLR_ROOT=$TEST_DIR/$NODE_NAME/solr
	SOLR_LOG=$SOLR_ROOT/solr.log
	export SOLR_PORT=`python $CURRENT_DIR/get_node_cfg.py $counter SOLR_PORT`
	SOLR_STOP_PORT=`python $CURRENT_DIR/get_node_cfg.py $counter SOLR_STOP_PORT`
	SOLR_STOP_KEY=`python $CURRENT_DIR/get_node_cfg.py $counter SOLR_STOP_KEY`

	DJANGO_PID=$TEST_DIR/$NODE_NAME/django.pid
	if [[ "$OP" == "start" ]] ; then
		# Copy schema files
		MAIN_SCHEMA_FILE=$SOLR_ROOT/main/conf/schema.xml
		TESTING_SCHEMA_FILE=$SOLR_ROOT/testing/conf/schema.xml
		cp $CURRENT_DIR/init_data/schema.xml $MAIN_SCHEMA_FILE
		cp $CURRENT_DIR/init_data/schema.xml $TESTING_SCHEMA_FILE
	
		# Start the Solr server for Node
		start_solr
		# Wait for Solr
		echo "Waiting for Solr to start and open connections ..."
		sleep 8
		# Copy an empty database
		export DJANGO_PORT=`python $CURRENT_DIR/get_node_cfg.py $counter DJANGO_PORT`
		DATABASE_NAME=`python $CURRENT_DIR/get_node_cfg.py $counter DATABASE_NAME`
		export DATABASE_FILE=$TEST_DIR/$NODE_NAME/$DATABASE_NAME
		cp $CURRENT_DIR/init_data/metashare.db $TEST_DIR/$NODE_NAME/$DATABASE_NAME
		export STORAGE_PATH=$TEST_DIR/$NODE_NAME/storageFolder
		mkdir $STORAGE_PATH
		# Start Django application
		start_django

		# Create a shell script that can set environment variables for this node
		CONF_FILE=$TEST_DIR/$NODE_NAME/setvars.sh
		echo "export DJANGO_PORT="$DJANGO_PORT >> $CONF_FILE
		echo "export STORAGE_PATH="$STORAGE_PATH >> $CONF_FILE
		echo "export SOLR_PORT="$SOLR_PORT >> $CONF_FILE
		echo "export DATABASE_FILE="$DATABASE_FILE >> $CONF_FILE
		chmod +x $CONF_FILE
	elif [[ "$OP" == "stop" ]] ; then
		stop_django
		stop_solr
	else
		rm -r $NODE_NAME
	fi

	cd $CURRENT_DIR
	let counter=counter+1
done

