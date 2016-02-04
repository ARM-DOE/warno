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
            self.assertTrue(u'%s' % instrument_id in execute_calls[0][1],
                            "cursor.execute is not called with correct instrument id")
            self.assertTrue("SELECT special, description" in execute_calls[0][0],
                            "cursor.execute does not select the columns 'special' and 'description'")
            self.assertEqual(result.status, '200 OK', "GET return is not '200 OK'")

    ### /instruments/instrument_id ###
    @mock.patch('psycopg2.connect')
    def test_method_type_delete_instrument_id_is_23(self, connect):
        with views.app.test_client() as c:
            connection = connect.return_value
            cursor = connection.cursor.return_value
            instrument_id = 23
            test_url = "/instruments/%s" % instrument_id
            result = c.delete(test_url)
            self.assertEqual(result.status, '200 OK', "GET return is not '200 OK'")

    def test_db_delete_instrument_id_is_10(self):
        cursor = mock.Mock()
        instrument_id = 10
        views.db_delete_instrument(instrument_id, cursor)
        execute_calls = cursor.execute.call_args_list
        self.assertTrue(instrument_id in execute_calls[2][0][1],
                        "Third cursor.execute is not called with correct instrument id")
        self.assertTrue("COMMIT" in execute_calls[-1][0][0], "Final cursor.execute is not called as 'COMMIT'")
        self.assertTrue("DELETE FROM instruments" in execute_calls[-2][0][0],
                        "cursor.execute does not delete from instruments")

    ### Database Helpers ###
    def test_db_get_instrument_references(self):
        cursor = mock.Mock()
        db_return = ["return"]
        cursor.fetchall.return_value = db_return
        instrument_id = 5
        result = views.db_get_instrument_references(instrument_id, cursor)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1], "cursor.execute is not called with correct instrument id")
        self.assertTrue("SELECT" in executed_call[0][0], "cursor.execute does not 'SELECT'")
        self.assertTrue("special" in executed_call[0][0], "cursor.execute does not involve 'special'")
        self.assertTrue("FROM instrument_data_references" in executed_call[0][0],
                        "cursor.execute does not access 'instrument_data_references'")
        self.assertEqual(db_return, result, "cursor.execute does not return the select result")


    def test_db_select_instrument_id_is_10(self):
        cursor = mock.Mock()
        db_return = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        cursor.fetchone.return_value = db_return
        instrument_id = 10
        result = views.db_select_instrument(instrument_id, cursor)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1], "cursor.execute is not called with correct instrument id")
        self.assertTrue("SELECT" in executed_call[0][0], "cursor.execute does not 'SELECT'")
        self.assertTrue("instrument_id" in executed_call[0][0], "cursor.execute does not involve 'instrument_id'")
        self.assertTrue("name_short" in executed_call[0][0], "cursor.execute does not involve 'name_short'")
        values = [value for key, value in result.iteritems()]
        self.assertTrue(0 in values, "Value '0' is not in the returned dictionary")
        self.assertTrue(1 in values, "Value '1' is not in the returned dictionary")
        self.assertTrue(10 in values, "Value '10' is not in the returned dictionary")
        #self.assertTrue(False)

    def test_db_recent_logs_by_instrument_id_is_15_default_maximum_number(self):
        cursor = mock.Mock()
        db_return = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]
        cursor.fetchall.return_value = db_return
        instrument_id = 15
        result = views.db_recent_logs_by_instrument(instrument_id, cursor)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1], "cursor.execute is not called with correct instrument id")
        # Make sure the default maximum number (whatever it is) made it into the cursor.execute
        self.assertTrue(executed_call[0][1][1] != None,
                        "cursor.execute is not called with an argument for maximum number of logs")
        self.assertTrue("SELECT" in executed_call[0][0], "cursor.execute does not 'SELECT'")
        self.assertTrue("instrument_logs" in executed_call[0][0], "cursor.execute does not involve 'instrument_logs'")
        self.assertTrue("status" in executed_call[0][0], "cursor.execute does not involve 'status'")
        values = [value for key, value in result[1].iteritems()]
        self.assertTrue(5 in values, "Value '5' is not in the returned dictionary for the second log")
        self.assertTrue(6 in values, "Value '6' is not in the returned dictionary for the second log")
        self.assertTrue(9 in values, "Value '9' is not in the returned dictionary for the second log")

    def test_db_recent_logs_by_instrument_id_is_15_maximum_number_is_11(self):
        cursor = mock.Mock()
        db_return = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]
        cursor.fetchall.return_value = db_return
        instrument_id = 15
        maximum_number = 11
        views.db_recent_logs_by_instrument(instrument_id, cursor, maximum_number)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1], "cursor.execute is not called with correct instrument id")
        self.assertTrue(maximum_number in executed_call[0][1], "cursor.execute is not called with correct maximum number")
        self.assertTrue("SELECT" in executed_call[0][0], "cursor.execute does not 'SELECT'")
        self.assertTrue("instrument_logs" in executed_call[0][0], "cursor.execute does not involve 'instrument_logs'")
        self.assertTrue("status" in executed_call[0][0], "cursor.execute does not involve 'status'")


    ### Helper Functions ###

    def test_valid_columns_for_instrument(self):
        cursor = mock.Mock()
        expected_column_list = ["integer", "not_special_table"]
        references = [[True, "special_table"], [False, "not_special_table"]]
        special_table_entries = [["integer", "integer"],["datetime", "datetime"]]
        cursor.fetchall.side_effect = [references, special_table_entries]
        instrument_id = 10
        result_column_list = views.valid_columns_for_instrument(instrument_id, cursor)
        executed_calls = cursor.execute.call_args_list
        self.assertTrue(expected_column_list[0] in result_column_list,
                        "First valid column string '%s' not returned in columns" % expected_column_list[0])
        self.assertTrue(expected_column_list[1] in result_column_list,
                        "Second valid column string '%s' not returned in columns" % expected_column_list[1])
        self.assertTrue("datetime" not in result_column_list, "Invalid column string 'datetime' in returned columns")

        self.assertTrue("instrument_data_references" in executed_calls[0][0][0],
                        "First cursor.execute never accesses 'instrument_data_references'")
        self.assertTrue(instrument_id in executed_calls[0][0][1],
                        "First cursor.execute not called with correct instrument id")

        self.assertTrue("FROM information_schema.columns" in executed_calls[1][0][0],
                        "Second cursor.execute never accesses 'information_schema.columns'")
        self.assertTrue("special_table" in executed_calls[1][0][1],
                        "Second cursor.execute not called with 'special_table' table name")


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
