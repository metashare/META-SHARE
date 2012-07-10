#!/bin/bash

# Create the metashare database.
# If the database does not exists create an empty database.
# If the database already exists try to update it
# If '-r' option is given in command line the database is deleted
# if already exists and created empty.

CURRENT_DIR=`pwd`
METASHARE_DIR=$METASHARE_SW_DIR/metashare

cp init_data/settings_orig.py ../../metashare/settings.py
cp init_data/local_settings_test.py ../../metashare/local_settings.py

export DJANGO_PORT=12345
export STORAGE_PATH=/tmp/storageFolder
export SOLR_PORT=54321
export DATABASE_FILE=$CURRENT_DIR/init_data/metashare_test.db

if [[ "$1" == "-r" ]] ; then
	if [[ -f $DATABASE_FILE ]] ; then
		echo "Deleting current database ..."
		rm -f $DATABASE_FILE
	fi
fi

# find the best Python binary to use: only use the platform default if ther is
# no custom Python installation for META-SHARE available
if [ -x "$METASHARE_SW_DIR/opt/bin/python" ] ; then
	PYTHON="$METASHARE_SW_DIR/opt/bin/python"
else
	PYTHON=`which python`
fi

cd $METASHARE_DIR
"$PYTHON"  manage.py syncdb --noinput
"$PYTHON"  manage.py createsuperuserwithpassword --username=admin --password=secret
cd $CURRENT_DIR

rmdir "$STORAGE_PATH"

echo "Database file " $DATABASE_FILE " has been created/updated."

