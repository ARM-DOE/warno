import flask
import mock
import requests
from flask.ext.testing import TestCase

from UserPortal import instruments
from UserPortal import views

class test_instruments(TestCase):

    render_templates = False

    def create_app(self):
        views.app.config['TESTING'] = True
        return views.app


    @mock.patch('psycopg2.connect')
    def test_list_instruments_returns_200_and_passes_mock_db_instruments_as_context_variable_using_correct_template(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value
        # Mocked return is larger than necessary to allow the code some flexibility
        db_return = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]
        cursor.fetchall.return_value = db_return
        result = self.client.get('/instruments')
        self.assert200(result, "GET return is not '200 OK'")
        # Accessing context variable by name feels brittle, but it seems to be the only way
        context_instruments = self.get_context_variable('instruments')
        values = [value for key, value in context_instruments[0].iteritems()]
        self.assertTrue(0 in values, "Value '0' is not in the returned dictionary")
        self.assertTrue(1 in values, "Value '1' is not in the returned dictionary")
        self.assertTrue(2 in values, "Value '2' is not in the returned dictionary")
        self.assert_template_used('instrument_list.html')


    @mock.patch('psycopg2.connect')
    def test_method_get_on_new_instrument_returns_200_ok_and_passes_mock_db_sites_as_context_variable_using_correct_template(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value
        # Mocked return is larger than necessary to allow the code some flexibility
        db_return = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]
        cursor.fetchall.return_value = db_return
        result = self.client.get('/instruments/new')
        self.assert200(result)
        # Accessing context variable by name feels brittle, but it seems to be the only way
        context_instruments = self.get_context_variable('sites')
        values = [value for key, value in context_instruments[0].iteritems()]
        self.assertTrue(0 in values, "Value '0' is not in the returned dictionary")
        self.assertTrue(1 in values, "Value '1' is not in the returned dictionary")
        self.assert_template_used('new_instrument.html')


    @mock.patch('psycopg2.connect')
    def test_method_get_on_instrument_when_id_is_23_calls_db_with_correct_arguments_and_returns_200(self, connect):
        connection = connect.return_value
        cursor = connection.cursor.return_value
        instrument_id = 23
        test_url = "/instruments/%s" % instrument_id
        result = self.client.get(test_url)
        execute_calls = cursor.execute.call_args
        print execute_calls
        self.assertTrue(u'%s' % instrument_id in execute_calls[0][1],
                        "cursor.execute is not called with correct instrument id")
        self.assertTrue("SELECT" in execute_calls[0][0],
                        "cursor.execute does not 'SELECT'")
        self.assertTrue("special" in execute_calls[0][0],
                        "cursor.execute does not involve 'special'")
        self.assertTrue("description" in execute_calls[0][0],
                        "cursor.execute does not involve 'description'")
        self.assert200(result, "GET return is not '200 OK'")


    ### /instruments/instrument_id ###
    @mock.patch('psycopg2.connect')
    def test_method_delete_on_instrument_when_id_is_23_returns_200(self, connect):
        instrument_id = 23
        test_url = "/instruments/%s" % instrument_id
        result = self.client.delete(test_url)
        self.assert200(result, "GET return is not '200 OK'")


    def test_db_delete_instrument_when_id_is_10_calls_db_with_correct_arguments_and_returns_200(self):
        # TODO Fix the reliance on 3rd execute, split delete from instruments, add 200 check
        cursor = mock.Mock()
        instrument_id = 10
        instruments.db_delete_instrument(instrument_id, cursor)
        execute_calls = cursor.execute.call_args_list
        self.assertTrue(instrument_id in execute_calls[2][0][1],
                        "Third cursor.execute is not called with correct instrument id")
        self.assertTrue("COMMIT" in execute_calls[-1][0][0], "Final cursor.execute is not called as 'COMMIT'")
        self.assertTrue("DELETE FROM instruments" in execute_calls[-2][0][0],
                        "cursor.execute does not delete from instruments")


    ### Database Helpers ###
    def test_db_get_instrument_references_calls_db_with_correct_arguments_and_returns_mock_db_results(self):
        cursor = mock.Mock()
        db_return = ["return"]
        cursor.fetchall.return_value = db_return
        instrument_id = 5
        result = instruments.db_get_instrument_references(instrument_id, cursor)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1], "cursor.execute is not called with correct instrument id")
        self.assertTrue("SELECT" in executed_call[0][0], "cursor.execute does not 'SELECT'")
        self.assertTrue("special" in executed_call[0][0], "cursor.execute does not involve 'special'")
        self.assertTrue("FROM instrument_data_references" in executed_call[0][0],
                        "cursor.execute does not access 'instrument_data_references'")
        self.assertEqual(db_return, result, "cursor.execute does not return the select result")


    def test_db_select_instrument_when_id_is_10_calls_db_with_correct_arguments_and_returns_mock_db_results(self):
        cursor = mock.Mock()
        # Mocked return is larger than necessary to allow the code some flexibility
        db_return = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        cursor.fetchone.return_value = db_return
        instrument_id = 10
        result = instruments.db_select_instrument(instrument_id, cursor)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1], "cursor.execute is not called with correct instrument id")
        self.assertTrue("SELECT" in executed_call[0][0], "cursor.execute does not 'SELECT'")
        self.assertTrue("instrument_id" in executed_call[0][0], "cursor.execute does not involve 'instrument_id'")
        self.assertTrue("name_short" in executed_call[0][0], "cursor.execute does not involve 'name_short'")
        values = [value for key, value in result.iteritems()]
        self.assertTrue(0 in values, "Value '0' is not in the returned dictionary")
        self.assertTrue(1 in values, "Value '1' is not in the returned dictionary")
        self.assertTrue(2 in values, "Value '2' is not in the returned dictionary")


    def test_db_recent_logs_by_instrument_when_id_is_15_and_maximum_number_is_default_calls_db_with_correct_arguments(self):
        cursor = mock.Mock()
        # Mocked returns are larger than necessary to allow the code some flexibility
        db_return = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [11, 12, 13, 14, 15, 16, 17, 18, 19]]
        cursor.fetchall.return_value = db_return
        instrument_id = 15
        result = instruments.db_recent_logs_by_instrument(instrument_id, cursor)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1], "cursor.execute is not called with correct instrument id")
        # Make sure the default maximum number (whatever it is) made it into the cursor.execute
        self.assertTrue(executed_call[0][1][1] != None,
                        "cursor.execute is not called with an argument for maximum number of logs")
        self.assertTrue("SELECT" in executed_call[0][0], "cursor.execute does not 'SELECT'")
        self.assertTrue("instrument_logs" in executed_call[0][0], "cursor.execute does not involve 'instrument_logs'")
        self.assertTrue("status" in executed_call[0][0], "cursor.execute does not involve 'status'")
        values = [value for key, value in result[1].iteritems()]
        self.assertTrue(11 in values, "Value '11' is not in the returned dictionary for the second log")
        self.assertTrue(12 in values, "Value '12' is not in the returned dictionary for the second log")
        self.assertTrue(13 in values, "Value '13' is not in the returned dictionary for the second log")


    def test_db_recent_logs_by_instrument_when_id_is_15_and_maximum_number_is_11_calls_db_with_correct_arguments(self):
        cursor = mock.Mock()
        # Mocked returns are larger than necessary to allow the code some flexibility
        db_return = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [11, 12, 13, 14, 15, 16, 17, 18, 19]]
        cursor.fetchall.return_value = db_return
        instrument_id = 15
        maximum_number = 11
        instruments.db_recent_logs_by_instrument(instrument_id, cursor, maximum_number)
        executed_call = cursor.execute.call_args
        self.assertTrue(instrument_id in executed_call[0][1], "cursor.execute is not called with correct instrument id")
        self.assertTrue(maximum_number in executed_call[0][1], "cursor.execute is not called with correct maximum number")
        self.assertTrue("SELECT" in executed_call[0][0], "cursor.execute does not 'SELECT'")
        self.assertTrue("instrument_logs" in executed_call[0][0], "cursor.execute does not involve 'instrument_logs'")
        self.assertTrue("status" in executed_call[0][0], "cursor.execute does not involve 'status'")


    ### Helper Functions ###

    def test_valid_columns_for_instrument_calls_db_with_correct_arguments_and_returns_expected_column_list(self):
        cursor = mock.Mock()
        expected_column_list = ["integer", "not_special_table"]
        # Each reference is a boolean specifying whether it is a 'special' table along with the name of the table
        references = [[True, "special_table"], [False, "not_special_table"]]
        # Datetime should not be a valid data type and should not make it into results
        special_table_entries = [["integer", "integer"],["datetime", "datetime"]]
        cursor.fetchall.side_effect = [references, special_table_entries]
        instrument_id = 10
        result_column_list = instruments.valid_columns_for_instrument(instrument_id, cursor)
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

        # Second database execute expected to be performed on a 'special' table only
        self.assertTrue("FROM information_schema.columns" in executed_calls[1][0][0],
                        "Second cursor.execute never accesses 'information_schema.columns'")
        self.assertTrue("special_table" in executed_calls[1][0][1],
                        "Second cursor.execute not called with 'special_table' table name")