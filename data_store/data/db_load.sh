#! /usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Source http://stackoverflow.com/questions/10822790/can-i-call-a-function-of-a-shell-script-from-another-shell-script
source $DIR/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml $DIR/config.yml)
eval $(parse_yaml $DIR/secrets.yml)

USERNAME=$database__DB_USER
DB_ADDRESS=$database__DB_HOST


ZIPFILE=$DIR/db_dump.data.gz
DUMPFILE=$DIR/db_dump.data
ready=0

# Loops until the database is ready, then loads the postgresql database dump file and exits.

PATH=/vagrant/data_store/data/anaconda/bin:$PATH
if [[ -f $ZIPFILE ]]; then
    cp $ZIPFILE tmp.zip
    gunzip $ZIPFILE
    mv tmp.zip $ZIPFILE
    echo "Waiting for database to be ready to load data."
    while [ $ready -lt 1 ]; do
      PGPASSWORD=$s_database__DB_PASS psql -h $DB_ADDRESS --username=$USERNAME -t -c "select now()" postgres &> /dev/null

      if [ $? == 0 ]; then
        ready=1
        PGPASSWORD=$s_database__DB_PASS psql -h $DB_ADDRESS --username=$USERNAME < $DUMPFILE
        if [ $? != 0 ]; then
          echo "Could not load database from file."
        fi
      fi
    done
    rm $DUMPFILE
else
    echo "No dumpfile found"
fi