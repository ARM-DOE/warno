#!/usr/bin/env bash
pip install -r /opt/warno-event-manager/requirements.txt
pip install requests --upgrade
echo "Utility.py Call"
python /opt/warno-event-manager/database/utility.py
echo "Event Manager Startup"
python warno_event_manager.py