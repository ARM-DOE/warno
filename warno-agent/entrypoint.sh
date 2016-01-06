#!/usr/bin/env bash
pip install -r /opt/warno-agent/requirements.txt
pip install requests --upgrade
echo "Starting Agent"
python warno-agent.py