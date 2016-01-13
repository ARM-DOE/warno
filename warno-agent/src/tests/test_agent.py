from unittest import TestCase
from Agent import Agent
import os
import glob
import sys

TEST_PLUGIN_PATH = 'test_plugins/'

class TestAgent(TestCase):

    def setUp(self):
        self.agent = Agent.Agent()
        plugin_test_directory = os.path.abspath('./')
        sys.path.append(plugin_test_directory)

    def test_set_plugin_path_sets_to_string_and_default_on_None(self):

        test_directory = '/test'

        self.agent.set_plugin_path(test_directory)
        self.assertEqual(self.agent.get_plugin_path(), test_directory,'Plugin Paths not equal after set')

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
        self.assertNotIn('test_plugins.bad_plugin', plugin_name_list, 'Accepted a bad plugin.')

        self.agent.set_plugin_path()

