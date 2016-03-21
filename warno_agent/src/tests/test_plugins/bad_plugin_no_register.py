# This is a bad plugin, it is missing a register function.

from Agent.Plugin import Plugin


class BadPluginNoRegister(Plugin):

    def __init__(self):
        super(Plugin, self).__init__()

    def run(self, msg_queue, instrument_id):
        pass


def get_plugin():
    return BadPluginNoRegister()
