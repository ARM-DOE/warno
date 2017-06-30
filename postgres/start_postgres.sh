#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$VAGRANT_HOME" = "" ]; then
    VAGRANT_HOME=/vagrant
fi

# postgres_log.txt probably only contains the startup data.  The rest of the postgres logs should be in the standard
# Postgres log location.
sudo -u postgres PGDATA=/var/lib/pgsql/9.3/data /usr/pgsql-9.3/bin/pg_ctl start >> $VAGRANT_HOME/logs/postgres_server.log 2>&1 &

