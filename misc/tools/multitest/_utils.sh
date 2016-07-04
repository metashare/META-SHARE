
get_meta_log()
{
	local META_LOG_SCR="$MSERV_DIR/get_meta_log.py"
	local PYTHON_CMD="execfile(\"$META_LOG_SCR\")"
	local CURRENT_DIR=`pwd`
	local RES_ID=`tempfile`
	#cd "$METASHARE_DIR"
	echo "$PYTHON_CMD" | "$PYTHON" manage.py shell 1>/dev/null 2>/dev/null 5>"$RES_ID"
	cat "$RES_ID"
	rm -f "$RES_ID"
	#cd $CURRENT_DIR
}

