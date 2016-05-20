#! /usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Source http://stackoverflow.com/questions/10822790/can-i-call-a-function-of-a-shell-script-from-another-shell-script
source $DIR/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml $DIR/config.yml)
eval $(parse_yaml $DIR/secrets.yml)

USERNAME=$database__DB_USER
DB_ADDRESS=$database__DB_HOST
DB_PORT=$database__DB_PORT


PATH=/vagrant/data_store/data/anaconda/bin:$PATH

PGPASSWORD=$s_database__DB_PASS psql -h $DB_ADDRESS --username=$USERNAME -p $DB_PORT -Atq -f $DIR/reset.sql -o $DIR/temp #&> /dev/null

PGPASSWORD=$s_database__DB_PASS psql -h $DB_ADDRESS --username=$USERNAME -p $DB_PORT -f $DIR/temp #&> /dev/null

rm $DIR/temp