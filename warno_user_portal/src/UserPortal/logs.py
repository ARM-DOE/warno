import psycopg2
import requests
import logging
import json
import os

from flask import render_template, redirect, url_for, request, abort
from flask import Blueprint, Markup
from flask_user import current_user

from WarnoConfig.utility import status_code_to_text, status_text
from WarnoConfig.models import InstrumentLog, User, Instrument
from WarnoConfig.models import db
from WarnoConfig import config


logs = Blueprint('logs', __name__, template_folder='templates')

log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

# Logs to the user portal log
up_logger = logging.getLogger(__name__)
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
up_logger.addHandler(up_handler)


@logs.route('/manage_logs')
def manage_logs():
    if current_user.is_anonymous or current_user.authorizations not in ["engineer"]:
        abort(403)

    db_instrument_logs = db.session.query(InstrumentLog).order_by(InstrumentLog.time.desc()).all()

    instrument_logs = [dict(status=status_code_to_text(log.status), author=log.author.name, time=log.time,
                            instrument=log.instrument.site.name_short + "-" + log.instrument.name_short,
                            contents=Markup(log.contents), id=log.id)
                       for log in db_instrument_logs]

    return render_template("manage_logs.html", instrument_logs=instrument_logs)

@logs.route("/delete_log")
def delete_log():
    if current_user.is_anonymous or current_user.authorizations not in ["engineer"]:
        abort(403)

    instrument_id = request.args.get("id")
    if not instrument_id:
        abort(400)

    instrument_log = db.session.query(InstrumentLog).filter(InstrumentLog.id == instrument_id).first()

    db.session.delete(instrument_log)
    db.session.commit()

    return  redirect(url_for("logs.manage_logs"))

@logs.route('/submit_log')
def new_log():
    """Submit a new log entry to WARNO.

    Rather than having the normal 'Get' 'Post' format, this is designed to be available to
        more than just web users.  If there are no optional arguments user_id, instrument_id,
        time, or status (or if one of those options is missing), the normal form to create a new
        log will render. If all of those options exist, the function will attempt a database insertion
        with the data.  If the insertion fails, the form to create a new log will render with an error
        message.  If the insertion is successful, the user will be redirected instead to the page of
        the instrument the log was submitted for.  Also, upon success, if it is not the central facility,
        the log's information will be sent to the central facility's Event Manager.

    Parameters
    ----------
    error: optional, integer
        Passed as an HTML parameter, an error message set if the latitude or longitude are not
        floating point numbers
    user-id: optional, integer
        Passed as an HTML parameter, the database id of the author of the new log

    instrument: optional, integer
        Passed as an HTML parameter, the database id of the instrument the log is for

    time: optional, string
        Passed as an HTML parameter, a string representing the date and time for the log

    status: optional, integer
        Passed as an HTML parameter, the status code of the instrument for the log

    contents: optional, string
        Passed as an HTML parameter, the message contents for the log

    create-another: optional, string
        Passed as an HTML parameter, 'on' indicates that the option to create a new log was selected, '' otherwise

    Returns
    -------
    new_log.html: HTML document
        If the new log insertion was attempted but failed, or if no insertion was attempted,
            returns an HTML form to create a new site, with an optional argument 'error' if it
            was a failed database insertion.
    instrument: Flask redirect location
        If a new log insertion was attempted and succeeded,  returns a Flask redirect location
            to the instrument function, redirecting the user to the page showing the
            instrument with the instrument_id matching the insertion.
    """
    if current_user.is_anonymous or current_user.authorizations not in ["engineer", "technician"]:
        abort(403)

    # Default error message will not show on template when its the empty string
    error = ""

    if request.args.get('create-another') == "on":
        create_another = True
    else:
        create_another = False

    new_db_log = InstrumentLog()
    new_db_log.author_id = request.args.get('user-id')
    new_db_log.instrument_id = request.args.get('instrument')
    new_db_log.time = request.args.get('time')
    new_db_log.status = request.args.get('status')
    new_db_log.contents = request.args.get('contents')

    cfg = config.get_config_context()
    cert_verify = cfg['setup']['cert_verify']

    # If there is valid data entered with the get request, insert and redirect to the instrument
    # that the log was placed for
    if new_db_log.author_id and new_db_log.instrument_id and new_db_log.status and new_db_log.time:
        # Attempt to insert an item into the database. Try/Except is necessary because
        # the timedate datatype the database expects has to be formatted correctly.
        if new_db_log.time == 'Invalid Date':
            error = "Invalid Date/Time Format"
            up_logger.error("Invalid Date/Time format for new log entry. "
                            "'Invalid Date' passed from JavaScript parser in template")
        else:
            try:
                db.session.add(new_db_log)
                db.session.commit()
            except psycopg2.DataError:
                # If the timedate object expected by the database was incorrectly formatted, error is set
                # for when the page is rendered again
                error = "Invalid Date/Time Format"
                up_logger.error("Invalid Date/Time format for new log entry.  Value: %s", new_db_log.time)
            else:
                # If it is not a central facility, pass the log to the central facility
                if not cfg['type']['central_facility']:
                    packet = dict(event_code=5,
                                  data=dict(instrument_id=new_db_log.instrument_id, author_id=new_db_log.author_id,
                                            time=str(new_db_log.time), status=new_db_log.status,
                                            contents=new_db_log.contents, supporting_images=None))
                    payload = json.dumps(packet)
                    requests.post(cfg['setup']['cf_url'], data=payload,
                                  headers={'Content-Type': 'application/json'}, verify=cert_verify)

                # If planning to create another, redirect back to this page.  Prevents previous log information
                # from staying in the url bar, which would cause refreshes to submit new logs.  If not creating another,
                # redirect to the instrument page that the log was submitted for
                if create_another:
                    return redirect(url_for('logs.new_log'))
                else:
                    return redirect(url_for('instruments.instrument', instrument_id=new_db_log.instrument_id))

    # If there was no valid insert render normally but pass the indicative error

    # Format the instrument names to be more descriptive
    db_instruments = db.session.query(Instrument).all()
    instruments = [dict(id=instrument.id, name=instrument.site.name_short + ":" + instrument.name_short)
                   for instrument in db_instruments]
    for instrument in instruments:
        recent_log = db.session.query(InstrumentLog).filter(InstrumentLog.instrument_id == instrument["id"]).order_by(InstrumentLog.time.desc()).first()
        if recent_log:
            instrument["status"] = status_code_to_text(recent_log.status)
            recent_log.contents = Markup(recent_log.contents)
        instrument["log"] = recent_log

    sorted_instruments = sorted(instruments, key=lambda x: x["name"])

    return render_template('new_log.html', instruments=sorted_instruments, status=status_text, error=error)
