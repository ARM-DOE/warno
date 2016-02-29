from flask import Flask, request, g
import requests
import psutil
import os
import json
import yaml
import psycopg2
import time

from WarnoConfig import config
from WarnoConfig import utility

app = Flask(__name__)

cfg = None
ticks = 0
tocks = 0

config_path = "/opt/data/config.yml"

is_central = 0
cf_url = ""
headers = {'Content-Type': 'application/json'}


def connect_db():
    """Connect to database.

    Returns
    -------
    A Psycopg2 connection object to the default database.
    """

    db_cfg = config.get_config_context()['database']
    return psycopg2.connect("host=%s dbname=%s user=%s password=%s" %
                            (db_cfg['DB_HOST'], db_cfg['DB_NAME'], db_cfg['DB_USER'], db_cfg['DB_PASS']))


@app.before_request
def before_request():
    """Before each Request.

    Connects to the database.
    """
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    """Teardown for Requests.

    Closes the database connection if connected.

    Parameters
    ----------
    exception: optional, Exception
        An Exception that may have caused the teardown.
    """

    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route("/eventmanager/event", methods=['POST'])
def event():
    """Event comes as a web request with a JSON packet.  The JSON is loaded into dictionary, and the event code is extracted.
    Dependent on the event code, different functions are called.

    If it is part of a predefined set of special event codes, calls a new function to handle it, depending on the
    event code.  Passes the message in to the call, then returns the return of whichever sub-function was called.

    If it is not a special case, it extracts the information from the packet and saves the event to the database.
    If the 'is_central' flag is not set, it then forwards the packet on to the 'cf_url' (both specified in *config.yml*).

    Returns
    -------
    The original message packet if a sub-function was not called, the sub-function's return if it was called.

    """
    msg = request.data
    msg_struct = dict(json.loads(msg))

    msg_event_code = msg_struct['Event_Code']
    # Request for the event code for a given description
    if msg_event_code == utility.EVENT_CODE_REQUEST:
        save_instrument_data_reference(msg, msg_struct)
        return get_event_code(msg, msg_struct)

    # Request a site id from site name
    elif msg_event_code == utility.SITE_ID_REQUEST:
        return get_site_id(msg, msg_struct)

    # Request an instrument id from instrument name
    elif msg_event_code == utility.INSTRUMENT_ID_REQUEST:
        return get_instrument_id(msg, msg_struct)
    elif msg_event_code == utility.PULSE_CAPTURE:
        return save_pulse_capture(msg, msg_struct)
    # Event is special case: 'prosensing_paf' structure
    elif msg_event_code == utility.PROSENSING_PAF:
        return save_special_prosensing_paf(msg, msg_struct)

    # Any other event
    else:
        cur = g.db.cursor()
        timestamp = msg_struct['Data']['Time']
        try:
            # If it can cast as a number, save as a number.  If not, save as text
            value = float(msg_struct['Data']['Value'])
            cur.execute("INSERT INTO events_with_value(event_code, instrument_id, time, value) VALUES (%s, %s, %s, %s)",
                        (msg_event_code, msg_struct['Data']['Instrument_Id'], timestamp, value))
            cur.execute("COMMIT")
            print("Saved Value Event")
        except ValueError:
            cur.execute("INSERT INTO events_with_text(event_code, instrument_id, time, text) VALUES (%s, %s, %s, %s)",
                        (msg_event_code, msg_struct['Data']['Instrument_Id'], timestamp, msg_struct['Data']['Value']))
            cur.execute("COMMIT")
            print("Saved Text Event")
        # If application is at a site instead of the central facility, passes data on to be saved at central facility
        if not is_central:
            payload = json.loads(msg)
            requests.post(cf_url, json=payload, headers=headers)
        return msg


def save_special_prosensing_paf(msg, msg_struct):
    """Inserts the information given in 'msg_struct' into the database, with all of the values being mapped into columns
    for the database.  If the 'is_central' flag is not set, it then forwards the packet on to the 'cf_url'
    (both specified in *config.yml*).

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format:
        {Event_Code: *code*, Data: {Time: *ISO DateTime*, Site_Id: *Integer*, Instrument_Id: *Integer*,
        Value: *Dictionary of database column names mapped to their values*}}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    Returns
    -------
    The original message 'msg' passed to it.

    """

    cur = g.db.cursor()
    timestamp = msg_struct['Data']['Time']
    sql_query_a = "INSERT INTO prosensing_paf(time, site_id, instrument_id"
    sql_query_b = ") VALUES ('%s', %s, %s" % (timestamp, msg_struct['Data']['Site_Id'], msg_struct['Data']['Instrument_Id'])
    for key, value in msg_struct['Data']['Value'].iteritems():
        sql_query_a = ', '.join([sql_query_a, key])
        try:
            float(value)
            sql_query_b = ', '.join([sql_query_b, "%s" % value])
        except ValueError:
            sql_query_b = ', '.join([sql_query_b, "'%s'" % value])
    sql_query = ''.join([sql_query_a, sql_query_b, ")"])

    cur.execute(sql_query)
    cur.execute("COMMIT")
    "Saved Special Type: Prosensing PAF"

    if not is_central:
        payload = json.loads(msg)
        requests.post(cf_url, json=payload, headers=headers)
    return msg


