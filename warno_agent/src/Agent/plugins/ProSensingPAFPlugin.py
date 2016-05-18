import time
import traceback
import json
import os
import datetime
from pyarmret.io.PAFClient import PAFClient
from Plugin import Plugin as Plugin

from WarnoConfig import config

logfile = "/vagrant/logs/agent_exceptions.log"




white_list = ['KAZR-OLI','SACR', 'KAZR', 'WSACR', 'KASACR', 'KASACRO','WSACRO'] # We need to generalize this.


class ProSensingPAFPlugin(Plugin):
    """ Plugin to monitor basic system health on the agent system.
    """

    def __init__(self):
        super(ProSensingPAFPlugin, self).__init__()
        self.instrument_name = None
        self.plugin_name = 'ProSensing PAF Plugin'
        self.plugin_description = 'Monitors Prosensing Instruments via PAF'
        self.add_event_code("prosensing_paf")
        self.add_event_code("non_paf_event")
        self.white_list = white_list
        self.config_ctxt = config.get_config_context()
        self.config_id = None

    def run(self, msg_queue, config, ctrl_queue):
        self.ctrl_queue= ctrl_queue
        base_url = self.config_ctxt['agent']['instrument_list'][self.config_id]['base_url']
        base_port = self.config_ctxt['agent']['instrument_list'][self.config_id]['base_port']
        fmt = self.config_ctxt['agent']['instrument_list'][self.config_id]['pstype']
        pafc = PAFClient(base_url, base_port, fmt=fmt)
        pafc.connect()
        i = 1
        while True:
            timestamp = self.get_timestamp()
            try:
                events = pafc.get_all_text_dict()
                events_payload = json.dumps(events)
                msg_queue.put('{"event": "%s", "data": {"instrument_id": %s, "time": "%s", "values": %s}}'\
                              % ("prosensing_paf", config['instrument_id'], timestamp, events_payload))
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
            msg_queue.put('{"event": "non_paf_event", "data": {"instrument_id": %s, "time": "%s", "value": "%s"}}'\
                          % (config['instrument_id'], timestamp, i))

            i = i + 1
            self.process_ctrl_queue()

            time.sleep(self.config_ctxt['agent']['instrument_list'][self.config_id]['sampling_interval'])

    def get_timestamp(self):
        return datetime.datetime.utcnow()


def get_plugin():
    return ProSensingPAFPlugin()