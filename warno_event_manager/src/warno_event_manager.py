import datetime
import requests
import logging
import psutil
import json
import csv
import os

from flask import Flask, request, render_template, redirect, url_for
from flask_migrate import Migrate, upgrade
from flask_migrate import migrate as db_migrate
from flask_migrate import downgrade

from WarnoConfig import config
from WarnoConfig import utility
from WarnoConfig.models import db
from WarnoConfig.models import EventWithValue, EventWithText, ProsensingPAF, InstrumentDataReference, User
from WarnoConfig.models import Instrument, Site, InstrumentLog, PulseCapture, EventCode


# Set up logging
LOG_PATH = os.environ.get("LOG_PATH")
if LOG_PATH is None:
    LOG_PATH = "/vagrant/logs/"

# Logs to the main log
logging.basicConfig(format='%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s',
                    filename='%scombined.log' % LOG_PATH,
                    filemode='a', level=logging.DEBUG)

# Logs to the event manager log
EM_LOGGER = logging.getLogger(__name__)
EM_HANDLER = logging.FileHandler("%sevent_manager_server.log" % LOG_PATH, mode="a")
EM_HANDLER.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
EM_LOGGER.addHandler(EM_HANDLER)
# Add event manager handler to the main werkzeug logger
logging.getLogger("werkzeug").addHandler(EM_HANDLER)


# Located http://flask.pocoo.org/snippets/35/
class ReverseProxied(object):
    """Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    In nginx:
    location /myprefix {
    proxy_pass http://192.168.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Scheme $scheme;
    proxy_set_header X-Script-Name /myprefix;
    }

    Parameters
    ----------
    given_app: the WSGI application

    """
    def __init__(self, given_app):
        self.app = given_app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        server = environ.get('HTTP_X_FORWARDED_SERVER', '')
        if server:
            environ['HTTP_HOST'] = server
        return self.app(environ, start_response)

app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)

# Database Setup
db_cfg = config.get_config_context()['database']
s_db_cfg = config.get_config_context()['s_database']
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%s:%s@%s:%s/%s' % (db_cfg['DB_USER'], s_db_cfg['DB_PASS'],
                                                                         db_cfg['DB_HOST'], db_cfg['DB_PORT'],
                                                                         db_cfg['DB_NAME'])
db.init_app(app)
migrate = Migrate(app, db)
migration_path = os.environ.get("MIGRATION_PATH")

is_central = 0
cf_url = ""
cfg = None

headers = {'Content-Type': 'application/json'}

cert_verify = False


def save_json_db_info():
    """Saves database tables containing more permanent information, such as sites or instruments, to a json file.
    File name has the format 'db_info_*day*_*month*_*year*', where the date corresponds to the date the function was run,
    because it shows the current status of the database.

    Example File (indentation unnecessary):

    [
        {
            "definition":
                {

                    "table_name":
                        *database table name*,

                    "columns":
                        [(column_name_1, column_type_1), ..., (column_name_N, column_type_N)]

                }

            "data":
                [
                [val_1, val_2, ..., val_N],
                [val_1, val_2, ..., val_N],
                ...,
                [val_1, val_2, ..., val_N] ]

            },

            { *table_2* },

            ...,

            { *table_N* }

        ]

    """

    save_time = datetime.datetime.now()
    filename = "db_info_" + str(save_time.day) + "_" + str(save_time.month) + "_" + str(save_time.year) + "_t_" +\
               str(save_time.hour) + "_" + str(save_time.minute) + ".json"
    tables = ["event_codes", "users", "sites", "instruments", "instrument_data_references"]

    first_table = True

    with open(filename, "w") as datafile:
        # Begin the list of tables
        datafile.write("[")
        # Only prepend a comma separation if it is not the first table to be saved
        for table in tables:
            if not first_table:
                datafile.write(", ")
            else:
                first_table = False

            datafile.write('{"definition": ')

            definition = dict()
            definition['table_name'] = table

            rows = db.session.execute("SELECT column_name, data_type FROM information_schema.columns "
                                      "WHERE table_name = :table", dict(table=table)).fetchall()
            definition['columns'] = [(row[0], row[1]) for row in rows]

            # Write the definition and start the data section, with its list of records
            json.dump(definition, datafile)
            datafile.write(', "data": [')

            first_record = True
            rows = db.session.execute("SELECT * FROM %s" % (table,)).fetchall()

            data = [list(row) for row in rows]

            # Datetimes must be converted to iso compliant time format for json.dump
            # Different tables have time in different places

            for record in data:
                # If the record is not the first, prepends a comma separation to separate the list elements
                if not first_record:
                    datafile.write(", ")
                else:
                    first_record = False
                json.dump(record, datafile)

            # Close the JSON for this table section
            datafile.write("]}")
        # Close the list of tables
        datafile.write("]")


