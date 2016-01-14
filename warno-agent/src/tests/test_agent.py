from unittest import TestCase
from Agent import Agent
import os
import sys
import mock
import requests


TEST_PLUGIN_PATH = 'test_plugins/'

class TestAgent(TestCase):

    def setUp(self):
        self.agent = Agent.Agent()
        plugin_test_directory = os.path.abspath('./')
        sys.path.append(plugin_test_directory)

    def test_set_plugin_path_sets_to_string_and_default_on_None(self):

        test_directory = '/test'

        self.agent.set_plugin_path(test_directory)
        self.assertEqual(self.agent.get_plugin_path(), test_directory, 'Plugin Paths not equal after set')

        self.agent.set_plugin_path()

        self.assertEqual(self.agent.get_plugin_path(), Agent.DEFAULT_PLUGIN_PATH,
                         'Empty plugin set does not return default')

    def test_list_plugins_base_test(self):

        plugin_test_directory = os.path.abspath('./')
        self.agent.set_plugin_path(TEST_PLUGIN_PATH)
        plugin_list = self.agent.list_plugins()

        # Get list of plugin names..a little hacky.
        plugin_name_list = [plugin.__name__ for plugin in plugin_list]

        self.assertIn('test_plugins.test_plugin1', plugin_name_list,'Did not see test plugins')

        self.assertNotIn('test_plugins.bad_plugin_no_register', plugin_name_list,
                         'Accepted a plugin with no register function.')

        self.assertNotIn('test_plugins.bad_plugin_no_run', plugin_name_list,
                         'Accepted a bad plugin with no run function.')

        self.agent.set_plugin_path()


    @mock.patch.object(Agent, 'requests')
    def test_request_site_id_from_event_manager_proceses_site_id(self, mock_post):
        post_return = mock.Mock()
        post_return.status_code = requests.codes.ok
        post_return.content='{"Site_Id": 1}'

        mock_post.codes = requests.codes  # Pass Through

        mock_post.post.return_value = post_return

        self.agent.request_site_id_from_event_manager()
        self.assertTrue(mock_post.post.called, "Post was not called")
        self.assertEqual(self.agent.site_id, 1, 'Site Id was not 1')
        self.agent.site_id = None


    @mock.patch.object(Agent, 'requests')
    def test_request_site_id_from_event_manager_raises_exception_on_bad_request(self,mock_post):
        post_return = mock.Mock()
        previous_agent_value = self.agent.site_id
        self.agent.site_id = None
        post_return.status_code = requests.codes.ok
        post_return.content='{"Site_Id": 1}'

        mock_post.codes = requests.codes  # Pass Through

        mock_post.post.return_value = post_return

        post_return.status_code = requests.codes.bad_request
        mock_post.post.return_value = post_return
        self.assertRaises(requests.exceptions.HTTPError,
                          self.agent.request_site_id_from_event_manager())

        self.assertIsNone(self.agent.site_id)
        self.agent.site_id = previous_agent_value

