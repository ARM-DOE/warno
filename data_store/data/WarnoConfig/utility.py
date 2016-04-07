import sys
import os
import psycopg2
import numpy as np
import pandas
from sqlalchemy import create_engine
import subprocess

import config

EVENT_CODE_REQUEST = 1
SITE_ID_REQUEST = 2
INSTRUMENT_ID_REQUEST = 3
PULSE_CAPTURE = 4
INSTRUMENT_LOG = 5
PROSENSING_PAF = 6

status_text = {1: "OPERATIONAL",
               2: "NOT WORKING",
               3: "TESTING",
               4: "IN-UPGRADE",
               5: "TRANSIT"}


def status_code_to_text(status):
    """Convert an instrument's status code to its text equivalent.

    Parameters
    ----------
    status: integer
        The status code to be converted.

    Returns
    -------
    status_text: string
        Returns a string representation of the status code from the status_text dictionary.
    """
    return status_text[int(status)]


def is_number(s):
    """Checks if a string is a valid floating point number.

    Attempts to convert a string to a floating point number.

    Parameters
    ----------
    s: string
        The string to be checked.

    Returns
    -------
    True: Boolean
        Returns True if the conversion works successfully.

    False: Boolean
        Returns False if the conversion throws a 'ValueError' Exception.
    """

    try:
        # Attempts to convert the string into a float. Returns True if it works
        float(s)
        return True
    except ValueError:
        return False

def signal_handler( signal, frame):
    """ Set up Ctrl-C Handling

    This function sets up signal interrupt catching, primarily to handle Ctrl-C.

    Parameters
    ----------
    signal: signal
        Signal to catch.
    frame: frame
        frame
    """

    print("Exiting due to SIGINT")
    sys.exit(0)

### Database ###
def reset_db_keys():
    """Runs the 'db_sequence_reset' script in a subprocess to reset the postgres primary keys, and waits for the
    subprocess to finish. Without this reset, inserts that insert at a certain ID do not properly update the keys, so
    the next inserts will sometimes attempt to insert on the same id, which fails.  This approach may lead to some gaps
    in ids, but it will be more fault tolerant than it is currently.

    """
    if os.environ["DATA_STORE_PATH"]:
        script = os.environ["DATA_STORE_PATH"] + "db_sequence_reset.sh"
    else:
        script = "/vagrant/data_store/data/db_upgrade.sh"

    p = subprocess.Popen(["bash", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()


def load_dumpfile():
    """Runs the 'db_load' script in a subprocess to load a postgresql database dump into the database, and waits for the
    subprocess to finish.

    """
    if os.environ["DATA_STORE_PATH"]:
        script = os.environ["DATA_STORE_PATH"] + "db_load.sh"
    else:
        script = "/vagrant/data_store/data/db_upgrade.sh"

    p = subprocess.Popen(["bash", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()


def upgrade_db():
    """Runs the 'db_migrate' script in a subprocess to migrate the database using 'alembic'.

    """
    if os.environ["DATA_STORE_PATH"]:
        script = os.environ["DATA_STORE_PATH"] + "db_upgrade.sh"
    else:
        script = "/vagrant/data_store/data/db_upgrade.sh"

    p = subprocess.Popen(["bash", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()

def table_exists(table_name, curr):
    """Checks whether a table with name 'table_name' exists in the database.

    Parameters
    ----------
    table_name: string
        Name of the postgresql table to be checked.
    curr: database cursor

    Returns
    -------
    result: boolean
        Returns True if the table exists, otherwise False.

    """
    SQL = "SELECT relname FROM pg_class WHERE relname = %s;"
    curr.execute(SQL, (table_name,))
    if curr.fetchone() is None:
        return False
    else:
        return True


def drop_table(table_name, curr):
    """Drops the database table with the name 'table_name'

    Parameters
    ----------
    table_name: string
        Name of table to drop.
    curr: database cursor

    """
    SQL = "DROP TABLE IF EXISTS %s;"
    try:
        curr.execute(SQL, (table_name,))
    except Exception, e:
        print(e)


def create_table_from_file(filename, curr):
    """Reads in a data file written in postgresql and executes the contents in the database

    Parameters
    ----------
    filename: string
        Name of the file to read from.
    curr: database cursor
    """
    f = open(filename)
    try:
        curr.execute(f.read())
    except Exception, e:
        print(e)


def initialize_database(curr, path="schema/"):
    """Initializes the database with the schemas in the "path" directory. Current tables to be created are:

    - users

    - sites

    - instruments

    - instrument_logs

    - usage

    - prosensing_paf

    - event_codes

    - events_with_text

    - events_with_value

    - pulse_captures

    - table_references

    - instrument_data_references

    If the table does not already exist, creates it from the file 'path/table_name.schema'

    Parameters
    ----------
    curr: database cursor
    path: string, optional
        Path that the schema files are expected to be in, defaults to "schema/".

    """
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


def load_data_into_table(filename, table):
    """Loads a comma separated (no spaces) file 'filename' into the database table 'table'.

    Example data file "table_name.schema":

    | column_name_1,column_name_2
    | row_1_column_1_value,row_1_column_2_value
    | row_2_column_1_value,row_2_column_2_value
    | ...
    | (etc.)

    Parameters
    ----------
    filename: string
        Name of the file to load into the table.
    table: string
        Name of the table to load the file into.
    conn: database connection

    """
    df = pandas.read_csv(filename)
    db_cfg = config.get_config_context()['database']
    s_db_cfg = config.get_config_context()['s_database']
    engine = create_engine('postgresql://%s:%s@%s:%s/%s' %
                           (db_cfg['DB_USER'], s_db_cfg['DB_PASS'], db_cfg['DB_HOST'], db_cfg['DB_PORT'], db_cfg['DB_NAME']))
    df.to_sql(table, engine, if_exists='append', index=False, chunksize=900)


def dump_table_to_csv(filename, table, server=None):
    """Dumps the database table named 'table' as a comma separated file into 'filename', from database server 'server' if supplied.

    Parameters
    ----------
    filename: string
        Name of the file to be written to.
    table: string
        Name of the database table to dump into a file.
    server: sqlalchemy engine, optional
        A sqlalchemy engine for whichever database server the data will be read from, defaults to the default WARNO server.

    """
    if server is None:
        db_cfg = config.get_config_context()['database']
        s_db_cfg = config.get_config_context()['s_database']
        engine = create_engine('postgresql://%s:%s@%s:%s/%s' %
                           (db_cfg['DB_USER'], s_db_cfg['DB_PASS'], db_cfg['DB_HOST'], db_cfg['DB_PORT'], db_cfg['DB_NAME']))
    else:
        server = create_engine(server)

    df = pandas.read_sql_table(table, server)
    df.to_csv(filename, index=False)


def connect_db():
    """ Connects to the default WARNO database server.
    Returns
    -------
    psychopg2 connection object for the WARNO database server.

    """
    db_cfg = config.get_config_context()['database']
    s_db_cfg = config.get_config_context()['s_database']
    engine = create_engine('postgresql://%s:%s@%s:%s/%s' %
                           (db_cfg['DB_USER'], s_db_cfg['DB_PASS'], db_cfg['DB_HOST'], db_cfg['DB_PORT'], db_cfg['DB_NAME']))

