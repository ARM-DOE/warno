#!/usr/bin/env bash
DB_ADDRESS=192.168.50.99
DUMPFILE=/vagrant/warno-event-manager/src/database/db_dump.data
BACKUP=/vagrant/warno-event-manager/src/database/backup/db_dump.data
USERNAME=warno

if ls $DUMPFILE 1> /dev/null 2>&1
then
        cp -f $DUMPFILE $BACKUP
        echo "Database backed up to $BACKUP"
else
        echo "No dumpfile to back up"
fi


pg_dump -f $DUMPFILE -h $DB_ADDRESS --username=$USERNAME

if [ $? != 0 ]
then
        echo "Could not save database"
fi
