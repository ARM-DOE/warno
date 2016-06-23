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

    @mock.patch(__name__ + ".utility.create_engine")
    def test_save_rows_to_table_with_small_data_calls_expected_queries(self, create_engine):
        engine = mock.Mock()
        connection = mock.Mock()
        create_engine.return_value = engine
        engine.connect.return_value = connection
        utility.save_rows_to_table("prosensing_paf", ['column_1', 'column_2'],
                                   [[0, "01-01-2001T01:01:01"], [1, "02-02-2002T02:02:02"]])

        self.assertIn("), (", connection.execute.call_args_list[0][0][0],
                      "'), (' Not in call argument to database, indicating there may not be multiple data tuples.")
        self.assertIn("01-01-2001 01:01:01", connection.execute.call_args_list[0][0][0],
                      "'01-01-2001 01:01:01' Not in call argument to database, time string not converted as expected.")
        self.assertIn("'0'", connection.execute.call_args_list[0][0][0],
                      "Value '0' not added to database call as expected.")
        self.assertIn("'1'", connection.execute.call_args_list[0][0][0],
                      "Value '1' not added to database call as expected.")
        self.assertIn("COMMIT", connection.execute.call_args_list[-1][0][0], "'COMMIT' not in final call's arguments")