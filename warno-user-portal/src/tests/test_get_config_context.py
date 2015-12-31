from unittest import TestCase
from UserPortal import config


class TestGet_config_context(TestCase):

  def test_get_config_context(self):
    cfg = config.get_config_context()

    assert 'DB_HOST' in cfg