@app.route("/eventmanager/archive_data")
def save_json_db_data():
    """Saves database tables containing data information, such as 'events_with_value' or 'prosensing_paf' events, to a
    json file.  'num_entries' for each table specifies how many data rows are in the file for the table, making
    iterative parsing much easier.

    Example File (indentation unnecessary):

    [
        {
            "definition":
                {

                    "table_name":
                        *database table name*,

                    "columns":
                        [(column_name_1, column_type_1), ..., (column_name_N, column_type_N)]

                }

            "data":
                [
                [val_1, val_2, ..., val_N],
                [val_1, val_2, ..., val_N],
                ...,
                [val_1, val_2, ..., val_N] ]

            },

            { *table_2* },

            ...,

            { *table_N* }

        ]

    """
    # Get the cutoff time for the data.  Any data recorded before this time will be saved to json and deleted from the
    # database
    cutoff_time = datetime.datetime.now() + datetime.timedelta(-db_cfg['days_retained'])

    # First save off the supplementary database table information (users, instruments, etc.)
    # File name format described next
    save_json_db_info()

    # Each data file saved will use this extension, resulting in "*id*_archived_*day*_*month*_*year*.json".
    # For example, for an instrument id of 5, the filename would be "5_archived_30_12_1999", meaning all the data in the
    # archived file is dated on or before 30th of December, 1999
    filename_extension = "_archived_" + str(cutoff_time.day) + "_" + str(cutoff_time.month) + \
                         "_" + str(cutoff_time.year) + "_t_" + str(cutoff_time.hour) + "_" + \
                         str(cutoff_time.minute) + ".json"

    # Names of the tables to be saved.
    tables = ["prosensing_paf", "events_with_value", "events_with_text", "instrument_logs", "pulse_captures"]

    # Get a list of instrument_ids, so that the data can be archived according to the instrument the data is for
    rows = db.session.execute("SELECT instrument_id FROM instruments").fetchall()
    instrument_ids = [row[0] for row in rows]

    for instrument_id in instrument_ids:
        filename = str(instrument_id) + filename_extension
        first_table = True
        with open(filename, "w") as datafile:
            # Begin the list of tables
            datafile.write("[")
            # Only prepend a comma separation if it is not the first table to be saved
            for table in tables:
                if not first_table:
                    datafile.write(", ")
                else:
                    first_table = False
                datafile.write('{\n"definition": ')

                definition = dict()
                definition['table_name'] = table

                # List of (column_name, data_type) pairs to define the format of each data row
                rows = db.session.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = :table",
                                          dict(table=table)).fetchall()
                definition['columns'] = [(row[0], row[1]) for row in rows]

                # If there are any values to be saved, defines the oldest as the 'start_time' and the newest as the
                # 'end_time'.  Together they allow anyone reading the file to easily get the time range of the values
                rows = db.session.execute("SELECT time FROM %s WHERE instrument_id = :id ORDER BY time ASC LIMIT 1" % (table,),
                                          dict(id=instrument_id)).fetchall()
                if len(rows) > 0:
                    # A little extra work to make the database time JSON serializable UTC
                    definition['start_time'] = rows[0][0].isoformat() + "Z"
                else:
                    definition['start_time'] = None

                rows = db.session.execute("SELECT time FROM %s WHERE instrument_id = :id ORDER BY time DESC LIMIT 1" % (table,),
                                          dict(id=instrument_id)).fetchall()
                if len(rows) > 0:
                    # A little extra work to make the database time JSON serializable UTC
                    definition['end_time'] = rows[0][0].isoformat() + "Z"
                else:
                    definition['end_time'] = None

                # Count the number of rows to be saved off.  Having this defined makes reading in the data easier
                count = db.session.execute("SELECT count(*) FROM %s WHERE time < :time AND instrument_id = :id" % (table,),
                                           dict(time=cutoff_time.isoformat(), id=instrument_id)).fetchall()[0][0]
                definition['num_entries'] = count

                # Write the definition and start the data section, with its list of records
                json.dump(definition, datafile)
                datafile.write(', "data": [')

                offset = 0
                chunk_size = 5000
                first_record = True
                while True:
                    # Using offset and chunk_size in conjunction, retrieves and saves chunks of 5000 records at a time
                    # Loop runs until no records are returned, then breaks
                    rows = db.session.execute("SELECT * FROM %s WHERE time < :time AND instrument_id = :id ORDER BY time ASC OFFSET :offset LIMIT :chunk_size" % (table,),
                                              dict(offset=offset, chunk_size=chunk_size, time=cutoff_time.isoformat(), id=instrument_id)).fetchall()
                    if len(rows) <= 0:
                        break

                    # The data must be a list to update values by index
                    data = [list(row) for row in rows]

                    # Datetimes must be converted to iso compliant time format for json.dump
                    # Different tables have time in different places
                    if table in ["prosensing_paf", "instrument_logs"]:
                        time_index = 1
                    elif table == "pulse_captures":
                        time_index = 2
                    else:
                        time_index = 3
                    for item in data:
                        item[time_index] = item[time_index].isoformat() + "Z"

                    # Encode each data row into a JSON string
                    data = [json.dumps(item) for item in data]

                    # If the record is not the first, prepends a comma separation to separate the list elements.
                    # The rows are joined by commas to make them JSON compliant
                    if not first_record:
                        msg = ", ".join(data)
                        datafile.write(", %s" % msg)
                    else:
                        first_record = False
                        msg = ", ".join(data)
                        datafile.write(msg)

                    offset += chunk_size
                # Close the JSON for this table section
                datafile.write("]}")
                db.session.execute("DELETE FROM %s WHERE time < :time AND instrument_id = :id" % (table,),
                                   dict(time=cutoff_time.isoformat(), id=instrument_id))
                db.session.commit()
            # Close the list of tables
            datafile.write("]\n")

    return "Finish"


