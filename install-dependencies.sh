#!/bin/bash

CURRENTDIR=$(pwd)
BASEDIR=$(cd $(dirname .gitignore) ; pwd)
echo "This will install dependencies required by META-SHARE."

echo "Checking python version..."

EXPECTED_PYTHON_VERSION="Python 2.7"

# Check which python version to use
if [ -e "$BASEDIR/opt/bin/python" ] ; then
  PYTHON="$BASEDIR/opt/bin/python"
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

    wget "https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz" || exit 1
    echo "Verifying python"
    echo "5eebcaa0030dc4061156d3429657fb83  Python-2.7.9.tgz" | md5sum -c - || exit 1
    tar xzf "Python-2.7.9.tgz" || exit 1
    cd "Python-2.7.9" || exit 1
    ./configure --prefix="$BASEDIR/opt" || exit 1
    make || exit 1
    make install || exit 1
    cd ".."
    rm -rf "Python-2.7.9"
    PYTHON="$BASEDIR/opt/bin/python"
  else
    echo "expected $EXPECTED_PYTHON_VERSION, but found $PYTHON_VERSION in local install"
    echo "something is messed up, aborting."
    exit 1
  fi  
fi
echo "Create the virtual environment for package installation:"
# Select current version of virtualenv:
VENV_DIR="${BASEDIR}/venv"
VENV_VERSION="12.0.7"
URL_BASE="https://pypi.python.org/packages/source/v/virtualenv"

echo "Download virtualenv..."
wget --no-check-certificate "$URL_BASE/virtualenv-${VENV_VERSION}.tar.gz" || exit 1
echo "Verify virtualenv..."
echo "e08796f79d112f3bfa6653cc10840114  virtualenv-12.0.7.tar.gz" | md5sum -c - || exit 1
echo "Extracting virtualenv"
tar xzf "virtualenv-${VENV_VERSION}.tar.gz" || exit 1
echo "Create the virtual environment:"
"$PYTHON" "virtualenv-${VENV_VERSION}/virtualenv.py" "${VENV_DIR}"
# Don't need this anymore.
rm -rf "virtualenv-${VENV_VERSION}" "virtualenv-${VENV_VERSION}.tar.gz"

echo "Python virtual environment created"

echo "Install metashare python dependencies"
"${VENV_DIR}/bin/pip" install -r "${BASEDIR}/requirements.txt" || exit 1

echo
echo
echo "Installation of META-SHARE dependencies complete."

