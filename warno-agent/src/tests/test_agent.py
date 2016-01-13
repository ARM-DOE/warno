from unittest import TestCase
from Agent import Agent


class TestAgent(TestCase):

    def setUp(self):
        self.agent = Agent.Agent()

    def test_set_plugin_path_sets_to_string_and_default_on_None(self):

        test_directory = '/test'

        self.agent.set_plugin_path(test_directory)
        self.assertEqual(self.agent.get_plugin_path(), test_directory,'Plugin Paths not equal after set')

        self.agent.set_plugin_path()
        self.assertEqual(self.agent.get_plugin_path(), Agent.DEFAULT_PLUGIN_PATH,'Empty plugin set does not return default')