@app.route("/eventmanager/event", methods=['POST'])
def event():
    """Event comes as a web request with a JSON packet.  The JSON is loaded into dictionary, and the
    event code is extracted. Dependent on the event code, different functions are called.

    If it is part of a predefined set of special event codes, calls a new function to handle it, depending on the
    event code.  Passes the message in to the call, then returns the return of whichever sub-function was called.

    If it is not a special case, it extracts the information from the packet and saves the event to the database.
    If the 'is_central' flag is not set, it then forwards the packet on to the 'cf_url'
    (both specified in *config.yml*).

    Returns
    -------
    The original message packet if a sub-function was not called, the sub-function's return if it was called.

    """
    msg = request.data
    msg_struct = dict(json.loads(msg))

    msg_event_code = msg_struct['event_code']
    # Request for the event code for a given description
    if msg_event_code == utility.EVENT_CODE_REQUEST:
        save_instrument_data_reference(msg_struct)
        return get_event_code(msg, msg_struct)

    # Request a site id from site name
    elif msg_event_code == utility.SITE_ID_REQUEST:
        return get_site_id(msg, msg_struct)

    # Request an instrument id from instrument name
    elif msg_event_code == utility.INSTRUMENT_ID_REQUEST:
        return get_instrument_id(msg, msg_struct)
    elif msg_event_code == utility.PULSE_CAPTURE:
        return save_pulse_capture(msg, msg_struct)
    elif msg_event_code == utility.INSTRUMENT_LOG:
        return save_instrument_log(msg, msg_struct)
    # Event is special case: 'prosensing_paf' structure
    elif msg_event_code == utility.PROSENSING_PAF:
        return save_special_prosensing_paf(msg, msg_struct)

    # Any other event
    else:
        timestamp = msg_struct['data']['time']
        try:
            # If it can cast as a number, save as a number.  If not, save as text
            float_value = float(msg_struct['data']['value'])
            event_wv = EventWithValue()
            event_wv.event_code_id = msg_event_code
            event_wv.time = timestamp
            event_wv.instrument_id = msg_struct['data']['instrument_id']
            event_wv.value = float_value

            db.session.add(event_wv)
            db.session.commit()
            EM_LOGGER.info("Saved Value Event")
        except ValueError:
            event_wt = EventWithText()
            event_wt.event_code_id = msg_event_code
            event_wt.time = timestamp
            event_wt.instrument_id = msg_struct['data']['instrument_id']
            event_wt.text = msg_struct['data']['value']

            db.session.add(event_wt)
            db.session.commit()
            EM_LOGGER.info("Saved Text Event")
        # If application is at a site instead of the central facility, passes data on to be saved at central facility
        if not is_central:
            payload = json.loads(msg)
            requests.post(cf_url, json=payload, headers=headers, verify=cert_verify)
        return "OK"


