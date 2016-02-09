import flask
import mock
import requests
from unittest import TestCase

from .. import utility

class test_views(TestCase):

    def test_is_number(self):
        self.assertTrue(utility.is_number('1'), '"1 should be a number"')
        self.assertTrue(utility.is_number('1.1'), '1.1 should be a number')
        self.assertTrue(utility.is_number(' -5.1'), 'test_is_number failed')

        self.assertFalse(utility.is_number('a'), 'a is not a number')
        self.assertFalse(utility.is_number('1.1.1'), '1.1.1 is not a number')

    def test_status_code_to_text(self):
        result = utility.status_code_to_text(1)
        expected = "OPERATIONAL"
        self.assertEquals(result, expected, "1 should have been 'OPERATIONAL'")
        result = utility.status_code_to_text("2")
        expected = "NOT WORKING"
        self.assertEquals(result, expected, "2 should have been 'NOT WORKING'")