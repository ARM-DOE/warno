import json

from flask import g, render_template, request, redirect, url_for, request
from flask import Blueprint
from jinja2 import TemplateNotFound

from WarnoConfig import config
from WarnoConfig.utility import status_code_to_text


instruments = Blueprint('instruments', __name__, template_folder='templates')




@instruments.route('/instruments')
def list_instruments():
    """List  ARM Instruments.

    Returns
    -------
    instrument_list.html: HTML document
        Returns an HTML document with an argument for a list of instruments and their information.
    """

    cur = g.db.cursor()

    cur.execute('''SELECT i.instrument_id, i.name_short, i.name_long, i.type,
                i.vendor, i.description, i.frequency_band, s.name_short, s.site_id FROM instruments i
                JOIN sites s ON (i.site_id = s.site_id) ORDER BY i.instrument_id ASC''')
    instrument_list = [dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], description=row[5],
                        frequency_band=row[6], location=row[7], site_id=row[8], id=row[0])
                   for row in cur.fetchall()]

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

    cur = g.db.cursor()

    # If the form information has been received, insert the new instrument into the table
    if request.method == 'POST':
        # Get the instrument information from the request
        # Field lengths limited in the views
        abbv = request.form.get('abbv')
        name = request.form.get('name')
        itype = request.form.get('type')
        vendor = request.form.get('vendor')
        description = request.form.get('description')
        frequency_band = request.form.get('frequency_band')
        site = request.form.get('site')

        # Insert a new instrument into the database
        cur.execute('''INSERT INTO instruments(name_short, name_long, type, vendor, description, frequency_band, site_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                    (abbv, name, itype, vendor, description, frequency_band, site))
        cur.execute('COMMIT')

        # Redirect to the updated list of instruments
        return redirect(url_for("instruments.list_instruments"))

    # If the request is to get the form
    if request.method == 'GET':
        # Get a list of sites and their ids for the dropdown in the add user form
        cur.execute('''SELECT site_id, name_short FROM sites ''')
        # Add each site as a dictionary to a list of sites
        sites = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

        # Return the list of sites to the new instrument form
        return render_template('new_instrument.html', sites=sites)


def valid_columns_for_instrument(instrument_id, cursor):
    """Returns a list of columns of data for an instrument that is suitable for plotting.

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument to be searched

    cursor: database cursor

    Returns
    -------
        column_list: list of strings
            Each element corresponds to the database column name of a
            data value for the instrument that is suitable for plotting.

    """
    references = db_get_instrument_references(instrument_id, cursor)
    column_list = []
    for reference in references:
        if reference[0] == True:
            cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s",
                        (reference[1],))
            rows = cursor.fetchall()
            columns = [row[0] for row in rows if row[1] in ["integer", "boolean", "double precision"]]
        else:
            columns = [reference[1]]
        column_list.extend(columns)
    return column_list


def db_get_instrument_references(instrument_id, cursor):
    """Gets the set of table references for the specified instrument

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument to be searched

    cursor: database cursor

    Returns
    -------
        list of table references
            Each element being the name of the reference and whether or not it is a special reference
            (meaning it references a full table rather than just a certain event type)
    """
    cursor.execute("SELECT special, description FROM instrument_data_references WHERE instrument_id = %s",
                   (instrument_id,))
    return cursor.fetchall()


def db_select_instrument(instrument_id, cursor):
    """Get an instrument's information by its database id
    Parameters
    ----------
    instrument_id: integer
        database id of the instrument

    cursor: database cursor

    Returns
    -------
    Dictionary containing the instrument information.

    """
    cursor.execute('''SELECT i.instrument_id, i.name_short, i.name_long, i.type,
        i.vendor, i.description, i.frequency_band, s.name_short, s.latitude, s.longitude, s.site_id
        FROM instruments i JOIN sites s ON (i.site_id = s.site_id)
        WHERE i.instrument_id = %s''', (instrument_id,))
    row = cursor.fetchone()
    return dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], description=row[5],
                    frequency_band=row[6], location=row[7], latitude=row[8], longitude=row[9],
                    site_id=row[10], id=row[0])

def db_delete_instrument(instrument_id, cursor):
    """Delete an instrument by its id and delete any references to the instrument by other tables

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument.

    cursor: database cursor
    """
    cursor.execute("DELETE FROM table_references WHERE instrument_id = %s", (instrument_id,))
    cursor.execute("DELETE FROM prosensing_paf WHERE instrument_id = %s", (instrument_id,))
    cursor.execute("DELETE FROM instrument_logs WHERE instrument_id = %s", (instrument_id,))
    cursor.execute("DELETE FROM pulse_captures WHERE instrument_id = %s", (instrument_id,))
    cursor.execute("DELETE FROM instruments WHERE instrument_id = %s", (instrument_id,))
    cursor.execute("COMMIT")


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
    cur = g.db.cursor()
    if request.method == "GET":
        instrument = db_select_instrument(instrument_id, cur)
        recent_logs = db_recent_logs_by_instrument(instrument_id, cur)
        # If there are any logs, the most recent log (the first of the list) has the current status
        if recent_logs:
            status = status_code_to_text(recent_logs[0]["status"])
            # Change the status for each log from the enumerated code to the text name
            for log in recent_logs:
                log['status'] = status_code_to_text(log['status'])
        else:
            # If there are no recent logs, assume the instrument is operational
            status = "OPERATIONAL"

        cur = g.db.cursor()

        column_list = valid_columns_for_instrument(instrument_id, cur)
        return render_template('show_instrument.html', instrument=instrument,
                               recent_logs=recent_logs, status=status, columns=sorted(column_list))

    elif request.method == "DELETE":
        db_delete_instrument(instrument_id, cur)
        return json.dumps({'id': instrument_id}), 200

def db_recent_logs_by_instrument(instrument_id, cursor, maximum_number = 5):
    """Get the most recent logs for the specified instrument, up to "maximum_number" logs

    Parameters
    ----------
    instrument_id: integer
        Database id of the instrument

    cursor: database cursor

    maximum_number: integer
        The maximum number of logs that will be returned.

    Returns
    -------
    A list containing logs, each log returned as a dictionary containing its information.

    """
    cursor.execute('''SELECT l.time, l.contents, l.status, l.supporting_images, u.name
                FROM instrument_logs l JOIN users u
                ON l.author_id = u.user_id WHERE l.instrument_id = %s
                ORDER BY time DESC LIMIT %s''', (instrument_id, maximum_number))
    # Creates a list of dictionaries, each dictionary being one of the log entries
    return [dict(time=row[0], contents=row[1], status=row[2], supporting_images=row[3],
                author=row[4]) for row in cursor.fetchall()]


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

    cur = g.db.cursor()

    key = request.args.get("key")
    instrument_id = request.args.get("instrument_id")
    start = request.args.get("start")
    end = request.args.get("end")

    if key not in valid_columns_for_instrument(instrument_id, cur):
        return json.dumps({"x": [], "y": []})
    references = db_get_instrument_references(instrument_id, cur)
    # Build the SQL query for the given key.  If the key is a part of a special table, build a query based on the key and containing table
    for reference in references:
        if reference[1] == key:
            cur.execute('SELECT event_code FROM event_codes WHERE description = %s', (key,))
            event_code = cur.fetchone()
            sql_query = ('SELECT time, value FROM events_with_value WHERE instrument_id = %%s '
                         'AND time >= %%s AND time <= %%s AND event_code = %s') % event_code[0]
            break
        elif reference[0] == True:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (reference[1],))
            rows = cur.fetchall()
            columns = [row[0] for row in rows]
            if key in columns:
                sql_query = 'SELECT time, %s FROM %s WHERE instrument_id = %%s AND time >= %%s AND time <= %%s' % (
                key, reference[1])
    # Selects the time and the "key" column from the data table with time between 'start' and 'end'
    try:
        cur.execute(sql_query, (instrument_id, start, end))
    except Exception, e:
        print(e)
        return json.dumps({"x": [], "y": []})
    rows = cur.fetchall()

    # Prepares a JSON message, an array of x values and an array of y values, for the graph to plot
    # TODO Determine: Is iso format timezone ambiguous?
    x = [row[0].isoformat() for row in rows]
    y = [row[1] for row in rows]
    message = {"x": x, "y": y}
    message = json.dumps(message)

    # Send out the JSON message
    return message
