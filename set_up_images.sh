#!/usr/bin/env bash
wget http://yggdrasil.pnl.gov/warno1.box
wget http://yggdrasil.pnl.gov/warno-docker-image
vagrant box add warnobox1 warno1.box --force