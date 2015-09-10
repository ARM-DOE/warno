#!/usr/bin/env bash
tempdir=$(mktemp -d /tmp/wheelhouse-XXXXX)
cwd=$PWD
(cd $tempdir; tar -xvf "$cwd/wuppbundle.tar.bz2")
pip install --force-reinstall --ignore-installed --upgrade --no-index --no-deps $tempdir/*
