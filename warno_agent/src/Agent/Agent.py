import glob
import importlib
import json
import logging
import signal
import sys
import threading
import wsgiref.simple_server
from multiprocessing import Queue
from time import sleep
import psutil
import os

import requests
from WarnoConfig import config, utility
from flask import Flask, render_template, redirect, url_for, request

from PluginManager import PluginManager

global agent
global remote_server

headers = {'Content-Type': 'application/json'}

DEFAULT_PLUGIN_PATH = 'Agent/plugins/'
MAX_CONN_ATTEMPTS = 20
CONN_RETRY_TIME = 10
AGENT_DASHBOARD_PORT = 6309

ctx = config.get_config_context()
if ctx['agent']['local_debug']:
    AGENT_DASHBOARD_PORT = int(ctx['agent']['dev_port'])

app = Flask(__name__)

logfile = "/vagrant/data_store/data/agent_exceptions.log"


@app.route('/agent')
def serve_dashboard():
    """ Anchor point to serve the agent dashboard.
    Returns
    -------
    template: index.html
        Main dashboard page for agent.

    """
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    threads = len(psutil.pids())
    disk_usage = psutil.disk_usage('/').percent

    sys_stats = {"cpu": cpu, "mem": mem, "threads": threads/10.0, "disk_usage": disk_usage}
    print(sys_stats)

    instrument_list = []
    for manager in agent.plugin_managers:
        instrument_list.append({'instrument': manager.instrument['name'],
                            'plugin_list': manager.get_plugin_list()})

    return render_template('index.html',
                           instrument_list=instrument_list,
                           sys_stats=sys_stats)


@app.route('/agent/<instrument>/<plugin_name>/stop')
def serve_stop_plugin(instrument, plugin_name):
    """ Anchor point to stop a plugin by name.
    Parameters
    ----------
    plugin_name: str
        Name of plugin to stop

    Returns
    -------
    url_for(serve_dashboard): url
        Redirect to the dashboard front page.

    """
    for manager in agent.plugin_managers:
        if manager.instrument['name'] == instrument:
            manager.stop_plugin_by_name(plugin_name)
    return redirect(url_for("serve_dashboard"))


