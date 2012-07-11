# find the best Python binary to use: only use the platform default if ther is
# no custom Python installation for META-SHARE available
if [ -x "$METASHARE_SW_DIR/opt/bin/python" ] ; then
        PYTHON="$METASHARE_SW_DIR/opt/bin/python"
else
        PYTHON=`which python`
fi

