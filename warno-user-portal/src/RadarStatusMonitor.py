from flask import Flask, g, render_template, request, redirect, url_for
import psycopg2
import json
import yaml
import datetime

DB_HOST = '192.168.50.99'
DB_NAME = 'warno'
DB_USER = 'warno'
DB_PASS = 'warno'

is_central = 0

app = Flask(__name__)
app.config.from_object(__name__)


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


@app.route('/dygraph')
def show_dygraph():
    """Show Dygraphs.

    Returns
    -------
    instrument_dygraph.html: HTML document
        Returns an HTML document with a list of columns to select from, the columns
        being available table columns to plot against time.
    """

    # Initialize the database cursor
    cur = g.db.cursor()
    # Select the columns from the data table.
    # Allows the template to create a dropdown list with fixed values.
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'prosensing_paf'")
    rows = cur.fetchall()
    # Put all of  the names in one list
    columns = [row[0] for row in rows if row[1] in ["integer", "boolean", "double precision"]]

    # Render the template and pass the list of columns
    return render_template('instrument_dygraph.html', columns=columns)


@app.route('/generate_instrument_graph', methods=['GET', 'POST'])
def generate_instrument_graph():
    """Generate graph data for a Dygraph for an instrument.

    Uses the supplied key and instrument_id to get all data from the 'time' and
        specified 'key' column for the instrument with 'instrument_id', passing them
        as 'x' and 'y' values to be graphed together.

    Parameters
    ----------
    key: string
        Passed as an HTML query parameter, the name of the database column
            to plot against time.

    instrument_id: integer
        Passed as an HTML query parameter, the id of the instrument in the
            database, indicates which instrument's data to use.

    Returns
    -------
    message: JSON object
        Returns a JSON object with a list of 'x' values corresponding to a list of 'y' values.
    """

    cur = g.db.cursor()

    # Get the key and instrument_id from the arguments passed to the function.
    # The key is plotted against time in the graph data to be returned.
    # The key is from a selection on the form, not free typed by the user.
    # The instrument_id indicates which instrument's data to use for the graph.
    key = request.args.get("key")
    instrument_id = request.args.get("instrument_id")
    start = request.args.get("start")
    end = request.args.get("end")
    print("Start %s" % start)
    print("End %s" % end)

    # Get a list of valid column names for the table in the database
    cur.execute("SELECT special, description FROM instrument_data_references WHERE instrument_id = %s", (instrument_id,))
    references = cur.fetchall()
    print("Reference selection: %s" % references)
    column_list = []
    for reference in references:
        print("Current reference:")
        print reference
        if reference[0] == True:
            cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (reference[1],))
            rows = cur.fetchall()
            columns = [row[0] for row in rows if row[1] in ["integer", "boolean", "double precision"]]
        else:
            columns = [reference[1]]
        column_list.extend(columns)
    # If the key is not in the columns, return an empty message
    # Prevents a user from SQL injection when we combine key into the FROM clause of the next query
    # Standard parameterization does not work for the FROM clause, so we have to protect our own way
    if key not in column_list:
        return json.dumps({"x": [], "y": []})

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
                sql_query = 'SELECT time, %s FROM %s WHERE instrument_id = %%s AND time >= %%s AND time <= %%s' % (key, reference[1])
    # Selects the time and the "key" column from the data table for the supplied instrument_id
    try:
        cur.execute(sql_query, (instrument_id, start, end))
    except Exception, e:
        print(e)
        return json.dumps({"x": [], "y": []})
    rows = cur.fetchall()

    # Prepares a JSON message, an array of x values and an array of y values, for the graph to plot
    # ? Is iso format timezone ambiguous?
    x = [row[0].isoformat() for row in rows]
    y = [row[1] for row in rows]
    message = {"x": x, "y": y}
    message = json.dumps(message)

    # Send out the JSON message
    return message


