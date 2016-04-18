#!/usr/bin/env bash
# These installations cannot be located in the Dockerfile.
# Volumes_from links data_store container after Dockerfile finishes building.
pip install --user -r /opt/warno_user_portal/requirements.txt
echo "Starting User Portal"


source /opt/data/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml /opt/data/config.yml)

if [ "$setup__run_vm_user_portal" = "1" ]; then
    echo "Starting User Portal"
    if [ $NO_GUNICORN  -eq 1 ]
      then
      echo "Starting without GUNICORN"
      python runserver.py
    else
        echo "Starting with Green Unicorn"
        gunicorn -c gunicorn.conf --debug runserver:app
    fi
else
    echo "VM User Portal Disabled in Config"
fi