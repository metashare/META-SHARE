
start_light()
{
	local CONF_FILE="$1" ; shift

	echo "Starting lighttpd"
	lighttpd -f $CONF_FILE
}

stop_light()
{
	local PID_FILE="$1" ; shift

	echo "Stopping lighttpd"
	if [ -f "$PID_FILE" ] ; then
		kill -9 `cat -- "$PID_FILE"`
		rm -f -- "$PID_FILE"
	fi
}

