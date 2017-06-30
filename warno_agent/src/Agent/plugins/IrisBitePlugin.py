import datetime
import traceback
import time
import json
import os

from Plugin import Plugin as Plugin

from WarnoConfig import config
from WarnoConfig.bite_digest.digest import Digest


log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

LOGFILE = log_path + "agent_exceptions.log"

white_list = ['XSAPR-SW'] # We need to generalize this.


class IrisBitePlugin(Plugin):
    """ Plugin to monitor basic system health on the agent system.
    """

    def __init__(self):
        super(IrisBitePlugin, self).__init__()
        self.instrument_name = None
        self.plugin_name = 'Iris BITE Plugin'
        self.plugin_description = 'Monitors Iris BITE statuses on instruments'
        self.add_event_code("iris_bite")
        self.add_event_code("non_iris_event")
        self.white_list = white_list
        self.config_ctxt = config.get_config_context()
        self.config_id = None

    def run(self, msg_queue, config, ctrl_queue):

        self.ctrl_queue = ctrl_queue
        base_url = self.config_ctxt['agent']['instrument_list'][self.config_id]['base_url']
        base_port = self.config_ctxt['agent']['instrument_list'][self.config_id]['base_port']

        # Counter for the 'non_iris_event'
        i = 1

        while True:
            timestamp = self.get_timestamp()
            try:
                iris_digest = Digest()
                events = iris_digest.get_data(base_url, base_port)
                # Have to clean some of the BITE labels to allow them to be colummn names for postgresql
                clean_events = { key.replace('+', 'pos').replace('-', 'minus').replace('.', '_').replace('/', '_').replace(' ', '_'): value
                                 for key, value in events.iteritems()}
                events_payload = json.dumps(clean_events)
                msg_queue.put('{"event": "%s", "data": {"instrument_id": %s, "time": "%s", "values": %s}}'
                              % ("iris_bite", config['instrument_id'], timestamp, events_payload))
            except Exception, e:
                with open(LOGFILE, "a+") as log:
                    log.write("--%s\n%s\n" % (str(self.get_timestamp()), e))
                    traceback.print_exc(limit=5, file=log)
            finally:
                del iris_digest

            timestamp = self.get_timestamp()
            msg_queue.put('{"event": "non_iris_event", "data": {"instrument_id": %s, "time": "%s", "value": "%s"}}'\
                          % (config['instrument_id'], timestamp, i))

            i += 1
            self.process_ctrl_queue()

            time.sleep(self.config_ctxt['agent']['instrument_list'][self.config_id]['sampling_interval'])

    def get_timestamp(self):
        return datetime.datetime.utcnow()


def get_plugin():
    return IrisBitePlugin()
