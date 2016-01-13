import os
import json
import importlib
import glob
import multiprocessing
import signal
import sys
import requests
from WarnoConfig import config

from Queue import Empty
from time import sleep
from multiprocessing import Queue, Process

import utility

headers = {'Content-Type': 'application/json', 'Host': "warno-event-manager.local"}

DEFAULT_PLUGIN_PATH = 'plugins/'


class Agent(object):
    """ Class representing a radar agent to be run at each radar.

    Agent is the top level class for the WARNO Agent microservice. This class is responsible
    orchestrating the running of the different plugins, handling registration, and
    communicating data from each plugin up to the event manager.
    """
    def __init__(self):
        self.plugin_path = DEFAULT_PLUGIN_PATH

    def set_plugin_path(self, path=None):
        """
        Change the path to the plugins directory. If no path is passed, resets back to default.

        Parameters
        ----------
        path: str, optional
            String to new plugin directory.

        Returns
        -------
            Returns new plugin directory path.

        """

        if path is None:
            self.plugin_path = DEFAULT_PLUGIN_PATH
        else:
            self.plugin_path = path
        return self.plugin_path

    def get_plugin_path(self):
        """
        Get current plugin path.

        Returns
        -------
        path: str
            Current plugin path.

        """

        return self.plugin_path

    def list_plugins(self):
        """List the plugins in the plugins directory as modules.

        Return a list of module top levels that correspond to plugins. All plugins in the list
        are guaranteed to have a run and register method.

        Returns
        -------
        plugin_list: list
            list of modules representing plugins
        """

        plugin_path = self.get_plugin_path()

        plugin_module_list = []
        potential_plugin_list = glob.glob(plugin_path+'*.py')
        potential_plugin_list.sort()

        for plugin in potential_plugin_list:
            try:
                module_name = plugin[:-3].replace('/', '.')
                module_top = importlib.import_module(module_name)
                if hasattr(module_top, 'run') and hasattr(module_top, 'register'):
                    plugin_module_list.append(module_top)
            except Exception, e:
                print(e)
                pass  # Just ignore, there will be a lot of hits on this

        return plugin_module_list





if __name__ == "__main__":
    # while True:
    sleep(30)
    agent = Agent()
    signal.signal(signal.SIGINT, utility.signal_handler)
    plugin_module_list = agent.list_plugins()

    msg_queue = Queue()
    event_code_dict = {}
    cfg = config.get_config_context()
    em_url = cfg['setup']['em_url']

    # Get site_id
    msg = '{"Event_Code": 2, "Data": "%s"}' % cfg['setup']['site']
    payload = json.loads(msg)
    response = requests.post(em_url, json=payload, headers=headers)
    response_dict = dict(json.loads(response.content))
    site_id = response_dict['Site_Id']

    instrument_ids = []

    #  Loop through each plugin and register it, registering the plugin's event codes as well
    for plugin in plugin_module_list:
        response_dict = plugin.register(msg_queue)
        # Get the instrument Id for each
        instrument_name = response_dict['instrument_name']
        msg = '{"Event_Code": 3, "Data": "%s"}' % instrument_name
        payload = json.loads(msg)
        response = requests.post(em_url, json=payload, headers=headers)
        data = dict(json.loads(response.content))
        instrument_ids.append((plugin, data['Instrument_Id']))
        for event in response_dict['event_code_names']:
            msg = '{"Event_Code": 1, "Data": {"description": "%s", "instrument_id": %s}}' % (event, data['Instrument_Id'])
            payload = json.loads(msg)
            response = requests.post(em_url, json=payload, headers=headers)
            response_dict = dict(json.loads(response.content))
            event_code_dict[response_dict['Data']['description']] = response_dict['Event_Code']

    # Loop through plugins and start each up
    for plugin in plugin_module_list:
        plugin_instrument_id = [instrument_id for plugin_name, instrument_id in instrument_ids if plugin_name == plugin][0]
        p = Process(target=plugin.run, args=(msg_queue, plugin_instrument_id))
        p.start()

    while 1:
        if not msg_queue.empty():
            rec_msg = msg_queue.get_nowait()
            event = json.loads(rec_msg)
            event['data']['Site_Id'] = site_id
            event_code = event_code_dict[event['event']]
            event_msg = '{"Event_Code": %s, "Data": %s}' % (event_code, json.dumps(event['data']))
            payload = json.loads(event_msg)
            response = requests.post(em_url, json=payload, headers=headers)

        else:
            sleep(0.1)
