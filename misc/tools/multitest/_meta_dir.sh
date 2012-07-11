# Check it the environment variable is set and points
# to a valid directory
if [[ "$METASHARE_SW_DIR" == "" ]] ; then
        echo "The environment variable METASHARE_SW_DIR must be defined"
        echo "and contain the directory with Metashare software."
        exit 1
fi

# Remove trailing slash if present
METASHARE_SW_DIR=`echo $METASHARE_SW_DIR | sed -e "s/\/$//"`

# Verify METASHARE_SW_DIR is a valid directory
if [ ! -d "$METASHARE_SW_DIR" ] ; then
        echo $METASHARE_SW_DIR " is not a valid directory."
        exit 1
fi

export METASHARE_DIR="$METASHARE_SW_DIR/metashare"
MSERV_DIR="$METASHARE_SW_DIR/misc/multitest"

