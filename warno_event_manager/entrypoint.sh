#!/usr/bin/env bash
# These installations cannot be located in the Dockerfile.
# Volumes_from links data_store container after Dockerfile finishes building.
pip install --user -r /opt/warno_event_manager/requirements.txt
pip install --user requests --upgrade
echo "Starting Event Manager"
python warno_event_manager.py
