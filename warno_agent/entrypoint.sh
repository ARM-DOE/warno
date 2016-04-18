#!/usr/bin/env bash
# These installations cannot be located in the Dockerfile.
# Volumes_from links data_store container after Dockerfile finishes building.
pip install --user -r /opt/warno_agent/requirements.txt
pip install --user requests --upgrade
pip install  /opt/data/pyarmret/

source /opt/data/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml /opt/data/config.yml)

if [ "$setup__run_vm_agent" = "1" ]; then
    echo "Starting Agent"
    /opt/data/anaconda/bin/python Agent/Agent.py
else
    echo "VM Agent Disabled in Config"
fi
