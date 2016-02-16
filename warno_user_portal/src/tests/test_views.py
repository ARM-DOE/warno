import flask
import mock
import requests
from unittest import TestCase
from UserPortal import views

class test_views(TestCase):

    def test_status_log_for_each_instrument(self):
        cursor = mock.Mock()
        first_instrument_id = 2
        first_instrument_author = "first_author"
        first_instrument_contents = "first_contents"
        first_instrument_status = 5

        second_instrument_id = 4
        second_instrument_author = "second_author"
        second_instrument_contents = "second_contents"
        second_instrument_status = 1

        first_instrument = [first_instrument_id, first_instrument_author, first_instrument_status, first_instrument_contents]
        second_instrument = [second_instrument_id, second_instrument_author, second_instrument_status, second_instrument_contents]
        cursor.fetchall.return_value = [first_instrument, second_instrument]
        result = views.status_log_for_each_instrument(cursor)
        self.assertEquals(result[first_instrument_id]["author"], first_instrument_author,
                             "First instrument's author is not '%s'" % first_instrument_author)
        self.assertEquals(result[first_instrument_id]["status_code"], first_instrument_status,
                             "First instrument's status_code is not '%s'" % first_instrument_status)
        self.assertEquals(result[first_instrument_id]["contents"], first_instrument_contents,
                             "First instrument's contents are not '%s'" % first_instrument_contents)

        self.assertEquals(result[second_instrument_id]["author"], second_instrument_author,
                             "Second instrument's author is not '%s'" % second_instrument_author)
        self.assertEquals(result[second_instrument_id]["status_code"], second_instrument_status,
                             "Second instrument's status_code is not '%s'" % second_instrument_status)
        self.assertEquals(result[second_instrument_id]["contents"], second_instrument_contents,
                             "Second instrument's contents are not '%s'" % second_instrument_contents)


    @mock.patch('psycopg2.connect')
    def test_connect_db(self, connect):
        expected_result = "Connected"
        connect.return_value = expected_result
        result = views.connect_db()
        self.assertEqual(result, expected_result, "Result should have been 'Connected'")


    def test_two(self):
        self.assertTrue(True)