def save_special_prosensing_paf(msg, msg_struct):
    """Inserts the information given in 'msg_struct' into the database, with all of the values being mapped into columns
    for the database.  If the 'is_central' flag is not set, it then forwards the packet on to the 'cf_url'
    (both specified in *config.yml*).

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format:
        {event_code: *code*, data: {time: *ISO DateTime*, site_id: *Integer*, instrument_id: *Integer*,
        values: *Dictionary of database column names mapped to their values*}}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    """

    timestamp = msg_struct['data']['time']
    sql_query_a = "INSERT INTO prosensing_paf(time, site_id, instrument_id"
    sql_query_b = ") VALUES ('%s', %s, %s" % (timestamp, msg_struct['data']['site_id'],
                                              msg_struct['data']['instrument_id'])
    for key, value in msg_struct['data']['values'].iteritems():
        sql_query_a = ', '.join([sql_query_a, key])
        # Converts inf and -inf to Postgresql equivalents
        if "-inf" in str(value) or "inf" in str(value) or "-Inf" in str(value) or "Inf" in str(value):
            sql_query_b = ', '.join([sql_query_b, "NULL"])
        else:
            try:
                float(value)
                sql_query_b = ', '.join([sql_query_b, "%s" % value])
            except ValueError:
                sql_query_b = ', '.join([sql_query_b, "'%s'" % value.rstrip('\x00')])
    sql_query = ''.join([sql_query_a, sql_query_b, ")"])

    db.session.execute(sql_query)
    db.session.commit()

    if not is_central:
        payload = json.loads(msg)
        requests.post(cf_url, json=payload, headers=headers, verify=cert_verify)
    return "OK"


def save_instrument_log(msg, msg_struct):
    """Inserts the information given in 'msg_struct' into the database 'instrument_logs' table, with all of the values
    being mapped into columns for the database.

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format:
        {event_code: *code*, data: {time: *ISO DateTime*, author_id: *Integer*, instrument_id: *Integer*,
        status: *Integer Status Code*, contents: *Log Message*, supporting_images: *Image*}}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    """

    new_log = InstrumentLog()
    new_log.time = msg_struct['data']['time']
    new_log.instrument_id = msg_struct['data']['instrument_id']
    new_log.author_id = msg_struct['data']['author_id']
    new_log.status = msg_struct['data']['status']
    new_log.contents = msg_struct['data']['contents']
    new_log.supporting_images = msg_struct['data']['supporting_images']

    db.session.add(new_log)
    db.session.commit()

    return "OK"


