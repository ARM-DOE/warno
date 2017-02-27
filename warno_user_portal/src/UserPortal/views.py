import logging
import json
import os

from flask import render_template, request, redirect, url_for
from werkzeug.contrib.fixers import ProxyFix
from sqlalchemy import Float, Boolean, Integer, or_, and_
from sqlalchemy.exc import ProgrammingError as SAProgrammingError
from sqlalchemy.orm import aliased

from flask_mail import Mail
from flask_user import UserManager, SQLAlchemyAdapter

import flask.ext.restless

from UserPortal import app
from WarnoConfig import config
from WarnoConfig.models import db, MyRegisterForm
from WarnoConfig.models import PulseCapture, ProsensingPAF, Instrument, InstrumentLog, Site, User, ValidColumn
from WarnoConfig.utility import status_code_to_text
from WarnoConfig.models import EventWithText, EventWithValue, EventCode, ValidColumn

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

##################################################
######     REST API Registration       ###########
##################################################
## TODO: Register API...need to place this somewhere better.
## TODO: What is best practice on how to organize these?

api_manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
# TODO: Decide what all user information is appropriate to make available.
user_blueprint = api_manager.create_api(User, methods=['GET'], exclude_columns=['password', 'reset_password_token'], url_prefix='/api/v1')
site_blueprint = api_manager.create_api(Site, methods=['GET'], url_prefix='/api/v1')
instrument_blueprint = api_manager.create_api(Instrument, methods=['GET'], url_prefix='/api/v1')
log_blueprint = api_manager.create_api(InstrumentLog, methods=['GET'], url_prefix='/api/v1')
event_with_text_blueprint = api_manager.create_api(EventWithText, methods=['GET'], url_prefix='/api/v1')
event_with_value_blueprint = api_manager.create_api(EventWithValue, methods=['GET'], url_prefix='/api/v1', results_per_page=30)
ProsensingPAF_blueprint = api_manager.create_api(ProsensingPAF, methods=['GET'], url_prefix='/api/v1')
EventCode_blueprint = api_manager.create_api(EventCode, methods=['GET'], url_prefix='/api/v1', results_per_page=30)
ValidColumn_blueprint = api_manager.create_api(ValidColumn, methods=['GET'], url_prefix='/api/v1', results_per_page=30)


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

@app.route('/api/v1')
def top_level_rest_anchor():
    result = {}
    api_list = (("users",User),
                  ("sites", Site),
                  ("instruments", Instrument),
                  ("instrument_log", InstrumentLog),
                  ("events_with_text", EventWithText),
                  ("events_with_value",EventWithValue),
                  ("prosensing_paf",ProsensingPAF),
                  ("event_codes",EventCode),
                  ("valid_columns", ValidColumn))
    for model in api_list:
        result[model[0]] = api_manager.url_for(model[1])
    return flask.jsonify(result)


@app.route('/')
def landing_page():
    # Temporary home page
    return redirect(url_for('show_radar_status'))


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
