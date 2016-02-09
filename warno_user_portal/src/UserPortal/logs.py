import json

from flask import g, render_template, request, redirect, url_for, request
from flask import Blueprint
from jinja2 import TemplateNotFound
import psycopg2

from WarnoConfig import config
from WarnoConfig.network import status_code_to_text, status_text

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
            return redirect(url_for('instruments.instrument', instrument_id=instrument_id))
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
