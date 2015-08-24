#!/usr/bin/env bash
DB_ADDRESS=192.168.50.100
psql -h $DB_ADDRESS --username=warno < ./warno-event-manager/src/database/db_dump.data
