import logging
import json
import math
import os


from flask import g, render_template, request, redirect, url_for, jsonify
from werkzeug.contrib.fixers import ProxyFix
from sqlalchemy import Float, Boolean, Integer, or_, and_, asc
from sqlalchemy.exc import ProgrammingError as SAProgrammingError
from sqlalchemy.orm import aliased

from flask_mail import Mail
from flask_user import login_required, UserManager, SQLAlchemyAdapter, current_user

from UserPortal import app
from WarnoConfig import config
from WarnoConfig.models import db, MyRegisterForm
from WarnoConfig.models import PulseCapture, ProsensingPAF, Instrument, InstrumentLog, Site, User, ValidColumn
from WarnoConfig.utility import status_code_to_text

is_central = 0

status_text = {1: "OPERATIONAL",
               2: "NOT WORKING",
               3: "TESTING",
               4: "IN-UPGRADE",
               5: "TRANSIT"}

# Set Up app
app.config.from_object(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# Database Setup
db_cfg = config.get_config_context()['database']
s_db_cfg = config.get_config_context()['s_database']
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%s:%s@%s:%s/%s' % (db_cfg['DB_USER'], s_db_cfg['DB_PASS'],
                                                                         db_cfg['DB_HOST'], db_cfg['DB_PORT'],
                                                                         db_cfg['DB_NAME'])
app.config['SECRET_KEY'] = "THIS IS AN INSECURE SECRET"
app.config['CSRF_ENABLED'] = True

app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', '"WARNO" <noreply@relay.arm.gov>')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'relay.arm.gov')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '465'))
app.config['MAIL_USE_SSL'] = int(os.getenv('MAIL_USE_SSL', True))

app.config['USER_APP_NAME'] = "WARNO"
app.config['USER_SEND_PASSWORD_CHANGED_EMAIL'] = False
app.config['USER_SEND_REGISTERED_EMAIL'] = False
app.config['USER_SEND_USERNAME_CHANGED_EMAIL'] = False

db.init_app(app)
mail = Mail(app)

db_adapter = SQLAlchemyAdapter(db, User)
user_manager = UserManager(db_adapter, app, register_form=MyRegisterForm)


# Logging Setup
log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

# Logs to the user portal log
up_logger = logging.getLogger(__name__)
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
up_logger.addHandler(up_handler)

up_logger.info("Starting User Portal")


@app.route('/')
def landing_page():
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


# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv


def widget_log_viewer_controller(widget_id):
    """
    Controller for the log viewing widget.  Allows the user to re-query the database by changing the selection
    in the views.

    Parameters
    ----------
    widget_id: integer
        Allows for this widget to be dynamically created, tracked, and removed. Passed into the template and
        incorporated in element ids.

    Returns
    -------
    'widgets/log_viewer_controller.html': HTML document
        Renders the controller for the log_viewer widget, passing in the list of instruments available to select from as
        well as the widget id that marks all elements as part of this same widget.

    """

    db_instruments = db.session.query(Instrument)
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
        db_logs = (db.session.query(InstrumentLog).filter(InstrumentLog.instrument_id == instrument_id)
                   .order_by(InstrumentLog.time.desc()).limit(max_logs).all())
    else:
        db_logs = db.session.query(InstrumentLog).order_by(InstrumentLog.time.desc()).limit(max_logs).all()

    logs = [dict(time=log.time, contents=log.contents, status=status_code_to_text(log.status),
                 supporting_images=log.supporting_images, author=log.author.name,
                 instrument_name="%s:%s" % (log.instrument.site.name_short, log.instrument.name_short))
            for log in db_logs]

    return render_template('widgets/log_viewer.html', logs=logs)


def widget_status_plot_controller(widget_id):
    """
    Controller for the status plot widget.  Allows the user to re-query the database by changing the selection
    in the views.

    Parameters
    ----------
    widget_id: integer
        Allows for this widget to be dynamically created, tracked, and removed. Passed into the template and
        incorporated in element ids.

    Returns
    -------
    'widgets/status_plot_controller.html': HTML document
        Renders the controller for the status_plot widget, passing in the list of sites available to select from as
        well as the widget id that marks all elements as part of this same widget.

    """

    db_sites = db.session.query(Site)
    sites = [dict(id=site.id, name=site.name_short) for site in db_sites]
    return render_template('widgets/status_plot_controller.html', sites=sites, id=widget_id)


@app.route('/widget/status_plot')
def widget_status_plot():
    """
    Gets all instruments with site id matching 'site_id' (if less than 0 or not integer, assume all sites),
    the most recent log for each instrument, and sets the instrument's status as the status of the most recent log.
    Then groups the instruments by which site they are at, passing all the information back to the HTML template to
    render.

    Returns
    -------
    'widgets/status_plot.html': HTML document
        Returns an HTML document and passes in the instrument information and the widget id for the template generator.

    """
    site_id = request.args.get('site_id')

    try:
        int(site_id)
    except ValueError:
        site_id = -1

    # Get the most recent log for each instrument to determine its current status
    status = status_log_for_each_instrument()

    # Assume the instrument status is operational unless the status has changed, handled afterward
    if int(site_id) < 0:
        db_instruments = db.session.query(Instrument).join(Instrument.site).all()
    else:
        db_instruments = (db.session.query(Instrument).join(Instrument.site)
                          .filter(Instrument.site_id == int(site_id)).all())
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

    return render_template('widgets/status_plot.html', instrument_groups=instrument_groups)


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
        return render_template('instrument_dygraph.html', columns=['fake_entry', 'fake_value', 'antenna_temperature'], instrument_id=1)
    if widget_name == "log_viewer":
        return widget_log_viewer_controller(widget_id)
    if widget_name == "status_plot":
        return redirect(url_for('widget_status_plot', widget_id=widget_id))
    return render_template('widgets/%s.html' % widget_name)


