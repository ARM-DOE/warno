#!/usr/bin/env bash

# Source http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Source http://stackoverflow.com/questions/10822790/can-i-call-a-function-of-a-shell-script-from-another-shell-script
source $DIR/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml $DIR/config.yml)
eval $(parse_yaml $DIR/secrets.yml)

USERNAME=$database__DB_USER
DB_ADDRESS=$database__DB_HOST
DB_NAME=$database__DB_NAME


DUMPFILE=$DIR/db_dump.data
PGPASSWORD=$s_database__DB_PASS pg_dump --data-only --exclude-table 'alembic_version' -f $DUMPFILE -h "$DB_ADDRESS" --username=$USERNAME $DB_NAME

if [ $? != 0 ]
then
    echo "Could not save database"
else
    echo "Saving database dump to $DUMPFILE"
    gzip -f $DUMPFILE
fi
