from unittest import TestCase

from .. import redis_interface


class TestUtilityFunctions(TestCase):

    def test_build_base_attribute_key_function_without_table_name_succeeds_with_valid_input(self):
        """Tests that the _build_base_attribute_key function without the 'table_name' parameter builds the expected key
        when given valid parameters.
        """
        instrument_id = 4
        attribute_name = "attribute_string"
        expected_key = "instruments:4:attribute_string"
        result = redis_interface.RedisInterface._build_base_attribute_key(instrument_id, attribute_name)

        self.assertEqual(result, expected_key, "Built key '%s' does not match expected string '%s'."
                         % (result, expected_key))

    def test_build_base_attribute_key_function_with_table_name_succeeds_with_valid_input(self):
        """Tests that the _build_base_attribute_key function with the 'table_name' parameter builds the expected key
        when given valid parameters.
        """
        instrument_id = 4
        attribute_name = "attribute_string"
        table_name = "table_string"
        expected_key = "instruments:4:table_string:attribute_string"
        result = redis_interface.RedisInterface._build_base_attribute_key(instrument_id, attribute_name,
                                                                          table_name=table_name)

        self.assertEqual(result, expected_key, "Built key '%s' does not match expected string '%s'."
                         % (result, expected_key))

    def test_create_clean_integer_function_retursn_5_when_given_5_as_a_string(self):
        """Tests that the _create_clean_integer function returns the integer 5 when passed the string '5'

        """
        integer_string = "5"
        expected_result = 5
        result = redis_interface.RedisInterface._create_clean_integer(integer_string)

        self.assertIsInstance(result, int, "Result is not an instance of an integer.")
        self.assertEqual(result, expected_result, "Expected the converted integer %s. Got %s."
                         % (expected_result, result))

    def test_create_clean_integer_function_returns_none_when_given_invalid_string(self):
        """Tests that the _create_clean_integer function, when run with an invalid input (un-convertible
        string) will return None.

        """
        non_integer_string = "non_integer_string"
        result = redis_interface.RedisInterface._create_clean_integer(non_integer_string)

        self.assertIs(result, None, "Expected a 'None' return. Got '%s' instead'" % result)
