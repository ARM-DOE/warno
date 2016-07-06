import mock
import os

from flask.ext.fixtures import FixturesMixin
from flask.ext.testing import TestCase

from .. import warno_event_manager
from WarnoConfig.models import db
from WarnoConfig import config


@mock.patch("logging.Logger")
class TestEventManager(TestCase, FixturesMixin):
    render_templates = False
    db_cfg = config.get_config_context()['database']
    s_db_cfg = config.get_config_context()['s_database']
    TESTING = True

    # Fixtures are usually in warno-vagrant/data_store/data/WarnoConfig/fixtures
    fixtures = ['sites.yml', 'users.yml', 'instruments.yml', 'instrument_data_references.yml', 'instrument_logs.yml',
                'event_codes.yml', 'prosensing_paf.yml', 'events_with_text.yml', 'events_with_value.yml', 'pulse_captures.yml']

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_app(self):
        warno_event_manager.app.config['TESTING'] = True
        warno_event_manager.app.config['FIXTURES_DIRS'] = [os.environ.get('FIXTURES_DIR')]
        warno_event_manager.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%s:%s@%s:%s/%s' % (self.db_cfg['DB_USER'],
                                                                                                     self.s_db_cfg['DB_PASS'],
                                                                                                     self.db_cfg['DB_HOST'],
                                                                                                     self.db_cfg['DB_PORT'],
                                                                                                     self.db_cfg['TEST_DB_NAME'])

        FixturesMixin.init_app(warno_event_manager.app, db)

        return warno_event_manager.app

    def test_save_json_db_data_output_file_matches_expected_file(self, logger):
        # Have to manually clean up generated files if test fails

        warno_event_manager.save_json_db_data()

        parent_path = os.path.join(os.path.dirname(__file__), "../")
        possible_files = os.listdir(".")

        # Get the three most recently created files (which should have been created when the tested function was called)
        dated_files = [(os.path.getmtime(fn), os.path.basename(fn))
                       for fn in possible_files if fn.lower().endswith('.json')]

        dated_files.sort()
        dated_files.reverse()
        newest = dated_files[:3]

        first_instrument = [item[1] for item in newest if "1_archived_" in item[1]][0]
        second_instrument = [item[1] for item in newest if "2_archived_" in item[1]][0]
        db_info = [item[1] for item in newest if "db_info_" in item[1]][0]

        contents = ""
        expected = ""

        # Test each file against the expected example files
        with open(first_instrument, 'r') as borky:
            contents = borky.read()
        with open(os.path.join(os.path.dirname(__file__), "archive_testfile_1.json"), 'r') as borky:
            expected = borky.read()
        self.assertEqual(contents, expected, "Instrument 1's output does not match 'archive_testfile_1.json'")

        with open(second_instrument, 'r') as borky:
            contents = borky.read()
        with open(os.path.join(os.path.dirname(__file__), "archive_testfile_2.json"), 'r') as borky:
            expected = borky.read()
        self.assertEqual(contents, expected, "Instrument 2's output does not match 'archive_testfile_2.json'")

        with open(db_info, 'r') as borky:
            contents = borky.read()
        with open(os.path.join(os.path.dirname(__file__), "archive_testfile_info.json"), 'r') as borky:
            expected = borky.read()
        self.assertEqual(contents, expected, "Database info output does not match 'archive_testfile_info.json'")

        os.remove(first_instrument)
        os.remove(second_instrument)
        os.remove(db_info)