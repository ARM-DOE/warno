import logging
import json
import os

from flask import g, render_template, request, redirect, url_for
from werkzeug.contrib.fixers import ProxyFix
from sqlalchemy import Float, Boolean, Integer, or_, and_
from sqlalchemy.exc import ProgrammingError as SAProgrammingError
from sqlalchemy.orm import aliased
import math

from UserPortal import app
from WarnoConfig import config
from WarnoConfig import database
from WarnoConfig.models import PulseCapture, ProsensingPAF, Instrument, InstrumentLog, Site, User
from WarnoConfig.utility import status_code_to_text

is_central = 0

app.config.from_object(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

status_text = {1: "OPERATIONAL",
               2: "NOT WORKING",
               3: "TESTING",
               4: "IN-UPGRADE",
               5: "TRANSIT"}

log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

# Logs to the user portal log
up_logger = logging.getLogger(__name__)
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
up_logger.addHandler(up_handler)

up_logger.info("Starting User Portal")


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


def widget_log_viewer_controller(widget_id):
    """
    Controller for the log viewing widget.  Allows the user to re-query the database by changing the selection
    in the views.

    Parameters
    ----------
    widget_id: integer
        Allows for this widget to be dynamically created, tracked, and removed.

    Returns
    -------
    'widgets/log_viewer_controller.html': HTML document
        Renders the controller for the log_viewer widget, passing in the list of instruments available to select from as
        well as the widget id that marks all elements as part of this same widget.

    """

    db_instruments = database.db_session.query(Instrument)
    instruments = [dict(id=inst.id, site=inst.site.name_short, name=inst.name_short) for inst in db_instruments]
    return render_template('widgets/log_viewer_controller.html', instruments=instruments, id=widget_id)


@app.route('/widget/log_viewer')
def widget_log_viewer():
    """
    Gets the most recent logs for the instrument whose id matches the request's 'instrument_id' argument.  The returned
    list of instruments is limited by the request's 'max_logs' argument.

    Returns
    -------
    'widgets/log_viewer.html': HTML document
        Renders the log_viewer, passing in the logs' information.

    """

    instrument_id = request.args.get('instrument_id')
    req_max_logs = request.args.get('max_logs')

    max_logs = 5
    try:
        floor_max_logs = math.floor(float(req_max_logs))
        if (floor_max_logs < 100) and (floor_max_logs > 0):
            max_logs = floor_max_logs
    except ValueError:
        max_logs = 5

    if float(instrument_id) >= 0:
        db_logs = database.db_session.query(InstrumentLog).filter(InstrumentLog.instrument_id == instrument_id).order_by(InstrumentLog.time.desc()).limit(max_logs).all()
    else:
        db_logs = database.db_session.query(InstrumentLog).order_by(InstrumentLog.time.desc()).limit(max_logs).all()

    logs = [dict(time=log.time, contents=log.contents, status=status_code_to_text(log.status),
                 supporting_images=log.supporting_images, author=log.author.name)
            for log in db_logs]

    return render_template('widgets/log_viewer.html', logs=logs)


@app.route('/widget/status_plot')
def widget_status_plot():
    """
    Gets all instruments, the most recent log for each instrument, and sets the instrument's status as the status of the
    most recent log.  Then groups the instruments by which site they are at, passing all the information back to the
    HTML template to render.

    Returns
    -------
    'widgets/status_plot.html': HTML document
        Returns an HTML document and passes in the instrument information and the widget id for the template generator.

    """
    widget_id = request.args.get('widget_id')

    # Get the most recent log for each instrument to determine its current status
    status = status_log_for_each_instrument()

    # Assume the instrument status is operational unless the status has changed, handled afterward
    db_instruments = database.db_session.query(Instrument).join(Instrument.site).all()
    instruments = [dict(id=instrument.id, name=instrument.name_short, site_id=instrument.site.id,
                        site=instrument.site.name_short, status=1)
                   for instrument in db_instruments]

    # For each instrument, if there is a corresponding status entry from the query above,
    # add the status and the last log's author.  If not, status will stay default operational
    for instrument in instruments:
        if instrument['id'] in status:
            instrument['status'] = status[instrument['id']]["status_code"]
        instrument['status'] = status_code_to_text(instrument['status'])

    instrument_groups = {}

    for instrument in instruments:
        if instrument['site'] not in instrument_groups.keys():
            instrument_groups[instrument['site']] = [instrument]
        else:
            instrument_groups[instrument['site']].append(instrument)

    return render_template('widgets/status_plot.html', id=widget_id, instrument_groups=instrument_groups)


@app.route('/gen_widget')
def gen_widget():
    """
    Selects which widget to generate based on the request argument 'widget_name', and passes the request argument
    'widget_id' into the widget controller.  The use of 'widget_id' allows for the different widgets to be dynamically
    created, tracked, and removed.

    Returns
    -------
    An HTML page corresponding to the selected widget.

    """

    widget_name = request.args.get('widget_name')
    widget_id = request.args.get('widget_id')
    if widget_name == "instrument_dygraph":
        return render_template('instrument_dygraph.html', columns=['fake_entry', 'fake_value', 'antenna_temperature'], instrument_id = 1)
    if widget_name == "log_viewer":
        return widget_log_viewer_controller(widget_id)
    if widget_name == "status_plot":
        return redirect(url_for('widget_status_plot', widget_id=widget_id))
    return render_template('widgets/%s.html' % widget_name)


def instrument_widget(columns, instrument_id):
    """
    Placeholder to return just the basic instrument_dygraph html page with nothing extra added on.

    """
    return render_template('instrument_dygraph.html', columns=['fake_entry', 'fake_value', 'antenna_temperature'], instrument_id = 1)


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


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


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
    y = database.db_session.query(PulseCapture).filter_by(id=pulse_id).first().data
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
    sites = {}
    for instrument in instruments:
        if instrument['id'] in status:
            instrument['status'] = status[instrument['id']]["status_code"]
            instrument['author'] = status[instrument['id']]["author"]
            instrument['contents'] = status[instrument['id']]["contents"]
        instrument['status'] = status_code_to_text(instrument['status'])

    sites = {inst['site']: inst['site_id'] for inst in instruments}

    return render_template('radar_status.html', instruments=instruments, sites=sites)


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
        except SAProgrammingError, e:
            data = "Invalid Query.  Error: %s" % e
            up_logger.warn("Invalid Query.  Error: %s", e)

    if request.method == 'GET':
        pass

    return render_template("query.html", data=data)


if __name__ == '__main__':
    cfg = config.get_config_context()

    if cfg['type']['central_facility']:
        is_central = 1
