import os
import json
import logging
import ciso8601
import dateutil.parser

from flask import render_template, redirect, url_for, request
from flask import Blueprint
from sqlalchemy.sql import func
from sqlalchemy import asc

from WarnoConfig import redis_interface
from WarnoConfig.utility import status_code_to_text
from WarnoConfig.models import db
from WarnoConfig.models import Instrument, ProsensingPAF, PulseCapture, InstrumentLog, Site
from WarnoConfig.models import InstrumentDataReference, EventCode, EventWithValue, ValidColumn


instruments = Blueprint('instruments', __name__, template_folder='templates')

log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

# Logs to the user portal log
up_logger = logging.getLogger(__name__)
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
up_logger.addHandler(up_handler)


@instruments.route('/instruments')
def list_instruments():
    """List  ARM Instruments.

    Returns
    -------
    instrument_list.html: HTML document
        Returns an HTML document with an argument for a list of instruments and their information.
    """
    db_instruments = db.session.query(Instrument).order_by(asc(Instrument.id)).all()
    instrument_list = [dict(abbv=inst.name_short, name=inst.name_long, type=inst.type, vendor=inst.vendor,
                            description=inst.description, frequency_band=inst.frequency_band,
                            location=inst.site.name_short, site_id=inst.site_id, id=inst.id)
                       for inst in db_instruments]

    return render_template('instrument_list.html', instruments=instrument_list)


@instruments.route('/instruments/new', methods=['GET', 'POST'])
def new_instrument():
    """Create a new ARM Instrument.

    Returns
    -------
    new_instrument.html: HTML document
        If the request method is 'GET', returns a form to create a new instrument.

    list_instruments: Flask redirect location
        If the request method is 'POST', returns a Flask redirect location to the
            list_instruments function, redirecting the user to the list of instruments.
    """
    # If the form information has been received, insert the new instrument into the table
    if request.method == 'POST':
        # Get the instrument information from the request
        # Field lengths limited in the views
        new_db_instrument = Instrument()
        new_db_instrument.name_short = request.form.get('abbv')
        new_db_instrument.name_long = request.form.get('name')
        new_db_instrument.type = request.form.get('type')
        new_db_instrument.vendor = request.form.get('vendor')
        new_db_instrument.description = request.form.get('description')
        new_db_instrument.frequency_band = request.form.get('frequency_band')
        new_db_instrument.site_id = request.form.get('site')

        # Insert a new instrument into the database
        db.session.add(new_db_instrument)
        db.session.commit()

        # Redirect to the updated list of instruments
        return redirect(url_for("instruments.list_instruments"))

    # If the request is to get the form, get a list of sites and their ids for the dropdown in the add user form
    if request.method == 'GET':
        #
        db_sites = db.session.query(Site).all()
        sites = [dict(id=site.id, name=site.name_short) for site in db_sites]

        return render_template('new_instrument.html', sites=sites)


@instruments.route('/instruments/<instrument_id>/edit', methods=['GET', 'POST'])
def edit_instrument(instrument_id):
    """Update WARNO instrument.

    Parameters
    ----------
    instrument_id: integer
        Database id for the instrument entry to be updated.

    Returns
    -------
    new_instrument.html: HTML document
        If the request method is 'GET', returns a form to update instrument .

    list_instruments: Flask redirect location
        If the request method is 'POST', returns a Flask redirect location to the
            list_instruments function, redirecting the site to the list of instruments.
    """

    if request.method == 'POST':
        # Get the instrument information from the request
        # Field lengths limited in the views
        updated_instrument = db.session.query(Instrument).filter(Instrument.id == instrument_id).first()
        updated_instrument.name_short = request.form.get('abbv')
        updated_instrument.name_long = request.form.get('name')
        updated_instrument.type = request.form.get('type')
        updated_instrument.vendor = request.form.get('vendor')
        updated_instrument.description = request.form.get('description')
        updated_instrument.frequency_band = request.form.get('frequency_band')
        updated_instrument.site_id = request.form.get('site')

        # Update instrument in the database
        db.session.commit()

        # Redirect to the updated list of instruments
        return redirect(url_for("instruments.list_instruments"))

    # If the request is to get the form, get a list of sites and their ids for the dropdown
    # in the update instrument form
    if request.method == 'GET':
        db_sites = db.session.query(Site).all()
        sites = [dict(id=site.id, name=site.name_short) for site in db_sites]

        db_instrument = db.session.query(Instrument).filter(Instrument.id == instrument_id).first()
        instrument_dict = dict(name_short=db_instrument.name_short, name_long=db_instrument.name_long,
                               type=db_instrument.type, vendor=db_instrument.vendor,
                               description=db_instrument.description, frequency_band=db_instrument.frequency_band,
                               site_id=db_instrument.site_id)

        return render_template('edit_instrument.html', sites=sites, instrument=instrument_dict)


