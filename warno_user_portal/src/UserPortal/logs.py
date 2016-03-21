import json

from flask import g, render_template, request, redirect, url_for, request
from flask import Blueprint
from jinja2 import TemplateNotFound
import psycopg2
import sqlalchemy
import requests

from WarnoConfig import config
from WarnoConfig.utility import status_code_to_text, status_text
from WarnoConfig import database
from WarnoConfig.models import InstrumentLog, User, Instrument

logs = Blueprint('logs', __name__, template_folder='templates')

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
    author_id: optional, integer
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

    # Default error message will not show on template when its the empty string
    error = ""

    new_log = InstrumentLog()
    new_log.author_id = request.args.get('user-id')
    new_log.instrument_id = request.args.get('instrument')
    new_log.time = request.args.get('time')
    new_log.status = request.args.get('status')
    new_log.contents = request.args.get('contents')

    cfg = config.get_config_context()

    # If there is valid data entered with the get request, insert and redirect to the instrument
    # that the log was placed for
    if new_log.author_id and new_log.instrument_id and new_log.status and new_log.time:
        # Attempt to insert an item into the database. Try/Except is necessary because
        # the timedate datatype the database expects has to be formatted correctly.
        try:

            database.db_session.add(new_log)
            database.db_session.commit()

            # If it is not a central facility, pass the log to the central facility
            if not cfg['type']['central_facility']:
                packet = dict(Event_Code=5, Data = dict(instrument_id=instrument_id, author_id = user_id, time = time,
                                                status = status, contents = contents, supporting_images = None))
                payload = json.dumps(packet)
                requests.post(cfg['setup']['cf_url'], data = payload,
                                      headers = {'Content-Type': 'application/json'})

            # Redirect to the instrument page that the log was submitted for.
            return redirect(url_for('instruments.instrument', instrument_id=new_log.instrument_id))
        except sqlalchemy.exc.DataError:
            # If the timedate object expected by the database was incorrectly formatted, error is set
            # for when the page is rendered again
            error = "Invalid Date/Time Format"

    # If there was no valid insert, render form normally

    # Format the instrument names to be more descriptive
    db_instruments = database.db_session.query(Instrument).all()
    instruments = [dict(id=instrument.id, name=instrument.site.name_short + ":" + instrument.name_short)
                   for instrument in db_instruments]

    # Get a list of users so the user can choose who submitted the log.
    db_users = database.db_session.query(User).all()
    users = [dict(id=user.id, name=user.name) for user in db_users]

    return render_template('new_log.html', users=users, instruments=instruments, status=status_text, error=error)
