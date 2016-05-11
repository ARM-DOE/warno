import time
import traceback
import json
import os
import datetime
import psutil
from time import sleep
import logging

from Plugin import Plugin as Plugin

logfile = "/vagrant/data_store/data/agent_exceptions.log"


class SystemStatusPlugin(Plugin):
    ''' Plugin to monitor basic system health on the agent system.
    '''

    def __init__(self):
        super(SystemStatusPlugin, self).__init__()
        self.instrument_name = 'TEST'
        self.plugin_name = 'System Status Plugin'
        self.plugin_description = 'test'
        self.add_event_code("cpu_usage")
        # self.instrument_id = 1

    def get_registration_info(self):
        return {"event_code_names": self.event_code_names,
                "plugin_name": self.plugin_name}

    def run(self, msg_queue, config):
        for x in range(10):
            timestamp = datetime.datetime.utcnow()
            msg_queue.put('{"event": "%s", "data": {"instrument_id": %s, "time": "%s", "value": %s}}' %
            ("cpu_usage", config['instrument_id'], timestamp, psutil.cpu_percent()))
            logging.info("Log Made", psutil.cpu_percent())
            sleep(2)


def get_plugin():
    return SystemStatusPlugin()


