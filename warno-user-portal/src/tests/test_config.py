from unittest import TestCase

from UserPortal import config


class TestGet_config_context(TestCase):
    list_required_keys = ['DB_HOST', 'DB_USER', 'DB_PASS']

    def test_get_config_context(self):
        '''Test the configuration context'''

        cfg = config.get_config_context()

        for value in self.list_required_keys:
            self.assertIn(value, cfg, 'config context does not contain key:"%s"' % value)
