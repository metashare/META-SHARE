#!/bin/bash

. _meta_dir.sh
. _conf.sh



replace_vars()
{
  local IN_FILE="$1" ; shift
  local OUT_FILE="$1" ; shift

  local SED_SCR=/tmp/sed.scr

  echo -n > "$SED_SCR"
  echo "s#%%METASHARE_SW_DIR%%#$METASHARE_SW_DIR#g" >> "$SED_SCR"
  echo "s#%%SERVER_NAME%%#$SERVER_NAME#g" >> "$SED_SCR"
  echo "s#%%LIGHT_ADDR%%#$LIGHT_ADDR#g" >> "$SED_SCR"
  echo "s#%%LIGHT_HTTP_PORT%%#$LIGHT_HTTP_PORT#g" >> "$SED_SCR"
  echo "s#%%LIGHT_HTTPS_PORT%%#$LIGHT_HTTPS_PORT#g" >> "$SED_SCR"
  echo "s#%%LIGHT_USERNAME%%#$LIGHT_USERNAME#g" >> "$SED_SCR"
  echo "s#%%LIGHT_GROUPNAME%%#$LIGHT_GROUPNAME#g" >> "$SED_SCR"
  echo "s#%%LIGHT_TAG%%#$LIGHT_TAG#g" >> "$SED_SCR"
  echo "s#%%PYTHON_ADDR%%#$PYTHON_ADDR#g" >> "$SED_SCR"
  echo "s#%%PYTHON_PORT%%#$PYTHON_PORT#g" >> "$SED_SCR"
  echo "s#%%LOG_DIR%%#$LOG_DIR#g" >> "$SED_SCR"
  echo "s#%%PEM_FILE%%#$PEM_FILE#g" >> "$SED_SCR"
  echo "s#%%CA_FILE%%#$CA_FILE#g" >> "$SED_SCR"

  cat "$IN_FILE" | sed -f "$SED_SCR" > "$OUT_FILE"
  rm "$SED_SCR"
}

IN_FILE=lighttpd-ssl.conf.sample
OUT_FILE=lighttpd-ssl.conf

SERVER_NAME=0.0.0.0
LIGHT_ADDR=0.0.0.0
LIGHT_HTTP_PORT=6789
LIGHT_HTTPS_PORT=6443
LIGHT_USERNAME=lighttpd
LIGHT_GROUPNAME=lighttpd
LIGHT_TAG=lighttpd
PYTHON_ADDR=127.0.0.1
PYTHON_PORT=9191
PEM_FILE=$METASHARE_SW_DIR/misc/tools/ssl-config/cert/metashare.pem
CA_FILE=$METASHARE_SW_DIR/misc/tools/ssl-config/cert/metashare.crt

LOG_DIR=/tmp/log/light
mkdir -p "$LOG_DIR"

replace_vars "$IN_FILE" "$OUT_FILE"

