
test1()
{
	echo "test1"
	return 0
}

test2()
{
	echo "test2"
	return 1
}

fun()
{
	echo "This is fun"
}

FUN_LIST="test1 test2"

run_tests()
{
	TOTAL=0
	SUCCESS=0
	echo "Running tests."

	for F in $FUN_LIST ; do
		echo "Running " $F
		$F
		ret_val=$?
		let TOTAL=TOTAL+1
		if [ $ret_val -eq 0 ] ; then
			let SUCCESS=SUCCESS+1
		else
			echo $F " FAILED!"
		fi
	done

	echo "Tests run: " $TOTAL
	echo "Successful tests: " $SUCCESS
	echo "Failed tests: " $(( $TOTAL - $SUCCESS ))
}

run_tests

