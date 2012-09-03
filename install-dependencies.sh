#!/bin/bash

CURRENTDIR=$(pwd)
BASEDIR=$(cd $(dirname .gitignore) ; pwd)
echo "This will install dependencies required by META-SHARE."

echo "Checking python version..."

EXPECTED_PYTHON_VERSION="Python 2.7"

# Check which python version to use
if [ -e $BASEDIR/opt/bin/python ] ; then
  PYTHON=$BASEDIR/opt/bin/python
  echo "Using locally installed python version $PYTHON"
else
  PYTHON=python
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
PREFIX_MATCH=$(expr "$PYTHON_VERSION" : "\($EXPECTED_PYTHON_VERSION\)")

if [ "$PREFIX_MATCH" != "" ] ; then
  echo "$PYTHON_VERSION found, OK."
else
  if [ "$PYTHON" == "python" ] ; then
    echo "expected $EXPECTED_PYTHON_VERSION, but found $PYTHON_VERSION"
    echo "trying to install a local version in $BASEDIR/opt"

    cd $BASEDIR/installable-packages
    tar xjf Python-2.7.2.tar.bz2
    cd Python-2.7.2
    ./configure --prefix=$BASEDIR/opt
    make
    make install
  else
    echo "expected $EXPECTED_PYTHON_VERSION, but found $PYTHON_VERSION in local install"
    echo "something is messed up, aborting."
    exit 1
  fi  
fi

echo
echo
echo "Installation of META-SHARE dependencies complete."
if [ "$PYTHON" != "python" ] ; then
  echo "Python was installed locally -- make sure to include $BASEDIR/opt/bin at the beginning of your PATH!"
fi