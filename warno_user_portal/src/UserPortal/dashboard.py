import logging
import math
import json
import os

from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import asc, or_, and_
from sqlalchemy.orm import aliased

from WarnoConfig.utility import status_code_to_text
from WarnoConfig.models import Instrument, InstrumentLog, Site, ValidColumn, User, db

dashboard = Blueprint('dashboard', __name__, template_folder='templates')

log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

# Logs to the user portal log
up_logger = logging.getLogger(__name__)
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
up_logger.addHandler(up_handler)


@dashboard.route('/save_dashboard/<user_id>', methods=["POST"])
def save_dashboard(user_id):
    dashboard_string = json.dumps(request.json)
    user = User.query.filter_by(id=user_id).first()
    user.dashboard = dashboard_string
    db.session.commit()
    return dashboard_string


@dashboard.route('/load_dashboard/<user_id>', methods=["GET"])
def load_dashboard(user_id):
    user = User.query.filter_by(id=user_id).first()
    dashboard_string = user.dashboard
    return dashboard_string


@dashboard.route('/widget_controller')
def widget_controller():
    widget_name = request.args.get('widget_name')
    widget_id = request.args.get('widget_id')
    if widget_name == 'log_viewer':
        return widget_log_viewer_controller(widget_id)
    if widget_name == "status_plot":
        return widget_status_plot_controller(widget_id)
    if widget_name == "histogram":
        return widget_histogram_controller(widget_id)
    if widget_name == "instrument_graph":
        return widget_instrument_graph_controller(widget_id)
    return ""


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


@dashboard.route('/widget/log_viewer')
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


@dashboard.route('/widget/status_plot')
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


def widget_histogram_controller(widget_id):
    """
    This function has an unusual return, being both the rendered html and extra json data.  The response is designed to
    be pulled apart on the receiving end.  This allows the calling widget to build the histogram correctly.

    Parameters
    ----------
    widget_id: integer
        Allows for this widget to be dynamically created, tracked, and removed. Passed into the template and
        incorporated in element ids.

    Returns
    -------
    JSON dictionary of the form { "html": "*html for page generation*", "json": "*json for the widget to internalize*" }

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
    be pulled apart on the receiving end.  This allows the calling widget to build the instrument graph correctly.

    Parameters
    ----------
    widget_id: integer
        Allows for this widget to be dynamically created, tracked, and removed. Passed into the template and
        incorporated in element ids.

    Returns
    -------
    JSON dictionary of the form { "html": "*html for page generation*", "json": "*json for the widget to internalize*" }

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


# Helper Functions
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
