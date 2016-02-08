import json

from flask import g, render_template, request, redirect, url_for
from flask import Blueprint
from jinja2 import TemplateNotFound
import psycopg2

from UserPortal import app
from WarnoConfig import config

is_central = 0

app.config.from_object(__name__)

status_text = {1: "OPERATIONAL",
               2: "NOT WORKING",
               3: "TESTING",
               4: "IN-UPGRADE",
               5: "TRANSIT"}


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
    -------
    exception: optional, Exception
        An Exception that may have caused the teardown.
    """

    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/')
def hello_world():
    # Temporary home page
    return redirect(url_for('show_radar_status'))





@app.route('/dygraph')
def show_dygraph():
    """Show Dygraphs.

    Returns
    -------
    instrument_dygraph.html: HTML document
        Returns an HTML document with a list of table columns to select from.
    """

    cur = g.db.cursor()
    # Column list allows the template to create a dropdown list with fixed values.
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'prosensing_paf'")
    rows = cur.fetchall()
    # Only allows a an entry if it is an acceptable data type.
    columns = [row[0] for row in rows if row[1] in ["integer", "boolean", "double precision"]]

    return render_template('instrument_dygraph.html', columns=columns)


@app.route('/generate_instrument_graph', methods=['GET', 'POST'])
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

@app.route('/pulse')
def show_pulse():
    """Show a pulse from an instrument.

    Returns
    -------
    show_pulse.html: HTML document
        Returns an HTML document with an argument for a list of pulse_id's to choose from
        for deciding which pulse's series to plot.
    """

    cur = g.db.cursor()
    sql_query = """SELECT p.pulse_id, i.name_short, p.time FROM pulse_captures p JOIN instruments i ON (p.instrument_id = i.instrument_id)"""
    cur.execute(sql_query)
    pulses = [(row[0], row[1], row[2]) for row in cur.fetchall()]

    return render_template('show_pulse.html', pulses=pulses)


@app.route('/generate_pulse_graph', methods=['GET', 'POST'])
def generate_pulse_graph():
    """Generate graph data for a Dygraph.

    Uses the given pulse_id to get the data series to be graphed.

    Parameters
    ----------
    pulse_id: integer
        Passed as an HTML query parameter, the id of the pulse in the database,
        indicates which pulse's data to use.

    Returns
    -------
    message: JSON object
        Returns a JSON object with a list of 'x' values corresponding to a list of 'y' values.
    """

    cur = g.db.cursor()

    pulse_id = request.args.get("pulse_id")

    sql_query = """SELECT data FROM pulse_captures WHERE pulse_id = %s"""
    cur.execute(sql_query, (pulse_id,))
    row = cur.fetchone()

    # Prepares a JSON message, an array of x values and an array of y values, for the graph to plot
    # X is just a placeholder for now, since the x type is not known (time, distance, etc.)
    # TODO Determine 'X' units
    x = [i for i in range(len(row[0]))]
    y = row[0]

    message = {"x": x, "y": y}
    message = json.dumps(message)

    return message


@app.route('/radar_status')
def show_radar_status():
    """Show the status of all ARM Instruments

    Returns
    -------
    radar_status.html: HTML document
        Returns an HTML document with arguments including a list of instruments,
            their status and their most recent log entries.
    """
    cur = g.db.cursor()
    sql_query = '''SELECT i.name_short, i.instrument_id, sites.site_id, sites.name_short, l1.contents, users.name, l1.status
                FROM instruments i
                JOIN instrument_logs l1 ON (i.instrument_id = l1.instrument_id)
                LEFT OUTER JOIN instrument_logs l2 ON (i.instrument_id = l2.instrument_id AND
                    (l1.time < l2.time OR l1.time = l2.time AND l1.instrument_id < l2.instrument_id))
                LEFT OUTER JOIN sites
                      ON (sites.site_id = i.site_id)
                    LEFT OUTER JOIN users
                      ON (l1.author_id = users.user_id)
                WHERE l2.instrument_id IS NULL  ORDER BY sites.name_short;
            '''

    cur.execute(sql_query)
    logs = [dict(instrument_name=row[0], instrument_id=row[1], site_id=row[2], site=row[3],
                 contents=row[4], author=row[5], status=status_code_to_text(row[6])) for row in cur.fetchall()]
    return render_template('radar_status.html', logs=logs)


@app.route('/submit_log')
def new_log():
    """Submit a new log entry to WARNO.

    Rather than having the normal 'Get' 'Post' format, this is designed to be available to
        more than just web users.  If there are no optional arguments user_id, instrument_id,
        time, or status (or if one of those options is missing), the normal form to create a new
        log will render. If all of those options exist, the function will attempt a database insertion
        with the data.  If the insertion fails, the form to create a new log will render with an error
        message.  If the insertion is successful, the user will be redirected instead to the page of
        the instrument the log was submitted for.

    Parameters
    ----------
    error: optional, integer
        Passed as an HTML parameter, an error message set if the latitude or longitude are not
        floating point numbers
    user_id: optional, integer
        Passed as an HTML parameter, the database id of the author of the new log

    instrument_id: optional, integer
        Passed as an HTML parameter, the database id of the instrument the log is for

    time: optional, string
        Passed as an HTML parameter, a string representing the date and time for the log

    status: optional, integer
        Passed as an HTML parameter, the status code of the instrument for the log

    contents: optional, string
        Passed as an HTML parameter, the message contents for the log

    Returns
    -------
    new_log.html: HTML document
        If the new log insertion was attempted but failed, or if no insertion was attempted,
            returns an HTML form to create a new site, with an optional argument 'error' if it
            was a failed database insertion.
    instrument: Flask redirect location
        If a new log insertion was attempted and succeded,  returns a Flask redirect location
            to the instrument function, redirecting the user to the page showing the
            instrument with the instrument_id matching the insertion.
    """

    cur = g.db.cursor()
    # Default error message will not show on template when its the empty string
    error = ""

    user_id = request.args.get('user-id')
    instrument_id = request.args.get('instrument')
    time = request.args.get('time')
    status = request.args.get('status')
    contents = request.args.get('contents')

    # If there is valid data entered with the get request, insert and redirect to the instrument
    # that the log was placed for
    if user_id and instrument_id and status and time:
        # Attempt to insert an item into the database. Try/Except is necessary because
        # the timedate datatype the database expects has to be formatted correctly.
        try:
            cur.execute('''INSERT INTO instrument_logs(time, instrument_id, author_id, contents, status)
                           VALUES (%s, %s, %s, %s, %s)''', (time, instrument_id, user_id, contents, status))
            cur.execute('COMMIT')
            # Redirect to the instrument page that the log was submitted for.
            return redirect(url_for('instrument', instrument_id=instrument_id))
        except psycopg2.DataError:
            # If the timedate object expected by the database was incorrectly formatted, error is set
            # for when the page is rendered again
            error = "Invalid Date/Time Format"
        # Commit required, especially if there is an exception, or cursor breaks on next execute
        cur.execute('COMMIT')

    # If there was no valid insert, render form normally
    instrument_sql = (
        "SELECT i.instrument_id, i.name_short, s.name_short FROM instruments i, sites s "
        "WHERE i.site_id = s.site_id"
    )
    user_sql = "select u.user_id, u.name from users u"

    cur.execute(instrument_sql)
    # Format the instrument names to be more descriptive
    instruments = [dict(id=row[0], name=row[2] + ":" + row[1]) for row in cur.fetchall()]

    # Get a list of users so the user can choose who submitted the log.
    cur.execute(user_sql)
    # Add a dictionary for each site and its information to the list of sites
    users = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

    return render_template('new_log.html', users=users, instruments=instruments, status=status_text, error=error)


@app.route("/query", methods=['GET', 'POST'])
def query():
    """Execute a SQL query string specified by the user.
    Parameters
    ----------
    query: string
        Passed as an HTML form parameter, the sql query to execute.
    Returns
    -------
    query.html: HTML document
        Returns an HTML document with the results from the query displayed.
    """
    data = ""
    if request.method == 'POST':
        query = request.form.get("query")
        cur = g.db.cursor()
        try:
            cur.execute(query)
            data = cur.fetchall()
            cur.execute('COMMIT')
        except psycopg2.ProgrammingError, e:
            data = "Invalid Query.  Error: %s" % e

    if request.method == 'GET':
        pass

    return render_template("query.html", data=data)

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


if __name__ == '__main__':
    cfg = config.get_config_context()

    if cfg['type']['central_facility']:
        is_central = 1
