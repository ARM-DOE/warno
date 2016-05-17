import thread


class Plugin(object):
    """Plugin base object to be used to derive plugins from.
    """

    def __init__(self, path=None):
        self.path = path
        self.config_data = {}
        self.plugin_name = "base_plugin"
        self.plugin_description = "Base plugin class"
        self.event_code_names = []
        self.instrument_name = None
        self.run_flag = True
        self.ctrl_queue = None
        self.white_list = ['*',]

    def run(self, msg_queue, config, ctrl_queue):
        self.msg_queue = msg_queue
        self.ctrl_queue = ctrl_queue

    def get_registration_info(self):
        """  Returns registration information for plugin. This is a dictionary with the following entries:
        plugin_name
        plugin_description
        event_codes array with elements
            event_code_names,

        This does not need to be changed in inherited class.

        Returns
        -------
        registration_info: dict
            dict containing above entries at least.

        """

        return {'plugin_name': self.plugin_name,
                'plugin_description': self.plugin_description,
                'event_code_names': self.event_code_names,
                'path': self.path,
                'instrument_name': self.instrument_name}

    def add_event_code(self, event_code_name):
        """ Add an event code. Does not need to be changed in inherited class.
        """
        self.event_code_names.append(event_code_name)

    def initialize(self, config_data):
        self.config_data = config_data

    def process_ctrl_queue(self):
        if not self.ctrl_queue.empty():
            ctrl_msg = self.ctrl_queue.get_nowait()
            if ctrl_msg['command'] == 'shutdown':
                self.run_flag = False




