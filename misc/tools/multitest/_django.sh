
# Env vars required:
# - METASHARE_DIR
# - TEST_DIR
# - MSERV_DIR
# - PYTHON

if [[ "$METASHARE_DIR" == "" ]] ; then
	echo "METASHARE_DIR NOT set"
	exit 1
fi

if [[ "$TEST_DIR" == "" ]] ; then
	echo "TEST_DIR NOT set"
	exit 1
fi

if [[ "$MSERV_DIR" == "" ]] ; then
	echo "MSERV_DIR NOT set"
	exit 1
fi

if [[ "$PYTHON" == "" ]] ; then
	echo "PYTHON NOT set"
	exit 1
fi

get_django_pid_filename()
{
	local FILENAME="django.pid"
	echo "$FILENAME"
}

start_django()
{
	local NODE_NAME="$1" ; shift
	local DJANGO_PORT="$1" ; shift

	echo "Starting Django server"
	local CWD=`pwd`
	#cd "$METASHARE_DIR"
	export NODE_DIR="$TEST_DIR/$NODE_NAME"
	local PID_NAME=`get_django_pid_filename`
	local DJANGO_PID="$NODE_DIR/$PID_NAME"
	$PYTHON manage.py runserver 0.0.0.0:$DJANGO_PORT --noreload &> "$TEST_DIR/$NODE_NAME/metashare.log" &
	echo $! > "$DJANGO_PID"
	sleep 2
	#cd "$CWD"
}

stop_django()
{
	local NODE_NAME="$1" ; shift

	NODE_DIR=$TEST_DIR/$NODE_NAME
	local PID_NAME=`get_django_pid_filename`
	local DJANGO_PID="$NODE_DIR/$PID_NAME"
	echo "Stopping Django server"
	kill -9 `cat -- "$DJANGO_PID"`
	rm -f -- "$DJANGO_PID"
}

run_syncdb()
{
	local NODE_NAME="$1" ; shift
	local DATABASE_NAME="$1" ; shift

	cp "$MSERV_DIR/init_data/metashare_test.db" "$TEST_DIR/$NODE_NAME/$DATABASE_NAME"
	local CWD=`pwd`
	#cd "$METASHARE_DIR"
	echo "Running manage.py syncdb"
	export NODE_DIR=$TEST_DIR/$NODE_NAME
	$PYTHON manage.py syncdb
	#cd "$CWD"
}

create_django_settings()
{
	local NODE_NAME="$1" ; shift
	local SOLR_PORT="$1" ; shift
	local DATABASE_FILE="$1" ; shift
	local STORAGE_PATH="$1" ; shift
	local DJANGO_PORT="$1" ; shift
	local CORE_NODES="$1" ; shift
	local PROXIED_NODES="$1" ; shift
	local SYNC_USERS="$1" ; shift

	local NODE_SETTINGS_DIR="$TEST_DIR/$NODE_NAME/dj_settings"
        mkdir -p "$NODE_SETTINGS_DIR"
	local LOG_FILENAME="$TEST_DIR/$NODE_NAME/metashare.log"
	echo "s#%%LOG_FILENAME%%#$LOG_FILENAME#g" > /tmp/sed.scr
	echo "s/%%SOLR_PORT%%/$SOLR_PORT/g" >> /tmp/sed.scr
	echo "s#%%DATABASE_FILE%%#$DATABASE_FILE#g"  >> /tmp/sed.scr
	echo "s#%%STORAGE_PATH%%#$STORAGE_PATH#g" >> /tmp/sed.scr
	echo "s/%%DJANGO_PORT%%/$DJANGO_PORT/g" >> /tmp/sed.scr
	echo "s#%%CORE_NODES%%#$CORE_NODES#g" >> /tmp/sed.scr
	echo "s#%%PROXIED_NODES%%#$PROXIED_NODES#g" >> /tmp/sed.scr
	echo "s#%%SYNC_USERS%%#$SYNC_USERS#g" >> /tmp/sed.scr
	cat "$MSERV_DIR/init_data/node_settings.py" | sed -f /tmp/sed.scr \
		> "$NODE_SETTINGS_DIR/node_settings.py"
	rm /tmp/sed.scr
	cp "$MSERV_DIR/init_data/local_settings.sample" "$NODE_SETTINGS_DIR/multilocal_settings.py"
	touch "$NODE_SETTINGS_DIR/__init__.py"
}

