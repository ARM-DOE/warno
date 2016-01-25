#! /usr/bin/env bash
DB_ADDRESS=192.168.50.99
DUMPFILE=/vagrant/warno_event_manager/src/database/db_dump.data
DB_FOLDER=/vagrant/warno_event-manager/src/database
USERNAME=warno
ready=0

# Loops until the database is ready, then loads the postgresql database dump file and exits.

PATH=/vagrant/anaconda/bin:$PATH
echo "Waiting for database to be ready to load data."
while [ $ready -lt 1 ]; do
  psql -h $DB_ADDRESS --username=$USERNAME -t -c "select now()" postgres &> /dev/null

  if [ $? == 0 ]; then
    ready=1
    if [ -e $DUMPFILE ]; then
      echo "No trace of existing backup found. Initializing database."
      cd $DB_FOLDER
      python initialize_db.py
      python populate_base_db.py
    fi

  fi
done