@app.route('/agent/<instrument>/<plugin_name>/start')
def serve_start_plugin(instrument, plugin_name):
    """ Anchor point to start a plugin by name.
    Parameters
    ----------
    plugin_name: str
        Name of plugin to start

    Returns
    -------
    url_for(serve_dashboard): url
        Redirect to the dashboard front page.

    """
    for manager in agent.plugin_managers:
        if manager.instrument['name'] == instrument:
            manager.start_plugin_by_name(plugin_name)
    return redirect(url_for("serve_dashboard"))


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
        self.is_central = self.config_ctxt['type']['central_facility']
        self.site_id = None
        self.msg_queue = Queue()
        self.event_code_dict = {}
        self.instrument_ids = []
        self.continue_processing_events = True
        self.cert_verify = self.config_ctxt['setup']['cert_verify']
        self.info = {'site': self.config_ctxt['setup']['site']}
        self.plugin_managers = [PluginManager({
                                    'site': self.config_ctxt['setup']['site'],
                                    'config_id': instrument_name
                                    }, instrument)
                                for instrument_name, instrument
                                in self.config_ctxt['agent']['instrument_list'].iteritems()]

        #Set up logging
        log_path = os.environ.get("LOG_PATH")
        if log_path is None:
            log_path = "/vagrant/logs/"

        # Logs to the main log
        logging.basicConfig( format='%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s',
                             filename='%scombined.log' % log_path,
                             filemode='a', level=logging.DEBUG)

        # Logs to the agent log
        self.agent_logger = logging.getLogger(__name__)
        agent_handler = logging.FileHandler("%sagent_server.log" % log_path, mode="a")
        agent_handler.setFormatter(logging.Formatter('%(levelname)s:%(asctime)s:%(module)s:%(lineno)d:  %(message)s'))
        self.agent_logger.addHandler(agent_handler)
        # Add agent handler to the main werkzeug logger
        logging.getLogger("werkzeug").addHandler(agent_handler)

        self.agent_logger.info(self.info)

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

    def enumerate_plugins(self, plugin_manager):
        """List the plugins in the plugins directory as modules.

        Return a list of module top levels that correspond to plugins. All plugins in the list
        are guaranteed to have a run and register method.

        Returns
        -------
        plugin_list: list
            list of modules representing plugins
        """

        plugin_path = self.get_plugin_path()

        potential_plugin_list = glob.glob(plugin_path + '*.py')
        potential_plugin_list.sort()
        logging.info(potential_plugin_list)

        for plugin in potential_plugin_list:
            try:
                module_name = plugin[:-3].replace('/', '.')
                module_name = module_name.replace('Agent.', '')
                module_top = importlib.import_module(module_name[0:])
                if hasattr(module_top, 'get_plugin'):
                    candidate_plugin = module_top.get_plugin()
                    self.agent_logger.debug("candidate_plugin %s", candidate_plugin)
                    candidate_plugin.path = plugin
                    if hasattr(candidate_plugin, 'get_registration_info') and hasattr(candidate_plugin, 'run'):
                        plugin_manager.add_plugin(candidate_plugin)
            except Exception, e:
                logging.warning(e)

        return plugin_manager.get_plugin_handle_list()

    def request_site_id_from_event_manager(self):
        """Request site id from manager.

        Contact Event manager and request the site id number. This works by passing the site name
        in the configuration file to the event manager and asking for allocation of a site id.

        Returns
        -------
        site_id: int
            Site identification number.

        """
        response = self.send_em_message(
            utility.SITE_ID_REQUEST, self.config_ctxt['setup']['site'])

        if response.status_code == requests.codes.ok:
            response_dict = dict(json.loads(response.content))
            site_id = response_dict['data']['site_id']
            self.site_id = site_id
        else:
            response.raise_for_status()

        return self.site_id

    def register_plugin(self, plugin, plugin_manager):
        """
        Register a plugin.

        Parameters
        ----------
        plugin: module
            Plugin to be registered.
        plugin_manager: PluginManager
            Plugin manager for this plugin.

        Returns
        -------

        """
        self.agent_logger.info("Registering Plugin %s", plugin['plugin_handle'])
        plugin_manager.register_plugin_events(plugin)

        for event in plugin['event_codes']:
            data_send = {'description': event,
                         'instrument_id': plugin_manager.info['instrument_id']}

            response = self.send_em_message(
                utility.EVENT_CODE_REQUEST, data_send)

            response_dict = dict(json.loads(response.content))
            plugin_manager.event_code_dict[response_dict['data'][
                'description']] = response_dict['event_code']

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

        msg = '{"event_code": %d, "data": %s}' % (code, json.dumps(data))
        payload = json.loads(msg)
        response = requests.post(self.event_manager_url, json=payload, headers=headers, verify=self.cert_verify)
        return response

    def process_plugin_event(self, manager):
        """ Process message from a plugin.

        Parameters
        ----------

        Returns
        -------
        response: requests.response
            Response from Event Manager

        """

        rec_msg = manager.msg_queue.get_nowait()
        event = json.loads(rec_msg)
        event['data']['site_id'] = self.site_id
        event_code = manager.event_code_dict[event['event']]
        event_msg = '{"event_code": %s, "data": %s}' % (
            event_code, json.dumps(event['data']))
        payload = json.loads(event_msg)
        response = requests.post(
            self.event_manager_url, json=payload, headers=headers, verify=self.cert_verify)
        return response

    def main(self):
        """ Start radar agent.

        Returns
        -------
        """

        if not self.config_ctxt['setup']['run_vm_agent']:
            sys.exit(0)

        remote_server = wsgiref.simple_server.make_server(
            '0.0.0.0', AGENT_DASHBOARD_PORT, app)
        remote_server.timeout = 0

        logging.info("Starting up dashboard.")

        thread = threading.Thread(target=remote_server.serve_forever)
        thread.setdaemon = True
        try:
            thread.start()
        except KeyboardInterrupt:
            remote_server.shutdown()
            sys.exit()

        logging.info("Starting Agent Main Loop:")

        # Let's start by figuring out who we are.
        conn_attempt = 0
        while conn_attempt < MAX_CONN_ATTEMPTS:
            try:
                conn_attempt += 1
                self.site_id = self.request_site_id_from_event_manager()
                break
            except Exception as e:
                self.agent_logger.warn("Error Connecting. Connection Attempt %d. Sleeping for %d seconds.", conn_attempt, CONN_RETRY_TIME)
                self.agent_logger.warn(e)
                sleep(CONN_RETRY_TIME)

        for manager in self.plugin_managers:
            id_response = self.send_em_message(
                utility.INSTRUMENT_ID_REQUEST, manager.instrument_name)

            data = dict(json.loads(id_response.content))['data']
            manager.info['instrument_id'] = data['instrument_id']

        for manager in self.plugin_managers:
            self.enumerate_plugins(manager)

            logging.info("Found the following plugins: %s",
                manager.get_plugin_list())

        self.agent_logger.info("Registering Plugins with multiple managers.")
        for manager in self.plugin_managers:
            for plugin in manager.get_plugin_list():
                logging.debug(plugin)
                self.register_plugin(plugin, manager)

        for manager in self.plugin_managers:
            manager.start_all_plugins()

        while self.continue_processing_events:
            event_processed=0
            for manager in self.plugin_managers:
                if not manager.msg_queue.empty():
                    response = self.process_plugin_event(manager)
                    event_processed += 1
            if event_processed == 0:
                sleep(0.1)

if __name__ == "__main__":
    agent = Agent()
    signal.signal(signal.SIGINT, utility.signal_handler)
    agent.main()
