import numpy as np
import flask
import yaml
import json
import importlib
import glob
import os
import multiprocessing
import signal
import sys
import base64
import requests

from Queue import Empty
from time import sleep
from os.path import splitext
from multiprocessing import Queue, Process

# Eventually should be set by a check to config.yml
em_url = "http://localhost:5000/event"


def list_plugins():
    """List the plugins in the plugins directory as modules.

    Return a list of module top levels that correspond to plugins. All plugins in the list
    are guaranteed to have a run and register method.

    Returns:
    ---------
    plugin_list: list
        list of modules representing plugins
    """
    plugin_path = 'plugins/'

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
            pass  # Just ignore, there will be a lot of hits on this

    return plugin_module_list


def signal_handler(signal, frame):
    """ Set up Ctrl-C Handling

    This function sets up signal interrupt catching, primarily to handle Ctrl-C.

    Parameters
    ----------
    signal: signal
        Signal to catch
    frame: frame
        frame
    """

    print("Exiting due to SIGINT")
    sys.exit(0)


def load_config():
    """Load the configuration Object from the config file

    Loads a configuration Object from the config file.

    Returns
    -------
    config: dict
        Configuration Dictionary of Key Value Pairs
    """
    with open("config.yml", 'r') as ymlfile:
        config = yaml.load(ymlfile)
    return config

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    plugin_module_list = list_plugins()

    msg_queue = Queue()
    event_code_dict = {}
    cfg = load_config()

    # Get site_id
    msg = '{"Event_Code": 2, "Data": "%s"}' % cfg['setup']['site']
    payload = json.loads(msg)
    response = requests.post(em_url, json=payload, headers={'Content-Type': 'application/json'})
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
        response = requests.post(em_url, json=payload, headers={'Content-Type': 'application/json'})
        data = dict(json.loads(response.content))
        instrument_ids.append((plugin, data['Instrument_Id']))
        for event in response_dict['event_code_names']:
            msg = '{"Event_Code": 1, "Data": "%s"}' % event
            payload = json.loads(msg)
            response = requests.post(em_url, json=payload, headers={'Content-Type': 'application/json'})
            response_dict = dict(json.loads(response.content))
            event_code_dict[response_dict['Data']] = response_dict['Event_Code']


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
            requests.post(em_url, json=payload, headers={'Content-Type': 'application/json'})

        else:
            sleep(0.1)

