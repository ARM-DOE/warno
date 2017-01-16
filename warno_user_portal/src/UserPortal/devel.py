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


@devel.route('/devel', methods=['GET'])
def devel_front():
    return render_template('devel_front.html')
    pass