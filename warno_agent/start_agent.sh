#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$VAGRANT_HOME" = "" ]; then
    VAGRANT_HOME=/vagrant
fi

source $VAGRANT_HOME/data_store/data/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml $VAGRANT_HOME/data_store/data/config.yml)

if [ "$setup__run_vm_agent" = "1" ]; then
    echo "Starting Agent"
    cd $DIR/src
    python Agent/Agent.py >> $VAGRANT_HOME/logs/agent_server.log 2>&1 &
    disown
else
    echo "VM Agent Disabled in Config"
fi