def valid_columns_for_instrument(instrument_id):
    """Returns a list of columns of data for an instrument that is suitable for plotting.

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument to be searched

    Returns
    -------
        column_list: list of strings
            Each element corresponds to the database column name of a
            data value for the instrument that is suitable for plotting.

    """
    db_valid_columns = db.session.query(ValidColumn).filter(ValidColumn.instrument_id == instrument_id).all()
    column_list = [column.column_name for column in db_valid_columns]
    return column_list


def db_get_instrument_references(instrument_id):
    """Gets the set of table references for the specified instrument

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument to be searched

    Returns
    -------
        list of table references
            Each element being the name of the reference and whether or not it is a special reference
            (meaning it references a full table rather than just a certain event type)
    """
    references = (db.session.query(InstrumentDataReference)
                  .filter(InstrumentDataReference.instrument_id == instrument_id)
                  .all())
    return references


def db_select_instrument(instrument_id):
    """Get an instrument's information by its database id

    Parameters
    ----------
    instrument_id: integer
        database id of the instrument

    Returns
    -------
    Dictionary containing the instrument information.

    """
    inst = db.session.query(Instrument).filter(Instrument.id == instrument_id).first()
    return dict(abbv=inst.name_short, name=inst.name_long, type=inst.type, vendor=inst.vendor,
                description=inst.description, frequency_band=inst.frequency_band, location=inst.site.name_short,
                latitude=inst.site.latitude, longitude=inst.site.longitude, site_id=inst.site_id, id=inst.id)


def db_delete_instrument(instrument_id):
    """Delete an instrument by its id and delete any references to the instrument by other tables

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument.

    """
    db.session.query(InstrumentDataReference).filter(InstrumentDataReference.instrument_id == instrument_id).delete()
    db.session.query(ProsensingPAF).filter(ProsensingPAF.instrument_id == instrument_id).delete()
    db.session.query(InstrumentLog).filter(InstrumentLog.instrument_id == instrument_id).delete()
    db.session.query(PulseCapture).filter(PulseCapture.instrument_id == instrument_id).delete()
    db.session.query(Instrument).filter(Instrument.id == instrument_id).delete()
    db.session.commit()


@instruments.route('/instruments/<instrument_id>', methods=['GET', 'DELETE'])
def instrument(instrument_id):
    """If method is "GET", get for the instrument specified by the instrument id
        the instrument information, recent log entries, the status of the
        instrument and a list of which data columns are available to plot.
        If the method is "DELETE", instead deletes the instrument specified by the
        instrument id and any table entries that reference that instrument.

    Parameters
    ----------
    instrument_id: integer
        The database id of the instrument to be shown or deleted.

    Returns
    -------
    show_instrument.html: HTML document
        If called with a "GET" method, returns an HTML document with arguments including
        instrument information, the 5 most recent log entries, the status of the instrument,
        and the list of columns for available data to plot on graphs.
    """
    if request.method == "GET":
        db_instrument = db_select_instrument(instrument_id)
        recent_logs = db_recent_logs_by_instrument(instrument_id)
        # If there are any logs, the most recent log (the first of the list) has the current status
        if recent_logs:
            status = status_code_to_text(recent_logs[0]["status"])
            # Change the status for each log from the enumerated code to the text name
            for log in recent_logs:
                log['status'] = status_code_to_text(log['status'])
        else:
            # If there are no recent logs, assume the instrument is operational
            status = "OPERATIONAL"

        column_list = valid_columns_for_instrument(instrument_id)
        return render_template('show_instrument.html', instrument=db_instrument,
                               recent_logs=recent_logs, status=status, columns=sorted(column_list))

    elif request.method == "DELETE":
        db_delete_instrument(instrument_id)
        return json.dumps({'id': instrument_id}), 200


