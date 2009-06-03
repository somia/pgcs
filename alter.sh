#!/bin/sh
DIR=`dirname $0`
[ "x$DIR" != x ] && cd $DIR
exec python2.6 -m pgcs.alter "$@"
