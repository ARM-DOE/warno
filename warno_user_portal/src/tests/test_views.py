import flask
import mock
import requests
from unittest import TestCase
from UserPortal import views

class test_views(TestCase):



    @mock.patch('psycopg2.connect')
    def test_connect_db(self, connect):
        expected_result = "Connected"
        connect.return_value = expected_result
        result = views.connect_db()
        self.assertEqual(result, expected_result, "Result should have been 'Connected'")


    def test_status_code_to_text(self):
        result = views.status_code_to_text(1)
        expected = "OPERATIONAL"
        self.assertEquals(result, expected, "1 should have been 'OPERATIONAL'")
        result = views.status_code_to_text("2")
        expected = "NOT WORKING"
        self.assertEquals(result, expected, "2 should have been 'NOT WORKING'")

    def test_is_number(self):
        self.assertTrue(views.is_number('1'), '"1 should be a number"')
        self.assertTrue(views.is_number('1.1'), '1.1 should be a number')
        self.assertTrue(views.is_number(' -5.1'), 'test_is_number failed')

        self.assertFalse(views.is_number('a'), 'a is not a number')
        self.assertFalse(views.is_number('1.1.1'), '1.1.1 is not a number')

    def test_two(self):
        self.assertTrue(True)
