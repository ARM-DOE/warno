import json

from flask import g, render_template, request, redirect, url_for, request
from flask import Blueprint
from jinja2 import TemplateNotFound

from WarnoConfig.utility import status_code_to_text, is_number
from WarnoConfig.models import InstrumentLog, User, Instrument, Site
from WarnoConfig import database
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import aliased

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
        new_site = Site()
        new_site.name_short = request.form.get('abbv')
        new_site.name_long = request.form.get('name')
        new_site.latitude = request.form.get('lat')
        new_site.longitude = request.form.get('lon')
        new_site.facility = request.form.get('facility')
        new_site.location_name = request.form.get('location_name')

        mobile = request.form.get('mobile')
        # If the "mobile" box was checked in new_site, mobile is True. Else, false
        if mobile == "on":
            new_site.mobile = True
        else:
            new_site.mobile = False

        # Checks if latitude and longitude are valid values
        if is_number(new_site.latitude) and is_number(new_site.longitude):
            database.db_session.add(new_site)
            database.db_session.commit()
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

    db_sites = database.db_session.query(Site).all()
    sites = [dict(abbv=site.name_short, name=site.name_long, latitude=site.latitude, longitude=site.longitude,
                  facility=site.facility, mobile=site.mobile, location_name=site.location_name, id=site.id)
             for site in db_sites]

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
    db_site = database.db_session.query(Site).filter(Site.id == site_id).first()
    site = dict(abbv=db_site.name_short, name=db_site.name_long, latitude=db_site.latitude, longitude=db_site.longitude,
                  facility=db_site.facility, mobile=db_site.mobile, location_name=db_site.location_name, id=db_site.id)

    # Get the 5 most recent logs from all instruments at the site to display
    db_logs = database.db_session.query(InstrumentLog).join(InstrumentLog.instrument).join(Instrument.site).\
        filter(Instrument.site_id == site_id).order_by(desc(InstrumentLog.time)).limit(5).all()
    recent_logs = [dict(time=log.time, contents=log.contents, status=status_code_to_text(log.status),
                        supporting_images=log.supporting_images,
                        author=log.author.name, instrument=log.instrument.name_short)
                   for log in db_logs]

    # Get the most recent log for each instrument to determine its current status
    il_alias_1 = aliased(InstrumentLog, name='il_alias_1')
    il_alias_2 = aliased(InstrumentLog, name='il_alias_2')
    logs = database.db_session.query(il_alias_1).join(il_alias_1.instrument).join(il_alias_1.author).join(Instrument.site).\
        outerjoin(il_alias_2, and_(Instrument.id == il_alias_2.instrument_id,
                                 or_(il_alias_1.time < il_alias_2.time,
                                     and_(il_alias_1.time == il_alias_2.time, il_alias_1.instrument_id < il_alias_2.instrument_id)))).\
        filter(il_alias_2.id == None).filter(Instrument.site_id == site_id).all()
    status = {log.instrument.id: dict(last_author=log.author.name, status_code=log.status) for log in logs}

    # Assume the instrument status is operational unless the status has changed, handled afterward
    db_instruments = database.db_session.query(Instrument).filter(Instrument.site_id == site_id).all()
    instruments = [dict(abbv=instrument.name_short, name=instrument.name_long, type=instrument.type,
                        vendor=instrument.vendor, frequency_band=instrument.frequency_band,
                        description=instrument.description, status=1, last_author="", id=instrument.id)
                   for instrument in db_instruments]

    # For each instrument, if there is a corresponding status entry from the query above,
    # add the status and the last log's author.  If not, status will stay default operational
    for instrument in instruments:
        if instrument['id'] in status:
            instrument['status'] = status[instrument['id']]["status_code"]
            instrument['last_author'] = status[instrument['id']]["last_author"]
        instrument['status'] = status_code_to_text(instrument['status'])

    return render_template('show_site.html', site=site, instruments=instruments, recent_logs=recent_logs)




