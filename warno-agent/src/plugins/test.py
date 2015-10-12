import time
from datetime import datetime
import numpy as np
import pyarmret
from pyarmret.io.PAFClient import PAFClient


def register(msg_queue):

    pafc = PAFClient('ena-kazr', 3000)
    pafc.connect()
    event_code_names = pafc.get_text_status().keys()
    instrument_name = "KAZR-2"

    return {"instrument_name": instrument_name, "event_code_names": event_code_names}

i = 0
def run(msg_queue):
    print "Start Running"
    while True:
        pafc = PAFClient('ena-kazr', 3000)
        pafc.connect()
        events = pafc.get_text_status()
        timestamp = time.mktime(time.localtime())
        for key, value in events.iteritems():
            msg_queue.put('{"event": "%s", "data": {"Instrument_Id": 1, "Time": %s, "Value": %s}}' % (key, timestamp, value))
        time.sleep(10)
        # print "Enter Register"
        # pafc = PAFClient('ena-kazr', 3000)
        # pafc.connect()
        # timestamp = time.mktime(time.localtime())
        # if i < 4:
        #     print("Sending Value")
        #     msg_queue.put('{"Event_Code": 4, "Data": {"Instrument_Id": 1, "Time": %s, "Value": %s}}' % (timestamp, i))
        # if i >= 4:
        #     print("Sending Text")
        #     msg_queue.put('{"Event_Code": 5, "Data": {"Instrument_Id": 1, "Time": %s, "Value": "Alpha Operational"}}' % timestamp)
        #     time.sleep(1)

