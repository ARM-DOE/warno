import time
import traceback
import json
import os
import datetime
import psutil
from time import sleep
import logging

from Plugin import Plugin as Plugin
from WarnoConfig import config

log_path = os.environ.get("LOG_PATH")
if log_path is None:
    log_path = "/vagrant/logs/"

LOGFILE = log_path + "agent_exceptions.log"

white_list = ['*',]


class SystemStatusPlugin(Plugin):
    """ Plugin to monitor basic system health on the agent system.
    """

    def __init__(self):
        super(SystemStatusPlugin, self).__init__()
        self.plugin_name = 'System Status Plugin'
        self.plugin_description = 'test'
        self.add_event_code("cpu_usage")
        self.white_list = white_list
        self.config_ctxt = config.get_config_context()
        self.config_id = None

    def run(self, msg_queue, config, ctrl_queue):
        self.ctrl_queue = ctrl_queue
        while self.run_flag:
            timestamp = datetime.datetime.utcnow()
            msg_queue.put('{"event": "%s", "data": {"instrument_id": %s, "time": "%s", "value": %s}}' %
            ("cpu_usage", config['instrument_id'], timestamp, psutil.cpu_percent()))
            self.process_ctrl_queue()
            sleep(self.config_ctxt['agent']['instrument_list'][self.config_id]['sampling_interval'])


def get_plugin():
    return SystemStatusPlugin()


