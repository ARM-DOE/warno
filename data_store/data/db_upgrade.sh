#! /usr/bin/env bash
# Designed to be run within VM, otherwise the absolute paths will probably not be correct.
export PYTHONPATH=/vagrant/data_store/data/
export DATA_STORE_PATH=/vagrant/data_store/data/
cd /vagrant
alembic upgrade head



