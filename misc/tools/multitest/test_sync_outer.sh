#!/bin/bash

# Import several files in each node of the inner circle (i.e., the network of
# the META-SHARE Managing Nodes).
# Trigger synchronization on each node.
# Then verify that every published resource from each master node
# has been copied to every other node.
# Also verify that non-published resource are not copied to other nodes.

# Include environment variables and utility functions
. _meta_dir.sh
. _python.sh
. _solr.sh
. _node_info.sh
. _django.sh
. _sync.sh
. _fset.sh

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


# Synchronize and check before importing into the outer node (i.e., a
# non-managing META-SHARE node)
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

# Check resources after importing files on outer nodes (i.e., the non-managing
# META-SHARE Nodes).
# At this time a failure is acceptable since involving
# outer nodes can require two steps:
# 1) resources sent from outer nodes to proxy nodes
# 2) resources sent from proxy nodes to other inner nodes (i.e., other
# META-SHARE Managing Nodes)
if [[ $DO_CHECK_RESOURCES -eq 1 ]] ; then
  check_resources_on_inner_nodes
fi



if [[ $DO_DIGEST_UPDATE -eq 1 ]] ; then
  update_digests
fi

if [[ $DO_SYNCHRONIZE -eq 1 ]] ; then
  synchronize_nodes
fi

# Check resources again.
# This time the check should alwayd be successful.
if [[ $DO_CHECK_RESOURCES -eq 1 ]] ; then
  check_resources_on_inner_nodes
fi

