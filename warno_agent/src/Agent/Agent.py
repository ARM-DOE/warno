import json
import importlib
import glob
import multiprocessing
import signal
import requests
from WarnoConfig import config
from WarnoConfig import network
from time import sleep
from multiprocessing import Queue

import utility

headers = {'Content-Type': 'application/json'}

DEFAULT_PLUGIN_PATH = 'Agent/plugins/'


class Agent(object):
    """ Class representing a radar agent to be run at each radar.

    Agent is the top level class for the WARNO Agent microservice. This class is responsible
    orchestrating the running of the different plugins, handling registration, and
    communicating data from each plugin up to the event manager.
    """
    def __init__(self):
        self.plugin_path = DEFAULT_PLUGIN_PATH
        self.config_ctxt = config.get_config_context()
        self.event_manager_url = self.config_ctxt['setup']['em_url']
        self.em_url = self.config_ctxt['setup']['em_url']
        self.site_id = None
        self.msg_queue = Queue()
        self.event_code_dict = {}
        self.instrument_ids = []
        self.running_plugin_list = []
        self.plugin_module_list = []
        self.main_loop_boolean = True

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
                module_name = module_name.replace('Agent.','')
                module_top = importlib.import_module(module_name[0:])
                if hasattr(module_top, 'run') and hasattr(module_top, 'register'):
                    plugin_module_list.append(module_top)
            except Exception, e:
                print(e)
                pass  # Just ignore, there will be a lot of hits on this

        return plugin_module_list

    def request_site_id_from_event_manager(self):
        """Request site id from manager.

        Contact Event manager and request the site id number. This works by passing the site name
        in the configuration file to the event manager and asking for allocation of a site id.

        Returns
        -------
        site_id: int
            Site identification number.

        """
        response = self.send_em_message(network.SITE_ID_REQUEST, self.config_ctxt['setup']['site'])

        if response.status_code == requests.codes.ok:
            response_dict = dict(json.loads(response.content))
            site_id = response_dict['Site_Id']
            self.site_id = site_id
        else:
            response.raise_for_status()

        return self.site_id

    def register_plugin(self, plugin):
        """
        Register a plugin.

        Parameters
        ----------
        plugin: module
            Plugin to be registered.

        Returns
        -------

        """
        response_dict = plugin.register(self.msg_queue)

        # Get the instrument Id for each
        instrument_name = response_dict['instrument_name']
        response = self.send_em_message(network.INSTRUMENT_ID_REQUEST, instrument_name)

        data = dict(json.loads(response.content))
        self.instrument_ids.append((plugin, data['Instrument_Id']))

        for event in response_dict['event_code_names']:
            data_send = {'description': event, 'instrument_id': data['Instrument_Id']}
            response = self.send_em_message(network.EVENT_CODE_REQUEST, data_send )

            response_dict = dict(json.loads(response.content))
            self.event_code_dict[response_dict['Data']['description']] = response_dict['Event_Code']

    def startup_plugin(self, plugin):
        """
        Start up the listed plugin in a new thread and add it to the list of running plugins.

        Parameters
        ----------
        plugin: module
            Plugin to start

        Returns
        -------
        p: Process
            Running process.

        """
        plugin_instrument_id = [instrument_id for plugin_name, instrument_id in self.instrument_ids if plugin_name == plugin][0]
        p = multiprocessing.Process(target=plugin.run, args=(self.msg_queue, plugin_instrument_id))

        p.start()

        self.running_plugin_list.append(p)
        return p

    def send_em_message(self, code, data):
        """ Send event code message to event manager.

        Parameters
        ----------
        code: integer
            event manager code
        data: dict
            List of payloads for the Data dictionary.

        Returns
        -------
        response: `requests.response`
            Response from request.
        """

        msg = '{"Event_Code": %d, "Data": %s}' % (code, json.dumps(data))
        payload = json.loads(msg)
        response = requests.post(self.event_manager_url, json=payload, headers=headers)
        return response

    def main(self):
        """ Start radar agent.

        Returns
        -------
        """
        print("Starting Agent Main Loop:")
	sleep(30)

        self.plugin_module_list = self.list_plugins()
        print("Starting up the following plugins:", self.plugin_module_list)

        conn_attempt = 0
        while conn_attempt < 5:
            try:
                conn_attempt +=1
                self.site_id = self.request_site_id_from_event_manager()
                continue
            except Exception as e:
                print("Error Connecting. Connection Attempt {0}. Sleeping for 5 seconds.".format(conn_attempt))
                print(e)
                sleep(5)



        print("Registering Plugins.")
        for plugin in self.plugin_module_list:
            self.register_plugin(plugin)

        print("Starting up Plugins.")
        for plugin in self.plugin_module_list:
            self.startup_plugin(plugin)


        while self.main_loop_boolean:
            if not self.msg_queue.empty():
                rec_msg = self.msg_queue.get_nowait()
                event = json.loads(rec_msg)
                event['data']['Site_Id'] = self.site_id
                event_code = self.event_code_dict[event['event']]
                event_msg = '{"Event_Code": %s, "Data": %s}' % (event_code, json.dumps(event['data']))
                payload = json.loads(event_msg)
                response = requests.post(self.em_url, json=payload, headers=headers)
            else:
                sleep(0.1)


if __name__ == "__main__":
    agent = Agent()
    signal.signal(signal.SIGINT, utility.signal_handler)
    agent.main()


