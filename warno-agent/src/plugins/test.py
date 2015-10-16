import time
from datetime import datetime
import numpy as np
import json
from pyarmret.io.PAFClient import PAFClient


def register(msg_queue):
    event_names = ["prosensing_paf"]
    instrument_name = "KAZR-2"

    print "REGISTERING KAZR-2"

    return {"instrument_name": instrument_name, "event_code_names": event_names}


def run(msg_queue, instrument_id):
    pafc = PAFClient("192.148.95.5", 3000)
    pafc.connect()
    pafc.get_server_info()
    while True:
        i = 1
        i = i + 1
        events = pafc.get_text_status()
        events_payload = json.dumps(events)
        timestamp = time.mktime(time.localtime())
        # for key, value in events.iteritems():
        msg_queue.put('{"event": "%s", "data": {"Instrument_Id": %s, "Time": %s, "Value": %s}}' % ("prosensing_paf", instrument_id, timestamp, events_payload))
        time.sleep(5)
