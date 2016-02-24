#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Source http://stackoverflow.com/questions/10822790/can-i-call-a-function-of-a-shell-script-from-another-shell-script
source $DIR/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml $DIR/config.yml)
eval $(parse_yaml $DIR/secrets.yml)

USERNAME=$database__DB_USER
DB_ADDRESS=$database__DB_HOST
DB_NAME=$database__DB_NAME
DB_PASS=$s_database__DB_PASS

/usr/pgsql-9.3/bin/pg_ctl start
sleep 5
echo "root"
psql --command "CREATE USER root WITH SUPERUSER PASSWORD 'password';"
psql --command "CREATE USER $USERNAME WITH SUPERUSER PASSWORD '$DB_PASS';"
psql --command "CREATE DATABASE $DB_NAME;"