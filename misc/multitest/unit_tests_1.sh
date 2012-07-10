#!/bin/bash

export METASHARE_SW_DIR=/home/metashare/current/META-SHARE
export TEST_DIR=/tmp

cd "$METASHARE_SW_DIR/misc/multitest"

. _meta_dir.sh
. _python.sh


TESTSUITE_NAME="ConfigData"

setUp()
{
	return 0
}

tearDown()
{
	return 0
}

test_filesets()
{
	"$PYTHON" check_fset.py
	local ret_val=$?
	return $ret_val
}

TEST_LIST="test_filesets"

run_tests()
{
	REPORT="$WORKSPACE/${TESTSUITE_NAME}_report.xml"
	STDOUT="$WORKSPACE/${TESTSUITE_NAME}_stdout.log"
	STDERR="$WORKSPACE/${TESTSUITE_NAME}_stderr.log"
	DETAILS="$WORKSPACE/${TESTSUITE_NAME}_details.log"
	CLASSNAME="Sync"

	echo -n > "$STDOUT"
	echo -n > "$STDERR"
	echo "<testsuite name=\"$TESTSUITE_NAME\">" > "$REPORT"
	TOTAL=0
	SUCCESS=0
	echo "Running tests."

	setUp

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

	tearDown
}

METASHARE_DIR="$METASHARE_SW_DIR/metashare"
echo "MSERV_DIR = $MSERV_DIR"

run_tests

