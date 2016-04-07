import time
import traceback
import json
import os
import datetime
from pyarmret.io.PAFClient import PAFClient

from ..Plugin import Plugin

logfile = "/vagrant/logs/agent_exceptions.log"


class PAFPlugin(Plugin):

    def __init__(self):
        super(Plugin, self).__init__()
        self.add_event_code("prosensing_paf")
        self.add_event_code("non_paf_event")
        self.add_event_code("pulse_capture")
        self.sampling_interval = 60

    def register(self, msg_queue):
        event_names = ["prosensing_paf", "non_paf_event", "pulse_capture"]
        self.instrument_name = "KAZR1"

        print("REGISTERING KAZR1")

        return {"instrument_name": self.instrument_name, "event_code_names": event_names}

    def get_timestamp(self):
        return datetime.datetime.utcnow()

    def run(self, msg_queue, instrument_id):
        pafc = PAFClient("ena-kazr", 3000)
        pafc.connect()
        si = pafc.get_server_info()
        i = 1
        while True:
            timestamp = self.get_timestamp()
            try:
                events = pafc.get_all_text_dict()
                events_payload = json.dumps(events)
                msg_queue.put('{"event": "%s", "data": {"Instrument_Id": %s, "Time": "%s", "Value": %s}}' %
                              ("prosensing_paf", instrument_id, timestamp, events_payload))
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

            timestamp = self.get_timestamp()
            msg_queue.put('{"event": "non_paf_event", "data": {"Instrument_Id": %s, "Time": "%s", "Value": "%s"}}' %
                          (self.instrument_id, timestamp, i))

            timestamp = self.get_timestamp()
            i += 1
            if (i % 2) == 0:
                try:
                    data = pafc.get_data(product_code=32)
                    msg_queue.put('{"event": "pulse_capture", "data": {"Instrument_Id": %s, "Time": "%s", "Value": %s}}' %
                                  (self.instrument_id, timestamp, data['data_contents'][0]))
                except Exception:
                    with open(logfile, "a+") as log:
                        log.write("\nException Traceback\n")
                        traceback.print_exc(limit=5, file=log)

            time.sleep(self.sampling_interval)


def get_plugin():
    return PAFPlugin()

def get_timestamp():
    return datetime.datetime.utcnow()

def run(msg_queue, instrument_id):
    pafc = PAFClient("ena-kazr", 3000)
    pafc.connect()
    i = 1
    while True:
        timestamp = get_timestamp()
        try:
            events = pafc.get_all_text_dict()
            events_payload = json.dumps(events)
            msg_queue.put('{"event": "%s", "data": {"instrument_id": %s, "time": "%s", "values": %s}}'\
                          % ("prosensing_paf", instrument_id, timestamp, events_payload))
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

        msg_queue.put('{"event": "non_paf_event", "data": {"instrument_id": %s, "time": "%s", "value": "%s"}}'\
                      % (instrument_id, timestamp, i))

        i = i + 1

        time.sleep(60)