def instrument_widget(columns, instrument_id):
    """
    Placeholder to return just the basic instrument_dygraph html page with nothing extra added on.

    """
    return render_template('instrument_dygraph.html', columns=['fake_entry', 'fake_value', 'antenna_temperature'], instrument_id=1)


def widget_histogram_controller(widget_id):
    """
    This function has an unusual return, being both the rendered html and extra json data.  The response is designed to
    be pulled apart on the receiving end.

    Parameters
    ----------
    widget_id

    Returns
    -------

    """
    # We need to pass in a list of valid instruments:
    db_instruments = db.session.query(Instrument).order_by(asc(Instrument.id)).all()
    instrument_list = [dict(abbv=inst.name_short, name=inst.name_long, type=inst.type, vendor=inst.vendor,
                            description=inst.description, frequency_band=inst.frequency_band,
                            location=inst.site.name_short, site_id=inst.site_id, id=inst.id)
                       for inst in db_instruments]
    column_list = {}

    for instrument in instrument_list:
        db_valid_columns = db.session.query(ValidColumn).filter(ValidColumn.instrument_id == instrument['id']).all()
        column_list[instrument['id']] = [column.column_name for column in db_valid_columns]

    response_html = render_template("widgets/histogram_controller.html", instrument_list=instrument_list, id=widget_id)
    response_json = dict(instrument_list=instrument_list, column_list=column_list)
    return jsonify(dict(html=response_html, json=response_json))


def widget_instrument_graph_controller(widget_id):
    """
    This function has an unusual return, being both the rendered html and extra json data.  The response is designed to
    be pulled apart on the receiving end.

    Parameters
    ----------
    widget_id

    Returns
    -------

    """
    # We need to pass in a list of valid instruments:
    db_instruments = db.session.query(Instrument).order_by(asc(Instrument.id)).all()
    instrument_list = [dict(abbv=inst.name_short, name=inst.name_long, type=inst.type, vendor=inst.vendor,
                            description=inst.description, frequency_band=inst.frequency_band,
                            location=inst.site.name_short, site_id=inst.site_id, id=inst.id)
                       for inst in db_instruments]
    column_list = {}

    for instrument in instrument_list:
        db_valid_columns = db.session.query(ValidColumn).filter(ValidColumn.instrument_id == instrument['id']).all()
        column_list[instrument['id']] = [column.column_name for column in db_valid_columns]

    response_html = render_template("widgets/instrument_graph_controller.html",
                                    instrument_list=instrument_list, id=widget_id)
    response_json = dict(instrument_list=instrument_list, column_list=column_list)
    return jsonify(dict(html=response_html, json=response_json))


@app.route('/widget_controller')
def widget_controller():
    widget_name = request.args.get('widget_name')
    widget_id = request.args.get('widget_id')
    if widget_name == 'log_viewer':
        return widget_log_viewer_controller(widget_id)
    if widget_name == "status_plot":
        return widget_status_plot_controller(widget_id)
        # return redirect(url_for('widget_status_plot', widget_id=widget_id))
    if widget_name == "histogram":
        return widget_histogram_controller(widget_id)
    if widget_name == "instrument_graph":
        return widget_instrument_graph_controller(widget_id)
    return ""

# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


@app.route('/pulse')
def show_pulse():
    """Show a pulse from an instrument.

    Returns
    -------
    show_pulse.html: HTML document
        Returns an HTML document with an argument for a list of pulse_id's to choose from
        for deciding which pulse's series to plot.

    """

    db_pulses = db.session.query(PulseCapture).join(PulseCapture.instrument).all()
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
    y = db.session.query(PulseCapture).filter_by(id=pulse_id).first().data
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
    logs = db.session.query(il_alias_1).join(il_alias_1.instrument).join(il_alias_1.author).\
        outerjoin(il_alias_2, and_(Instrument.id == il_alias_2.instrument_id,
                                   or_(il_alias_1.time < il_alias_2.time,
                                       and_(il_alias_1.time == il_alias_2.time,
                                            il_alias_1.instrument_id < il_alias_2.instrument_id)))).\
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
    db_instruments = db.session.query(Instrument).join(Instrument.site).all()
    instruments = [dict(id=instrument.id, instrument_name=instrument.name_long, site_id=instrument.site_id,
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
        query_arg = request.form.get("query")
        try:
            data = db.session.execute(query_arg).fetchall()
            db.session.execute('COMMIT')
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