def save_pulse_capture(msg, msg_struct):
    """
    Inserts the information given in 'msg_struct' into the database 'pulse_captures' table, with all of the values
    being mapped into columns for the database.  If the 'is_central' flag is not set, it then forwards the packet on
    to the 'cf_url' (both specified in *config.yml*).

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format: \
        {event_code: *code*, data: {time: *ISO DateTime*, site_id: *Integer*, instrument_id: *Integer*, \
        values: *Array of Floats*}}

    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    """

    new_pulse = PulseCapture()
    new_pulse.time = msg_struct['data']['time']
    new_pulse.instrument_id = msg_struct['data']['instrument_id']
    new_pulse.data = msg_struct['data']['values']

    db.session.add(new_pulse)
    db.session.commit()

    if not is_central:
        payload = json.loads(msg)
        requests.post(cf_url, json=payload, headers=headers, verify=cert_verify)
    return "OK"


def get_instrument_id(msg, msg_struct):
    """Searches the database for any instruments where the instrument abbreviation matches
    'msg_struct['instrument']'.  If the 'is_central' flag is set and there is no instrument,
    returns a -1 to indicate nothing was found, but if it was found, returns the instrument's
    information to be saved. If the 'is_central' flag is not set, it then forwards the
    packet on to the 'cf_url' (both specified in *config.yml*) and returns whatever the central
    facility determines the instrument id is, saving the returned site.

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format: {Event_Code: *code*, Data: *instrument abbreviation*}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    Returns
    -------
    The instrument id or information determined by the function.

    Returned in the form of a string structured as
    {"event_code": *integer event code*, "data": {"instrument_id": *integer instrument id*, "site_id":
    *integer site id instrument is at*, "name_short": *string instrument abbreviation*, "name_long":
    *string full instrument name*, "type": *string type of instrument*, "vendor": *string instrument's vendor*,
    "description": *string description of instrument*, "frequency_band":
    *two character frequency band instrument operates at*}}.

    If no instrument was found, the instrument id is passed as -1.

    """
    db_instrument = db.session.query(Instrument).filter(Instrument.name_short == msg_struct['data']['name']).\
        filter(Instrument.site_id == msg_struct['data']['site_id']).first()

    # If there is an instrument with a matching name, returns all info to a site or just the id to an agent.
    if db_instrument:
        EM_LOGGER.info("Found Existing Instrument")
        return '{"event_code": %i, "data": {"instrument_id": %s, "site_id": %s, "name_short": "%s", '\
               '"name_long": "%s", "type": "%s", "vendor": "%s", "description": "%s", "frequency_band": "%s"}}' \
               % (utility.INSTRUMENT_ID_REQUEST, db_instrument.id, db_instrument.site_id, db_instrument.name_short,
                  db_instrument.name_long, db_instrument.type, db_instrument.vendor,
                  db_instrument.description, db_instrument.frequency_band)
    else:
        # If it does not exist at the central facility, returns an error indicator
        if is_central:
            EM_LOGGER.error("Instrument could not be found at central facility")
            return '{"data": {"instrument_id": -1}}'
        # If it does not exist at a site, requests the site information from the central facility
        else:
            payload = json.loads(msg)
            response = requests.post(cf_url, json=payload, headers=headers, verify=cert_verify)
            cf_msg = dict(json.loads(response.content))
            cf_data = cf_msg['data']
            # Need to add handler for if there is a bad return from CF (if clause above)
            new_instrument = Instrument()
            new_instrument.id = cf_data['instrument_id']
            new_instrument.site_id = cf_data['site_id']
            new_instrument.name_short = cf_data['name_short']
            new_instrument.name_long = cf_data['name_long']
            new_instrument.type = cf_data['type']
            new_instrument.vendor = cf_data['vendor']
            new_instrument.description = cf_data['description']
            new_instrument.frequency_band = cf_data['frequency_band']

            db.session.add(new_instrument)
            db.session.commit()
            utility.reset_db_keys()

            EM_LOGGER.info("Saved New Instrument")
            return '{"event_code": %i, "data": {"instrument_id": %s, "site_id": %s, "name_short": "%s", ' \
                   '"name_long": "%s", "type": "%s", "vendor": "%s", "description": "%s", "frequency_band": "%s"}}' \
                   % (utility.INSTRUMENT_ID_REQUEST, cf_data['instrument_id'], cf_data['site_id'],
                      cf_data['name_short'], cf_data['name_long'], cf_data['type'], cf_data['vendor'],
                      cf_data['description'], cf_data['frequency_band'])


