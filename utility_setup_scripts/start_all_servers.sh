#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Otherwise config cannot be found (unset PYTHONPATH, DATA_STORE_PATH)
echo "Start All Servers"
source $DIR/../set_env_for_testing.sh

# Postgres server is started in another script, as it requires sudo access
bash $DIR/../warno_event_manager/start_event_manager.sh
bash $DIR/../warno_user_portal/start_user_portal.sh
bash $DIR/../warno_agent/start_agent.sh