from unittest import TestCase
from Agent import Agent
import os
import sys
import mock
import requests
import importlib
from multiprocessing import Process
from WarnoConfig import utility
import os

TEST_PLUGIN_PATH = 'warno_agent/src/tests/test_plugins/'
PLUGIN_ROOT = 'warno_agent.src.tests.test_plugins.'



class TestAgent(TestCase):

    def setUp(self):
        self.agent = Agent.Agent()
        plugin_test_directory = os.path.abspath('./')
        sys.path.append(plugin_test_directory)

    def tearDown(self):
        sys.path.pop()

    def test_set_plugin_path_sets_to_string_and_default_on_None(self):

        test_directory = '/test'

        self.agent.set_plugin_path(test_directory)
        self.assertEqual(self.agent.get_plugin_path(), test_directory, 'Plugin Paths not equal after set')

        self.agent.set_plugin_path()

        self.assertEqual(self.agent.get_plugin_path(), Agent.DEFAULT_PLUGIN_PATH,
                         'Empty plugin set does not return default')

    def test_list_plugins_base_test(self):

        self.agent.set_plugin_path(TEST_PLUGIN_PATH)
        plugin_list = self.agent.list_plugins()
        print("Plugin List",plugin_list)
        print("Plugin Path:", TEST_PLUGIN_PATH)


        # Get list of plugin names..a little hacky.
        plugin_name_list = [plugin.__name__ for plugin in plugin_list]


        self.assertIn(PLUGIN_ROOT+'test_plugin1', plugin_name_list,'Did not see test plugins')

        self.assertNotIn('test_plugins.bad_plugin_no_register', plugin_name_list,
                         'Accepted a plugin with no register function.')

        self.assertNotIn('test_plugins.bad_plugin_no_run', plugin_name_list,
                         'Accepted a bad plugin with no run function.')

        self.agent.set_plugin_path()


    @mock.patch.object(Agent, 'requests')
    def test_request_site_id_from_event_manager_proceses_site_id(self, mock_post):
        post_return = mock.Mock()
        post_return.status_code = requests.codes.ok
        post_return.content='{"Data": {"Site_Id": 1}}'

        mock_post.codes = requests.codes  # Pass Through

        mock_post.post.return_value = post_return

        self.agent.request_site_id_from_event_manager()
        self.assertTrue(mock_post.post.called, "Post was not called")
        self.assertEqual(self.agent.site_id, 1, 'Site Id was not 1')
        self.agent.site_id = None


    @mock.patch.object(Agent, 'requests')
    def test_request_site_id_from_event_manager_raises_exception_on_bad_request(self, mock_request):
        post_return = mock.create_autospec(requests.models.Response)

        previous_agent_value = self.agent.site_id
        self.agent.site_id = None

        post_return.status_code = requests.codes.ok
        post_return.content='{"Site_Id": 1}'

        mock_request.codes = requests.codes  # Pass Through
        mock_request.post.return_value = post_return

        post_return.status_code = requests.codes.bad_request
        mock_request.post.return_value = post_return
        self.agent.request_site_id_from_event_manager()
        self.assertTrue(post_return.raise_for_status.called, 'Exception not raised')

        self.assertIsNone(self.agent.site_id)
        self.agent.site_id = previous_agent_value

    @mock.patch.object(Agent, 'requests')
    def test_register_plugin_executes_calls_and_puts_in_event_code(self, mock_post):
        return1 = mock.Mock()
        return2 = mock.Mock()
        return3 = mock.Mock()

        return1.status_code = requests.codes.ok
        return1.content = '{"Data": {"Instrument_Id": 2}}'

        return2.status_code = requests.codes.ok
        return2.content = '{"Event_Code": 3, "Data": {"description" : "description1"}}'

        return3.status_code = requests.codes.ok
        return3.content = '{"Event_Code": 4, "Data": {"description" : "description2"}}'

        mock_post.codes = requests.codes
        mock_post.post.side_effect = iter([return1, return2, return3])

        test_plugin = importlib.import_module(PLUGIN_ROOT+'test_plugin1')
        self.agent.register_plugin(test_plugin)
        dict_to_be_contained = {'description1': 3, 'description2': 4}

        self.assertDictContainsSubset(dict_to_be_contained, self.agent.event_code_dict,
                                      'Event Codes did not contain expected items')

    @mock.patch.object(Agent, 'multiprocessing')
    def test_startup_plugin_runs_process(self, mock_process):

        return_process = mock.create_autospec(Process)

        mock_process.Process.return_value = return_process
        test_plugin = importlib.import_module(PLUGIN_ROOT+'test_plugin1')

        self.agent.instrument_ids.append((test_plugin, 6))
        self.agent.startup_plugin(test_plugin)

        self.assertTrue(mock_process.Process.called, "Process was not called")

        self.assertTrue(return_process.start.called, "Process.run was not called")


    @mock.patch.object(Agent, 'requests')
    def test_send_em_message_request_site_id_works(self, mock_requests):

        code = utility.SITE_ID_REQUEST
        data = 'kazr'

        self.agent.send_em_message(code, data)

        self.assertTrue(mock_requests.post.called,'requests.post is never called')
        call_args = mock_requests.post.call_args
        print(call_args)

        self.assertTrue(len(call_args[0]) == 1, 'Wrong number of positional arguments in requests.post call')
        self.assertTrue(len(call_args[1]) == 3, 'Wrong number of named arguments in requests.post call')
        self.assertTrue('json' in call_args[1], 'json not passed as arg')
        self.assertTrue('headers' in call_args[1], 'headers not passed as arg')
        self.assertTrue('verify' in call_args[1], 'verify not passed as arg')

    @mock.patch.object(Agent, 'requests')
    def test_send_em_message_handles_multiple_data(self, mock_requests):

        code = utility.SITE_ID_REQUEST
        data = {'description': 'red', 'instrument_id': '1'}

        self.agent.send_em_message(code, data)

        self.assertTrue(mock_requests.post.called,'requests.post is never called')
        call_args = mock_requests.post.call_args


        self.assertTrue(len(call_args[0]) == 1, 'Wrong number of positional arguments in requests.post call')
        self.assertTrue(len(call_args[1]) == 3, 'Wrong number of named arguments in requests.post call')
        self.assertTrue('json' in call_args[1], 'json not passed as arg')
        self.assertTrue('headers' in call_args[1], 'headers not passed as arg')
        self.assertTrue('verify' in call_args[1], 'verify not passed as arg')

    @mock.patch.object(Agent, 'requests')
    @mock.patch.object(Agent.Agent, 'startup_plugin')
    @mock.patch.object(Agent.Agent, 'register_plugin')
    @mock.patch.object(Agent.Agent, 'request_site_id_from_event_manager')
    @mock.patch.object(Agent.Agent, 'list_plugins')
    def test_main_loop_when_not_central(self, mock_list_plugins, mock_request_id, mock_register, mock_startup, mock_requests):
        mock_list_plugins.return_value = ['test1', 'test2']
        mock_request_id.return_value = 123

        self.agent.main_loop_boolean=False
        self.agent.is_central=0
        self.agent.main()

        self.assertTrue(mock_list_plugins.called,'Plugins were never listed')
        self.assertTrue(mock_request_id.called, 'ID Never Requested')
        self.assertTrue(mock_register.called, 'Plugins never registered')
        self.assertTrue(mock_startup.called, 'Plugin Startup Never Called')

    @mock.patch.object(Agent, 'requests')
    @mock.patch.object(Agent.Agent, 'startup_plugin')
    @mock.patch.object(Agent.Agent, 'register_plugin')
    @mock.patch.object(Agent.Agent, 'request_site_id_from_event_manager')
    @mock.patch.object(Agent.Agent, 'list_plugins')
    def test_main_loop_exits_when_central(self, mock_list_plugins, mock_request_id, mock_register, mock_startup, mock_requests):
        mock_list_plugins.return_value = ['test1', 'test2']
        mock_request_id.return_value = 123

        self.agent.main_loop_boolean=False
        self.agent.is_central=1
        with self.assertRaises(SystemExit) as e:
            self.agent.main()
        self.assertEqual(e.exception.code, 0, "Main loop did not exit with the correct code")

        self.assertFalse(mock_list_plugins.called,'Plugins were listed')
        self.assertFalse(mock_request_id.called, 'ID Requested')
        self.assertFalse(mock_register.called, 'Plugins registered')
        self.assertFalse(mock_startup.called, 'Plugin Startup Called')