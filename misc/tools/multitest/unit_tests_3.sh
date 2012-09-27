#!/bin/bash

THIS_DIR=$(dirname "$0")
. "${THIS_DIR}/setvars.sh"
. "${THIS_DIR}/_meta_dir.sh"
. "${THIS_DIR}/_python.sh"
cd "$MSERV_DIR"

TESTSUITE_NAME="TwoNodesSync"

setUp()
{
	cd "$MSERV_DIR"
	"$MSERV_DIR"/mserv.sh start
	local ret_val=$?
	return $ret_val
}

tearDown()
{
	cd "$MSERV_DIR"
	"$MSERV_DIR"/mserv.sh stop
	local ret_val=$?

	if [[ $ret_val -ne 0 ]] ; then
		return $ret_val
	fi

	cd "$MSERV_DIR"
	"$MSERV_DIR"/mserv.sh clean
	local ret_val=$?

	return $ret_val
}

FILE1="$METASHARE_SW_DIR/misc/testdata/v3.0/METASHAREResources/ILC-CNR/KyotoDemo.xml"
FILE2="$METASHARE_SW_DIR/misc/testdata/v3.0/METASHAREResources/ILC-CNR/KyotoOntotagger.xml"
FILE3="$METASHARE_SW_DIR/misc/testdata/v3.0/METASHAREResources/ILC-CNR/SimpleOWL.xml"

test_sync_inner()
{
	cd "$MSERV_DIR"
	"$MSERV_DIR/test_import_s.sh" 1 0 "$FILE1"
	local ret_val=$?
	return $ret_val
}

test_sync_outer()
{
	cd "$MSERV_DIR"
	"$MSERV_DIR/test_import_s.sh" 2 1 "$FILE2"
	local ret_val=$?
	return $ret_val
}

test_del_inner()
{
	cd "$MSERV_DIR"
	"$MSERV_DIR/test_del_s.sh" 1 0
	local ret_val=$?
	return $ret_val
}

test_del_outer()
{
	cd "$MSERV_DIR"
	"$MSERV_DIR/test_del_s.sh" 2 1
	local ret_val=$?
	return $ret_val
}

TEST_LIST="test_sync_inner test_sync_outer test_del_inner test_del_outer"

run_tests()
{
	REPORT="$REPORT_DIR/${TESTSUITE_NAME}_report.xml"
	STDOUT="$REPORT_DIR/${TESTSUITE_NAME}_stdout.log"
	STDERR="$REPORT_DIR/${TESTSUITE_NAME}_stderr.log"
	DETAILS="$REPORT_DIR/${TESTSUITE_NAME}_details.log"
	CLASSNAME="Sync"

	echo -n > "$STDOUT"
	echo -n > "$STDERR"
	echo "<testsuite name=\"$TESTSUITE_NAME\">" > "$REPORT"
	TOTAL=0
	SUCCESS=0
	echo "Running tests."

	setUp 1>>"$STDOUT" 2>>"$STDERR"

	for F in $TEST_LIST ; do
		echo "Running " $F
		$F 1>>"$STDOUT" 2>>"$STDERR" 3>"$DETAILS"
		ret_val=$?
		let TOTAL=TOTAL+1
		if [ $ret_val -eq 0 ] ; then
			let SUCCESS=SUCCESS+1
		else
			echo $F " FAILED!"
		fi
		echo "    <testcase classname=\"$CLASSNAME\" name=\"$F\">" >> "$REPORT"
		if [ $ret_val -ne 0 ] ; then
			DETAILS_CONTENT=`cat "$DETAILS"`
			echo "        <failure message=\"message\" type=\"type\">$DETAILS_CONTENT</failure>" >> "$REPORT"
		fi
		echo "    </testcase>" >> "$REPORT"
	done

	echo "Tests run: " $TOTAL
	echo "Successful tests: " $SUCCESS
	echo "Failed tests: " $(( $TOTAL - $SUCCESS ))
	echo -n "    <system-out><![CDATA[" >> "$REPORT"
	cat "$STDOUT" >> "$REPORT"
	echo "]]></system-out>" >> "$REPORT"
	echo -n "    <system-err><![CDATA[" >> "$REPORT"
	cat "$STDERR" >> "$REPORT"
	echo "]]></system-err>" >> "$REPORT"
	echo "</testsuite>" >> "$REPORT"

	tearDown 1>>"$STDOUT" 2>>"$STDERR"
}

METASHARE_DIR="$METASHARE_SW_DIR/metashare"
echo "MSERV_DIR = $MSERV_DIR"

run_tests

