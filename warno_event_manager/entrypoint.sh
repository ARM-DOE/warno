#!/usr/bin/env bash
# These installations cannot be located in the Dockerfile.
# Volumes_from links data_store container after Dockerfile finishes building.
pip install --user -r /opt/warno_event_manager/requirements.txt
pip install --user requests --upgrade

source /opt/data/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml /opt/data/config.yml)

if [ "$setup__run_vm_event_manager" = "1" ]; then
    echo "Starting Event Manager"
    python warno_event_manager.py
else
    echo "VM Event Manager Disabled in Config"
fi
