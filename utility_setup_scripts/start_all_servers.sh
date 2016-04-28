#!/usr/bin/env bash

# Otherwise config cannot be found (not set PYTHONPATH, DATA_STORE_PATH)
echo "Start All Servers"
source /vagrant/utility_setup_scripts/set_env_for_testing.sh

# Postgres server is started in another script, as it requires sudo access
bash /vagrant/warno_event_manager/start_event_manager.sh
bash /vagrant/warno_user_portal/start_user_portal.sh
bash /vagrant/warno_agent/start_agent.sh