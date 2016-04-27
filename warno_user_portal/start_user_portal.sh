#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source /vagrant/data_store/data/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml /vagrant/data_store/data/config.yml)

if [ "$setup__run_vm_user_portal" = "1" ]; then
    echo "Starting User Portal"
    cd $DIR/src
    if [ "$NO_GUNICORN" = "1" ]
      then
      echo "Starting without GUNICORN"
      python user_portal_server.py >> /vagrant/logs/user_portal_server.log 2>&1 &
    disown
    else
        echo "Starting with Green Unicorn"
        gunicorn -c gunicorn.conf --log-level debug user_portal_server:app >> /vagrant/logs/user_portal_server.log 2>&1 &
    disown
    fi
else
    echo "VM User Portal Disabled in Config"
fi