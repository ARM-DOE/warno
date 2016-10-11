from unittest import TestCase
from ..synthesis import Synthesis


class testSynthesis(TestCase):

    def setUp(self):
        self.synthesis = Synthesis()

    def test_synthesis_has_config_context(self):
        self.assertIsNotNone(self.synthesis.config_ctxt)

