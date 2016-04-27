#!/usr/bin/env bash

source /vagrant/data_store/data/parse_yaml.sh
# Pulls the yaml variables out as constant variables.
eval $(parse_yaml /vagrant/data_store/data/config.yml)
eval $(parse_yaml /vagrant/data_store/data/secrets.yml)

USERNAME=$database__DB_USER
DB_NAME=$database__DB_NAME
DB_PASS=$s_database__DB_PASS

/usr/pgsql-9.3/bin/postgresql93-setup initdb
echo "host all all 0.0.0.0/0 trust" >> /var/lib/pgsql/9.3/data/pg_hba.conf
echo "listen_addresses='*'" >> /var/lib/pgsql/9.3/data/postgresql.conf

sudo -u postgres PGDATA=/var/lib/pgsql/9.3/data /usr/pgsql-9.3/bin/pg_ctl start >> /vagrant/logs/postgres_init.log 2>&1 &
sudo -u postgres sleep 5
sudo -u postgres psql --command "CREATE USER root WITH SUPERUSER PASSWORD 'password';"
sudo -u postgres psql --command "CREATE USER $USERNAME WITH SUPERUSER PASSWORD '$DB_PASS';"
sudo -u postgres psql --command "CREATE DATABASE $DB_NAME;"
