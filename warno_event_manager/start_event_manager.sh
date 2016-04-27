#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source /vagrant/data_store/data/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml /vagrant/data_store/data/config.yml)

if [ "$setup__run_vm_event_manager" = "1" ]; then
    echo "Starting Event Manager"
    cd $DIR/src
    python warno_event_manager.py >> /vagrant/logs/event_manager_server.log 2>&1 &
    disown
else
    echo "VM Event Manager Disabled in Config"
fi
