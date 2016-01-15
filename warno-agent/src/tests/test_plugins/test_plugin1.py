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
    pafc = PAFClient("ena-kazr", 3000)
    pafc.connect()
    si = pafc.get_server_info()
    i = 1
    while True:
        i = i + 1
        events = pafc.get_all_text_dict()
        events_payload = json.dumps(events)
        print ("Length: %s" % len(events_payload))
        timestamp = time.mktime(time.localtime())
        msg_queue.put('{"event": "non_paf_event", "data": {"Instrument_Id": %s, "Time": %s, "Value": "%s"}}' % (instrument_id, timestamp, i))
        # for key, value in events.iteritems():
        msg_queue.put('{"event": "%s", "data": {"Instrument_Id": %s, "Time": %s, "Value": %s}}' % ("prosensing_paf", instrument_id, timestamp, events_payload))
        if (i % 2) == 0:
            data = pafc.get_data(product_code=32)
            msg_queue.put('{"event": "pulse_capture", "data": {"Instrument_Id": %s, "Time": %s, "Value": %s}}' % (instrument_id, timestamp, data['data_contents'][0]))
        time.sleep(5)
