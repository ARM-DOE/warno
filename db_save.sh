#!/usr/bin/env bash
DB_ADDRESS=192.168.50.100
pg_dump -f ./warno-event-manager/src/database/db_dump.data -h $DB_ADDRESS --username=warno
