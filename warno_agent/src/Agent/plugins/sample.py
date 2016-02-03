import time
import traceback
import json
import os
from pyarmret.io.PAFClient import PAFClient


logfile = "/vagrant/data_store/data/agent_exceptions.log"

def register(msg_queue):
    event_names = ["prosensing_paf", "non_paf_event", "pulse_capture"]
    instrument_name = "KAZR1"

    print("REGISTERING KAZR1")

    return {"instrument_name": instrument_name, "event_code_names": event_names}

def get_timestamp():
    return time.mktime(time.localtime())

def run(msg_queue, instrument_id):
    pafc = PAFClient("ena-kazr", 3000)
    pafc.connect()
    si = pafc.get_server_info()
    i = 1
    while True:
        timestamp = get_timestamp()

        try:
            events = pafc.get_all_text_dict()
            events_payload = json.dumps(events)
            msg_queue.put('{"event": "%s", "data": {"Instrument_Id": %s, "Time": %s, "Value": %s}}' % ("prosensing_paf", instrument_id, timestamp, events_payload))
        except UnicodeDecodeError, e:
            with open(logfile, "a+") as log:
                log.write("\nUnicodeDecodeError\n")
                log.write(str(e))
                log.write("\nUndecoded Message\n")
                log.write(str(events))
                log.write("\nException Traceback\n")
                traceback.print_exc(limit=5, file=log)
        except Exception:
            with open(logfile, "a+") as log:
                log.write("\nException Traceback\n")
                traceback.print_exc(limit=5, file=log)

        timestamp = get_timestamp()
        msg_queue.put('{"event": "non_paf_event", "data": {"Instrument_Id": %s, "Time": %s, "Value": "%s"}}' % (instrument_id, timestamp, i))

        timestamp = get_timestamp()
        i = i + 1
        if (i % 2) == 0:
            try:
                data = pafc.get_data(product_code=32)
                msg_queue.put('{"event": "pulse_capture", "data": {"Instrument_Id": %s, "Time": %s, "Value": %s}}' % (instrument_id, timestamp, data['data_contents'][0]))
            except Exception:
                with open(logfile, "a+") as log:
                    log.write("\nException Traceback\n")
                    traceback.print_exc(limit=5, file=log)

        time.sleep(60)