@app.route('/users/new', methods=['GET', 'POST'])
def new_user():
    """Add a new User to WARNO.

    Returns
    -------
    new_user.html: html document
        If the request method is 'GET', returns a form to create a new user.

    list_instruments: Flask redirect location
        If the request method is 'POST', returns a Flask redirect location to the
            list_users function, redirecting the user to the list of users.
    """

    cur = g.db.cursor()

    if request.method == 'POST':
        # Get the information for the insert from the submitted form arguments
        # Lengths validated in views
        # ?email may need validation
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        position = request.form.get('position')
        password = request.form.get('password')

        # Insert the new user into the database
        cur.execute('''INSERT INTO users(name, "e-mail", location, position, password, authorizations)
                    VALUES (%s, %s, %s, %s, %s, %s)''', (name, email, location, position, password, "None"))
        cur.execute('COMMIT')

        # Redirect to the updated list of users
        return redirect(url_for("list_users"))

    # If the request is for the new form
    if request.method == 'GET':
        # Render the new user template
        return render_template('new_user.html')


@app.route('/users')
def list_users():
    """List WARNO Users.

    Returns
    -------
    users_template.html: HTML document
        Returns an HTML document with an argument for the list of users and their information.
    """

    cur = g.db.cursor()

    # Grab the list of users and their information
    cur.execute('SELECT user_id, name, "e-mail", location, position FROM users')
    # Add each user and their information to a dictionary in the list of users
    users = [dict(name=row[1], email=row[2], location=row[3], position=row[4], id=row[0]) for row in cur.fetchall()]

    # Render the template with the list of users
    return render_template('users_template.html', users=users)


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


@app.route('/instruments/new', methods=['GET', 'POST'])
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
        itype = request.form.get('itype')
        vendor = request.form.get('vendor')
        description = request.form.get('description')
        frequency_band = request.form.get('frequency_band')
        site = request.form.get('site')

        # Insert a new instrument into the database
        cur.execute('''INSERT INTO instruments(name_short, name_long, type, vendor, description, frequency_band, site_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)''', (abbv, name, itype, vendor, description, frequency_band, site))
        cur.execute('COMMIT')

        # Redirect to the updated list of instruments
        return redirect(url_for("list_instruments"))

    # If the request is to get the form
    if request.method == 'GET':
        # Get a list of sites and their ids for the dropdown in the add user form
        cur.execute('''SELECT site_id, name_short FROM sites ''')
        # Add each site as a dictionary to a list of sites
        sites = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

        # Return the list of sites to the new instrument form
        return render_template('new_instrument.html', sites=sites)


@app.route('/instruments')
def list_instruments():
    """List  ARM Instruments.

    Returns
    -------
    instrument_list.html: HTML document
        Returns an HTML document with an argument for a list of instruments and their information.
    """

    cur = g.db.cursor()

    # Grab the list of instruments and their information
    cur.execute('''SELECT i.instrument_id, i.name_short, i.name_long, i.type,
                i.vendor, i.description, i.frequency_band, s.name_short, s.site_id FROM instruments i
                JOIN sites s ON (i.site_id = s.site_id) ORDER BY i.instrument_id ASC''')
    instruments = [dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], description=row[5],
                        frequency_band=row[6], location=row[7], site_id=row[8], id=row[0])
                   for row in cur.fetchall()]

    # Render the template with the generated
    return render_template('instrument_list.html', instruments=instruments)


