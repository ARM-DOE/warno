import mock
import os

from flask.ext.testing import TestCase
from flask.ext.fixtures import FixturesMixin

from UserPortal import views
from WarnoConfig import config
from WarnoConfig.models import db


@mock.patch('logging.Logger')
class TestViews(TestCase, FixturesMixin):

    render_templates = False
    db_cfg = config.get_config_context()['database']
    s_db_cfg = config.get_config_context()['s_database']
    TESTING = True

    # Fixtures are usually in warno-vagrant/data_store/data/WarnoConfig/fixtures
    fixtures = ['sites.yml', 'users.yml', 'instruments.yml', 'instrument_logs.yml']

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

    def test_status_log_for_each_instrument_returns_expected_logs(self, logger):

        result = views.status_log_for_each_instrument()
        print result
        # Instrument id 1 has two logs, the most recent having contents 'Log 2 Contents'
        # Instrument id 2 has one log, having contents 'Log 3 Contents'

        self.assertEqual(result[1]['contents'], 'Log 2 Contents',
                         "Instrument with id 1's most recent log did not have contents 'Log 2 Contents'")
        self.assertEqual(result[2]['contents'], 'Log 3 Contents',
                         "Instrument with id 2's most recent log did not have contents 'Log 3 Contents'")

    def test_two(self, logger):
        self.assertTrue(True)