def save_pulse_capture(msg, msg_struct):
    """Inserts the information given in 'msg_struct' into the database 'pulse_captures' table, with all of the values
    being mapped into columns for the database.  If the 'is_central' flag is not set, it then forwards the packet on
    to the 'cf_url' (both specified in *config.yml*).

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format:
        {Event_Code: *code*, Data: {Time: *ISO DateTime*, Site_Id: *Integer*, Instrument_Id: *Integer*,
        Value: *Array of Floats*}}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    Returns
    -------
    The original message 'msg' passed to it.

    """

    cur = g.db.cursor()
    timestamp = msg_struct['Data']['Time']
    sql_query = ("INSERT INTO pulse_captures(time, instrument_id, data)"
                 " VALUES ('%s', %s, ARRAY%s)") % (timestamp, msg_struct['Data']['Instrument_Id'], msg_struct['Data']['Value'])

    cur.execute(sql_query)
    cur.execute("COMMIT")
    "Saved Pulse Capture"

    if not is_central:
        payload = json.loads(msg)
        requests.post(cf_url, json=payload, headers=headers)
    return msg

def get_instrument_id(msg, msg_struct):
    """Searches the database for any instruments where the instrument abbreviation matches 'msg_struct['Data']'.  If the
    'is_central' flag is set and there is no instrument, returns a -1 to indicate nothing was found, but if it was found,
    returns the instrument's information to be saved. If the 'is_central' flag is not set, it then forwards the
    packet on to the 'cf_url' (both specified in *config.yml*) and returns whatever the central facility determines
    the instrument id is, saving the returned site.

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format: {Event_Code: *code*, Data: *instrument abbreviation*}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    Returns
    -------
    The instrument id or information determined by the function.

    If returned from the central facility, returned in the form of a string structured as
    {"Event_code": *integer event code*, "Data": {"Instrument_Id": *integer instrument id*, "Site_Id":
    *integer site id instrument is at*, "Name_Short": *string instrument abbreviation*, "Name_Long":
    *string full instrument name*, "Type": *string type of instrument*, "Vendor": *string instrument's vendor*,
    "Description": *string description of instrument*, "Frequency_Band":
    *two character frequency band instrument operates at*}}.

    If returned from the non central event manager to the agent, sends a simplified version
    '{"Instrument_Id: *integer instrument id*}'.

    If no instrument was found, the instrument id is passed as -1.

    """
    cur = g.db.cursor()
    cur.execute('''SELECT * FROM instruments where name_short = %s''', (msg_struct['Data'],))
    row = cur.fetchone()

    # If there is an instrument with a matching name, returns all info to a site or just the id to an agent.
    if row:
        if is_central:
            print("Found Existing Instrument")
            return '{"Event_code": %i, "Data": {"Instrument_Id": %s, "Site_Id": %s, "Name_Short": "%s", "Name_Long": "%s", "Type": "%s", "Vendor": "%s", "Description": "%s", "Frequency_Band": "%s"}}' % (utility.INSTRUMENT_ID_REQUEST, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
        else:
            print("Found Existing Instrument")
            return '{"Instrument_Id": %i, "Data": "%s"}' % (row[0], msg_struct['Data'])
    else:
        # If it does not exist at the central facility, returns an error indicator
        if is_central:
            return '{"Instrument_Id": -1}'
        # If it does not exist at a site, requests the site information from the central facility
        else:
            payload = json.loads(msg)
            response = requests.post(cf_url, json=payload, headers=headers)
            cf_msg = dict(json.loads(response.content))
            cf_data = cf_msg['Data']
            # Need to add handler for if there is a bad return from CF (if clause above)
            cur.execute('''INSERT INTO instruments(instrument_id, site_id, name_short, name_long, type, vendor, description, frequency_band)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                        (cf_data['Instrument_Id'], cf_data['Site_Id'], cf_data['Name_Short'], cf_data['Name_Long'],
                         cf_data['Type'], cf_data['Vendor'], cf_data['Description'], cf_data['Frequency_Band']))
            cur.execute("COMMIT")
            print ("Saved New Instrument")
            return '{"Instrument_Id": %i}' % cf_data['Instrument_Id']


def get_site_id(msg, msg_struct):
    """Searches the database for any sites where the site abbreviation matches 'msg_struct['Data']'.  If the
    'is_central' flag is set and there is no site, returns a -1 to indicate nothing was found, but if it was found,
    returns the site's information to be saved. If the 'is_central' flag is not set, it then forwards the packet on
    to the 'cf_url' (both specified in *config.yml*) and returns whatever the central facility determines the site
    id is, saving the returned site.

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format: {Event_Code: *code*, Data: *site abbreviation*}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    Returns
    -------
    The site id or information determined by the function.

    If returned from the central facility, returned in the form of a string structured as
    {"Event_code": *integer event code*, "Data": {"Site_Id": *integer site id*, "Latitude":
    *float latitude coordinate*, "Longitude": *float longitude coordinate*, "Name_Short": *string site abbreviation*, "Name_Long":
    *string full site name*, "Facility": *string facility name*, "Mobile": *boolean true if is a mobile site*,
    "Location Name": *string location name*}}.
    
    If returned from the non central event manager to the agent, sends a simplified version
    '{"Site_Id: *integer site id*}'.

    If no site was found, the site id is passed as -1.

    """
    cur = g.db.cursor()
    cur.execute('''SELECT * FROM sites where name_short = %s''', (msg_struct['Data'],))
    row = cur.fetchone()

    # If there is a site with a matching name, returns all info to a site or just the id to an agent.
    if row:
        if is_central:
            print("Found Existing Site")
            return '{"Event_code": %i, "Data": {"Site_Id": %s, "Name_Short": "%s", "Name_Long": "%s", "Latitude": "%s", "Longitude": "%s", "Facility": "%s", "Mobile": "%s", "Location_Name": "%s"}}' % (utility.SITE_ID_REQUEST, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
        else:
            print("Found Existing Site")
            return '{"Site_Id": %i, "Data": "%s"}' % (row[0], msg_struct['Data'])
    else:
        # If it does not exist at the central facility, returns an error indicator
        if is_central:
            return '{"Site_Id": -1}'
        # If it does not exist at a site, requests the site information from the central facility
        else:
            payload = json.loads(msg)
            response = requests.post(cf_url, json=payload, headers=headers)
            cf_msg = dict(json.loads(response.content))
            cf_data = cf_msg['Data']
            # Need to add handler for if there is a bad return from CF (if clause above)
            cur.execute('''INSERT INTO sites(site_id, name_short, name_long, latitude, longitude, facility, mobile, location_name)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                        (cf_data['Site_Id'], cf_data['Name_Short'], cf_data['Name_Long'], cf_data['Latitude'],
                         cf_data['Longitude'], cf_data['Facility'], cf_data['Mobile'], cf_data['Location_Name']))
            cur.execute("COMMIT")
            print ("Saved New Site")
            return '{"Site_Id": %i}' % cf_data['Site_Id']


def save_instrument_data_reference(msg, msg_struct):
    """Checks to see if there is already an instrument data reference for this event code, and if there isn't, creates
    one. Instrument data references are used to allow the servers to track which events are pertinent to a particular
    instrument (some events are for all instruments, some only for specific instrument types).  If an instrument data
    reference is to be added, this function also determines whether the reference is 'special' or not.  If there is an
    entire special table devoted to the event (where 'description' is the table name), then it is classified as 'special'.

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format:
        {Event_Code: *code*, Data: {instrument_id: *instrument id*, description: *event description*}}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    """
    print("Message Struct for Data Reference: %s", msg_struct)
    cur = g.db.cursor()
    cur.execute('''SELECT * FROM instrument_data_references WHERE instrument_id = %s AND description = %s''', (msg_struct['Data']['instrument_id'], msg_struct['Data']['description']))
    rows = cur.fetchall()
    if not rows:
        special = "false"
        # "special" indicates whether this particual data description has its own table
        cur.execute('''SELECT column_name FROM information_schema.columns WHERE table_name = %s''', (msg_struct['Data']['description'],))
        rows = cur.fetchall()
        if rows:
            special = "true"
        cur.execute('''INSERT INTO instrument_data_references(instrument_id, description, special) VALUES (%s, %s, %s)''', (msg_struct['Data']['instrument_id'], msg_struct['Data']['description'], special))
        cur.execute("COMMIT")
        print("Saved new instrument data reference")


def get_event_code(msg, msg_struct):
    """Searches the database for any event codes where the description matches 'msg_struct['Data']'.  If the
    'is_central' flag is set and there is no event code, creates the event code in the database and returns it. If the
    'is_central' flag is not set, it then forwards the packet on to the 'cf_url' (both specified in *config.yml*) and
    returns whatever the central facility determines the event code is.

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format: {Event_Code: *code*, Data: *description*}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    Returns
    -------
    The site id determined by the function, in the form of a string structured as
    '{"Site_Id: *site id*}'.

    """
    cur = g.db.cursor()
    cur.execute('''SELECT event_code FROM event_codes WHERE description = %s''', (msg_struct['Data']['description'],))
    row = cur.fetchone()

    # If the event code defined here, return it downstream
    if row:
        print("Found Existing Event Code")
        return '{"Event_Code": %i, "Data": {"description": "%s", "instrument_id": %s}}' % (row[0], msg_struct['Data']['description'], msg_struct['Data']['instrument_id'])
    # If it is not defined at the central facility, inserts a new entry into the table and returns the new code
    elif is_central:
        cur.execute('''INSERT INTO event_codes(description) VALUES (%s)''', (msg_struct['Data']['description'],))
        cur.execute("COMMIT")
        cur.execute("SELECT event_code FROM event_codes WHERE description = %s", (msg_struct['Data']['description'],))
        row = cur.fetchone()
        new_event_code = row[0]

        print("Created New Event Code")
        return '{"Event_Code": %i, "Data": {"description": "%s", "instrument_id": %s}}' % (new_event_code, msg_struct['Data']['description'], msg_struct['Data']['instrument_id'])
    # If it is not defined at a site, requests the event code from the central facility
    else:
        payload = json.loads(msg)
        response = requests.post(cf_url, json=payload, headers=headers)
        cf_msg = dict(json.loads(response.content))
        cur.execute('''INSERT INTO event_codes(event_code, description) VALUES (%s, %s)''',
                    (cf_msg['Event_Code'], cf_msg['Data']['description']))
        cur.execute("COMMIT")
        print("Saved Event Code")
        return '{"Event_Code": %i, "Data": {"description": "%s", "instrument_id": %s}}' % (cf_msg['Event_Code'], cf_msg['Data']['description'], cf_msg['Data']['instrument_id'])



def initialize_database():
    """Initializes the database.  If the database is specified in config.yml as a 'test_db', the database is wiped when
    at the beginning to ensure a clean load.  If it is not a test database, a utility function is called to attempt to
    load in a postgresql database dumpfile if it exists.  First, the tables are initialized, and then if no basic database
    entries exists (users, sites, event codes), they are created.  Then, if it is designated a test database, any table
    that does not contain any entries will be filled with demo data.

    """
    print("Initialization Function")
    db = utility.connect_db()
    cur = db.cursor()

    # If it is a test database, first wipe and clean up the database.
    if cfg['database']['test_db']:
        cur.execute("DROP SCHEMA public CASCADE;")
        cur.execute("CREATE SCHEMA public;")
        db.commit()
    else:
        # If it is not a test database, first attempt to load database from an existing postgres dumpfile
        utility.load_dumpfile()

    utility.initialize_database(cur, path="database/schema")
    db.commit()

    cur.execute("SELECT * FROM users LIMIT 1")
    if cur.fetchone() == None:
        print("Populating Users")
        utility.load_data_into_table("database/schema/users.data", "users", db)
    else:
        print("Users in table.")

    cur.execute("SELECT * FROM sites LIMIT 1")
    if cur.fetchone() == None:
        print("Populating Sites")
        utility.load_data_into_table("database/schema/sites.data", "sites", db)
    else:
        print("Sites in table.")

    cur.execute("SELECT * FROM event_codes LIMIT 1")
    if cur.fetchone() == None:
        print("Populating Sites")
        utility.load_data_into_table("database/schema/event_codes.data", "event_codes", db)
    else:
        print("Event_codes in table.")


    # If it is set to be a test database, populate extra information.
    if cfg['database']['test_db']:
        print ("Test Database Triggered")
        test_tables = [
                       "instruments",
                       "instrument_logs",
                       "prosensing_paf",
                       "events_with_text",
                       "events_with_value",
                       "pulse_captures",
                       "table_references",
                       "instrument_data_references"
                   ]
        for table in test_tables:
            cur.execute("SELECT * FROM %s LIMIT 1" % table)
            if cur.fetchone() == None:
                print("Populating %s" % table)
                utility.load_data_into_table("database/schema/%s.data" % table, table, db)
            else:
                print("Sites in table.")
    else:
        print ("Test Database is a falsehood")

@app.route('/eventmanager')
def hello_world():
    """Calculates very basic information and returns a string with it.  Used to verify that the event manager is
    operational and accessible from the outside.

    Returns
    -------
    String message with basic information such as current CPU usage.
    """
    ret_message = 'Hello World! Event Manager is operational. CPU Usage on Event Manager VM is: %g \n ' % psutil.cpu_percent()
    ret_message2 = '\n Site is: %s' % os.environ.get('SITE')
    return ret_message + ret_message2


if __name__ == '__main__':
    cfg = config.get_config_context()

    if cfg['type']['central_facility']:
        is_central = 1
    else:
        cf_url = cfg['setup']['cf_url']

    initialize_database()

    app.run(host='0.0.0.0', port=80, debug=True)
