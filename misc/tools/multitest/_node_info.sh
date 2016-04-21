
# Env vars required:
# - PYTHON
# - MSERV_DIR

get_node_info()
{
	NODE_NUM="$1" ; shift
	NODE_KEY="$1" ; shift
	NODE_VAL=`$PYTHON "$MSERV_DIR/get_node_cfg.py" $NODE_NUM $NODE_KEY`
	EX_STAT=$?
	if [[ "$EX_STAT" != "0" ]] ; then
		return $EX_STAT
	fi
	echo "$NODE_VAL"
}

