import logging
import multiprocessing
from multiprocessing import Queue


class PluginManager(object):

    white_list = '*'

    def __init__(self, config ):
        self.plugin_list = []
        self.msg_queue = Queue()
        self.info = config
        self.site = config['site']
        self.instrument = config['instrument']
        self.event_code_dict = {}

    def add_plugin(self, plugin):
        self.plugin_list.append({'plugin_handle': plugin,
                                 'status': 'notstarted',
                                 'thread': None,
                                 'ctrl_queue': Queue(),
                                 'plugin_metadata': None,
                                 'event_codes': []})

    def get_plugin_handle_list(self):
        return [plugin['plugin_handle'] for plugin in self.plugin_list]

    def get_plugin_list(self):
        return self.plugin_list

    def start_plugin(self, plugin):
        ''' Starts a plugin.
        Returns
        -------
        p: thread_handle
            Running thread for the plugin.

        '''
        p = multiprocessing.Process(target=plugin['plugin_handle'].run, args=(
            self.msg_queue, self.info))

        p.start()
        plugin['thread'] = p
        plugin['status'] = 'started'

        return p

    def start_all_plugins(self):
        for plugin in self.plugin_list:
            self.start_plugin(plugin)

    def register_plugin_events(self, plugin):
        """
        Register a plugin.

        Parameters
        ----------
        plugin: module
            Plugin to be registered.

        Returns
        -------
        """

        logging.info("Registering Plugin", plugin)
        registration_info = plugin['plugin_handle'].get_registration_info()

        for event in registration_info['event_code_names']:
            plugin['event_codes'].append(event)

        plugin['plugin_name'] = registration_info['plugin_name']

        logging.debug("Event Codes List", plugin['event_codes'])