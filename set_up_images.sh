#!/usr/bin/env bash
wget http://yggdrasil.pnl.gov/warno1.box -N
wget http://yggdrasil.pnl.gov/warno-docker-image -N
vagrant box add warnobox1 warno1.box --force