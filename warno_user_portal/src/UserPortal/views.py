import json

from flask import g, render_template, request, redirect, url_for
from flask import Blueprint
from jinja2 import TemplateNotFound
import psycopg2
from sqlalchemy import Float, Boolean, Integer, or_, and_
from sqlalchemy.orm import aliased

from UserPortal import app
from WarnoConfig import config
from WarnoConfig import database
from WarnoConfig.models import PulseCapture, ProsensingPAF, Instrument, InstrumentLog, Site, User
from WarnoConfig.utility import status_code_to_text

is_central = 0

app.config.from_object(__name__)

status_text = {1: "OPERATIONAL",
               2: "NOT WORKING",
               3: "TESTING",
               4: "IN-UPGRADE",
               5: "TRANSIT"}


@app.before_request
def before_request():
    """Before each Request.
    """


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

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Closes database session on request or application teardown.

    Parameters
    ----------
    exception: optional, Exception
        An Exception that may have caused the teardown.

    """
    database.db_session.remove()

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

    # Lists available columns to graph, and only allows an entry if it is an acceptable data type (graphable).
    columns = [col.key for col in ProsensingPAF.__table__.columns
               if type(col.type) in [Integer, Boolean, Float]]

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

    db_pulses = database.db_session.query(PulseCapture).join(PulseCapture.instrument).all()
    pulses = [(pulse.id, pulse.instrument.name_short, pulse.time)
              for pulse in db_pulses]

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
    pulse_id = request.args.get("pulse_id")

    # Prepares a JSON message, an array of x values and an array of y values, for the graph to plot
    # X is just a placeholder for now, since the x type is not known (time, distance, etc.)
    # TODO Determine 'X' units
    y = database.db_session.query(PulseCapture).filter_by(pulse_id=pulse_id).first().data
    x = [i for i in range(len(y))]

    message = {"x": x, "y": y}
    message = json.dumps(message)

    return message

def status_log_for_each_instrument():
    """Get a dictionary containing the most recent log entry for each instrument with log entries.

    Returns
    -------
    Dictionary with the instrument ids for each log as the key and a dictionary for the log's 'author', 'status code',
    and 'contents' as the value.

    """
    il_alias_1 = aliased(InstrumentLog, name='il_alias_1')
    il_alias_2 = aliased(InstrumentLog, name='il_alias_2')
    logs = database.db_session.query(il_alias_1).join(il_alias_1.instrument).join(il_alias_1.author).\
        outerjoin(il_alias_2, and_(Instrument.id == il_alias_2.instrument_id,
                                 or_(il_alias_1.time < il_alias_2.time,
                                     and_(il_alias_1.time == il_alias_2.time, il_alias_1.instrument_id < il_alias_2.instrument_id)))).\
        filter(il_alias_2.id == None).all()

    recent_logs = {log.instrument.id: dict(author=log.author.name, status_code=log.status, contents=log.contents)
                   for log in logs}

    return recent_logs

@app.route('/radar_status')
def show_radar_status():
    """Show the status of all ARM Instruments

    Returns
    -------
    radar_status.html: HTML document
        Returns an HTML document with arguments including a list of instruments,
            their status and their most recent log entries.
    """

    # Get the most recent log for each instrument to determine its current status
    status = status_log_for_each_instrument()

    # Assume the instrument status is operational unless the status has changed, handled afterward
    db_instruments = database.db_session.query(Instrument).join(Instrument.site).all()
    instruments = [dict( id=instrument.id, instrument_name=instrument.name_long, site_id=instrument.site_id,
                         site=instrument.site.name_short, status=1, author="", contents="")
                   for instrument in db_instruments]

    # For each instrument, if there is a corresponding status entry from the query above,
    # add the status and the last log's author.  If not, status will stay default operational
    for instrument in instruments:
        if instrument['id'] in status:
            instrument['status'] = status[instrument['id']]["status_code"]
            instrument['author'] = status[instrument['id']]["author"]
            instrument['contents'] = status[instrument['id']]["contents"]
        instrument['status'] = status_code_to_text(instrument['status'])

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
        try:
            data = database.db_session.execute(query).fetchall()
            database.db_session.execute('COMMIT')
        except psycopg2.ProgrammingError, e:
            data = "Invalid Query.  Error: %s" % e

    if request.method == 'GET':
        pass

    return render_template("query.html", data=data)



if __name__ == '__main__':
    cfg = config.get_config_context()

    if cfg['type']['central_facility']:
        is_central = 1
