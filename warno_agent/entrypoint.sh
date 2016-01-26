#!/usr/bin/env bash
# These installations cannot be located in the Dockerfile.
# Volumes_from links data_store container after Dockerfile finishes building.
pip install --user -r /opt/warno_agent/requirements.txt
pip install --user requests --upgrade
pip install  /opt/data/pyarmret/
echo "Starting Agent"
/opt/data/anaconda/bin/python Agent/Agent.py
