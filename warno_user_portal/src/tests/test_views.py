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


    def test_two(self):
        self.assertTrue(True)
