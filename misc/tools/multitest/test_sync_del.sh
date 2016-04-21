#!/bin/bash

# Import several files in each node of the inner circle (i.e., the network of
# the META-SHARE Managing Nodes).
# Trigger synchronization on each node.
# Then verify that every published resource from each master node
# has been copied to every other node.
# Also verify that non-published resource are not copied to other nodes.

# Include environment variables and utility functions
MSERV_DIR=$(dirname "$0")
. "${MSERV_DIR}/_meta_dir.sh"
. "${MSERV_DIR}/_python.sh"
. "${MSERV_DIR}/_solr.sh"
. "${MSERV_DIR}/_node_info.sh"
. "${MSERV_DIR}/_django.sh"
. "${MSERV_DIR}/_sync.sh"
. "${MSERV_DIR}/_fset.sh"

usage()
{
	echo "usage: $0 [options]"
	echo "   --help, -h  :   show this help"
	echo "   --no-import :   skip import step"
	echo "   --no-sync   :   skip synchronization step"
	echo "   --no-check  :   skip resource checking step"
	echo "   --no-digest :   skip digest updating step"
}

CURRENT_DIR=`pwd`
RES_DIR="$METASHARE_SW_DIR/misc/testdata/v3.0"

DO_IMPORT_FILES=1
DO_SYNCHRONIZE=1
DO_CHECK_RESOURCES=1
DO_DIGEST_UPDATE=1

NODE_COUNT=`get_node_count`

for arg
do
	if [[ "$arg" == "--no-import" ]] ; then
		DO_IMPORT_FILES=0
	fi
	if [[ "$arg" == "--no-sync" ]] ; then
		DO_SYNCHRONIZE=0
	fi
	if [[ "$arg" == "--no-check" ]] ; then
		DO_CHECK_RESOURCES=0
	fi
	if [[ "$arg" == "--no-digest" ]] ; then
		DO_DIGEST_UPDATE=0
	fi
	if [[ "$arg" == "--help" || "$arg" == "-h" ]] ; then
		usage
		exit
	fi
done

if [[ $DO_IMPORT_FILES -eq 1 ]] ; then
  import_files fileset1 inner
fi


if [[ $DO_SYNCHRONIZE -eq 1 ]] ; then
  synchronize_nodes
fi

if [[ $DO_CHECK_RESOURCES -eq 1 ]] ; then
  check_resources_on_inner_nodes
fi


if [[ $DO_IMPORT_FILES -eq 1 ]] ; then
  import_files fileset1 outer
fi

if [[ $DO_SYNCHRONIZE -eq 1 ]] ; then
  synchronize_nodes
fi

if [[ $DO_CHECK_RESOURCES -eq 1 ]] ; then
  check_resources_on_inner_nodes
fi

if [[ $DO_DIGEST_UPDATE -eq 1 ]] ; then
  update_digests
fi

if [[ $DO_SYNCHRONIZE -eq 1 ]] ; then
  synchronize_nodes
fi

if [[ $DO_CHECK_RESOURCES -eq 1 ]] ; then
  check_resources_on_inner_nodes
fi

