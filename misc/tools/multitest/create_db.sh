#!/bin/bash

# Create the metashare database.
# If the database does not exists create an empty database.
# If the database already exists try to update it
# If '-r' option is given in command line the database is deleted
# if already exists and created empty.

. _meta_dir.sh
. _python.sh

CURRENT_DIR=`pwd`

cp init_data/settings_orig.py $METASHARE_DIR/settings.py
cp init_data/local_settings_test.py $METASHARE_DIR/local_settings.py

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

cd $METASHARE_DIR
"$PYTHON"  manage.py syncdb --noinput
"$PYTHON"  manage.py createsuperuserwithpassword --username=admin --password=secret
cd $CURRENT_DIR

rmdir "$STORAGE_PATH"

echo "Database file " $DATABASE_FILE " has been created/updated."