def db_recent_logs_by_instrument(instrument_id, maximum_number=5):
    """Get the most recent logs for the specified instrument, up to "maximum_number" logs

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument

    maximum_number: integer
        The maximum number of logs that will be returned.

    Returns
    -------
    A list containing logs, each log returned as a dictionary containing its information.

    """
    # Creates a list of dictionaries, each dictionary being one of the log entries
    db_logs = (db.session.query(InstrumentLog).filter(InstrumentLog.instrument_id == instrument_id)
               .order_by(InstrumentLog.time.desc()).limit(maximum_number).all())

    return [dict(time=log.time, contents=log.contents, status=log.status,
                 supporting_images=log.supporting_images, author=log.author.name)
            for log in db_logs]


@instruments.route('/recent_values', methods=['GET', 'POST'])
def recent_values():
    """
    Get the most recent value for each given key for the given instrument, along with the time it was collected, as a
    JSON object.  If the key is not a valid key for the instrument, the returned object will be an empty array.

    Parameters
    ----------
    keys: comma separated string
        Passed as an HTML query parameter, the names of the database columns
            to plot against time.

    instrument_id: integer
        Passed as an HTML query parameter, the id of the instrument in the
            database, indicates which instrument's data to use.

    do_stats: integer
        Passed as an HTML query parameter, indicates whether to do aggregates stats for an attribute (1=true, 0=false).

    Returns
    -------

    message: JSON object
        List of dictionaries, one for each attribute, each of the form {"key": **attribute name**, "data":
        {"time": **ISO format UTC time that most recent value was collected**,
        "value": **most recently collected value for attribute**} }

    """
    arg_keys = request.args.get("keys")
    arg_keys = arg_keys.split(',')

    instrument_id = request.args.get("instrument_id")
    do_stats = request.args.get("do_stats")

    key_pairs = [dict(key=a_key, data=None) for a_key in arg_keys]

    # If any key is invalid, sends a blank response
    for key_pair in key_pairs:
        if key_pair["key"] not in valid_columns_for_instrument(instrument_id):
            up_logger.debug("key %s not in valid columns for instrument id %s", key_pair["key"], instrument_id)
            return json.dumps([])
    references = db_get_instrument_references(instrument_id)

    # First see if we gan get entries from Redis.  Any keys that couldn't get data from Redis will then hit the main DB
    # Hopefully will keep the majority of requests within memory.
    # TODO Fix any unit tests this breaks.  Might not break any if there is a way to cleanly fake connection to Redis
    redint = redis_interface.RedisInterface()

    for reference in references:
        for key_pair in key_pairs:
            # If the reference is not 'special', it counts as a non table-organized Redis entry.
            if reference.description == key_pair["key"]:
                result = redint.get_most_recent_value_for_attribute(instrument_id, key_pair["key"])
                if result and (len(result.keys()) > 0):
                    key_pair["data"] = (dateutil.parser.parse(result["time"]), float(result["value"]))
            # If the reference is 'special', it counts as a table-organized Redis entry.
            elif reference.special is True:
                result = redint.get_most_recent_value_for_attribute(instrument_id, key_pair["key"],
                                                                    table_name=reference.description)
                if result and (len(result.keys()) > 0):
                    key_pair["data"] = (dateutil.parser.parse(result["time"]), float(result["value"]))


    for reference in references:
        for key_pair in key_pairs:
            if key_pair["data"] is None:
                sql_query = None
                if reference.description == key_pair["key"]:
                    event_code = db.session.execute('SELECT event_code FROM event_codes WHERE description = :key',
                                                    dict(key=key_pair["key"])).fetchone()

                    sql_query = ('SELECT time, value FROM events_with_value WHERE instrument_id = :id '
                                 'AND event_code = %s ORDER BY time DESC LIMIT 1') % event_code[0]
                elif reference.special is True:
                    rows = db.session.execute("SELECT column_name FROM information_schema.columns WHERE table_name = :table",
                                              dict(table=reference.description)).fetchall()

                    columns = [row[0] for row in rows]
                    if key_pair["key"] in columns:
                        sql_query = 'SELECT time, %s FROM %s WHERE instrument_id = :id ORDER BY time DESC LIMIT 1' % (
                            key_pair["key"], reference.description)
                # Selects the time and the "key" column from the data table
                if sql_query:
                    try:
                        key_pair["data"] = db.session.execute(sql_query, dict(id=instrument_id)).fetchone()
                    except Exception, e:
                        print(e)
                        return json.dumps([])




    # Convert each data entry into a dictionary with ISO formatted time and current value
    for key_pair in key_pairs:
        key_pair["data"] = dict(time=key_pair["data"][0].isoformat(), value=key_pair["data"][1])


    if (do_stats):
        for key_pair in key_pairs:
            stats_json = get_attribute_stats(key_pair["key"], instrument_id)
            key_pair["data"]["stats"] = dict(json.loads(stats_json))

    return json.dumps(key_pairs)


