import mock

from unittest import TestCase
from flask.ext.testing import TestCase

from UserPortal import views
#from UserPortal import users
from WarnoConfig import database
from WarnoConfig.models import User


class test_users(TestCase):

    def setUp(self):
        database.db_session = mock.Mock()
        self.log_patch = mock.patch('logging.Logger')
        self.mock_log = self.log_patch.start()

    def tearDown(self):
        self.log_patch.stop()

    def create_app(self):
        views.app.config['TESTING'] = True
        return views.app

    def test_method_get_on_edit_user_returns_200_ok_and_passes_mock_db_user_as_context_variables_using_correct_template(
            self):
        user_return = mock.Mock()
        user_return.name = 2
        user_return.location = 3
        database.db_session.query().filter().first.return_value = user_return

        result = self.client.get('/users/10/edit')
        self.assert200(result)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [User in call[0] for call in calls], "'User' class not called in a query")

        # Accessing context variable by name feels brittle, but it seems to be the only way
        context_user = self.get_context_variable('user')
        values = [value for key, value in context_user.iteritems()]
        self.assertTrue(2 in values, "Value '2' is not in the returned user dictionary")
        self.assertTrue(3 in values, "Value '3' is not in the returned user dictionary")

        self.assert_template_used('edit_user.html')
