#!/usr/bin/env bash

if [ "$VAGRANT_HOME" = "" ]; then
    VAGRANT_HOME=/vagrant
fi

# Otherwise config cannot be found (not set PYTHONPATH, DATA_STORE_PATH)
echo "Start All Servers"
source $VAGRANT_HOME/utility_setup_scripts/set_vagrant_env.sh

# Postgres server is started in another script, as it requires sudo access
bash $VAGRANT_HOME/warno_event_manager/start_event_manager.sh
bash $VAGRANT_HOME/warno_user_portal/start_user_portal.sh
bash $VAGRANT_HOME/warno_agent/start_agent.sh