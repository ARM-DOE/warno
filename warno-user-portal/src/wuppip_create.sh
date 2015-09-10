#!/usr/bin/env bash
tempdir=$(mktemp -d /tmp/wheelhouse-XXXXX)
pip wheel -r requirements.txt --wheel-dir=$tempdir
cwd=$PWD
(cd $tempdir; tar -cjvf "$cwd/wuppbundle.tar.bz2")