@instruments.route('/generate_instrument_graph', methods=['GET', 'POST'])
def generate_instrument_graph():
    """Generate graph data for a Dygraph for an instrument.

    Uses the supplied keys and instrument_id to get all data from the 'time' and
        specified 'key' column for the instrument with 'instrument_id', passing them
        into a sorting function to get the values at each point in time.  Limits range to those with
        timestamps between 'start' and 'end' time

    Parameters
    ----------
    keys: comma separated string
        Passed as an HTML query parameter, the names of the database columns
            to plot against time.

    instrument_id: integer
        Passed as an HTML query parameter, the id of the instrument in the
            database, indicates which instrument's data to use.

    start: JSON JavaScript Date
        Passed as an HTML query parameter, the beginning time to limit results to.

    end: JSON JavaScript Date
        Passed as an HTML query parameter, the end time to limit results to.

    do_stats: integer
        Passed as an HTML query parameter, indicates whether to do aggregates stats for an attribute (1=true, 0=false).

    Returns
    -------
    message: JSON object
        Returns a JSON object as a list of attribute values at points in time, of the form:
        {data: [[Time0, Attribute0, Attribute1, ... AttributeN], [T1, A0, A1, ...AN], ... [TN, A0, A1, ... AN]],
        lower_deviation: (average for attribute if only one was given - 3 standard deviations),
        upper_deviation: (average for attribute if only one was given + 3 standard deviations)
        }
    """

    arg_keys = request.args.get("keys")
    arg_keys = arg_keys.split(',')

    instrument_id = request.args.get("instrument_id")
    origin = request.args.get("origin")
    start = request.args.get("start")
    end = request.args.get("end")
    do_stats = request.args.get("do_stats")

    keys = {index: dict(key=a_key, data=None) for index, a_key in enumerate(arg_keys)}

    # If any key is invalid, sends a blank response
    for key, value in keys.iteritems():
        if value["key"] not in valid_columns_for_instrument(instrument_id):
            up_logger.debug("key %s not in valid columns for instrument id %s", value["key"], instrument_id)
            return json.dumps("[]")
    references = db_get_instrument_references(instrument_id)

    average = None
    std_deviation = None

    # TODO Need to make sure that this redis functionality is either reflected or omitted in the (probably broken) tests
    # TODO Hit redis first, may need to run averages and std_deviation on the returned data.

    redint = redis_interface.RedisInterface()

    for reference in references:
        for key, value in keys.iteritems():
            # If the reference is not 'special', it counts as a non table-organized Redis entry.
            if reference.description == value["key"]:
                if redint.is_time_before_last_time_for_attribute(instrument_id, value["key"],
                                                                 dateutil.parser.parse(start)):
                    result = redint.get_values_for_attribute_between_times(instrument_id, value["key"],
                                                                           dateutil.parser.parse(start),
                                                                           dateutil.parser.parse(end))
                    if result and (len(result) > 0):
                        value["data"] = [(ciso8601.parse_datetime(entry[0]), float(entry[1])) if entry[1] != "NULL"
                                         else (ciso8601.parse_datetime(entry[0]), entry[1])
                                         for entry in result]
            # If the reference is 'special', it counts as a table-organized Redis entry.
            elif reference.special is True:
                if redint.is_time_before_last_time_for_attribute(instrument_id, value["key"],
                                                                 dateutil.parser.parse(start),
                                                                 table_name=reference.description):
                    result = redint.get_values_for_attribute_between_times(instrument_id, value["key"],
                                                                           dateutil.parser.parse(start),
                                                                           dateutil.parser.parse(end),
                                                                           table_name=reference.description)
                    if result and (len(result) > 0):
                        # Might be a case where a string that cannot be converted to float other than 'NULL' breaks this
                        value["data"] = [(ciso8601.parse_datetime(entry[0]), float(entry[1])) if entry[1] != "NULL"
                                         else (ciso8601.parse_datetime(entry[0]), entry[1])
                                         for entry in result]

    # For each reference that could not be resolved by Redis, fall back to the main database. Build the SQL query for
    # the given key. If the key is a part of a special table, build a query based on the key and containing table.
    for reference in references:
        for key, value in keys.iteritems():
            if value["data"] is None:
                sql_query = None
                if reference.description == value["key"]:
                    event_code = db.session.execute('SELECT event_code FROM event_codes WHERE description = :key',
                                                    dict(key=value["key"])).fetchone()
                    aggregate_query = ('SELECT avg(value), stddev_pop(value) FROM events_with_value '
                                       'WHERE instrument_id = :id AND event_code = :event_code AND '
                                       'time >= :origin AND time <= :end')
                    db_aggregates = db.session.execute(aggregate_query, dict(id=instrument_id, event_code=event_code[0],
                                                                             origin=origin, end=end)).fetchall()[0]

                    average = db_aggregates[0]
                    std_deviation = db_aggregates[1]

                    sql_query = ('SELECT time, value FROM events_with_value WHERE instrument_id = :id '
                                 'AND time >= :start AND time <= :end AND event_code = %s ORDER BY time DESC') % event_code[0]
                elif reference.special is True:
                    rows = db.session.execute("SELECT column_name FROM information_schema.columns WHERE table_name = :table",
                                              dict(table=reference.description)).fetchall()

                    columns = [row[0] for row in rows]
                    if value["key"] in columns:
                        aggregate_query = 'SELECT avg(%s), stddev_pop(%s) FROM %s WHERE instrument_id = :id AND time >= :origin AND time <= :end' % (value['key'], value['key'], reference.description)
                        db_aggregates = db.session.execute(aggregate_query,
                                                           dict(id=instrument_id, origin=origin, end=end)).fetchall()[0]

                        average = db_aggregates[0]
                        std_deviation = db_aggregates[1]

                        sql_query = 'SELECT time, %s FROM %s WHERE instrument_id = :id AND time >= :start AND time <= :end AND %s IS NOT NULL ORDER BY time DESC' % (
                            value["key"], reference.description, value["key"])
                # Selects the time and the "key" column from the data table with time between 'start' and 'end'
                if sql_query:
                    try:
                        value["data"] = db.session.execute(sql_query, dict(id=instrument_id, start=start, end=end)).fetchall()

                    except Exception, e:
                        print(e)
                        return json.dumps("[]")

    data = synchronize_sort(keys)
    map(iso_first_element, data)

    lower_deviation = 0
    upper_deviation = 0
    if len(keys) == 1 and average is not None and std_deviation is not None:
        upper_deviation = float(average) + (2. * float(std_deviation))
        lower_deviation = float(average) - (2. * float(std_deviation))

    message = dict(data=data, lower_deviation=lower_deviation, upper_deviation=upper_deviation)

    if do_stats == "1":
        # This will do the first key it can get to do stats on.  The caller of the generate function
        # should assure that there is only one key before specifying 'do_stats', otherwise it will
        # randomly pick a key to do stats on.
        stats = get_attribute_stats(keys[0]['key'], instrument_id)
        stats_dict = dict(json.loads(stats))
        message.update(stats_dict)
    serialized_message = json.dumps(message)

    # Send out the JSON message
    # TODO this return data should be compressed, it can get pretty heavy when on large data sets.  May need headers
    return serialized_message


