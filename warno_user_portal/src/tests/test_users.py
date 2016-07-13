import mock
import os

from flask.ext.testing import TestCase
from flask.ext.fixtures import FixturesMixin

from UserPortal import views
from WarnoConfig import config
from WarnoConfig.models import db


@mock.patch('logging.Logger')
class TestUsers(TestCase, FixturesMixin):
    """Contains tests for the UserPortal 'users' file."""

    render_templates = False
    db_cfg = config.get_config_context()['database']
    s_db_cfg = config.get_config_context()['s_database']
    TESTING = True

    # Fixtures are usually in warno-vagrant/data_store/data/WarnoConfig/fixtures
    fixtures = ['users.yml']

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

    def test_method_get_on_edit_user_returns_200_ok_and_passes_fixture_user_using_correct_template(self, logger):
        """Method 'GET' on /users/<user_id>/edit gets the edit page for the user matching 'user_id'.  The user's
        database information is passed as a context variable to the template.  The response for the 'GET' request
        is '200' OK."""
        # Should get database fixture user entry with id 2
        get_request_return = self.client.get('/users/2/edit')
        self.assert200(get_request_return)

        context_user = self.get_context_variable('user')

        self.assertEqual(context_user['name'], 'Test User 2',
                         "'Test User 2' is not equal to the 'name' field for the context variable user.")

        self.assert_template_used('edit_user.html')
