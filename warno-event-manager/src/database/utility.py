import psycopg2
import numpy as np
import pandas
from sqlalchemy import create_engine



def table_exists(table_name, curr):
    SQL = "SELECT relname FROM pg_class WHERE relname = %s;"
    curr.execute(SQL, (table_name,))
    if curr.fetchone() == None:
        return False
    else:
        return True

def drop_table(table_name, curr):
    SQL = "DROP TABLE IF EXISTS %s;"
    #try:
    curr.execute(SQL, (table_name,))
    #except Exception as e:
    #    print("Table Does not Exist")



def create_table_from_file(filename, curr):
    f = open(filename)
    try:
        curr.execute(f.read())
    except Exception as e:
        print("Table Already exists")
        print(e)


def initialize_database(curr):
    schema_list = [
                   "users",
                   "sites",
                   "instruments",
                   "log",
                   "usage"
                   ]

    for schema in schema_list:
        print("Initializing relation %s", schema)
        create_table_from_file("schema/%s.schema"% schema, curr)


def load_data_into_table(filename, table, conn):
    df = pandas.read_csv(filename )
    keys = df.keys()
    engine = create_engine('postgresql://warno:warno@192.168.50.100:5432/warno')
    df.to_sql(table, engine, if_exists='append', index=False)

def dump_table_to_csv(filename, table, server=None):

    if server is None:
        server = create_engine('postgresql://warno:warno@192.168.50.100:5432/warno')
    else:
        server = create_engine(server)

    df = pandas.read_sql_table(table, server)
    df.to_csv(filename)

DB_HOST = '192.168.50.100'
DB_NAME = 'warno'
DB_USER = 'warno'
DB_PASS = 'warno'

def connect_db():
    return psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (DB_HOST, DB_NAME, DB_USER, DB_PASS))




    
    

