#!/usr/bin/env bash
# These installations cannot be located in the Dockerfile.
# Volumes_from links data_store container after Dockerfile finishes building.
pip install --user -r /opt/warno-user-portal/requirements.txt
echo "Starting User Portal"
python runserver.py
