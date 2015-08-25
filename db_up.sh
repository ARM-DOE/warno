#!/usr/bin/env bash
DB_ADDRESS=192.168.50.100
DUMPFILE=./warno-event-manager/src/database/db_dump.data
USERNAME=warno
ready=0

# Loops until the database is ready, then loads the postgresql database dump file and exits.
echo "Waiting for database to be ready to load data."
while [ $ready -lt 1 ]; do
  psql -h $DB_ADDRESS --username=$USERNAME -t -c "select now()" postgres &> /dev/null

  if [ $? == 0 ]; then
    echo "Loading data for database from " $DUMPFILE
    ready=1;
    psql -h $DB_ADDRESS --username=$USERNAME < $DUMPFILE
  fi
done
