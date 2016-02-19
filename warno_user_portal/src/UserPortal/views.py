import json

from flask import g, render_template, request, redirect, url_for
from flask import Blueprint
from jinja2 import TemplateNotFound
import psycopg2

from UserPortal import app
from WarnoConfig import config
from WarnoConfig.utility import status_code_to_text

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
    ----------
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

def status_log_for_each_instrument(cursor):
    """Get a dictionary containing the most recent log entry for each instrument with log entries.

    Parameters
    ----------
    cursor: database cursor

    Returns
    -------
    Dictionary with the instrument ids for each log as the key and a dictionary for the log's 'author', 'status code',
    and 'contents' as the value.

    """
    sql_query = '''SELECT i.instrument_id, users.name, l1.status, l1.contents
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
    cursor.execute(sql_query)
    return {row[0]: dict(author=row[1], status_code=row[2], contents=row[3]) for row in cursor.fetchall()}

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

    # Get the most recent log for each instrument to determine its current status
    status = status_log_for_each_instrument(cur)

    # Assume the instrument status is operational unless the status has changed, handled afterward
    cur.execute('''SELECT i.instrument_id, i.name_long, i.site_id, s.name_short
                    FROM instruments i JOIN sites s ON s.site_id = i.site_id''')
    rows = cur.fetchall()
    instruments = [dict( id=row[0], instrument_name=row[1], site_id=row[2],
                         site=row[3], status=1, author="", contents="") for row in rows]

    # For each instrument, if there is a corresponding status entry from the query above,
    # add the status and the last log's author.  If not, status will stay default operational
    for instrument in instruments:
        if instrument['id'] in status:
            instrument['status'] = status[instrument['id']]["status_code"]
            instrument['author'] = status[instrument['id']]["author"]
            instrument['contents'] = status[instrument['id']]["contents"]
        instrument['status'] = status_code_to_text(instrument['status'])

    #logs = [dict(instrument_name=row[0], instrument_id=row[1], site_id=row[2], site=row[3],
    #             contents=row[4], author=row[5], status=status_code_to_text(row[6])) for row in cur.fetchall()]

    return render_template('radar_status.html', instruments=instruments)


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



if __name__ == '__main__':
    cfg = config.get_config_context()

    if cfg['type']['central_facility']:
        is_central = 1
