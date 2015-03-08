#!/bin/bash

# Create the metashare database.
# If the database does not exists create an empty database.
# If the database already exists try to update it
# If '-r' option is given in command line the database is deleted
# if already exists and created empty.

MSERV_DIR=$(dirname "$0")
. "${MSERV_DIR}/_meta_dir.sh"
. "${MSERV_DIR}/_python.sh"
. "${MSERV_DIR}/_utils.sh"
. "${MSERV_DIR}/_django.sh"

CURRENT_DIR=`pwd`

cp $MSERV_DIR/init_data/settings_multitest.py $METASHARE_DIR/settings.py
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Cannot copy settings/local_settings"
	exit $ret_val
fi

NODE_NAME="NodeDB"
DJANGO_PORT=12345
STORAGE_PATH="$TEST_DIR/$NODE_NAME/storageFolder"
SOLR_PORT=54321
DATABASE_FILE=$MSERV_DIR/init_data/metashare_test.db
CORE_NODES="()"
PROXIED_NODES="()"
SYNC_USERS="()"
export NODE_DIR="$TEST_DIR/$NODE_NAME"
mkdir -p "$TEST_DIR/$NODE_NAME/dj_settings"
create_django_settings "$NODE_NAME" $SOLR_PORT "$DATABASE_FILE" \
	"$STORAGE_PATH" $DJANGO_PORT "$CORE_NODES" \
	"$PROXIED_NODES" "$SYNC_USERS"

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

#cd $METASHARE_DIR
echo "NODE_DIR = $NODE_DIR"
echo "Creating database ...."
$PYTHON  manage.py syncdb --noinput
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Cannot build database"
	exit $ret_val
fi
$PYTHON  manage.py createsuperuserwithpassword --username=admin --password=secret
ret_val=$?
if [[ $ret_val -ne 0 ]] ; then
	echo "Cannot create superuser"
	exit $ret_val
fi
#cd $CURRENT_DIR

META_LOG=`get_meta_log`
rm -f "$META_LOG"
rmdir "$STORAGE_PATH"

echo "Database file " $DATABASE_FILE " has been created/updated."

rm -r "$TEST_DIR/$NODE_NAME"
