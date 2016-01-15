#!/usr/bin/env bash
DB_ADDRESS=192.168.50.100
# Source http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DUMPFILE=$DIR/db_dump.data
USERNAME=warno

pg_dump -f $DUMPFILE -h $DB_ADDRESS --username=$USERNAME

if [ $? != 0 ]
then
    echo "Could not save database"
else
    echo "Saving database dump to $DUMPFILE"
    gzip -f $DUMPFILE
fi
