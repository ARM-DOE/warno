#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

wget http://yggdrasil.pnl.gov/warno6.box -N
vagrant box add warnobox1 warno6.box --force
