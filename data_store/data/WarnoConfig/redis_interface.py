from __future__ import print_function

import datetime
import redis
import pytz

import ciso8601


class RedisInterface:
    MAX_ENTRIES = 21600  # 15 days at 1/Min
    MAX_INDEX = MAX_ENTRIES - 1
    _r = None

    def __init__(self, host='localhost', port=6379):
        """Initialize RedisInterface by connecting to a Redis server before any other actions.

        Parameters
        ----------

        host: string, optional
            The hostname of the Redis server to connect to. Default is 'localhost'.

        port: integer, optional
            The port of the Redis server to connect to. Default Redis port is 6379.

        """
        self._r = redis.Redis(host, port)

    def get_most_recent_value_for_attribute(self, instrument_id, attribute, table_name=None):
        """Return the most recent value for each of the given 'attribute' for the specified 'instrument_id'. If
        'table_name' is defined, it will assume the attribute is organized under the specified name.


        Parameters
        ----------

        instrument_id: integer
            The database id for the particular instrument.

        attribute: string
            The name of the particular attribute, such as 'temperature' or 'voltage'.

        table_name: string, optional
            Default None. The name of a table the attribute is grouped under.

        Returns
        -------

        results: list of dictionaries
            Returns the most recent value/time pair for 'attribute'.  Each returned element is of the form
            '{ "time": <time of value>, "value": <the value itself> }'

        """

        if not isinstance(attribute, str) and not isinstance(attribute, unicode):
            print("Attribute must be a string.")
            return {}

        clean_instrument_id = self._create_clean_integer(instrument_id,
                                                         "Could not convert instrument ID to valid integer.")
        if not clean_instrument_id:
            return {}

        # If the instrument id or an attribute does not match the Redis database entries, the return for that
        # id/attribute combination will be invalid and will return an empty entry.

        result = {}
        # If the attribute is part of a table organization, slight modification to the access keys.
        # Either way, get the list of times and list of values for the attribute, returning the most recent pair.
        if table_name:
            db_time_key = self._build_table_time_key(clean_instrument_id, table_name)

            db_base_key = self._build_base_attribute_key(clean_instrument_id, attribute, table_name=table_name)
            db_value = self._r.lindex(db_base_key + ":value", 0)
            db_time = self._r.lindex(db_time_key, 0)
        else:
            db_base_key = self._build_base_attribute_key(clean_instrument_id, attribute)
            db_value = self._r.lindex(db_base_key + ":value", 0)
            db_time = self._r.lindex(db_base_key + ":time", 0)

        if db_value and db_time:
            if (len(db_value) > 0) and (len(db_time) > 0):
                result = dict(time=db_time, value=db_value)

        return result

    def get_values_for_attribute_between_times(self, instrument_id, attribute, start_time, end_time, table_name=None):
        """Return the list of all values for the specified 'attribute' for the specified 'instrument_id' with times
        between the given 'start_time' and 'end_time'. If 'table_name' is defined, it will assume the attribute is
        organized under the specified name.


        Parameters
        ----------

        instrument_id: integer
            The database id for the particular instrument.

        attribute: string
            The name of the particular attribute, such as 'temperature' or 'voltage'.

        start_time: datetime.datetime
            The start time (UTC) to compare against.  Expected to be already translated into UTC

        end_time: datetime.datetime
            The end time (UTC) to compare against.  Expected to be already translated into UTC

        table_name: string, optional
            Default None. The name of a table the attribute is grouped under.

        Returns
        -------

        result: list of dictionaries
            Returns the list of entries between the given 'start_time' and 'end_time'.  Each returned element is of the
            form '{ "time": <time of value>, "value": <the value itself> }'

        """
        if end_time < start_time:
            # The times are input incorrectly.  An end time before a start time is a mistake
            print("Start time must be before or the same as the end time.")
            return []

        clean_instrument_id = self._create_clean_integer(instrument_id,
                                                         "Could not convert instrument ID to valid integer.")

        if not clean_instrument_id:
            return []

        if table_name:
            db_time_key = self._build_table_time_key(instrument_id, table_name)
            db_base_key = self._build_base_attribute_key(instrument_id, attribute, table_name=table_name)
            db_times = self._r.lrange(db_time_key, 0, self.MAX_INDEX)
            db_values = self._r.lrange(db_base_key + ":value", 0, self.MAX_INDEX)
        else:
            db_base_key = self._build_base_attribute_key(clean_instrument_id, attribute)
            db_times = self._r.lrange(db_base_key + ":time", 0, self.MAX_INDEX)
            db_values = self._r.lrange(db_base_key + ":value", 0, self.MAX_INDEX)
        db_time_value_pairs = zip(db_times, db_values)

        start_time_unaware = start_time.replace(tzinfo=None)
        end_time_unaware = end_time .replace(tzinfo=None)

        result = [(entry_time, entry_value) for entry_time, entry_value in db_time_value_pairs
                  if (ciso8601.parse_datetime(entry_time) >= start_time_unaware)
                  and (ciso8601.parse_datetime(entry_time) <= end_time_unaware)]

        return result

    def add_values_for_attribute(self, instrument_id, attribute, given_times, values):
        """ Adds values to the Redis database for an attribute of an instrument. Values and their times are expected to
        be, for all intents and purposes, paired together.  For example, if the times and values given are lists, the
        time at index 5 of the 'times' list is expected to match the value at index 5 of the 'values' list.  Naturally,
        this means that the two lists are expected to be the same length.  The times and values given are expected to be
        given in the order from oldest time to newest time.  After the entries are inserted, if the length of the lists
        exceed MAX_LENGTH, the oldest values (assuming all insertions have been ordered correctly) will be trimmed out.

        Parameters
        ----------
        instrument_id: integer
            The database id for the particular instrument.

        attribute: string
            The name of the particular attribute, such as 'temperature' or 'voltage'.

        given_times: datetime.datetime or list of datetime.datetimes
            List of times (UTC) corresponding to the list of 'values' to be added to the database.  Should be the same
            length as the list of 'values', and should be ordered from oldest time to most recent time.

        values: integer, float, string, or list of any of these types
            List of values corresponding to the list of 'given_times' to be added to the database.  Should be the same
            length as the list of 'given_times', and should be ordered from oldest time to most recent time.

        """
        # This makes a possibly dangerous assumption that both lists are paired and ordered correctly, oldest to newest

        clean_instrument_id = self._create_clean_integer(instrument_id,
                                                         "Could not convert instrument ID to valid integer.")
        # TODO Add error handling for assertions?
        if not clean_instrument_id:
            return

        # Force non-list arguments to be lists, which homogenizes the rest of the algorithm.
        if not isinstance(given_times, list):
            given_time_list = [given_times]
        else:
            given_time_list = given_times

        if not isinstance(values, list):
            value_list = [values]
        else:
            value_list = values

        # The time list and value list should end up the same length, because they are supposed to represent pairs
        # Might be better to convert this into accepting tuples eventually.  I'm not sold on either method.
        if not len(given_time_list) == len(value_list):
            return

        for given_time in given_time_list:
            if not isinstance(given_time, datetime.datetime):
                return

        # Entries are much faster to parse back out if they are stored in ISO 8601 format.
        iso_format_times = [given_time.isoformat() for given_time in given_time_list]

        base_key = self._build_base_attribute_key(clean_instrument_id, attribute)
        time_key = "".join([base_key, ":time"])
        value_key = "".join([base_key, ":value"])

        # Add the entries to Redis, but assure that the length of each list never exceeds MAX_INDEX.
        self._r.lpush(time_key, *iso_format_times)
        self._r.lpush(value_key, *value_list)

        self._r.ltrim(time_key, 0, self.MAX_INDEX)
        self._r.ltrim(value_key, 0, self.MAX_INDEX)

    def add_value_set_for_table_attributes(self, instrument_id, attributes, given_time, values, table_name):
        """Adds values to the Redis database for an attribute of an instrument, organized by a given table_name.
        Supposed to mirror traditional database organization of attributes as columns of a table.  A full set of values
        is expected to be mapped to one time.  For example, for one time, there may be a value for 100 different
        attributes. The list of attribute names is expected to be in the same order as the list of attributes.  For
        example, if the second attribute in 'attributes' is "temperature" and the second value in 'values' is 10, this
        means the "temperature" value at the given time is "10".  After the entries are inserted, if the length of any
        of the Redis lists exceeds MAX_LENGTH, the oldest values (assuming all insertions have been ordered correctly)
        will be trimmed out.

        All calls of this function should try to use the same list of attributes every time for the same table.  The way
        this interface uses lists will have multiple lists implied to match the same 'time' list (e.g. entry 5 in
        'time' is associated to entry 5 of 'temp', entry 5 of 'voltage', etc).  However, because on Redis these are
        being pushed to their own lists, if one call of the function pushes a time and 2 attributes, but the second call
        only pushes a time and one of the attributes, the second attribute will not have a value pushed to it, meaning
        that the time list and this attribute are not all in sync, possibly causing issues.  If no value is available at
        the time, it would be best to just push a placeholder value, such as "NULL".

        Parameters
        ----------
        instrument_id: integer
            The database id for the particular instrument.

        attributes: list of strings
            The name of the particular attributes, such as 'temperature' or 'voltage', that is mapped to the list of
            'values'.  The list of attributes must be the same length as the list of 'values'

        given_time: datetime.datetime
            Time (UTC) corresponding to the set of 'attributes' and their 'values' to be added to the database.

        values: List of any integers, floats, or strings
            List of values corresponding to the list of 'given_times' to be added to the database, mapped to the list of
            corresponding 'attributes'.  The list of values must be the same length as the list of 'attributes'.

        table_name: string
            The name of the "table" the attributes are organized under.  In reality only effects the building of the key
            for the attributes to help keep them organized.

        """
        # One time, and one attribute per value

        clean_instrument_id = self._create_clean_integer(instrument_id,
                                                         "Could not convert instrument ID to valid integer.")
        # TODO Add error handling for assertions?
        if not clean_instrument_id:
            return

        if not isinstance(values, list):
            value_list = [values]
        else:
            value_list = values

        if not isinstance(attributes, list):
            attribute_list = [attributes]
        else:
            attribute_list = attributes
        # Each attribute should correspond to a value
        if not len(attribute_list) == len(value_list):
            return

        if not isinstance(given_time, datetime.datetime):
            return

        # Entries are much faster to parse back out if they are stored in ISO 8601 format.
        iso_format_time = given_time.isoformat()

        time_key = self._build_table_time_key(instrument_id, table_name)
        self._r.lpush(time_key, iso_format_time)
        self._r.ltrim(time_key, 0, self.MAX_INDEX)

        keys = []
        for index in xrange(0, len(attribute_list)):
            base_key = self._build_base_attribute_key(clean_instrument_id, attribute_list[index], table_name=table_name)
            value_key = "".join([base_key, ":value"])
            keys.append(value_key)

            # Add the entries to Redis, but assure that the length of each list never exceeds MAX_INDEX.
            self._r.lpush(value_key, value_list[index])
            self._r.ltrim(value_key, 0, self.MAX_INDEX)

    def bulk_insert_values_for_table_attributes(self, instrument_id, attributes, given_times, values, table_name=None):
        """Adds values to the Redis database for an attribute of an instrument, organized by a given table_name.
        Supposed to mirror traditional database organization of attributes as columns of a table.  A full set of values
        is expected to be mapped to one time.  For example, for one time, there may be a value for 100 different
        attributes. The list of attribute names is expected to be in the same order as the list of attributes.  For
        example, if the second attribute in 'attributes' is "temperature" and the second value in 'values' is 10, this
        means the "temperature" value at the given time is "10".  After the entries are inserted, if the length of any
        of the Redis lists exceeds MAX_LENGTH, the oldest values (assuming all insertions have been ordered correctly)
        will be trimmed out.

        All calls of this function should try to use the same list of attributes every time for the same table.  The way
        this interface uses lists will have multiple lists implied to match the same 'time' list (e.g. entry 5 in
        'time' is associated to entry 5 of 'temp', entry 5 of 'voltage', etc).  However, because on Redis these are
        being pushed to their own lists, if one call of the function pushes a time and 2 attributes, but the second call
        only pushes a time and one of the attributes, the second attribute will not have a value pushed to it, meaning
        that the time list and this attribute are not all in sync, possibly causing issues.  If no value is available at
        the time, it would be best to just push a placeholder value, such as "NULL".

        This function assumes that values will be given as a two dimensional list, with the first dimension being the
        list of 'rows' for the table, each one corresponding to a time in 'given_times'. Therefore, the length of the
        first dimension of this list should match the length of 'given_times'.  For each of these rows, the list of
        values maps to the list of 'attributes' (each one supposed to represent an entry into one of the 'columns' of a
        table. The length of each of these rows should be the length of the 'attributes' list, otherwise it may throw an
        error.

        Parameters
        ----------
        instrument_id: integer
            The database id for the particular instrument.

        attributes: list of strings
            The name of the particular attributes, such as 'temperature' or 'voltage', that is mapped to the list of
            'values'.  The list of attributes must be the same length as each second dimension list of 'values'

        given_times: datetime.datetime
            List of times (UTC), each corresponding to the set of 'attributes' and their 'values' to be added to the
            database. The list of times must be the same length as the first dimension list of 'values', each time
            corresponding to its own of values.  The list of times should be ordered from oldest to most recent.

        values: List of lists of any integers, floats, or strings
            Two dimensional list, with the first dimension being the
            list of 'rows' for the table, each one corresponding to a time in 'given_times'. Therefore, the length of
            the first dimension of this list should match the length of 'given_times'.  For each of these rows, the list
            of values maps to the list of 'attributes' (each one supposed to represent an entry into one of the
            'columns' of a table. The length of each of these rows should be the length of the 'attributes' list,
            otherwise it may throw an error.

            The order of the first dimension list should match the list of 'given_times'.  It should go from oldest time
            to most recent time.

        table_name: string, optional
            Default: None. The name of the "table" the attributes are organized under.  In reality only effects the
            building of the key for the attributes to help keep them organized.  If this is None, the algorithm runs
            differently in how it inserts values, attempting to avoid the tabular organization.

        """
        # This makes a possibly dangerous assumption that every input list is ordered correctly, oldest to newest

        clean_instrument_id = self._create_clean_integer(instrument_id,
                                                         "Could not convert instrument ID to valid integer.")

        # TODO Add error handling for assertions?
        if not clean_instrument_id:
            return

        if not isinstance(given_times, list):
            given_time_list = [given_times]
        else:
            given_time_list = given_times

        if not isinstance(values, list):
            value_list = [values]
        else:
            value_list = values

        # Each element of 'attributes' is supposed to correspond to a list in 'values'.  If the lengths don't match,
        # something is wrong.
        if not (len(attributes) == len(values)):
            return

        # Every element must be a valid python datetime, or the function finishes without altering the Redis database.
        for given_time in given_time_list:
            if not isinstance(given_time, datetime.datetime):
                return

        # Entries are much faster to parse back out if they are stored in ISO 8601 format.
        iso_format_times = [given_time.isoformat() for given_time in given_time_list]

        # By executing commands in chunks using piping, the overall transactions/second is much greater.
        pipe = self._r.pipeline()

        # If the table name is specified, will group attributes and values as if each row was a column in a table.
        # This allows the program to assume that one list of times represents all entries.  If it is not organized this
        # way, it instead makes a copy of the time lis for each attribute.
        if table_name:
            time_key = self._build_table_time_key(clean_instrument_id, table_name)
            # Save the list of times to Redis, but assure that the length of the list never exceeds MAX_INDEX.
            pipe.lpush(time_key, *iso_format_times)
            pipe.ltrim(time_key, 0, self.MAX_INDEX)
            # Checks each value row's first element. If it is "NULL", it is worth checking if the whole row is "NULL".
            check_nulls_for_row = [True if row[0] == "NULL" else False for row in value_list]
            for index in xrange(0, len(attributes)):
                attribute = attributes[index]
                all_nulls_in_row = False

                if check_nulls_for_row[index]:
                    if False not in [True if value == "NULL" else False for value in value_list[index]]:
                        all_nulls_in_row = True

                base_key = self._build_base_attribute_key(clean_instrument_id, attribute, table_name=table_name)
                value_key = "".join([base_key, ":value"])

                # If every entry in a row is "NULL", don't bother adding anything to the database.
                if not all_nulls_in_row:
                    # Add the entries to Redis, but assure that the length of each list never exceeds MAX_INDEX.
                    pipe.lpush(value_key, *value_list[index])
                    pipe.ltrim(value_key, 0, self.MAX_INDEX)

                # Have the pipe execute commands in chunks, rather than every time or all at once at the end.
                if (index % 50) == 0:
                    pipe.execute()
        else:
            # This condition may be extraneous, due to the fact that this function was primarily created for bulk
            # inserts of table-organized data.
            for index in xrange(0, len(attributes)):
                attribute = attributes[index]
                base_key = self._build_base_attribute_key(clean_instrument_id, attribute, table_name=table_name)
                time_key = "".join([base_key, ":time"])
                value_key = "".join([base_key, ":value"])

                pipe.lpush(time_key, *iso_format_times)

                pipe.lpush(value_key, *value_list[index])

                pipe.ltrim(time_key, 0, self.MAX_INDEX)
                pipe.ltrim(value_key, 0, self.MAX_INDEX)

                # Have the pipe execute commands in chunks, rather than every time or all at once at the end.
                if (index % 50) == 0:
                    pipe.execute()

        # Force the pipe to execute at the very end to assure no transactions are missed.
        pipe.execute()

    def is_time_before_last_time_for_attribute(self, instrument_id, attribute, given_time, table_name=None):
        """Checks whether the time supplied is more recent than the last time for a particular attribute of an
        instrument.  Allows the caller to determine whether the Redis database is likely to hold the entire
        desired series or has likely trimmed off some desired values.  If 'table_name' is defined, it will assume
        the attribute is organized under the specified name.

        Parameters
        ----------

        instrument_id: integer
            The database id for the particular instrument.

        attribute: string
            The name of the particular attribute, such as 'temperature' or 'voltage'.

        given_time: datetime.datetime
            The time (UTC) to compare against.  Expected to be already translated to UTC version.

        table_name: string, optional
            Default None. The name of a table the attribute is grouped under.

        Returns
        -------

        result: integer
            Returns 1 if 'given_time' is more recent than the last time for the specified 'attribute', or 0 otherwise.

        """
        clean_instrument_id = self._create_clean_integer(instrument_id,
                                                         "Could not convert instrument ID to valid integer.")
        if not clean_instrument_id:
            return 0

        result = 0

        # Key construction varies depending on whether the attribute is organized under a table.
        if table_name:
            db_time_key = self._build_table_time_key(clean_instrument_id, table_name)
            db_result = self._r.lindex(db_time_key, -1)
        else:
            db_key = self._build_base_attribute_key(clean_instrument_id, attribute)
            db_result = self._r.lindex(db_key + ":time", -1)

        if len(db_result) > 0:
            last_time = ciso8601.parse_datetime(db_result).replace(tzinfo=pytz.utc)
            if given_time.replace(tzinfo=pytz.utc) > last_time:
                result = 1

        return result

    def get_attribute_by_event_code(self, event_code_id):
        """ Get the attribute name associated with an event code id.

        Parameters
        ----------

        event_code_id: integer
            The database event code id number

        Returns
        -------

        attribute: string
            The name of the attribute associated with the event code.

        """

        db_key = "".join(["event_code:", str(event_code_id)])
        attribute = self._r.get(db_key)
        return attribute

    def add_event_code(self, event_code_id, attribute_name):
        """ Add an event code to the database with its associated attribute name.

        Parameters
        ----------

        event_code_id: integer
            The database event code id number.

        attribute_name: string
            The name of the attribute associated with the event code.

        """

        db_key = "".join(["event_code:", str(event_code_id)])
        self._r.set(db_key, attribute_name)

    def clear_database(self):
        """Clears the entire Redis database.  Will wipe any other information on the same server."""
        self._r.flushdb()

    @staticmethod
    def _build_table_time_key(instrument_id, table_name):
        """Builds a Redis key for the list of times associated with the 'instrument_id' and the 'table_name' of the form
        'instruments:<instrument_id>:<table_name>:time'. For
        example, "instruments:1:prosensing_paf:time.

        Parameters
        ----------
        instrument_id: integer
            The database id for the particular instrument.

        table_name: string
            The name of the table of attributes the times are for.


        Returns
        -------

        time_key: string
            Redis key of the form 'instruments:<instrument_id>:<table_name>:time'.  For example,
            'instruments:1:prosensing_paf:time'.

        """
        time_key = "".join(["instruments:", str(instrument_id), ":", table_name, ":time"])
        return time_key

    @staticmethod
    def _build_base_attribute_key(instrument_id, attribute, table_name=None):
        """Builds a base Redis key for a particular instrument's attribute.  Final key base should be of the form
        'instruments:<instrument_id>:<table_name>:<attribute>' as a contiguous string.  E.g,
        'instruments:1:prosensing_paf:voltage'.  The table_name is optional, allows attributes to be grouped by table.

        Parameters
        ----------

        instrument_id: integer
            The database id for the particular instrument.

        attribute: string
            The name of the particular attribute, such as 'temperature' or 'voltage'.

        table_name: string, optional
            Default None. The name of a table the attributes are grouped under.

        Returns
        -------

        base_key: string
            Base Redis key of the form 'instruments:<instrument_id>:<table_name>:<attribute>',
            e.g. 'instruments:1:prosensing_paf:voltage'.

        """
        if table_name:
            table_section = "".join([table_name, ":"])
        else:
            table_section = ""
        base_key = "".join(["instruments:", str(instrument_id), ":", table_section,  attribute])
        return base_key

    @staticmethod
    def _create_clean_integer(dirty_input, error_message=None):
        """Attempt to convert an input into a valid integer.  If it fails, None is returned and an error message is
        displayed if one was passed.

        Parameters
        ----------

        dirty_input: object
            Input that is converted into a valid integer.

        error_message: string, optional
            Defaults to None.  If specified, the error message will be printed to the screen if the conversion to
            integer fails.

        Returns
        -------

        result: integer or None
            If the conversion was successful, returns the new integer.  If it failed, returns None.

        """
        clean_integer = None

        try:
            clean_integer = int(dirty_input)
        except ValueError:
            if error_message:
                print(error_message)

        return clean_integer
