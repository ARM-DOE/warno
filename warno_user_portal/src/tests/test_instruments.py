import flask
import mock
import requests
from flask.ext.testing import TestCase

from UserPortal import instruments
from UserPortal import views

from WarnoConfig import database
from WarnoConfig.models import Instrument, InstrumentLog, Site, InstrumentDataReference

class test_instruments(TestCase):

    render_templates = False

    def setUp(self):
        database.db_session = mock.Mock()

    def create_app(self):
        views.app.config['TESTING'] = True
        return views.app



    def test_list_instruments_returns_200_and_passes_mock_db_instruments_as_context_variable_using_correct_template(self):
        # SQLAlchemy turns our previous testing methodology fairly brittle/bulky
        db_return = mock.Mock()
        db_return.id = 0
        db_return.name_short = 1
        db_return.name_long = 2
        db_return.type = 3
        db_return.vendor = 4
        db_return.description = 5
        db_return.frequency_band = 6
        db_return.site.site_id = 7
        db_return.site.name_short = 8
        database.db_session.query().order_by().all.return_value = [db_return]

        result = self.client.get('/instruments')
        self.assert200(result, "GET return is not '200 OK'")

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [Instrument in call[0] for call in calls], "'Instrument' class not called in a query")

        # Accessing context variable by name feels brittle, but it seems to be the only way
        context_instruments = self.get_context_variable('instruments')
        values = [value for key, value in context_instruments[0].iteritems()]
        self.assertTrue(0 in values, "Value '0' is not in the returned dictionary")
        self.assertTrue(1 in values, "Value '1' is not in the returned dictionary")
        self.assertTrue(2 in values, "Value '2' is not in the returned dictionary")
        self.assertTrue(8 in values, "Value '8' is not in the returned dictionary")
        self.assert_template_used('instrument_list.html')


    def test_method_get_on_new_instrument_returns_200_ok_and_passes_mock_db_sites_as_context_variable_using_correct_template(self):
        db_return = mock.Mock()
        db_return.id = 0
        db_return.name_short = 1
        database.db_session.query().all.return_value = [db_return]

        result = self.client.get('/instruments/new')
        self.assert200(result)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [Site in call[0] for call in calls], "'Site' class not called in a query")

        # Accessing context variable by name feels brittle, but it seems to be the only way
        context_sites = self.get_context_variable('sites')
        values = [value for key, value in context_sites[0].iteritems()]
        self.assertTrue(0 in values, "Value '0' is not in the returned dictionary")
        self.assertTrue(1 in values, "Value '1' is not in the returned dictionary")
        self.assert_template_used('new_instrument.html')


    def test_method_get_on_edit_instrument_returns_200_ok_and_passes_mock_db_sites_and_instrument_as_context_variables_using_correct_template(self):
        site_return = mock.Mock()
        site_return.id = 0
        site_return.name_short = 1
        instrument_return = mock.Mock()
        instrument_return.name_long= 2
        instrument_return.name_short = 3
        database.db_session.query().all.return_value = [site_return]
        database.db_session.query().filter().first.return_value = instrument_return

        result = self.client.get('/instruments/10/edit')
        self.assert200(result)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [Site in call[0] for call in calls], "'Site' class not called in a query")
        self.assertTrue(True in [Instrument in call[0] for call in calls], "'Instrument' class not called in a query")

        # Accessing context variable by name feels brittle, but it seems to be the only way
        context_sites = self.get_context_variable('sites')
        values = [value for key, value in context_sites[0].iteritems()]
        self.assertTrue(0 in values, "Value '0' is not in the returned sites dictionary")
        self.assertTrue(1 in values, "Value '1' is not in the returned sites dictionary")

        context_instrument = self.get_context_variable('instrument')
        values = [value for key, value in context_instrument.iteritems()]
        self.assertTrue(2 in values, "Value '2' is not in the returned instrument dictionary")
        self.assertTrue(3 in values, "Value '3' is not in the returned instrument dictionary")

        self.assert_template_used('edit_instrument.html')

    # TODO method post new instrument, post edit instrument
    # TODO method get generate_instrument_dygraph arguments?
    @mock.patch('psycopg2.connect')
    @mock.patch('UserPortal.instruments.db_recent_logs_by_instrument')
    @mock.patch('UserPortal.instruments.valid_columns_for_instrument')
    def test_method_get_on_instrument_when_id_is_23_calls_db_with_correct_arguments_and_returns_200(self, valid_columns, recent_logs, connect):
        recent_logs.return_value = [dict(time="01/01/2001 01:01:01", contents="contents", status="1",
                                    supporting_images="supporting_images", author="author")]
        valid_columns.return_value = ["column"]
        instrument_id = 23
        test_url = "/instruments/%s" % instrument_id
        result = self.client.get(test_url)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [Instrument in call[0] for call in calls], "'Instrument' class not called in a query")

        filter_calls = database.db_session.query().filter.call_args_list
        for index, call in enumerate(filter_calls):
            self.assertTrue("instrument" in str(call[0][0]), "'instrument' nowhere in call %s to query filter" % index)

        self.assert200(result, "GET return is not '200 OK'")
        self.assert_template_used('show_instrument.html')


    ### /instruments/instrument_id ###
    def test_method_delete_on_instrument_when_id_is_23_returns_200(self):
        instrument_id = 23
        test_url = "/instruments/%s" % instrument_id
        result = self.client.delete(test_url)
        self.assert200(result, "GET return is not '200 OK'")


    def test_db_delete_instrument_when_id_is_10_calls_db_with_correct_arguments(self):
        instrument_id = 10
        instruments.db_delete_instrument(instrument_id)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [Instrument in call[0] for call in calls], "'Instrument' class not called in a query")
        self.assertTrue(True in [InstrumentLog in call[0] for call in calls], "'InstrumentLog' class not called in a query")

        filter_calls = database.db_session.query().filter.call_args_list
        for index, call in enumerate(filter_calls):
            self.assertTrue("instrument" in str(call[0][0]), "'instrument' nowhere in call %s to query filter" % index)


    ### Database Helpers ###
    def test_db_get_instrument_references_calls_db_with_correct_arguments_and_returns_mock_db_results(self):
        db_return = ["return"]
        database.db_session.query().filter().all.return_value = db_return

        instrument_id = 5
        result = instruments.db_get_instrument_references(instrument_id)

        query_calls = database.db_session.query.call_args_list
        self.assertTrue(True in [InstrumentDataReference in call[0] for call in query_calls],
                        "'InstrumentDataReference' class not called in a query")

        filter_call = database.db_session.query().filter.call_args
        self.assertTrue("instrument" in str(filter_call[0][0]), "'instrument' nowhere in query filter call")

        self.assertEqual(db_return, result, "cursor.execute does not return the select result")


    def test_db_select_instrument_when_id_is_10_calls_db_with_correct_arguments_and_returns_mock_db_results(self):
        db_return = mock.Mock()
        db_return.id = 0
        db_return.name_short = 1
        db_return.name_long = 2
        db_return.type = 3
        db_return.vendor = 4
        db_return.description = 5
        db_return.frequency_band = 6
        db_return.site.site_id = 7
        db_return.site.name_short = 8
        db_return.site.latitude = 9
        db_return.site.longitude = 10

        database.db_session.query().filter().first.return_value = db_return
        instrument_id = 10
        result = instruments.db_select_instrument(instrument_id)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [Instrument in call[0] for call in calls], "'Instrument' class not called in a query")

        filter_calls = database.db_session.query().filter.call_args_list
        # The 'if len(call[0]) > 0'  prevents the generator from accessing the next level index [0][0] if there is no index
        # The 'True in [list]' means that this will be true if it is true for any call (decoupling call order/number)
        self.assertTrue(True in ["instrument" in str(call[0][0]) for call in filter_calls if len(call[0]) > 0],
                        "'instrument' nowhere in calls to query filter")

        values = [value for key, value in result.iteritems()]
        self.assertTrue(0 in values, "Value '0' is not in the returned dictionary")
        self.assertTrue(1 in values, "Value '1' is not in the returned dictionary")
        self.assertTrue(10 in values, "Value '10' is not in the returned dictionary")


    def test_db_recent_logs_by_instrument_when_id_is_15_and_maximum_number_is_default_calls_db_with_correct_arguments(self):
        log1 = mock.Mock()
        log2 = mock.Mock()
        log1.time = 0
        log1.contents = 1
        log1.status = 2
        log1.supporting_images = 3
        log1.author.name = 4
        log2.time = 10
        log2.contents = 11
        log2.status = 12
        log2.supporting_images = 13
        log2.author.name = 14
        db_return = [log1, log2]
        database.db_session.query().filter().order_by().limit().all.return_value = db_return

        # The parameters for the instrument id integer seem to be passed in a strange way for the 'filter' part
        # of a query, and I cannot find a way to access it from the tests.
        instrument_id = 15
        result = instruments.db_recent_logs_by_instrument(instrument_id)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [InstrumentLog in call[0] for call in calls], "'InstrumentLog' class not called in a query")

        filter_calls = database.db_session.query().filter.call_args_list
        # The 'if len(call[0]) > 0'  prevents the generator from accessing the next level index [0][0] if there is no index
        # The 'True in [list]' means that this will be true if it is true for any call (decoupling call order/number)
        self.assertTrue(True in ["log" in str(call[0][0]) for call in filter_calls if len(call[0]) > 0],
                        "'log' nowhere in calls to query filter")

        limit_calls = database.db_session.query().filter().order_by().limit.call_args_list
        self.assertTrue(True in [call[0] != None for call in limit_calls],
                        "No default maximum number in calls to query filter")

        values = [value for key, value in result[1].iteritems()]
        self.assertTrue(11 in values, "Value '11' is not in the returned dictionary for the second log")
        self.assertTrue(12 in values, "Value '12' is not in the returned dictionary for the second log")
        self.assertTrue(13 in values, "Value '13' is not in the returned dictionary for the second log")


    def test_db_recent_logs_by_instrument_when_id_is_15_and_maximum_number_is_11_calls_db_with_correct_arguments(self):
        log1 = mock.Mock()
        log2 = mock.Mock()
        log1.time = 0
        log1.contents = 1
        log1.status = 2
        log1.supporting_images = 3
        log1.author.name = 4
        log2.time = 10
        log2.contents = 11
        log2.status = 12
        log2.supporting_images = 13
        log2.author.name = 14
        db_return = [log1, log2]
        database.db_session.query().filter().order_by().limit().all.return_value = db_return

        # The parameters for the instrument id integer seem to be passed in a strange way for the 'filter' part
        # of a query, and I cannot find a way to access it from the tests.
        instrument_id = 15
        maximum_number = 11
        instruments.db_recent_logs_by_instrument(instrument_id, maximum_number)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [InstrumentLog in call[0] for call in calls], "'InstrumentLog' class not called in a query")

        filter_calls = database.db_session.query().filter.call_args_list
        # The 'if len(call[0]) > 0'  prevents the generator from accessing the next level index [0][0] if there is no index
        # The 'True in [list]' means that this will be true if it is true for any call (decoupling call order/number)
        self.assertTrue(True in ["log" in str(call[0][0]) for call in filter_calls if len(call[0]) > 0],
                        "'log' nowhere in calls to query filter")

        limit_calls = database.db_session.query().filter().order_by().limit.call_args_list
        self.assertTrue(True  in [maximum_number in call[0] for call in limit_calls],
                        "maximum_number '%s' nowhere in calls to query filter" % maximum_number)


    ### Helper Functions ###
    @mock.patch('UserPortal.instruments.db_get_instrument_references')
    def test_valid_columns_for_instrument_calls_db_with_correct_arguments_and_returns_expected_column_list(self, get_refs):
        expected_column_list = ["integer", "not_special_table"]
        # Each reference is a boolean specifying whether it is a 'special' table along with the name of the table
        ref1 = mock.Mock()
        ref2 = mock.Mock()
        ref1.special = True
        ref1.description = "special_table"
        ref2.special = False
        ref2.description = "not_special_table"
        references = [ref1, ref2]
        get_refs.return_value = references
        # Datetime should not be a valid data type and should not make it into results
        special_table_entries = [["integer", "integer"],["datetime", "datetime"]]
        database.db_session.execute().fetchall.return_value = special_table_entries
        instrument_id = 10
        result_column_list = instruments.valid_columns_for_instrument(instrument_id)
        executed_calls = database.db_session.execute.call_args_list

        self.assertTrue(expected_column_list[0] in result_column_list,
                        "First valid column string '%s' not returned in columns" % expected_column_list[0])
        self.assertTrue(expected_column_list[1] in result_column_list,
                        "Second valid column string '%s' not returned in columns" % expected_column_list[1])
        self.assertTrue("datetime" not in result_column_list, "Invalid column string 'datetime' in returned columns")

        # Second database execute expected to be performed on a 'special' table only
        self.assertTrue("FROM information_schema.columns" in executed_calls[1][0][0],
                        "cursor.execute never accesses 'information_schema.columns'")
        self.assertTrue("special_table" in str(executed_calls[1][0][1]),
                        "cursor.execute not called with 'special_table' table name")