@instruments.route('/attribute_stats')
def get_attribute_stats(attribute=None, instrument_id=None):
    """Generates aggregate data on an attribute for an instrument (min, max, mean, standard deviation)
    and returns it in a JSON dictionary.

    Parameters
    ----------
    attribute: string
        Can be passed as an HTML query parameter, the name of the database column to get aggregate data for.

    instrument_id: integer
        Can be passed as an HTML query parameter, the id of the instrument in the
            database, indicates which instrument's data to use.

    Returns
    -------
    message: JSON object
        Returns a JSON object as a list of the attribute's aggregate data, of the form:
        {'min': (minimum of all values), 'max': (maximum of all values), 'average': (average of all values),
        'std_deviation': (standard deviation for the data set)
        }

    """
    arg_attribute = request.args.get("attribute")
    if arg_attribute:
        attribute = arg_attribute
    arg_instrument_id = request.args.get("instrument_id")
    if arg_instrument_id:
        instrument_id = arg_instrument_id

    minimum = None
    maximum = None
    median = None
    average = None
    std_deviation = None

    if attribute not in valid_columns_for_instrument(instrument_id):
        up_logger.debug("key %s not in valid columns for instrument id %s", attribute, instrument_id)

    references = db_get_instrument_references(instrument_id)

    db_aggregates = None

    for ref in references:
        if ref.description == attribute:
            event_code = db.session.execute('SELECT event_code FROM event_codes WHERE description = :attribute',
                                            dict(attribute=attribute)).fetchone()[0]
            aggregate_sql = 'SELECT min(value), max(value), avg(value), stddev_pop(value) FROM events_with_value WHERE instrument_id = :id AND event_code = %s' % (event_code,)
            db_aggregates = db.session.execute(aggregate_sql, dict(column=attribute, id=instrument_id)).fetchall()[0]

            db_values = (db.session.query(EventWithValue.value)
                         .filter(EventWithValue.instrument_id == instrument_id)
                         .filter(EventWithValue.event_code_id == int(event_code))
                         .filter(EventWithValue.value.isnot(None)).all())

            values = [value[0] for value in db_values]
            values = sorted(values)
            median = values[len(values)/2]

        elif ref.special is True:
            rows = db.session.execute("SELECT column_name FROM information_schema.columns WHERE table_name = :table",
                                      dict(table=ref.description)).fetchall()
            columns = [row[0] for row in rows]

            if attribute in columns:
                aggregate_parameters = (attribute, attribute, attribute, attribute, ref.description)
                aggregate_sql = 'SELECT min(%s), max(%s), avg(%s), stddev_pop(%s) FROM %s WHERE instrument_id = :id' % aggregate_parameters
                db_aggregates = db.session.execute(aggregate_sql, dict(id=instrument_id)).fetchall()[0]

                values_sql = "SELECT %s FROM %s WHERE instrument_id = :id" % (attribute, ref.description,)
                db_values = db.session.execute(values_sql, dict(id=instrument_id)).fetchall()
                values = [value[0] for value in db_values]
                values = sorted(values)
                median = values[len(values)/2]
                break

    if db_aggregates:
        minimum = float(db_aggregates[0])
        maximum = float(db_aggregates[1])
        average = float(db_aggregates[2])
        std_deviation = float(db_aggregates[3])

    payload = dict(min=minimum, max=maximum, median=median, average=average, std_deviation=std_deviation)
    message = json.dumps(payload)

    return message


