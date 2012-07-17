#!/bin/bash

# Create the metashare database.
# If the database does not exists create an empty database.
# If the database already exists try to update it
# If '-r' option is given in command line the database is deleted
# if already exists and created empty.

. _meta_dir.sh
. _python.sh
. _utils.sh

CURRENT_DIR=`pwd`

cp init_data/settings_orig.py $METASHARE_DIR/settings.py
ret_val=$?
cp init_data/local_settings_test.py $METASHARE_DIR/local_settings.py
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Cannot copy settings/local_settings"
	exit $ret_val
fi

export DJANGO_PORT=12345
export STORAGE_PATH=/tmp/storageFolder
export SOLR_PORT=54321
export DATABASE_FILE=$CURRENT_DIR/init_data/metashare_test.db

if [[ "$1" == "-r" ]] ; then
	if [[ -f $DATABASE_FILE ]] ; then
		echo "Deleting current database ..."
		rm -f $DATABASE_FILE
		ret_val=$?
		if [[ $ret_val -ne 0 ]] ; then
			echo "Cannot delete $DATABASE_FILE"
			exit $ret_val
		fi
	fi
fi

cd $METASHARE_DIR
"$PYTHON"  manage.py syncdb --noinput
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Cannot build database"
	exit $ret_val
fi
"$PYTHON"  manage.py createsuperuserwithpassword --username=admin --password=secret
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Cannot create superuser"
	exit $ret_val
fi
cd $CURRENT_DIR

META_LOG=`get_meta_log`
rm -f "$META_LOG"
rmdir "$STORAGE_PATH"

echo "Database file " $DATABASE_FILE " has been created/updated."

