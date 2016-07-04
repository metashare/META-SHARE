#!/bin/sh

BINDIR=$(dirname $0)

if [ $# -ne 2 ] ; then
  echo "usage: model2png.sh appdir outfile.png"
  exit 1
fi

APPDIR=$1
OUTFILE=$2

python $BINDIR/modelviz.py $APPDIR > /tmp/modelviz.dot

dot -Tpng /tmp/modelviz.dot > $OUTFILE
