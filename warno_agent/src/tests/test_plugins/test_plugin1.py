import time
from datetime import datetime
import numpy as np
import json
from pyarmret.io.PAFClient import PAFClient


def register(msg_queue):
    event_names = ["event1", "event2"]
    instrument_name = "test-instrument"

    return {"instrument_name": instrument_name, "event_code_names": event_names}


def run(msg_queue, instrument_id):
    i = 1
    pass