def iso_first_element(input_list):
    """Update first element of input list from a python datetime object into an ISO formatted time.
    (Used as map function).

    Parameters
    ----------
    input_list: list
        First element of 'input_list' is a python datetime object.

    Returns
    -------
    No actual return, but updates list in place.

    """

    input_list[0] = input_list[0].isoformat()


@instruments.route("/valid_columns")
def update_all_valid_columns():
    """Updates the 'valid_columns' table for each instrument with all data attributes that are no longer exclusively null

    Returns
    -------
    HTML displaying how many entries have been updated per instrument.

    """
    message = "Adding data attributes that are no longer all null to list of valid columns:<hr>"
    db_instruments = db.session.query(Instrument).all()
    for inst in db_instruments:
        message += "<h3>Instrument " + str(inst.id) + " " + inst.name_long + "</h3><br>"
        message += update_valid_columns_for_instrument(inst.id)
        message += "<hr>"
    return message


def update_valid_columns_for_instrument(instrument_id):
    """Updates the 'valid_columns' table for the instrument matching 'instrument_id'.  Checks through all references for
    the instrument, filtering out the attributes that are already represented in the 'valid_columns' table.  All entries
    left are entries that need to be checked.  For the check, the attribute's column in its respective table is summed,
    and if that sum is no longer NULL (e.g. there is at least one valid data entry in that column) that attribute is
    added to the 'valid_columns' table for the instrument.

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument whose attributes are to be checked.

    Returns
    -------
    HTML displaying how many entries have been updated for this instrument.

    """
    message = ""
    current_references = (db.session.query(InstrumentDataReference)
                          .filter(instrument_id == InstrumentDataReference.instrument_id)
                          .all())

    special_refs = []
    non_special_refs = []
    for ref in current_references:
        if ref.special:
            special_refs.append(ref)
        else:
            non_special_refs.append(ref)

    db_non_special_valid_columns = (db.session.query(ValidColumn)
                                    .filter(ValidColumn.instrument_id == instrument_id)
                                    .filter(ValidColumn.table_name == "events_with_value")
                                    .all())
    non_special_valid_columns = [column.column_name for column in db_non_special_valid_columns]

    excluded_refs = [ref for ref in non_special_refs if ref.description not in non_special_valid_columns]

    for ref in excluded_refs:
        db_sum = db.session.query(func.sum(EventWithValue.value)).first()
        if db_sum[0] is not None:
            new_valid_column = ValidColumn()
            new_valid_column.table_name = "events_with_value"
            new_valid_column.column_name = ref.description
            new_valid_column.instrument_id = instrument_id
            db.session.add(new_valid_column)
            db.session.commit()
            message += " -- Added previously null 'events_with_value' column '" + str(ref.description) + "'<br>"

    for ref in special_refs:
        db_special_valid_columns = (db.session.query(ValidColumn)
                                    .filter(ValidColumn.instrument_id == instrument_id)
                                    .filter(ValidColumn.table_name == ref.description)
                                    .all())
        special_valid_columns = [column.column_name for column in db_special_valid_columns]

        db_table_columns = db.session.execute(
                "SELECT column_name, data_type from information_schema.columns WHERE table_name = :table",
                dict(table=ref.description))
        table_columns = [row[0] for row in db_table_columns if row[1] in ["integer", "double precision"]]

        # These columns are viable columns that are not already in the Valid Columns table.
        # These are the columns that need to be checked to determine if they are now valid columns
        # (e.g., this instrument has received data in the column).
        excluded_columns = [column for column in table_columns if column not in special_valid_columns]

        sum_string = ", ".join(["sum(%s)" % column for column in excluded_columns])
        sql = "SELECT %s FROM %s WHERE instrument_id = %s" % (sum_string, ref.description, instrument_id)
        column_sums = db.session.execute(sql).first()
        zipper = zip(excluded_columns, column_sums)
        # Only add each column if the sum associated with it is not 'None', meaning there is a valid value
        # somewhere in the column.
        added_columns = [column[0] for column in zipper if column[1] is not None]

        for column in added_columns:
            new_valid_column = ValidColumn()
            new_valid_column.table_name = ref.description
            new_valid_column.column_name = column
            new_valid_column.instrument_id = instrument_id
            db.session.add(new_valid_column)
        db.session.commit()

        # Small message to give the caller an idea of how many rows successfully updated.
        message += (" -- Added " + str(len(added_columns)) + " of " + str(len(excluded_columns))
                    + " previously null columns.<br>")

    return message


