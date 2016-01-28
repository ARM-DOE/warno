import flask
import mock
import requests
from unittest import TestCase
from UserPortal import views

class test_views(TestCase):

    @mock.patch('psycopg2.connect')
    def test_method_type_get_instrument_id_is_23(self, connect):
        with views.app.test_client() as c:
            connection = connect.return_value
            cursor = connection.cursor.return_value
            instrument_id = 23
            test_url = "/instruments/%s" % instrument_id
            result = c.get(test_url)
            execute_calls = cursor.execute.call_args
            print execute_calls
            self.assertTrue(u'%s' % instrument_id in execute_calls[0][1])
            self.assertTrue("SELECT special, description" in execute_calls[0][0])
            self.assertEqual(result.status, '200 OK')
            #self.assertEqual(True, False)

    ### /instruments/instrument_id ###
    @mock.patch('psycopg2.connect')
    def test_method_type_delete_instrument_id_is_23(self, connect):
        with views.app.test_client() as c:
            connection = connect.return_value
            cursor = connection.cursor.return_value
            instrument_id = 22
            test_url = "/instruments/%s" % instrument_id
            result = c.delete(test_url)
            self.assertEqual(result.status, '200 OK')

    def test_db_delete_instrument_id_is_10(self):
        cursor = mock.Mock()
        instrument_id = 10
        views.db_delete_instrument(instrument_id, cursor)
        execute_calls = cursor.execute.call_args_list
        print execute_calls
        self.assertTrue(instrument_id in execute_calls[2][0][1])
        self.assertTrue("COMMIT" in execute_calls[-1][0][0])
        self.assertTrue("DELETE FROM instruments" in execute_calls[-2][0][0])
        #self.assertEqual(True, False)

    ### Database Helpers ###
    def test_db_select_instrument_id_is_10(self):
        cursor = mock.Mock()
        db_return = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        cursor.fetchone.return_value = db_return
        instrument_id = 10
        result = views.db_select_instrument(instrument_id, cursor)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1])
        self.assertTrue("SELECT" in executed_call[0][0])
        self.assertTrue("instrument_id" in executed_call[0][0])
        self.assertTrue("name_short" in executed_call[0][0])
        values = [value for key, value in result.iteritems()]
        self.assertTrue(0 in values)
        self.assertTrue(1 in values)
        self.assertTrue(10 in values)
        #self.assertTrue(False)

    def test_db_recent_logs_by_instrument_id_is_15_default_maximum_number(self):
        cursor = mock.Mock()
        db_return = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]
        cursor.fetchall.return_value = db_return
        instrument_id = 15
        result = views.db_recent_logs_by_instrument(instrument_id, cursor)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1])
        # Make sure the default maximum number (whatever it is) made it into the cursor.execute
        self.assertTrue(executed_call[0][1][1] != None)
        self.assertTrue("SELECT" in executed_call[0][0])
        self.assertTrue("instrument_logs" in executed_call[0][0])
        self.assertTrue("status" in executed_call[0][0])
        values = [value for key, value in result[1].iteritems()]
        self.assertTrue(5 in values)
        self.assertTrue(6 in values)
        self.assertTrue(9 in values)

    def test_db_recent_logs_by_instrument_id_is_15_maximum_number_is_11(self):
        cursor = mock.Mock()
        db_return = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]
        cursor.fetchall.return_value = db_return
        instrument_id = 15
        maximum_number = 11
        views.db_recent_logs_by_instrument(instrument_id, cursor, maximum_number)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1])
        self.assertTrue(maximum_number in executed_call[0][1])
        self.assertTrue("SELECT" in executed_call[0][0])
        self.assertTrue("instrument_logs" in executed_call[0][0])
        self.assertTrue("status" in executed_call[0][0])

    ### Helper Functions ###
    @mock.patch('psycopg2.connect')
    def test_connect_db(self, connect):
        expected_result = "Connected"
        connect.return_value = expected_result
        result = views.connect_db()
        self.assertEqual(result, expected_result)


    def test_status_code_to_text(self):
        result = views.status_code_to_text(1)
        expected = "OPERATIONAL"
        self.assertEqual(result, expected)
        result = views.status_code_to_text("2")
        expected = "NOT WORKING"
        self.assertEquals(result, expected)

    def test_is_number(self):
        self.assertTrue(views.is_number('1'), '"1 should be a number"')
        self.assertTrue(views.is_number('1.1'), '1.1 should be a number')
        self.assertTrue(views.is_number(' -5.1'), 'test_is_number failed')

        self.assertFalse(views.is_number('a'), 'a is not a number')
        self.assertFalse(views.is_number('1.1.1'), '1.1.1 is not a number')

    def test_two(self):
        self.assertTrue(True)
