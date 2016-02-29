import json

from flask import g, render_template, request, redirect, url_for, request
from flask import Blueprint
from jinja2 import TemplateNotFound

from WarnoConfig.utility import status_code_to_text, is_number

sites = Blueprint('sites', __name__, template_folder='templates')



@sites.route('/sites/new', methods=['GET', 'POST'])
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

        # Checks if latitude and longitude are valid values
        if is_number(lat) and is_number(lon):
            cur = g.db.cursor()
            cur.execute('''INSERT INTO sites(name_short, name_long, latitude, longitude, facility, mobile, location_name)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                        (abbv, name, float(lat), float(lon), facility, mobile, location_name))
            cur.execute('COMMIT')

            # After insertion, redirect to the updated list of sites
            return redirect(url_for("sites.list_sites"))
        else:
            return redirect(url_for("sites.new_site", error="Latitude and Longitude must be numbers."))

    if request.method == 'GET':
        error = request.args.get('error')
        return render_template('new_site.html', error=error)


@sites.route('/sites')
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


@sites.route('/sites/<site_id>')
def show_site(site_id):
    """Show an individual ARM Site's information, instruments at the site, and recent logs
        for those instruments.

    Parameters
    ----------
    site_id: integer
        The database id of the site to be shown.

    Returns
    -------
    show_site.html: HTML document
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

    # Get the 5 most recent logs from all instruments at the site to display
    cur.execute('''SELECT l.time, l.contents, l.status, l.supporting_images, u.name, i.name_short
                    FROM instrument_logs l JOIN users u
                    ON l.author_id = u.user_id JOIN instruments i ON i.instrument_id = l.instrument_id
                    JOIN sites s ON i.site_id = s.site_id
                    WHERE s.site_id = %s
                    ORDER BY time DESC LIMIT 5''', (site_id,))
    recent_logs = [dict(time=row[0], contents=row[1], status=status_code_to_text(row[2]), supporting_images=row[3],
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




