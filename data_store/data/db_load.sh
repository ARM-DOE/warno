#! /usr/bin/env bash
DB_ADDRESS=192.168.50.100
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ZIPFILE=$DIR/db_dump.data.gz
DUMPFILE=$DIR/db_dump.data
USERNAME=warno
ready=0

# Loops until the database is ready, then loads the postgresql database dump file and exits.

PATH=/vagrant/data_store/data/anaconda/bin:$PATH
if [[ -f $ZIPFILE ]]; then
    cp $ZIPFILE tmp.zip
    gunzip $ZIPFILE
    mv tmp.zip $ZIPFILE
    echo "Waiting for database to be ready to load data."
    while [ $ready -lt 1 ]; do
      psql -h $DB_ADDRESS --username=$USERNAME -t -c "select now()" postgres &> /dev/null

      if [ $? == 0 ]; then
        ready=1
        psql -h $DB_ADDRESS --username=$USERNAME < $DUMPFILE
        if [ $? != 0 ]; then
          echo "Could not load database from file."
        fi
      fi
    done
else
    echo "No dumpfile found"
fi