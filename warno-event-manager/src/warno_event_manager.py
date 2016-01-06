from flask import Flask, request, g
import requests
import psutil
import os
import json
import yaml
import psycopg2
import time

import database.utility

app = Flask(__name__)

cfg = None
ticks = 0
tocks = 0

DB_HOST = '192.168.50.100'
DB_NAME = 'warno'
DB_USER = 'warno'
DB_PASS = 'warno'
config_path = "/opt/data/config.yml"

is_central = 0
cf_url = ""
headers = {'Content-Type': 'application/json', 'Host': "warno-event-manager.local"}


def connect_db():
    """Connect to database.

    Returns
    -------
    A Psycopg2 connection object to the default database.
    """

    return psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (DB_HOST, DB_NAME, DB_USER, DB_PASS))


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
    -------
    exception: optional, Exception
        An Exception that may have caused the teardown.
    """

    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route("/eventmanager/event", methods=['POST'])
def event():
    msg = request.data
    msg_struct = dict(json.loads(msg))

    msg_event_code = msg_struct['Event_Code']
    # Request for the event code for a given description
    if msg_event_code == 1:
        save_instrument_data_reference(msg, msg_struct)
        return get_event_code(msg, msg_struct)

    # Request a site id from site name
    elif msg_event_code == 2:
        return get_site_id(msg, msg_struct)

    # Request an instrument id from instrument name
    elif msg_event_code == 3:
        return get_instrument_id(msg, msg_struct)
    elif msg_event_code == 4:
        return save_pulse_capture(msg, msg_struct)
    # Event is special case: 'prosensing_paf' structure
    elif msg_event_code == 5:
        return save_special_prosensing_paf(msg, msg_struct)

    # Any other event
    else:
        cur = g.db.cursor()
        timestamp = time.asctime(time.gmtime(msg_struct['Data']['Time']))
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
    cur = g.db.cursor()
    timestamp = time.asctime(time.gmtime(msg_struct['Data']['Time']))
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
    cur = g.db.cursor()
    timestamp = time.asctime(time.gmtime(msg_struct['Data']['Time']))
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
    cur = g.db.cursor()
    cur.execute('''SELECT * FROM instruments where name_short = %s''', (msg_struct['Data'],))
    row = cur.fetchone()

    # If there is an instrument with a matching name, returns all info to a site or just the id to an agent.
    if row:
        if is_central:
            print("Found Existing Instrument")
            return '{"Event_code": 3, "Data": {"Instrument_Id": %s, "Site_Id": %s, "Name_Short": "%s", "Name_Long": "%s", "Type": "%s", "Vendor": "%s", "Description": "%s", "Frequency_Band": "%s"}}' % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
        else:
            print("Found Existing Instrument")
            return '{"Instrument_Id": %i, "Data": "%s"}' % (row[0], msg_struct['Data'])
    else:
        # If it does not exist at the central facility, returns an error indicator
        if is_central:
            return '{"Instrument_Id": -1}'
        # If it does not exist at a site, requests the site information from the central facility
        else:
            print "\n\nmessage ************* %s ************\n\n" % msg
            payload = json.loads(msg)
            print "\n\npayload *********** %s ************\n\n" % msg
            response = requests.post(cf_url, json=payload, headers=headers)
            print "\n\nresponst ************** %s ***********\n\n" % response
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
    cur = g.db.cursor()
    cur.execute('''SELECT * FROM sites where name_short = %s''', (msg_struct['Data'],))
    row = cur.fetchone()

    # If there is a site with a matching name, returns all info to a site or just the id to an agent.
    if row:
        if is_central:
            print("Found Existing Site")
            return '{"Event_code": 2, "Data": {"Site_Id": %s, "Name_Short": "%s", "Name_Long": "%s", "Latitude": "%s", "Longitude": "%s", "Facility": "%s", "Mobile": "%s", "Location_Name": "%s"}}' % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
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


def load_config():
    """Load the configuration Object from the config file

    Loads a configuration Object from the config file.

    Returns
    -------
    config: dict
        Configuration Dictionary of Key Value Pairs
    """
    with open(config_path, 'r') as ymlfile:
        config = yaml.load(ymlfile)
    return config


def initialize_database():
    print("Initialization Function")
    db = database.utility.connect_db()
    cur = db.cursor()

    database.utility.initialize_database(cur, path="database/schema")
    db.commit()

    cur.execute("SELECT * FROM users LIMIT 1")
    if cur.fetchone() == None:
        print("Populating Users")
        database.utility.load_data_into_table("database/schema/users.data", "users", db)
    else:
        print("Users in table.")

    cur.execute("SELECT * FROM sites LIMIT 1")
    if cur.fetchone() == None:
        print("Populating Sites")
        database.utility.load_data_into_table("database/schema/sites.data", "sites", db)
    else:
        print("Sites in table.")

@app.route('/eventmanager')
def hello_world():
    ret_message = 'Hello World! Event Manager is operational. CPU Usage on Event Manager VM is: %g \n ' % psutil.cpu_percent()
    ret_message2 = '\n Site is: %s' % os.environ.get('SITE')
    return ret_message + ret_message2


if __name__ == '__main__':
    cfg = load_config()

    if cfg['type']['central_facility']:
        is_central = 1
        DB_HOST = "192.168.50.100"
    else:
        cf_url = cfg['setup']['cf_url']

    initialize_database()

    app.run(host='0.0.0.0', port=80, debug=True)
