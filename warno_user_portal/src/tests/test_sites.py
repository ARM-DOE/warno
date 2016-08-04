import mock
import os

from flask.ext.testing import TestCase
from flask.ext.fixtures import FixturesMixin

from UserPortal import views
from WarnoConfig import config
from WarnoConfig.models import db


@mock.patch('logging.Logger')
class TestSites(TestCase, FixturesMixin):
    """Contains tests for the UserPortal 'sites' file."""

    render_templates = False
    db_cfg = config.get_config_context()['database']
    s_db_cfg = config.get_config_context()['s_database']
    TESTING = True

    # Fixtures are usually in warno-vagrant/data_store/data/WarnoConfig/fixtures
    fixtures = ['sites.yml']

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

    def test_method_get_on_edit_site_returns_200_ok_and_passes_fixture_site_as_context_variable_using_correct_template(self, logger):
        """A 'GET' request to /sites/<site_id>/edit returns a response of '200' OK and passes the database information
        of the site with an id matching 'site_id' as a context variable to the 'edit_site.html' template."""
        # Should get database fixture site entry with id 2
        get_request_return = self.client.get('/sites/2/edit')
        self.assert200(get_request_return)

        context_site = self.get_context_variable('site')

        self.assertEqual(context_site['name_short'], 'TESTSIT2',
                         "'TESTSIT2' is not in the 'name_short' field for the context variable site.")
        self.assertEqual(context_site['location_name'], 'Test Location 2',
                         "'Test Location 2' is not in the 'location_name' field for the context variable site.")

        self.assert_template_used('edit_site.html')
