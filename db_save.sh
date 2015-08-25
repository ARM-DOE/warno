#!/usr/bin/env bash
DB_ADDRESS=192.168.50.100
DUMPFILE=./warno-event-manager/src/database/db_dump.data
USERNAME=warno

pg_dump -f $DUMPFILE -h $DB_ADDRESS --username=$USERNAME