def get_site_id(msg, msg_struct):
    """Searches the database for any sites where the site abbreviation matches 'msg_struct['site']'.  If the
    'is_central' flag is set and there is no site, returns a -1 to indicate nothing was found, but if it was found,
    returns the site's information to be saved. If the 'is_central' flag is not set, it then forwards the packet on
    to the 'cf_url' (both specified in *config.yml*) and returns whatever the central facility determines the site
    id is, saving the returned site.

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format: {event_code: *code*, data: {site: *site abbreviation*}}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    Returns
    -------
    The site id or information determined by the function.

    Returned in the form of a string structured as
    {"event_code": *integer event code*, "data": {"site_id": *integer site id*, "latitude":
    *float latitude coordinate*, "longitude": *float longitude coordinate*, "name_short": *string site abbreviation*,
    "name_long": *string full site name*, "facility": *string facility name*,
    "mobile": *boolean true if is a mobile site*, "Location Name": *string location name*}}.


    If no site was found, the site id is passed as -1.

    """

    db_site = db.session.query(Site).filter(Site.name_short == msg_struct['data']).first()

    # If there is a site with a matching name, returns all info to a site or just the id to an agent.
    if db_site:
        EM_LOGGER.info("Found Existing Site")
        return '{"event_code": %i, "data": {"site_id": %s, "name_short": "%s", "name_long": "%s", "latitude": "%s", ' \
               '"longitude": "%s", "facility": "%s", "mobile": "%s", "location_name": "%s"}}' \
               % (utility.SITE_ID_REQUEST, db_site.id, db_site.name_short, db_site.name_long, db_site.latitude,
                  db_site.longitude, db_site.facility, db_site.mobile, db_site.location_name)

    else:
        # If it does not exist at the central facility, returns an error indicator
        if is_central:
            EM_LOGGER.error("Site could not be found at central facility")
            return '{"data": {"site_id": -1}}'
        # If it does not exist at a site, requests the site information from the central facility
        else:
            payload = json.loads(msg)
            response = requests.post(cf_url, json=payload, headers=headers, verify=cert_verify)
            cf_msg = dict(json.loads(response.content))
            cf_data = cf_msg['data']
            # Need to add handler for if there is a bad return from CF (if clause above)
            new_site = Site()
            new_site.id = cf_data['site_id']
            new_site.name_short = cf_data['name_short']
            new_site.name_long = cf_data['name_long']
            new_site.latitude = cf_data['latitude']
            new_site.longitude = cf_data['longitude']
            new_site.facility = cf_data['facility']
            new_site.mobile = cf_data['mobile']
            new_site.location_name = cf_data['location_name']

            db.session.add(new_site)
            db.session.commit()
            utility.reset_db_keys()

            EM_LOGGER.info("Saved New Site")
            return '{"event_code": %i, "data": {"site_id": %s, "name_short": "%s", "name_long": "%s", ' \
                   '"latitude": "%s", "longitude": "%s", "facility": "%s", "mobile": "%s", "location_name": "%s"}}' \
                   % (utility.SITE_ID_REQUEST, cf_data['site_id'], cf_data['name_short'],
                      cf_data['name_long'], cf_data['latitude'], cf_data['longitude'],
                      cf_data['facility'], cf_data['mobile'], cf_data['location_name'])


