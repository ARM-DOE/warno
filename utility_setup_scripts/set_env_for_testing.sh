#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH="$DIR/../data_store/data:$PYTHONPATH"
export DATA_STORE_PATH="$DIR/../data_store/data/"
export VAGRANT_HOME="$DIR/.."
export USER_PORTAL_PATH="$DIR/../warno_user_portal/src/"
export NO_GUNICORN="1"
export LOG_PATH="$DIR/../logs/"
export MIGRATION_PATH="$DIR/../migrations/"
export FIXTURES_DIR="$DIR/../data_store/data/WarnoConfig/fixtures/"