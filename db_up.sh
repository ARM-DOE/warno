#! /usr/bin/env bash
DB_ADDRESS=192.168.50.99
DUMPFILE=/vagrant/warno-event-manager/src/database/db_dump.data
DB_FOLDER=/vagrant/warno-event-manager/src/database
USERNAME=warno
ready=0

# Loops until the database is ready, then loads the postgresql database dump file and exits.

PATH=/vagrant/anaconda/bin:$PATH
echo "Waiting for database to be ready to load data."
while [ $ready -lt 1 ]; do
  psql -h $DB_ADDRESS --username=$USERNAME -t -c "select now()" postgres &> /dev/null
  echo $?

  if [ $? == 0 ]; then
    echo "Loading data for database from " $DUMPFILE
    ready=1;
    psql -h $DB_ADDRESS --username=$USERNAME < $DUMPFILE
    if [ $? != 0 ]; then
      echo "No database file found.  Initializing new database"
      cd $DB_FOLDER
      python initialize_db.py
    fi

  fi
done