def save_instrument_data_reference(msg_struct):
    """Checks to see if there is already an instrument data reference for this event code, and if there isn't, creates
    one. Instrument data references are used to allow the servers to track which events are pertinent to a particular
    instrument (some events are for all instruments, some only for specific instrument types).  If an instrument data
    reference is to be added, this function also determines whether the reference is 'special' or not.  If there is an
    entire special table devoted to the event (where 'description' is the table name), then it is classified as
    'special'.

    Parameters
    ----------
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    """
    db_refs = db.session.query(InstrumentDataReference)\
        .filter(InstrumentDataReference.instrument_id == msg_struct['data']['instrument_id'])\
        .filter(InstrumentDataReference.description == msg_struct['data']['description']).all()
    if not db_refs:
        special = "false"
        # "special" indicates whether this particular data description has its own table
        rows = db.session.execute('''SELECT column_name FROM information_schema.columns WHERE table_name = :table''',
                                  dict(table=msg_struct['data']['description'])).fetchall()
        if rows:
            special = "true"
        new_instrument_data_ref = InstrumentDataReference()
        new_instrument_data_ref.instrument_id = msg_struct['data']['instrument_id']
        new_instrument_data_ref.description = msg_struct['data']['description']
        new_instrument_data_ref.special = special

        db.session.add(new_instrument_data_ref)
        db.session.commit()
        EM_LOGGER.info("Saved new instrument data reference")


def get_event_code(msg, msg_struct):
    """Searches the database for any event codes where the description matches 'msg_struct['description']'.  If the
    'is_central' flag is set and there is no event code, creates the event code in the database and returns it. If the
    'is_central' flag is not set, it then forwards the packet on to the 'cf_url' (both specified in *config.yml*) and
    returns whatever the central facility determines the event code is.

    Parameters
    ----------
    msg: JSON
        JSON message structure, expected format: {event_code: *code*, data: {description: *description*}}
    msg_struct: dictionary
        Decoded version of msg, converted to python dictionary.

    Returns
    -------
    The event code determined by the function, in the form of a string structured as
    '{"event_code": *event code*, "data": {"description": *description*}}'.

    """

    db_code = db.session.query(EventCode).filter(EventCode.description == msg_struct['data']['description']).first()
    # If the event code defined here, return it downstream
    if db_code:
        EM_LOGGER.info("Found Existing Event Code")
        return '{"event_code": %i, "data": {"description": "%s"}}' % (
            db_code.event_code, msg_struct['data']['description'])

    # If it is not defined at the central facility, inserts a new entry into the table and returns the new code
    elif is_central:
        # Gets the highest current event code number
        max_id = db.session.query(EventCode.event_code).order_by(EventCode.event_code.desc()).first()[0]
        # Manually sets the new ID to be the next available ID
        insert_id = max_id + 1
        # ID's 1-9999 are reserved for explicitly set event codes, such as 'instrument_id_request'
        # Generated event codes have id's of 10000 or greater
        if insert_id < 10000:
            insert_id = 10000

        new_ec = EventCode()
        new_ec.event_code = insert_id
        new_ec.description = msg_struct['data']['description']

        db.session.add(new_ec)
        db.session.commit()

        new_event_code = db.session.query(EventCode.event_code).filter(
                EventCode.description == msg_struct['data']['description']).first()[0]

        EM_LOGGER.info("Created New Event Code")
        return '{"event_code": %i, "data": {"description": "%s"}}' % (
            new_event_code, msg_struct['data']['description'])

    # If it is not defined at a site, requests the event code from the central facility
    else:
        payload = json.loads(msg)
        response = requests.post(cf_url, json=payload, headers=headers, verify=cert_verify)
        cf_msg = dict(json.loads(response.content))

        new_ec = EventCode()
        new_ec.event_code = cf_msg['event_code']
        new_ec.description = cf_msg['data']['description']

        db.session.add(new_ec)
        db.session.commit()
        utility.reset_db_keys()

        EM_LOGGER.info("Saved Event Code")
        return '{"event_code": %i, "data": {"description": "%s"}}' % (
            cf_msg['event_code'], cf_msg['data']['description'])


