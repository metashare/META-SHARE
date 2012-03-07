#!/bin/bash

#
# Replaces a specified Solr configuration with a new sample configuration.
#

# make sure that a single directory is given before going on
if [ -z "$1" -o \( "x$1" = "x-n" -a -z "$2" \) \
     -o \( "x$1" != "x-n" -a -n "$2" \) -o -n "$3" ]
then
  echo "Usage: $0 [-n] solr_install_dir"
  echo "    -n  run in non-interactive mode"
  exit 1
fi
if [ "x$1" = "x-n" ]
then
  if [ ! -d "$2" ]
  then
    echo "Not a directory: $2"
    exit 2
  fi
  INTERACTIVE=""
  SOLR_MAIN_DIR="$2/example/solr"
else
  if [ ! -d "$1" ]
  then
    echo "Not a directory: $1"
    exit 2
  fi
  INTERACTIVE=1
  SOLR_MAIN_DIR="$1/example/solr"
fi


SAMPLE_CONF_BASE_DIR="$(cd $(dirname $0); pwd)"

# check whether the given directory is really a Solr installation directory
if [ ! -d "$SOLR_MAIN_DIR" ]
then
  echo "The specified directory does not appear to be a default Solr" \
    "installation directory. We're missing this subdirectory: $SOLR_MAIN_DIR"
  exit 3
fi

# let the user confirm that the existing configuration will be entirely replaced
# (only in interactive mode)
if [ $INTERACTIVE ]
then
  echo "This will replace your Solr configuration and search indexes at" \
    "'$SOLR_MAIN_DIR' with a new sample configuration."
  read -n 1 -r -p "Are you sure? [y/n] "
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
      exit 0
  fi
fi

# replace the existing configuration with a brand new one
rm -rf "$SOLR_MAIN_DIR"
for core in main testing
do
  mkdir -p "$SOLR_MAIN_DIR/$core/conf"
  cp "$SAMPLE_CONF_BASE_DIR/solrconfig.xml" "$SOLR_MAIN_DIR/$core/conf"
  cp "$SAMPLE_CONF_BASE_DIR/stopwords.txt" "$SOLR_MAIN_DIR/$core/conf"
  cp "$SAMPLE_CONF_BASE_DIR/synonyms.txt" "$SOLR_MAIN_DIR/$core/conf"
  python "$SAMPLE_CONF_BASE_DIR/../../metashare/manage.py" \
    build_solr_schema --filename="$SOLR_MAIN_DIR/$core/conf/schema.xml"
done
cp "$SAMPLE_CONF_BASE_DIR/solr.xml" "$SOLR_MAIN_DIR"
