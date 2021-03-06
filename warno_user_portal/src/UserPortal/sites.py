import logging
import os

from flask import render_template, redirect, url_for, request, abort
from flask import Blueprint, Markup
from flask_user import current_user
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import aliased

from WarnoConfig.utility import status_code_to_text, is_number
from WarnoConfig.models import InstrumentLog, User, Instrument, Site
from WarnoConfig.models import db

sites = Blueprint('sites', __name__, template_folder='templates')

log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

# Logs to the user portal log
up_logger = logging.getLogger(__name__)
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
up_logger.addHandler(up_handler)


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
    if current_user.is_anonymous or current_user.authorizations != "engineer":
        abort(403)

    # If the method is post, the user has submitted the information in the form.
    # Try to insert the new site into the database, if the values are incorrect redirect
    # with an appropriate error message
    if request.method == 'POST':
        # Get the parameters from the url request
        # Field lengths limited in the views
        new_db_site = Site()
        new_db_site.name_short = request.form.get('abbv')
        new_db_site.name_long = request.form.get('name')
        new_db_site.latitude = request.form.get('lat')
        new_db_site.longitude = request.form.get('lon')
        new_db_site.facility = request.form.get('facility')
        new_db_site.location_name = request.form.get('location_name')

        mobile = request.form.get('mobile')
        # If the "mobile" box was checked in new_db_site, mobile is True. Else, false
        if mobile == "on":
            new_db_site.mobile = True
        else:
            new_db_site.mobile = False

        errors = []
        # Validate values
        if not (is_number(new_db_site.latitude)
                and (float(new_db_site.latitude) >= -90.0)
                and (float(new_db_site.latitude) <= 90.0)):
            errors.append("Latitude must be a number between -90.0 and 90.0")
        if not (is_number(new_db_site.longitude)
                and (float(new_db_site.longitude) >= -180.0)
                and (float(new_db_site.longitude) <= 180.0)):
            errors.append("Longitude must be a number between -180.0 and 180.0")

        if len(errors) > 0:
            error_message = "<br>".join(errors)
            return redirect(url_for("sites.new_site", error=error_message))
        else:
            db.session.add(new_db_site)
            db.session.commit()
            # After insertion, redirect to the updated list of sites
            return redirect(url_for("sites.list_sites"))

    if request.method == 'GET':
        error = request.args.get('error')
        if error:
            errors = error.split("<br>")
        else:
            errors = []
        return render_template('new_site.html', errors=errors)


@sites.route('/sites/<site_id>/edit', methods=['GET', 'POST'])
def edit_site(site_id):
    """Update WARNO site.

    Parameters
    ----------
    site_id: integer
        Database id of the site entry to be updated.

    Returns
    -------
    new_site.html: HTML document
        If the request method is 'GET', returns a form to update site .

    list_sites: Flask redirect location
        If the request method is 'POST', returns a Flask redirect location to the
            list_sites function, redirecting the site to the list of sites.
    """
    if current_user.is_anonymous or current_user.authorizations != "engineer":
        abort(403)

    # If the form information has been received, update the site in the database
    if request.method == 'POST':
        # Get the site information from the request
        updated_site = db.session.query(Site).filter(Site.id == site_id).first()
        updated_site.name_short = request.form.get('abbv')
        updated_site.name_long = request.form.get('name')
        updated_site.latitude = request.form.get('lat')
        updated_site.longitude = request.form.get('lon')
        updated_site.facility = request.form.get('facility')
        updated_site.location_name = request.form.get('location_name')

        mobile = request.form.get('mobile')
        # If the "mobile" box was checked in new_site, mobile is True. Else, false
        if mobile == "on":
            updated_site.mobile = True
        else:
            updated_site.mobile = False

        errors = []
        # Validate values
        if not (is_number(updated_site.latitude)
                and (float(updated_site.latitude) >= -90.0)
                and (float(updated_site.latitude) <= 90.0)):
            errors.append("Latitude must be a number between -90.0 and 90.0")
        if not (is_number(updated_site.longitude)
                and (float(updated_site.longitude) >= -180.0)
                and (float(updated_site.longitude) <= 180.0)):
            errors.append("Longitude must be a number between -180.0 and 180.0")

        if len(errors) > 0:
            error_message = "<br>".join(errors)
            return redirect(url_for("sites.edit_site", site_id=site_id, error=error_message))
        else:
            db.session.commit()
            # After update, redirect to the updated list of sites
            return redirect(url_for("sites.list_sites"))

    # If the request is to get the form, get the site and pass it to fill default values.
    if request.method == 'GET':
        error = request.args.get('error')
        if error:
            errors = error.split("<br>")
        else:
            errors = []
        db_site = db.session.query(Site).filter(Site.id == site_id).first()
        site = dict(name_short=db_site.name_short, name_long=db_site.name_long, latitude=db_site.latitude,
                    longitude=db_site.longitude, facility=db_site.facility, location_name=db_site.location_name,
                    mobile=db_site.mobile)

        return render_template('edit_site.html', site=site, errors=errors)


