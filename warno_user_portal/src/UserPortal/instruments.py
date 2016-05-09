import logging
import json
import os


from flask import render_template, redirect, url_for, request
from flask import Blueprint
from sqlalchemy import asc

from WarnoConfig import config
from WarnoConfig.utility import status_code_to_text
from WarnoConfig import database
from WarnoConfig.models import Instrument, ProsensingPAF, PulseCapture, InstrumentLog, Site
from WarnoConfig.models import InstrumentDataReference, EventCode, EventWithValue


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
    db_instruments = database.db_session.query(Instrument).order_by(asc(Instrument.id)).all()
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
        new_instrument = Instrument()
        new_instrument.name_short = request.form.get('abbv')
        new_instrument.name_long = request.form.get('name')
        new_instrument.type = request.form.get('type')
        new_instrument.vendor = request.form.get('vendor')
        new_instrument.description = request.form.get('description')
        new_instrument.frequency_band = request.form.get('frequency_band')
        new_instrument.site_id = request.form.get('site')

        # Insert a new instrument into the database
        database.db_session.add(new_instrument)
        database.db_session.commit()

        # Redirect to the updated list of instruments
        return redirect(url_for("instruments.list_instruments"))

    # If the request is to get the form, get a list of sites and their ids for the dropdown in the add user form
    if request.method == 'GET':
        #
        db_sites = database.db_session.query(Site).all()
        sites = [dict(id=site.id, name=site.name_short) for site in db_sites]

        return render_template('new_instrument.html', sites=sites)