@app.route('/instruments/<instrument_id>')
def show_instrument(instrument_id):
    """Show an individual ARM Instrument.

    Parameters
    ----------
    instrument_id: integer
        The database id of the instrument to be shown.

    Returns
    -------
    show_instrument.html: HTML document
        Returns an HTML document with arguments including instrument information,
            the 5 most recent log entries, the status of the instrument, and the list of
            columns for available data to plot on graphs.
    """

    cur = g.db.cursor()

    # Grabs the instrument information for the instrument matching "instrument_id" from the database
    cur.execute('''SELECT i.instrument_id, i.name_short, i.name_long, i.type,
            i.vendor, i.description, i.frequency_band, s.name_short, s.latitude, s.longitude, s.site_id
            FROM instruments i JOIN sites s ON (i.site_id = s.site_id)
            WHERE i.instrument_id = %s''', (instrument_id,))
    row = cur.fetchone()
    # Inserts the information from the query into a dictionary object
    instrument = dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], description=row[5],
                      frequency_band=row[6], location=row[7], latitude=row[8], longitude=row[9],
                      site_id=row[10], id=row[0])

    # Grabs the most recent 5 logs for the instrument matching "instrument_id" from the database
    cur.execute('''SELECT l.time, l.contents, l.status, l.supporting_images, u.name
                    FROM instrument_logs l JOIN users u
                    ON l.author_id = u.user_id WHERE l.instrument_id = %s
                    ORDER BY time DESC LIMIT 5''', (instrument_id,))
    # Creates a list of dictionaries, each dictionary being one of the log entries
    recent_logs = [dict(time=row[0], contents=row[1], status=row[2], supporting_images=row[3],
                        author=row[4]) for row in cur.fetchall()]

    # If there are any log, the most recent log (the first of the list) has the status
    # Uses helper function to print the status code to text
    if recent_logs:
        status = status_code_to_text(recent_logs[0]["status"])
    # If there are no recent logs, assume the instrument is operational
    else:
        status = "OPERATIONAL"

    cur = g.db.cursor()
    # Grabs all columns available to plot. Uses the table data references table to determine which columns to use
    # and which references are to full tables, in which case, it pulls all value columns from the table.
    cur.execute("SELECT special, description FROM instrument_data_references WHERE instrument_id = %s", (instrument_id,))
    references = cur.fetchall()
    column_list = []
    for reference in references:
        if reference[0] == True:
            cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (reference[1],))
            rows = cur.fetchall()
            columns = [row[0] for row in rows if row[1] in ["integer", "boolean", "double precision"]]
        else:
            columns = [reference[1]]
        column_list.extend(columns)

    return render_template('show_instrument.html', instrument=instrument,
                           recent_logs=recent_logs, status=status, columns=sorted(column_list))


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
    # Selects the time and the "key" column from the data table for the supplied instrument_id
    cur.execute(sql_query, (pulse_id,))
    row = cur.fetchone()

    # Prepares a JSON message, an array of x values and an array of y values, for the graph to plot
    # X is just a placeholder for now, since the x type is not known (time, distance, etc.)
    x = [i for i in range(len(row[0]))]
    y = row[0]

    message = {"x": x, "y": y}
    message = json.dumps(message)

    # Send out the JSON message
    return message


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
        # Attempts to convert the string into a float. Returns true if it works
        float(s)
        return True
    except ValueError:
        # If the conversion doesn't work, return false
        return False


@app.route('/sites/new', methods=['GET', 'POST'])
def new_site():
    """Add a new ARM Site to WARNO.

    If the request method is 'GET', it will just render the form for a new site. However, if
        the method is 'POST', it checks if the values are valid for insertion. If they are not
        valid, it will render the from for a new site, but with an error message.  If the values
        are valid, the new site is created and the user is redirected to a list of sites.

    Parameters
    ----------
    error: optional, integer
        Passed as an HTML parameter, an error message set if the latitude or longitude are
            not floating point numbers

    Returns
    -------
    new_site.html: HTML document
        If the request method is 'GET' or the method is 'POST' but the new site was invalid,
            returns an HTML form to create a new site, with an optional argument 'error' if it
            was a failed 'POST' request.
    list_sites: Flask redirect location
        If the request method is 'POST' and the new site is valid, returns a Flask redirect
            location to the list_sites function, redirecting the user to the list of ARM sites.
    """

    # If the method is post, the user has submitted the information in the form.
    # Try to insert the new site into the database, if the values are incorrect redirect
    # with an appropriate error message
    if request.method == 'POST':
        # Get the parameters from the url request
        # Field lengths limited in the views
        abbv = request.form.get('abbv')
        name = request.form.get('name')
        lat = request.form.get('lat')
        lon = request.form.get('lon')
        facility = request.form.get('facility')
        mobile = request.form.get('mobile')
        location_name = request.form.get('location_name')

        # If the "mobile" box was checked in new_site, mobile is True. Else, false
        if mobile == "on":
            mobile = True
        else:
            mobile = False

        # Uses helper function to check if latitude and longitude are valid numbers
        if is_number(lat) and is_number(lon):
            cur = g.db.cursor()
            cur.execute('''INSERT INTO sites(name_short, name_long, latitude, longitude, facility, mobile, location_name)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)''', (abbv, name, float(lat), float(lon), facility, mobile, location_name))
            cur.execute('COMMIT')

            # After insertion, redirect to the updated list of sites
            return redirect(url_for("list_sites"))
        else:
            # Redirects with error
            return redirect(url_for("new_site", error="Latitude and Longitude must be numbers."))

    if request.method == 'GET':
        # If there was an error from before, passes the error message
        # Otherwise, error will be an empty string and will not show up in the template
        error = request.args.get('error')
        return render_template('new_site.html', error=error)