def initialize_database():
    """Initializes the database.  If the database is specified in config.yml as a 'test_db',
    the database is wiped when at the beginning to ensure a clean load.  If it is not a test
    database, a utility function is called to attempt to load in a postgresql database dumpfile
    if it exists.  First, the tables are initialized, and then if no basic database entries
    exist (users, sites, event codes), they are created.  Then, if it is designated a test database,
    any table that does not contain any entries will be filled with demo data.

    """
    with app.app_context():
        EM_LOGGER.info("Database initializing")
        # If it is a test database, first wipe and clean up the database.
        if cfg['database']['test_db']:
            EM_LOGGER.debug("Test database enabled.  Clearing database")

            db.session.execute("DROP SCHEMA public CASCADE;")
            db.session.execute("CREATE SCHEMA public;")
            db.session.commit()
            # If it is not a test database, first attempt to load database from an existing postgres dumpfile

        upgrade(directory=migration_path)
        # db_migrate(directory=migration_path) # These functions can be used instead of upgrade for Flask Migrate
        # downgrade(directory=migration_path)
        # exit(0)

        # If there there are no users in the database (which any active db should have users) and it is not a test db,
        # attempt to load in a dumpfile.
        if not cfg['database']['test_db']:
            db_user = User.query.first()
            if db_user is None:
                utility.load_dumpfile()

        # If there are still no users, assume the database is empty and populate the basic information
        db_user = User.query.first()
        if db_user is None:
            EM_LOGGER.info("Populating Users")
            utility.load_data_into_table("database/schema/users.data", "users")
        else:
            EM_LOGGER.info("Users in table.")

        db_site = db.session.query(Site).first()
        if db_site is None:
            EM_LOGGER.info("Populating Sites")
            utility.load_data_into_table("database/schema/sites.data", "sites")
        else:
            EM_LOGGER.info("Sites in table.")

        db_event_code = db.session.query(EventCode).first()
        if db_event_code is None:
            EM_LOGGER.info("Populating Event Codes")
            utility.load_data_into_table("database/schema/event_codes.data", "event_codes")
        else:
            EM_LOGGER.info("Event_codes in table.")

        # If it is set to be a test database, populate extra information.
        if cfg['database']['test_db']:
            EM_LOGGER.info("Test database demo data loading")
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
                result = db.session.execute("SELECT * FROM %s LIMIT 1" % table).fetchone()
                if result is None:
                    EM_LOGGER.info("Populating %s", table)
                    utility.load_data_into_table("database/schema/%s.data" % table, table)
                else:
                    EM_LOGGER.info("%ss in table.", table)
        else:
            EM_LOGGER.info("Test database demo data disabled")

        # Without this, the database prevents the server from running properly.
        utility.reset_db_keys()


@app.route('/eventmanager')
def event_manager_home():
    """Calculates very basic information (cpu usage, site name) and passes the information to a template, serving as
    a home page for the event manager.

    Returns
    -------
    index.html: HTML document

    """
    table_stats = []
    data_tables = ["prosensing_paf", "events_with_value", "events_with_text", "instrument_logs", "pulse_captures"]

    cutoff_time = datetime.datetime.now() + datetime.timedelta(-db_cfg['days_retained'])

    for table in data_tables:
        table_stat_name = table

        # Total entry count in table
        entry_count = db.session.execute("SELECT count(*) from %s" % table).first()[0]
        # Number of entries that are beyond the cutoff date (if data is archived, number of entries archived)
        cutoff_entries = db.session.execute("SELECT count(*) from %s WHERE time < :cutoff_time" % table,
                                            dict(cutoff_time=cutoff_time.isoformat())).first()[0]

        oldest_entry = db.session.execute("SELECT time from %s ORDER BY time ASC" % table).first()

        if oldest_entry is not None:
            oldest_entry = oldest_entry[0].strftime("%d-%m-%Y %H:%M")

        table_stats.append(dict(name=table_stat_name, count=int(entry_count), oldest=oldest_entry,
                                cutoff_entries=int(cutoff_entries)))

    return render_template('index.html', usage=psutil.cpu_percent(), site=os.environ.get('SITE'),
                           days_retained=db_cfg['days_retained'], cutoff_time=cutoff_time.strftime("%d-%m-%Y %H:%M"),
                           table_stats=table_stats)


if __name__ == '__main__':
    cfg = config.get_config_context()

    if cfg['type']['central_facility']:
        is_central = 1
    else:
        cf_url = cfg['setup']['cf_url']
        cert_verify = cfg['setup']['cert_verify']

    initialize_database()

    EM_LOGGER.info("Starting Event Manager")
    app.run(host='0.0.0.0', port=cfg['setup']['event_manager_port'], debug=True)
