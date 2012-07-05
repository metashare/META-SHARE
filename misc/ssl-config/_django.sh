
# Env vars required:
# - METASHARE_DIR
# - PYTHON

start_django()
{
	local PYTHON_PORT="$1" ; shift
	local DJANGO_PID="$1" ; shift

	echo "Starting Django server"
	local CWD=`pwd`
	cd "$METASHARE_DIR"
	"$PYTHON" manage.py runfcgi host=localhost port=$PYTHON_PORT method=threaded pidfile=$DJANGO_PID
	cd "$CWD"
}

stop_django()
{
	local DJANGO_PID="$1" ; shift

	echo "Stopping Django server"
	kill -9 `cat -- "$DJANGO_PID"`
	rm -f -- "$DJANGO_PID"
}

run_syncdb()
{

	local CWD=`pwd`
	cd "$METASHARE_DIR"
	echo "Running syncdb"
	"$PYTHON" manage.py syncdb
	cd "$CWD"
}