@sites.route('/sites')
def list_sites():
    """List  ARM Sites.

    Returns
    -------
    site_list.html: HTML document
        Returns an HTML document with an argument for a list of sites and their information.
    """

    db_sites = db.session.query(Site).all()
    sites_dict = [dict(abbv=site.name_short, name=site.name_long, latitude=site.latitude, longitude=site.longitude,
                  facility=site.facility, mobile=site.mobile, location_name=site.location_name, id=site.id)
                  for site in db_sites]

    return render_template('site_list.html', sites=sites_dict)


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
    db_site = db.session.query(Site).filter(Site.id == site_id).first()
    site = dict(abbv=db_site.name_short, name=db_site.name_long, latitude=db_site.latitude, longitude=db_site.longitude,
                facility=db_site.facility, mobile=db_site.mobile, location_name=db_site.location_name, id=db_site.id)

    # Get the 5 most recent logs from all instruments at the site to display
    db_logs = db.session.query(InstrumentLog).join(InstrumentLog.instrument).join(Instrument.site).\
        filter(Instrument.site_id == site_id).order_by(desc(InstrumentLog.time)).limit(5).all()
    recent_logs = [dict(time=log.time, contents=Markup(log.contents), status=status_code_to_text(log.status),
                        supporting_images=log.supporting_images,
                        author=log.author.name, instrument=log.instrument.name_short)
                   for log in db_logs]

    # Get the most recent log for each instrument to determine its current status
    il_alias_1 = aliased(InstrumentLog, name='il_alias_1')
    il_alias_2 = aliased(InstrumentLog, name='il_alias_2')
    logs = db.session.query(il_alias_1).join(il_alias_1.instrument).join(il_alias_1.author).join(Instrument.site).\
        outerjoin(il_alias_2, and_(Instrument.id == il_alias_2.instrument_id,
                                   or_(il_alias_1.time < il_alias_2.time,
                                       and_(il_alias_1.time == il_alias_2.time,
                                            il_alias_1.instrument_id < il_alias_2.instrument_id)))).\
        filter(il_alias_2.id == None).filter(Instrument.site_id == site_id).all()
    status = {log.instrument.id: dict(last_author=log.author.name, status_code=log.status) for log in logs}

    # Assume the instrument status is operational unless the status has changed, handled afterward
    db_instruments = db.session.query(Instrument).filter(Instrument.site_id == site_id).all()
    instruments = [dict(abbv=instrument.name_short, name=instrument.name_long, type=instrument.type,
                        vendor=instrument.vendor, description=instrument.description, status=1,
                        last_author="", id=instrument.id, latitude=instrument.latitude, longitude=instrument.longitude,
                        effective_radius=instrument.effective_radius)
                   for instrument in db_instruments]

    # For each instrument, if there is a corresponding status entry from the query above,
    # add the status and the last log's author.  If not, status will stay default operational
    for instrument in instruments:
        if instrument['id'] in status:
            instrument['status'] = status[instrument['id']]["status_code"]
            instrument['last_author'] = status[instrument['id']]["last_author"]
        instrument['status'] = status_code_to_text(instrument['status'])

    return render_template('show_site.html', site=site, instruments=instruments, recent_logs=recent_logs)