@instruments.route('/instruments/<instrument_id>/edit', methods=['GET', 'POST'])
def edit_instrument(instrument_id):
    """Update WARNO instrument.

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
        updated_instrument = database.db_session.query(Instrument).filter(Instrument.id == instrument_id).first()
        updated_instrument.name_short = request.form.get('abbv')
        updated_instrument.name_long = request.form.get('name')
        updated_instrument.type = request.form.get('type')
        updated_instrument.vendor = request.form.get('vendor')
        updated_instrument.description = request.form.get('description')
        updated_instrument.frequency_band = request.form.get('frequency_band')
        updated_instrument.site_id = request.form.get('site')

        # Update instrument in the database
        database.db_session.commit()

        # Redirect to the updated list of instruments
        return redirect(url_for("instruments.list_instruments"))

    # If the request is to get the form, get a list of sites and their ids for the dropdown in the update instrument form
    if request.method == 'GET':
        db_sites = database.db_session.query(Site).all()
        sites = [dict(id=site.id, name=site.name_short) for site in db_sites]

        db_instrument = database.db_session.query(Instrument).filter(Instrument.id == instrument_id).first()
        instrument = dict(name_short=db_instrument.name_short, name_long=db_instrument.name_long, type=db_instrument.type,
                          vendor=db_instrument.vendor, description=db_instrument.description,
                          frequency_band=db_instrument.frequency_band, site_id=db_instrument.site_id)

        return render_template('edit_instrument.html', sites=sites, instrument=instrument)

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
    references = db_get_instrument_references(instrument_id)
    column_list = []
    for reference in references:
        if reference.special == True:
            rows = database.db_session.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = :table",
                                               dict(table= reference.description)).fetchall()
            columns = [row[0] for row in rows if row[1] in ["integer", "boolean", "double precision"]]
        else:
            columns = [reference.description]
        column_list.extend(columns)
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
    references = database.db_session.query(InstrumentDataReference).filter(InstrumentDataReference.instrument_id == instrument_id).all()
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
    inst = database.db_session.query(Instrument).filter(Instrument.id == instrument_id).first()
    return dict(abbv=inst.name_short, name=inst.name_long, type=inst.type, vendor=inst.vendor, description=inst.description,
                frequency_band=inst.frequency_band, location=inst.site.name_short, latitude=inst.site.latitude,
                longitude=inst.site.longitude, site_id=inst.site_id, id=inst.id)

def db_delete_instrument(instrument_id):
    """Delete an instrument by its id and delete any references to the instrument by other tables

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument.

    """
    database.db_session.query(InstrumentDataReference).filter(InstrumentDataReference.instrument_id == instrument_id).delete()
    database.db_session.query(ProsensingPAF).filter(ProsensingPAF.instrument_id == instrument_id).delete()
    database.db_session.query(InstrumentLog).filter(InstrumentLog.instrument_id == instrument_id).delete()
    database.db_session.query(PulseCapture).filter(PulseCapture.instrument_id == instrument_id).delete()
    database.db_session.query(Instrument).filter(Instrument.id == instrument_id).delete()
    database.db_session.commit()


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
        instrument = db_select_instrument(instrument_id)
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
        return render_template('show_instrument.html', instrument=instrument,
                               recent_logs=recent_logs, status=status, columns=sorted(column_list))

    elif request.method == "DELETE":
        db_delete_instrument(instrument_id)
        return json.dumps({'id': instrument_id}), 200

def db_recent_logs_by_instrument(instrument_id, maximum_number = 5):
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
    db_logs = database.db_session.query(InstrumentLog).filter(InstrumentLog.instrument_id == instrument_id)\
            .order_by(InstrumentLog.time.desc()).limit(maximum_number).all()

    return [dict(time=log.time, contents=log.contents, status=log.status,
                 supporting_images=log.supporting_images,author=log.author.name)
            for log in db_logs]


@instruments.route('/generate_instrument_graph', methods=['GET', 'POST'])
def generate_instrument_graph():
    """Generate graph data for a Dygraph for an instrument.

    Uses the supplied key and instrument_id to get all data from the 'time' and
        specified 'key' column for the instrument with 'instrument_id', passing them
        as 'x' and 'y' values to be graphed together.  Limits range to those with
        timestamps between 'start' and 'end' time

    Parameters
    ----------
    key: string
        Passed as an HTML query parameter, the name of the database column
            to plot against time.

    instrument_id: integer
        Passed as an HTML query parameter, the id of the instrument in the
            database, indicates which instrument's data to use.

    start: JSON JavaScript Date
        Passed as an HTML query parameter, the beginning time to limit results to.

    end: JSON JavaScript Date
        Passed as an HTML query parameter, the end time to limit results to.

    Returns
    -------
    message: JSON object
        Returns a JSON object with a list of 'x' values corresponding to a list of 'y' values.
    """

    key = request.args.get("key")
    instrument_id = request.args.get("instrument_id")
    start = request.args.get("start")
    end = request.args.get("end")

    if key not in valid_columns_for_instrument(instrument_id):
        return json.dumps({"x": [], "y": []})
    references = db_get_instrument_references(instrument_id)
    # Build the SQL query for the given key.  If the key is a part of a special table, build a query based on the key and containing table
    for reference in references:
        if reference.description == key:
            event_code = database.db_session.execute('SELECT event_code FROM event_codes WHERE description = :key',
                                                     {'key': key}).fetchone()
            sql_query = ('SELECT time, value FROM events_with_value WHERE instrument_id = :id '
                         'AND time >= :start AND time <= :end AND event_code = %s') % event_code[0]
            break
        elif reference.special == True:
            rows = database.db_session.execute("SELECT column_name FROM information_schema.columns WHERE table_name = :table",
                                               {'table': reference.description}).fetchall()
            columns = [row[0] for row in rows]
            if key in columns:
                sql_query = 'SELECT time, %s FROM %s WHERE instrument_id = :id AND time >= :start AND time <= :end' % (
                key, reference.description)
    # Selects the time and the "key" column from the data table with time between 'start' and 'end'
    try:
        rows = database.db_session.execute(sql_query, dict(id = instrument_id, start= start, end= end)).fetchall()
    except Exception, e:
        print(e)
        return json.dumps({"x": [], "y": []})

    # Prepares a JSON message, an array of x values and an array of y values, for the graph to plot
    # TODO Determine: Is iso format timezone ambiguous?
    x = [row[0].isoformat() for row in rows]
    y = [row[1] for row in rows]
    message = {"x": x, "y": y}
    message = json.dumps(message)

    # Send out the JSON message
    return message
