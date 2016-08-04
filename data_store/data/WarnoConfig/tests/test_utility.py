import mock

from unittest import TestCase

from .. import utility


class TestUtilityFunctions(TestCase):

    def test_is_number_properly_identifies_safe_numbers_from_strings(self):
        """Tests that the 'is_number' function returns 'True' only on strings that can be safely converted into python
        numbers."""
        self.assertTrue(utility.is_number('1'), '"1 should be a number"')
        self.assertTrue(utility.is_number('1.1'), '1.1 should be a number')
        self.assertTrue(utility.is_number(' -5.1'), 'test_is_number failed')

        self.assertFalse(utility.is_number('a'), 'a is not a number')
        self.assertFalse(utility.is_number('1.1.1'), '1.1.1 is not a number')

    def test_status_code_to_text_converts_integer_status_codes_to_corresponding_string_status_descriptions(self):
        """Tests that the 'status_code_to_text' function correctly converts the integer status codes into their
        corresponding human readable string descriptions.  Also tests that the argument supplied to the function may be
        either an integer or a basic string representation of an integer."""
        function_return_for_2 = utility.status_code_to_text(1)
        expected_return_for_1 = "OPERATIONAL"
        self.assertEquals(function_return_for_2, expected_return_for_1, "1 should have been 'OPERATIONAL'")

        function_return_for_2 = utility.status_code_to_text("2")
        expected_return_for_2 = "NOT WORKING"
        self.assertEquals(function_return_for_2, expected_return_for_2, "2 should have been 'NOT WORKING'")

    @mock.patch(__name__ + ".utility.create_engine")
    def test_save_rows_to_table_with_small_data_calls_expected_queries(self, create_engine):
        """Tests that the 'save_rows_to_table' function correctly builds and calls a SQL query to insert the information
        in it into the database.  Rather than checking for an exact query build, checks that key architectural pieces of
        the query exist, such as the comma separated value tuples, the actual data, etc.  Needs to be tested due to the
        custom procedural building of the query."""
        # This set of mocks prevents the query from ever hitting the database, but allows us to view the passed query.
        engine = mock.Mock()
        connection = mock.Mock()
        create_engine.return_value = engine
        engine.connect.return_value = connection

        utility.save_rows_to_table("prosensing_paf", ['column_1', 'column_2'],
                                   [[0, "01-01-2001T01:01:01"], [1, "02-02-2002T02:02:02"]])

        # Digging this deep into the call args feels brittle, but there does not appear to be much of an easier way.
        self.assertIn("), (", connection.execute.call_args_list[0][0][0],
                      "'), (' Not in call argument to database, indicating there may not be multiple data tuples.")
        self.assertIn("01-01-2001 01:01:01", connection.execute.call_args_list[0][0][0],
                      "'01-01-2001 01:01:01' Not in call argument to database, time string not converted as expected.")
        self.assertIn("'0'", connection.execute.call_args_list[0][0][0],
                      "Value '0' not added to database call as expected.")
        self.assertIn("'1'", connection.execute.call_args_list[0][0][0],
                      "Value '1' not added to database call as expected.")
        self.assertIn("COMMIT", connection.execute.call_args_list[-1][0][0], "'COMMIT' not in final call's arguments")