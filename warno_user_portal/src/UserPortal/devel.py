import logging
import json
import os

from flask import render_template, redirect, url_for, request
from flask import Blueprint
from sqlalchemy.sql import func
from sqlalchemy import asc

from WarnoConfig.utility import status_code_to_text
from WarnoConfig.models import db
from WarnoConfig.models import Instrument, ProsensingPAF, PulseCapture, InstrumentLog, Site
from WarnoConfig.models import InstrumentDataReference, EventCode, EventWithValue, ValidColumn

from .instruments import valid_columns_for_instrument, db_get_instrument_references, db_select_instrument

devel = Blueprint('devel', __name__, template_folder='templates')

log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

# Logs to the user portal log
up_logger = logging.getLogger(__name__)
up_handler = logging.FileHandler("%suser_portal_server.log" % log_path, mode="a")
up_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
up_logger.addHandler(up_handler)



@devel.route('/devel/histogram', methods=['GET' ])
def histogram_page():
    """If method is "GET", get for the instrument specified by the instrument id
        the instrument information, recent log entries, the status of the
        instrument and a list of which data columns are available to plot.
        If the method is "DELETE", instead deletes the instrument specified by the
        instrument id and any table entries that reference that instrument.

    Parameters
    ----------
    instrument_id: integer
        The database id of the instrument to be shown or deleted.

    Returns
    -------
    show_instrument.html: HTML document
        If called with a "GET" method, returns an HTML document with arguments including
        instrument information, the 5 most recent log entries, the status of the instrument,
        and the list of columns for available data to plot on graphs.
    """
    #We need to pass in a list of valid instruments:
    db_instruments = db.session.query(Instrument).order_by(asc(Instrument.id)).all()
    instrument_list = [dict(abbv=inst.name_short, name=inst.name_long, type=inst.type, vendor=inst.vendor,
                            description=inst.description, frequency_band=inst.frequency_band,
                            location=inst.site.name_short, site_id=inst.site_id, id=inst.id)
                       for inst in db_instruments]
    column_list = {}

    for instrument in instrument_list:
        db_valid_columns = db.session.query(ValidColumn).filter(ValidColumn.instrument_id == instrument['id']).all()
        column_list[instrument['id']] = [column.column_name for column in db_valid_columns]

    return render_template('show_histogram.html', instrument_list=instrument_list, column_list = json.dumps(column_list))


