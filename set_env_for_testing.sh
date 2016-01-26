#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH="$DIR/data_store/data:$PYTHONPATH"
export DATA_STORE_PATH="$DIR/data_store/data/"
export USER_PORTAL_PATH="$DIR/warno_user_portal/src/"