import datetime
import mock
import os

from flask.ext.testing import TestCase
from flask.ext.fixtures import FixturesMixin

from UserPortal import instruments
from UserPortal import views
from WarnoConfig import config
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


    def test_histogram_page_loads(self, logger):
        get_request_return = self.client.get('/devel/histogram')
        self.assert200(get_request_return)

