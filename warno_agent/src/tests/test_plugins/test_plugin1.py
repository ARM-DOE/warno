import time
from datetime import datetime
import numpy as np
from pyarmret.io.PAFClient import PAFClient

from Agent.Plugin import Plugin


class TestPassingPlugin(Plugin):

    def __init__(self):
        super(Plugin, self).__init__()


    def register(self, msg_queue):
        event_names = ["event1", "event2"]
        instrument_name = "test-instrument"

        return {"instrument_name": instrument_name, "event_code_names": event_names}


    def run(self, msg_queue, instrument_id):
        i = 1
        pass


def get_plugin():
    return TestPassingPlugin()
