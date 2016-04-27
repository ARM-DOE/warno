#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

wget http://yggdrasil.pnl.gov/warno1.box -N
wget http://yggdrasil.pnl.gov/warno-docker-image -N
vagrant box add warnobox1 warno1.box --force