#! /usr/bin/env bash
PYTHONPATH=/vagrant/data_store/data/
export PYTHONPATH
DATA_STORE_PATH=/vagrant/data_store/data/
export DATA_STORE_PATH
echo ""
echo ""
echo "UPGRADING"
echo ""
echo ""
alembic upgrade head
echo "Schleep?"



