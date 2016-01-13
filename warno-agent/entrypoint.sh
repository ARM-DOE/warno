#!/usr/bin/env bash
# These installations cannot be located in the Dockerfile.
# Volumes_from links data_store container after Dockerfile finishes building.
pip install --user -r /opt/warno-agent/requirements.txt
pip install --user requests --upgrade
echo "Starting Agent"
python Agent/Agent.py
