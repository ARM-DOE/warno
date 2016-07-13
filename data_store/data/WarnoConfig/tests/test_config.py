from unittest import TestCase

from .. import config


class TestGetConfigContext(TestCase):
    required_config_keys = ['DB_HOST', 'DB_USER', 'DB_NAME']

    def test_get_config_context_construct_contains_expected_database_keys(self):
        """The configuration context should be properly set with the expected database keys."""

        config_construct = config.get_config_context()

        for value in self.required_config_keys:
            self.assertIn(value, config_construct['database'], 'config context does not contain key:"%s"' % value)

        self.assertIn('DB_PASS', config_construct['s_database'], 'config context does not contain key: "DB_PASS"')

    def test_get_config_context_construct_top_level_dicts_setup_and_type(self):
        """Configuration construct should have top level dictionaries 'setup' and 'type'"""
        config_construct = config.get_config_context()

        self.assertIn('setup', config_construct, 'Configuration construct should have "setup" entry')
        self.assertIn('type', config_construct, 'Configuration construct should have "type" entry')
