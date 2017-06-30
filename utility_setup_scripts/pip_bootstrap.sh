#!/usr/bin/env bash

if [ "$VAGRANT_HOME" = "" ]; then
    VAGRANT_HOME=/vagrant
fi

# Has to be run separately from bootstrap.sh, reason unknown

# If Flask is upgraded to 0.11, sometimes it will just stop working, and requests to the user portal will time out
pip install numpy selenium requests django==1.7 Flask==0.10.1 pyyaml gevent ijson
pip install gunicorn psycogreen psutil enum34 sqlalchemy alembic flask-sqlalchemy flask-migrate flask-fixtures flask-testing flask-user configparser flask-user flask-restless redis ciso8601
pip install requests --upgrade
pip install  $VAGRANT_HOME/data_store/data/pyarmret/
