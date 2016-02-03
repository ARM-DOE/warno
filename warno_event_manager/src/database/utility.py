import psycopg2
import numpy as np
import pandas
from sqlalchemy import create_engine

from WarnoConfig import config


def table_exists(table_name, curr):
    SQL = "SELECT relname FROM pg_class WHERE relname = %s;"
    curr.execute(SQL, (table_name,))
    if curr.fetchone() == None:
        return False
    else:
        return True


def drop_table(table_name, curr):
    SQL = "DROP TABLE IF EXISTS %s;"
    try:
        curr.execute(SQL, (table_name,))
    except Exception, e:
        print(e)


def create_table_from_file(filename, curr):
    f = open(filename)
    try:
        curr.execute(f.read())
    except Exception, e:
        print(e)


def initialize_database(curr, path="schema/"):
    schema_list = [
                   "users",
                   "sites",
                   "instruments",
                   "instrument_logs",
                   "usage",
                   "prosensing_paf",
                   "event_codes",
                   "events_with_text",
                   "events_with_value",
                   "pulse_captures",
                   "table_references",
                   "instrument_data_references"
                   ]

    for schema in schema_list:
        if not table_exists(schema, curr):
            print("Initializing relation %s", schema)
            create_table_from_file("%s/%s.schema" % (path, schema), curr)


def load_data_into_table(filename, table, conn):
    df = pandas.read_csv(filename)
    keys = df.keys()
    db_cfg = config.get_config_context()['database']
    engine = create_engine('postgresql://%s:%s@%s:5432/%s' %
                           (db_cfg['DB_USER'], db_cfg['DB_PASS'], db_cfg['DB_HOST'], db_cfg['DB_NAME']))
    df.to_sql(table, engine, if_exists='append', index=False, chunksize=900)


def dump_table_to_csv(filename, table, server=None):

    if server is None:
        db_cfg = config.get_config_context()['database']
        server = create_engine('postgresql://%s:%s@%s:5432/%s' %
                               (db_cfg['DB_USER'], db_cfg['DB_PASS'], db_cfg['DB_HOST'], db_cfg['DB_NAME']))
    else:
        server = create_engine(server)

    df = pandas.read_sql_table(table, server)
    df.to_csv(filename, index=False)


def connect_db():
    db_cfg = config.get_config_context()['database']
    return psycopg2.connect("host=%s dbname=%s user=%s password=%s" %
                            (db_cfg['DB_HOST'], db_cfg['DB_NAME'], db_cfg['DB_USER'], db_cfg['DB_PASS']))
