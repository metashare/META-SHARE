
# Env vars required
# - PYTHON
# - MSERV_DIR

get_fileset()
{
	local NAME="$1" ; shift
	local NODE_NUM="$1" ; shift

	$PYTHON $MSERV_DIR/fset.py $NAME $NODE_NUM
}

