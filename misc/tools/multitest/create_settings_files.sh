#!/bin/bash

MSERV_DIR=$(dirname "$0")
. "${MSERV_DIR}/_meta_dir.sh"

MULTI_TEST_SETT_MARKER="# __MultiNode__settings__file__"

copy_settings()
{
    local METASHARE_DIR="$METASHARE_SW_DIR/metashare"
    local SETT_FILE="$METASHARE_DIR/settings.py"

    # Check if settings.py has already been replaced with
    # the multinode version
    local res=`grep -e "$MULTI_TEST_SETT_MARKER" "$SETT_FILE"` 
    echo $res
    if [[ "$res" == "" ]] ; then
        echo "Copying original settings.py"
        mkdir -p "$MSERV_DIR/init_data"
        cp "$SETT_FILE" "$MSERV_DIR/init_data/settings_original.py"
        local root_path_line=`grep -e "^ROOT_PATH =" "$SETT_FILE"`
        echo "1 i\
$MULTI_TEST_SETT_MARKER" > /tmp/sed.scr
        echo "/^from local_settings import */ c\
cmd_folder = os.environ['NODE_DIR']\n\
import sys\n\
sys.path.insert(1, cmd_folder)\n\
from dj_settings.multilocal_settings import *\n\
from dj_settings.node_settings import *\n\
$root_path_line\n\
" >> /tmp/sed.scr
        sed -f /tmp/sed.scr "$MSERV_DIR/init_data/settings_original.py" > "$MSERV_DIR/init_data/settings_multitest.py"
        rm /tmp/sed.scr
    fi 
}

copy_local_settings()
{
    local METASHARE_DIR="$METASHARE_SW_DIR/metashare"
    local L_SETT_FILE="$METASHARE_DIR/local_settings.sample"
    local root_path_line="ROOT_PATH = \'$METASHARE_DIR\'"
    echo "/^ROOT_PATH =/c \
$root_path_line" > /tmp/sed.scr

    mkdir -p init_data
    sed -f /tmp/sed.scr "$L_SETT_FILE" > $MSERV_DIR/init_data/local_settings.sample
}

copy_settings
copy_local_settings

