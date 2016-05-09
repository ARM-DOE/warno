import mock

from unittest import TestCase

from UserPortal import views
from WarnoConfig import database
from WarnoConfig.models import InstrumentLog

class test_views(TestCase):

    def setUp(self):
        self.log_patch = mock.patch('logging.Logger')
        self.mock_log = self.log_patch.start()

    def tearDown(self):
        self.log_patch.stop()

    def test_status_log_for_each_instrument(self):
        first_log = mock.Mock()
        first_log.instrument.id = 2
        first_log.author.name = "first_author"
        first_log.contents = "first_contents"
        first_log.status = 5

        second_log = mock.Mock()
        second_log.instrument.id = 4
        second_log.author.name = "second_author"
        second_log.contents = "second_contents"
        second_log.status = 1

        # Quite ugly, but only way to mock a complex sqlalchemy call
        database.db_session.query().join().join().outerjoin().filter().all.return_value = [first_log, second_log]
        result = views.status_log_for_each_instrument()

        self.assertEquals(result[first_log.instrument.id]["author"], first_log.author.name,
                             "First instrument's author is not '%s'" % first_log.author.name)
        self.assertEquals(result[first_log.instrument.id]["status_code"], first_log.status,
                             "First instrument's status_code is not '%s'" % first_log.status)
        self.assertEquals(result[first_log.instrument.id]["contents"], first_log.contents,
                             "First instrument's contents are not '%s'" % first_log.contents)

        self.assertEquals(result[second_log.instrument.id]["author"], second_log.author.name,
                             "Second instrument's author is not '%s'" % second_log.author.name)
        self.assertEquals(result[second_log.instrument.id]["status_code"], second_log.status,
                             "Second instrument's status_code is not '%s'" % second_log.status)
        self.assertEquals(result[second_log.instrument.id]["contents"], second_log.contents,
                             "Second instrument's contents are not '%s'" % second_log.contents)


    def test_two(self):
        self.assertTrue(True)
