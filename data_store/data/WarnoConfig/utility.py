import sys
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
PROSENSING_PAF = 5

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
        Signal to catch
    frame: frame
        frame
    """

    print("Exiting due to SIGINT")
    sys.exit(0)


### Database ###
def load_dumpfile():
    #cmd = "ls /vagrant; ls /vagrant/data_store; ls vagrant/data_store/data"#; bash /vagrant/data_store/data/db_load.sh"
    p = subprocess.Popen(["bash", "/vagrant/data_store/data/db_load.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()

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