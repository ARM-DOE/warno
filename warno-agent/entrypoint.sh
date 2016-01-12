#!/usr/bin/env bash
echo "Conda List"
conda list
echo "which conda"
which conda
echo "pip installs"
pip install -r /opt/warno-agent/requirements.txt
pip install requests --upgrade
echo "Starting Agent"
python warno-agent.py