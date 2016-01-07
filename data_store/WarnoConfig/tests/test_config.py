from unittest import TestCase

from .. import config


class TestGet_config_context(TestCase):
    list_required_keys = ['DB_HOST', 'DB_USER', 'DB_PASS']

    def test_get_config_context_database_entries(self):
        '''Test the configuration context'''

        cfg = config.get_config_context()

        for value in self.list_required_keys:
            self.assertIn(value, cfg['database'], 'config context does not contain key:"%s"' % value)

    def test_get_config_context_top_level_dicts(self):
        cfg = config.get_config_context()

        self.assertIn('setup', cfg, 'Configuration should have "setup" entry' )
        self.assertIn('type', cfg, 'Configuration should have "type" entry')



