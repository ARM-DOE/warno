import datetime
import mock
import json
import os

from flask.ext.testing import TestCase
from flask.ext.fixtures import FixturesMixin

from UserPortal import instruments
from UserPortal import views
from WarnoConfig import config
from WarnoConfig import redis_interface
from WarnoConfig.models import db
from WarnoConfig.models import Instrument, InstrumentLog, Site, InstrumentDataReference, ValidColumn


@mock.patch("logging.Logger")
class TestInstruments(TestCase, FixturesMixin):
    """Contains tests for the UserPortal 'instruments' file."""
    render_templates = False
    db_cfg = config.get_config_context()['database']
    s_db_cfg = config.get_config_context()['s_database']
    TESTING = True

    # Fixtures are usually in warno-vagrant/data_store/data/WarnoConfig/fixtures
    # Note that, especially with this many different tables, the fixtures should be loaded in the proper order.
    # For example, in this case, instruments have foreign keys to sites, so it errors if sites have not yet been defined
    fixtures = ['sites.yml', 'users.yml', 'instruments.yml', 'instrument_data_references.yml', 'event_codes.yml',
                'instrument_logs.yml', 'valid_columns.yml', 'prosensing_paf.yml', 'events_with_value.yml']

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_app(self):
        views.app.config['TESTING'] = True
        views.app.config['FIXTURES_DIRS'] = [os.environ.get('FIXTURES_DIR')]
        views.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%s:%s@%s:%s/%s' % (self.db_cfg['DB_USER'],
                                                                                       self.s_db_cfg['DB_PASS'],
                                                                                       self.db_cfg['DB_HOST'],
                                                                                       self.db_cfg['DB_PORT'],
                                                                                       self.db_cfg['TEST_DB_NAME'])

        FixturesMixin.init_app(views.app, db)

        return views.app

    def test_list_instruments_passes_fixture_instruments_using_correct_template(self, logger):
        """A 'GET' request to '/instruments' returns a response of '200 OK' and then  renders 'instrument_list.html',
        passing in the list of database instruments as a context variable 'instruments'."""
        get_request_return = self.client.get('/instruments')
        self.assert200(get_request_return, "GET return is not '200 OK'")

        # Accessing context variable by name feels brittle, but it seems to be the only way
        # Check that test fixture data is passed by context as expected
        context_instruments = self.get_context_variable('instruments')

        self.assertTrue('Test Vendor 1' in context_instruments[0]['vendor'],
                        "'Test Vendor 1' is not in the 'vendor' field for the first instrument.")
        self.assertTrue('TESTSIT1' in context_instruments[0]['location'],
                        "'TESTSIT1' is not in the 'location' field for the first instrument.")
        self.assertTrue('Test Vendor 2' in context_instruments[1]['vendor'],
                        "'Test Vendor 2' is not in the 'vendor' field for the second instrument.")
        self.assertTrue('TESTSIT2' in context_instruments[1]['location'],
                        "'TESTSIT2' is not in the 'location' field for the second instrument.")
        self.assert_template_used('instrument_list.html')

    @mock.patch("UserPortal.instruments.current_user")
    def test_method_get_on_new_instrument_passes_fixture_sites_using_correct_template(self, current_user, logger):
        """A 'GET' request to '/instruments/new' returns a response of '200 OK' and then  renders 'new_instrument.html',
        passing in the list of database sites as a context variable 'sites'."""
        # Mocks an authorized user
        current_user.is_anonymous = False
        current_user.authorizations = "engineer"

        get_request_return = self.client.get('/instruments/new')
        self.assert200(get_request_return)

        # Accessing context variable by name feels brittle, but it seems to be the only way
        # Fixture sites should be passed as expected
        context_sites = self.get_context_variable('sites')
        self.assertTrue('TESTSIT1' in context_sites[0]['name'],
                        "'TESTSIT1' is not in the 'name' field for the first context variable site.")
        self.assertEqual(1, context_sites[0]['id'], "First context variable site does not have the correct id of '1'")
        self.assertTrue('TESTSIT2' in context_sites[1]['name'],
                        "'TESTSIT2' is not in the 'name' field for the second context variable site.")
        self.assert_template_used('new_instrument.html')

    @mock.patch("UserPortal.instruments.current_user")
    def test_method_get_on_edit_instrument_with_id_2_passes_fixture_sites_and_correct_instrument_as_context_variables_using_correct_template(self, current_user, logger):
        """A 'GET' request to '/instruments/<instrument_id>/edit' returns a response of '200 OK' and then  renders
        'edit_instrument.html', passing in the list of database sites and the instrument with an id matching
        'instrument_id' as context variables 'sites' and 'instrument' respectively."""
        # Mocks an authorized user
        current_user.is_anonymous = False
        current_user.authorizations = "engineer"

        get_request_return = self.client.get('/instruments/2/edit')
        self.assert200(get_request_return)

        # Accessing context variable by name feels brittle, but it seems to be the only way
        # Fixture sites should be passed as expected
        context_sites = self.get_context_variable('sites')
        self.assertTrue("TESTSIT1" in context_sites[0]['name'],
                        "'TESTSIT1' is not in the first context variable site.")
        self.assertTrue("TESTSIT2" in context_sites[1]['name'],
                        "'TESTSIT1' is not in the second context variable site.")

        # Second fixture instrument should be passed
        context_instrument = self.get_context_variable('instrument')
        self.assertTrue('TESTINS2' in context_instrument['name_short'],
                        "'TESTINS2' is not in the 'name_short' field for the context variable instrument.")
        self.assertTrue('Test Description 2' in context_instrument['description'],
                        "'Test Description 2' is not in the 'description' field for the context variable instrument.")

        self.assert_template_used('edit_instrument.html')

    # TODO method post new instrument, post edit instrument
    # TODO method get generate_instrument_dygraph arguments?
    @mock.patch('UserPortal.instruments.db_recent_logs_by_instrument')
    @mock.patch('UserPortal.instruments.valid_columns_for_instrument')
    def test_method_get_on_instrument_when_id_is_2_calls_db_with_correct_arguments_and_returns_200(self, valid_columns, recent_logs, logger):
        """A 'GET' request on '/instruments/<instrument_id>' returns a response of '200 OK' and passes various context
        variables to the template 'show_instrument.html'.  Context variables: 'instrument' as the database information
        for the instrument with id matching 'instrument_id', 'recent_logs' as he list of the most recent instrument logs
        for the instrument, 'status' being the status of the instrument indicated by the most recent log, and 'columns'
        being the list of valid columns to graph."""
        recent_logs.return_value = [dict(time="01/01/2001 01:01:01", contents="contents", status="1",
                                    supporting_images="supporting_images", author="author")]
        valid_columns_return = ["column"]
        valid_columns.return_value = valid_columns_return
        instrument_id = 2

        test_url = "/instruments/%s" % instrument_id
        result = self.client.get(test_url)

        context_instrument = self.get_context_variable('instrument')
        context_recent_logs = self.get_context_variable('recent_logs')
        context_status = self.get_context_variable('status')
        context_columns = self.get_context_variable('columns')

        # Second fixture instrument should be acquired and passed back as a context variable
        self.assertTrue('TESTINS2' in context_instrument['abbv'],
                        "'TESTINS2' is not in the 'abbv' field for the context variable instrument.")
        self.assertTrue('Test Description 2' in context_instrument['description'],
                        "'Test Description 2' is not in the 'description' field for the context variable instrument.")

        # Confirm that the status for the returned log has been converted from code to text
        self.assertEqual('OPERATIONAL', context_recent_logs[0]['status'],
                         "'status' field for the most recent log was not properly changed from 1 to 'OPERATIONAL'.")
        # Status context variable should also be set to 'OPERATIONAL'
        self.assertEqual('OPERATIONAL', context_status, "'status' context variable was not 'OPERATIONAL'")

        self.assertListEqual(valid_columns_return, context_columns,
                             "Valid columns were not passed properly as a context variable")

        self.assert200(result, "GET return is not '200 OK'")
        self.assert_template_used('show_instrument.html')

    # /instruments/instrument_id
    def test_method_delete_on_instrument_when_id_is_2_returns_200_and_reduces_count_by_1(self, logger):
        """A 'DELETE' request on '/instruments/<instrument_id>' returns a response of '200 OK' and reduces the total
        count of instruments in the database by 1."""
        instrument_id = 2
        test_url = "/instruments/%s" % instrument_id

        # Instrument count after delete should be reduced by one
        count_before = db.session.query(Instrument).count()
        delete_request_return = self.client.delete(test_url)
        self.assert200(delete_request_return, "GET return is not '200 OK'")
        count_after = db.session.query(Instrument).count()

        self.assertEqual(count_before - 1, count_after, "The count of instruments was not decremented by exactly one.")

    def test_db_delete_instrument_when_id_is_2_removes_the_entry_with_id_of_2(self, logger):
        """A 'DELETE' request on '/instruments/<instrument_id>' returns a response of '200 OK' and removes the
        instrument entry from the database with an id matching 'instrument_id'."""
        instrument_id = 2
        instruments.db_delete_instrument(instrument_id)

        after_delete_count = db.session.query(Instrument).filter(Instrument.id == instrument_id).count()
        self.assertEqual(after_delete_count, 0, "The Instrument with id %s was not deleted." % instrument_id)

    @mock.patch('redis_interface.RedisInterface')
    def test_recent_values_for_instrument_id_1_with_valid_key_antenna_humidity_returns_expected_object(self, interface, logger):
        instrument_id = 1
        key = "antenna_humidity"
        test_url = "/recent_values?instrument_id=%s&keys=%s" % (instrument_id, key)
        result = self.client.get(test_url)
        result_object = result.json

        # Expected values are defined in the fixtures
        expected_value = 75.0
        expected_time = "2001-01-01T01:01:01"

        # There should only be one key returned, so every access is index [0]
        self.assertEqual(1, len(result_object),
                         "Expected returned object to have a length of 1. Length is '%s'." % len(result_object))
        self.assertEqual(key, result_object[0]["key"],
                         "The returned object's key did not match the requested key '%s'." % key)
        self.assertEqual(expected_value, result_object[0]["data"]["value"],
                         "The returned objects first entry's data did not have a value of '%s'." % expected_value)
        self.assertEqual(expected_time, result_object[0]["data"]["time"],
                         "The returned objects first entry's data did not have a time of '%s'." % expected_time)

    @mock.patch('redis_interface.RedisInterface')
    def test_recent_values_for_instrument_id_1_with_invalid_key_antenna_temp_returns_empty_object(self, interface, logger):
        instrument_id = 1
        key = "antenna_temp"
        test_url = "/recent_values?instrument_id=%s&keys=%s" % (instrument_id, key)
        result = self.client.get(test_url)
        result_object = result.json

        # There should only be no keys returned, because the key is not in 'valid_columns' in the fixtures
        self.assertEqual(0, len(result_object),
                         "Expected returned object to have a length of 0. Length is '%s'." % len(result_object))


    # Database Helpers
    def test_db_get_instrument_references_returns_the_instrument_data_references_for_the_correct_instrument(self, logger):
        """Calling the 'db_get_instrument_references' function returns all the instrument data references for the
        instrument with an id matching 'instrument_id'."""
        instrument_id = 1
        function_result = instruments.db_get_instrument_references(instrument_id)
        db_result = db.session.query(InstrumentDataReference).filter(InstrumentDataReference.instrument_id ==
                                                                     instrument_id).all()

        self.assertListEqual(function_result, db_result,
                             "Returned InstrumentDataReferences do not match database query.")
        # 'matches' will only have a 'True' in it if  the expected description matches one of the returned descriptions
        matches = [True if res.description == 'prosensing_paf' else False for res in function_result]
        self.assertIn(True, matches, "No reference's 'description' does not matches the fixture's 'prosensing_paf'.")

    def test_db_select_instrument_when_id_is_2_returns_the_correct_instrument_dictionary(self, logger):
        """Calling the 'db_select_instrument function returns a dictionary containing the database information for the
        instrument with an id matching 'instrument_id'."""
        instrument_id = 2
        function_return = instruments.db_select_instrument(instrument_id)
        db_result = db.session.query(Instrument).filter(Instrument.id == instrument_id).first()

        self.assertEqual(db_result.name_short, function_return['abbv'],
                         "The function result's 'abbv' field does not match 'name_short' of the instrument with id 2.")
        self.assertEqual(function_return['id'], instrument_id,
                         "The function result's 'id' field does not match the id it was called with.")

    def test_db_recent_logs_by_instrument_when_id_is_1_returns_logs_in_the_correct_order(self, logger):
        """Calling the 'db_recent_logs_by_instrument' function returns the most recent instrument logs for the
        instrument with an id matching 'instrument_id'.  These logs are ordered by the 'time' field, with the greatest
        time being the most recently created log, which is at the head of the list."""
        # The parameters for the instrument id integer seem to be passed in a strange way for the 'filter' part
        # of a query, and I cannot find a way to access it from the tests.
        instrument_id = 1
        function_return = instruments.db_recent_logs_by_instrument(instrument_id)

        # Assert the logs are in the correct order (later time first)
        self.assertTrue(function_return[0]['time'] > function_return[1]['time'],
                        "First log's time is not more recent than the second.")
        self.assertEqual(function_return[0]['contents'], "Log 2 Contents",
                         "Most recent log's 'contents' are not the expected 'Log 2 Contents'")

    def test_db_recent_logs_by_instrument_when_id_is_1_and_maximum_number_is_1_limits_count_of_returned_logs_to_1(self, logger):
        """Calling the 'db_recent_logs_by_instrument' function with a specified maximum number of logs as 1 reduces the
        number of returned instrument logs to a maximum count of 1."""
        instrument_id = 1
        maximum_number = 1
        result = instruments.db_recent_logs_by_instrument(instrument_id, maximum_number)

        self.assertEqual(len(result), maximum_number,
                         "Number of logs returned does not match given 'maximum_number' parameter.")

    # Helper Functions
    def test_valid_columns_for_instrument_returns_expected_column_list_for_both_special_and_non_special_references(self, logger):
        """Calling the 'valid_columns_for_instrument' function returns a list of the columns available to graph for the
        instrument with the id matching 'instrument_id'.  This test checks that some expected columns from  the fixtures
        are available as expected."""
        instrument_id = 1
        returned_column_list = instruments.valid_columns_for_instrument(instrument_id)

        # Check that column list contains the non_special entry as well as some prosensing_paf specific entries
        self.assertIn("not_special", returned_column_list, "'not_special' reference is not in returned column list.")
        self.assertIn("packet_id", returned_column_list, "prosensing_paf 'packet_id' not in returned column list.")
        self.assertIn("antenna_humidity", returned_column_list,
                      "prosensing_paf 'antenna_humidity' not in returned column list.")

    def test_update_valid_columns_for_instrument_successfully_adds_expected_entries(self, logger):
        """Calling the 'update_valid_columns_for_instrument' function updates the list of valid columns for the
        instrument with an id matching 'instrument_id'.  The count of valid columns after the function is called should
        be greater than the count before the function was called, and there should be some expected values in the set
        of valid columns."""
        instrument_id = 1
        pre_function_column_count = db.session.query(ValidColumn).count()
        _ = instruments.update_valid_columns_for_instrument(instrument_id)
        post_function_column_count = db.session.query(ValidColumn).count()

        db_valid_columns = db.session.query(ValidColumn).filter(ValidColumn.instrument_id == instrument_id).all()
        result_column_list = [column.column_name for column in db_valid_columns]

        self.assertTrue(pre_function_column_count < post_function_column_count,
                        "The count of valid columns did not increase")
        self.assertIn("packet_id", result_column_list, "prosensing_paf 'packet_id' not in returned valid column list.")
        self.assertIn("antenna_temp", result_column_list,
                      "prosensing_paf 'antenna_temp' not in returned valid column list.")
        self.assertNotIn("ad_skip_count", result_column_list,
                         "prosensing_paf 'ad_skip_count' in returned valid column list, even though it shouldn't.")

    def test_synchronize_sort_correctly_sorts_3_simple_data_sets_into_expected_output_format(self, logger):
        """Test that three simple data sets are correctly sorted and used to construct a return value.  The explanation
        of the sorting algorithm is a little long, so please see the function's docstring for the details. The test
        compares the expected output to the actual output."""
        input_data_0 = dict(data=[(datetime.datetime.strptime("2015-05-11 02:00", "%Y-%m-%d %H:%M"), 03),
                                  (datetime.datetime.strptime("2015-05-11 01:30", "%Y-%m-%d %H:%M"), 02),
                                  (datetime.datetime.strptime("2015-05-11 01:00", "%Y-%m-%d %H:%M"), 01)])
        input_data_1 = dict(data=[(datetime.datetime.strptime("2015-05-11 03:00", "%Y-%m-%d %H:%M"), 13),
                                  (datetime.datetime.strptime("2015-05-11 02:30", "%Y-%m-%d %H:%M"), 12),
                                  (datetime.datetime.strptime("2015-05-11 02:00", "%Y-%m-%d %H:%M"), 11)])
        input_data_2 = dict(data=[(datetime.datetime.strptime("2015-05-11 02:30", "%Y-%m-%d %H:%M"), 23),
                                  (datetime.datetime.strptime("2015-05-11 02:00", "%Y-%m-%d %H:%M"), 22),
                                  (datetime.datetime.strptime("2015-05-11 01:00", "%Y-%m-%d %H:%M"), 21)])

        expected_return = [[datetime.datetime.strptime("2015-05-11 01:00", "%Y-%m-%d %H:%M"),   01, None,   21],
                           [datetime.datetime.strptime("2015-05-11 01:30", "%Y-%m-%d %H:%M"),   02, None, None],
                           [datetime.datetime.strptime("2015-05-11 02:00", "%Y-%m-%d %H:%M"),   03,   11,   22],
                           [datetime.datetime.strptime("2015-05-11 02:30", "%Y-%m-%d %H:%M"), None,   12,   23],
                           [datetime.datetime.strptime("2015-05-11 03:00", "%Y-%m-%d %H:%M"), None,   13, None]]

        input_dictionary = {0: input_data_0, 1: input_data_1, 2: input_data_2}

        returned_list = instruments.synchronize_sort(input_dictionary)

        self.assertListEqual(returned_list, expected_return, "The expected result list of synchronize_sort and the "
                                                             "actual list returned do not match.")

    def test_iso_first_elements_changes_the_datetime_object_first_element_of_a_list_to_iso_format_in_place(self, logger):
        """Tests that the first element of a list is properly converted from a python datetime object into an ISO 8601
        formatted string in place."""
        input_list = [datetime.datetime.strptime("2015-01-01 01:30:30", "%Y-%m-%d %H:%M:%S"), 0, 1, 2]
        expected_list = ['2015-01-01T01:30:30', 0, 1, 2]

        # Should update input list in place
        instruments.iso_first_element(input_list)

        self.assertListEqual(input_list, expected_list, "The updated input list and the expected list do not match.")