def synchronize_sort(dataset_dict):
    """Sorts a dictionary of data sets to be consistent in time.  Each iteration, it checks the earliest time of each
    data set, gets the earliest time from among them, then sets that as the time for the next return element.  It then
    checks the earliest element of each data set to see which data set elements match, removing matching elements and
    placing their values in the set's place in the resulting element.  The process iterates until all data sets are
    empty, and then returns the list of the merged time/value sets.

    Starts with data sets:

    *Set 0*                 *Set 1*                   *Set 2*
    [                       [                       [
    (2015-05-11 02:00, 03), (2015-05-11 03:00, 13), (2015-05-11 02:30, 23),
    (2015-05-11 01:30, 02), (2015-05-11 02:30, 12), (2015-05-11 02:00, 22),
    (2015-05-11 01:00, 01)] (2015-05-11 02:00, 11)] (2015-05-11 01:00, 21)]

    Ends with a sorted list:
    [
    [2015-05-11 01:00,   01, None,   21],
    [2015-05-11 01:30,   02, None, None],
    [2015-05-11 02:00,   03,   11,   22],
    [2015-05-11 02:30, None,   12,   23],
    [2015-05-11 03:00, None,   13, None]]

    Parameters
    ----------
    dataset_dict: dictionary to be sorted
    Dictionary for the algorithm to sort.  Of the form {**integer** set number: {'data':
        [(**Datetime** time1, **float/int** value1), (time2, value2) ... (timeN, valueN)]}}
    The set numbers must increment as integers from 1 to N, but can be in any order (dictionaries are unsorted).
    Each data set should be sorted from latest to earliest time.

    Returns
    -------
    Sorted list, of form [**Datetime** 2015-05-11 02:00, 15, None, 12, ...], [2015-05-11 01:00, None, 30, None, ...],
        ...[Earliest Datetime, Dataset0 Value, Dataset1 Value, Dataset2 Value, ... AttributeN Value]]
    """
    results = []
    length = len(dataset_dict)

    # This sums the lengths of the data sets being sorted.
    while sum([len(value["data"]) for _, value in dataset_dict.iteritems()]) > 0:

        # Gets a list of the times containing the first element of each data set (therefore, the most earliest time for
        # the set), but only if the set is not empty.
        first_elem_times = [value["data"][-1][0] for _, value in dataset_dict.iteritems() if len(value["data"]) > 0]
        # Gets the earliest of the times of the data sets
        min_time = min(first_elem_times)

        # Creates an element to be pushed into the return list.  The first is the time for that particular element, the
        # rest are initialized to none.  If the next value of a data set occurs at the time that this list is designated
        # for, the value is put into the element according to the set's attribute number.  For example, if there are 3
        # data sets and the first elements of each are (1:00, 15), (2:00, 30) and (1:00, 20), the result element would
        # be [1:00, 15, None, 20].
        values_at_time = [min_time] + [None] * length
        for set_number, value in dataset_dict.iteritems():
            # Any data sets that have elements and have a time equal to the time for this point puts that data
            # in for that point and removes that element from its list.  Updates the index of the data point
            # that corresponds to the list's dictionary value.  This assures that each element of the packet
            # stays in the same order as the list.  If there is no valid value, stays None
            if len(value["data"]) > 0 and value["data"][-1][0] == min_time:
                # 'set_number + 1' is necessary because the first element [0] is for the time.
                values_at_time[set_number + 1] = value["data"][-1][1]
                del value["data"][-1]

        # Add point in time to result list
        results.append(values_at_time)
    return results