@app.route('/sites')
def list_sites():
    """List  ARM Sites.

    Returns
    -------
    site_list.html: HTML document
        Returns an HTML document with an argument for a list of sites and their information.
    """

    cur = g.db.cursor()

    sql_query = '''SELECT s.name_short, s.name_long, s.latitude, s.longitude,
                    s.facility, s.mobile, s.location_name, s.site_id FROM sites s'''
    cur.execute(sql_query)
    sites = [dict(abbv=row[0], name=row[1], latitude=row[2], longitude=row[3], facility=row[4],
             mobile=row[5], location_name=row[6], id=row[7]) for row in cur.fetchall()]

    return render_template('site_list.html', sites=sites)


@app.route('/sites/<site_id>')
def show_site(site_id):
    """Show an individual ARM Site.

    Parameters
    ----------
    site_id: integer
        The database id of the site to be shown.

    Returns
    -------
    show_instrument.html: HTML document
        Returns an HTML document with arguments including site information, the 5 most
            recent logs of all instruments at the site, and a list of the instruments at the site
            along with their information.
    """

    cur = g.db.cursor()

    cur.execute('''SELECT site_id, name_short, name_long, latitude, longitude, facility,
                    mobile, location_name FROM sites WHERE site_id = %s''', (site_id,))
    row = cur.fetchone()
    site = dict(abbv=row[1], name=row[2], latitude=row[3], longitude=row[4],
                facility=row[5], mobile=row[6], location_name=row[7], id=row[0])

    # Get the 5 most recent logs to display
    cur.execute('''SELECT l.time, l.contents, l.status, l.supporting_images, u.name, i.name_short
                    FROM instrument_logs l JOIN users u
                    ON l.author_id = u.user_id JOIN instruments i ON i.instrument_id = l.instrument_id
                    JOIN sites s ON i.site_id = s.site_id
                    WHERE s.site_id = %s
                    ORDER BY time DESC LIMIT 5''', (site_id,))
    recent_logs = [dict(time=row[0], contents=row[1], status=row[2], supporting_images=row[3],
                        author=row[4], instrument=row[5]) for row in cur.fetchall()]

    # Get the most recent log for each instrument to determine its current status
    sql_query = '''SELECT i.instrument_id, users.name, l1.status
                FROM instruments i
                JOIN instrument_logs l1 ON (i.instrument_id = l1.instrument_id)
                LEFT OUTER JOIN instrument_logs l2 ON (i.instrument_id = l2.instrument_id AND
                    (l1.time < l2.time OR l1.time = l2.time AND l1.instrument_id < l2.instrument_id))
                LEFT OUTER JOIN sites
                      ON (sites.site_id = i.site_id)
                    LEFT OUTER JOIN users
                      ON (l1.author_id = users.user_id)
                WHERE (l2.instrument_id IS NULL AND i.site_id = %s)  ORDER BY sites.name_short;
            '''
    cur.execute(sql_query, (site_id,))
    status = {row[0]: dict(last_author=row[1], status_code=row[2]) for row in cur.fetchall()}

    # Assume the instrument status is operational unless the status has changed, handled afterward
    cur.execute('''SELECT instrument_id, name_short, name_long, type, vendor, frequency_band, description
                    FROM instruments WHERE site_id = %s''', (site_id,))
    rows = cur.fetchall()
    instruments = [dict(abbv=row[1], name=row[2], type=row[3], vendor=row[4], frequency_band=row[5],
                        description=row[6], status=1, last_author="", id=row[0]) for row in rows]

    # For each instrument, if there is a corresponding status entry from the query above,
    # add the status and the last log's author.  If not, status will stay default operational
    for instrument in instruments:
        if instrument['id'] in status:
            instrument['status'] = status[instrument['id']]["status_code"]
            instrument['last_author'] = status[instrument['id']]["last_author"]
        instrument['status'] = status_code_to_text(instrument['status'])

    return render_template('show_site.html', site=site, instruments=instruments, recent_logs=recent_logs)


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
    show_instrument: Flask redirect location
        If a new log insertion was attempted and succeded,  returns a Flask redirect location
            to the show_instrument function, redirecting the user to the page showing the
            instrument with the instrument_id matching the insertion.
    """

    cur = g.db.cursor()
    # Set the default error message. Will not show on template when its the empty string
    error = ""

    user_id = request.args.get('user-id')
    instrument_id = request.args.get('instrument')
    time = request.args.get('time')
    status = request.args.get('status')
    contents = request.args.get('contents')

    # If there is valid data entered with the get request, insert and redirect to the instrument
    # that the log was placed for
    # (If a user visits the page for the first time with no arguments,
    # skips this section and renders form.)
    if user_id and instrument_id and status and time:
        # Attempt to insert an item into the database. Try/Except is necessary because
        # the timedate datatype the database expects has to be formatted correctly.
        try:
            cur.execute('''INSERT INTO instrument_logs(time, instrument_id, author_id, contents, status)
                           VALUES (%s, %s, %s, %s, %s)''', (time, instrument_id, user_id, contents, status))
            cur.execute('COMMIT')
            # Redirect to the instrument page that the log was submitted for.
            # Log will likely appear on page.
            # May not appear if the date was set to older than the 5 most recent logs
            return redirect(url_for('show_instrument', instrument_id=instrument_id))
        except psycopg2.DataError:
            # If the timedate object expected by the database was incorrectly formatted, error is set
            # for when the page is rendered again
            error = "Invalid Date/Time Format"
        # Commit required, especially if there is an exception,
        # otherwise the cursor breaks on the next execute
        cur.execute('COMMIT')

    # If there was no valid insert, render form normally
    instrument_sql = (
                                "SELECT i.instrument_id, i.name_short, s.name_short FROM instruments i, sites s "
                                "WHERE i.site_id = s.site_id"
                                )
    user_sql = "select u.user_id, u.name from users u"

    # Get a list of instruments to select from in the form
    cur.execute(instrument_sql)
    # Format the instrument names to be more descriptive
    instruments = [dict(id=row[0], name=row[2]+":"+row[1]) for row in cur.fetchall()]

    # Get a list of users to choose who submitted the log.
    # This list will be selected from in the form
    cur.execute(user_sql)
    # Add a dictionary for each site and its information to the list of sites
    users = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

    return render_template('new_log.html', users=users, instruments=instruments, status=status_text, error=error)


@app.route("/query", methods=['GET', 'POST'])
def query():
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


def load_config():
    """Load the configuration Object from the config file

    Loads a configuration Object from the config file.

    Returns
    -------
    config: dict
        Configuration Dictionary of Key Value Pairs
    """
    with open("config.yml", 'r') as ymlfile:
        config = yaml.load(ymlfile)
    return config


@app.route('/')
def hello_world():
    # Temporary home page
    return redirect(url_for('show_radar_status'))


if __name__ == '__main__':
    cfg = load_config()

    if cfg['type']['central_facility']:
        is_central = 1
        DB_HOST = "192.168.50.100"

    app.run(debug=True, host='0.0.0.0', port=80)
