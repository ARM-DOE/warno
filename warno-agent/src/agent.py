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

from Queue import Empty
from time import sleep
from os.path import splitext
from multiprocessing import Queue, Process

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
            module_name = plugin[:-3].replace('/','.')
            module_top = importlib.import_module(module_name)
            if hasattr(module_top, 'run') and hasattr(module_top, 'register'):
                plugin_module_list.append(module_top)
        except Exception, e:
            pass  #  Just ignore, there will be a lot of hits on this

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

    cfg = load_config()

    print(cfg)
    #  Loop through each plugin and register it
    for plugin in plugin_module_list:
        print(plugin.register())
        print(json.dumps(plugin.register()))


    #  Loop through plugins and start each up
    for plugin in plugin_module_list:
        p = Process(target = plugin.run, args=(msg_queue,))
        p.start()


    while 1:
        if not msg_queue.empty():
            msg = msg_queue.get_nowait()
            print(json.dumps(msg))
        else:
            sleep(0.1)



