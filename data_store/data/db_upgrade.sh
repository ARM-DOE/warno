#! /usr/bin/env bash
# Designed to be run within VM, otherwise the absolute paths will probably not be correct.
# If PYTHONPATH and DATA STORE PATH are already defined, use them, otherwise, define them as the VM defaults

if [ "" = "$PYTHONPATH" ]; then
    export PYTHONPATH=/vagrant/data_store/data/
fi
if [ "" = "$DATA_STORE_PATH" ]; then
    export DATA_STORE_PATH=/vagrant/data_store/data/
fi
if [ "" = "$VAGRANT_HOME" ]; then
    cd /vagrant
else
    cd  $VAGRANT_HOME
fi
alembic upgrade head