import mock

from flask.ext.testing import TestCase

from UserPortal import views
#from UserPortal import sites
from WarnoConfig import database
from WarnoConfig.models import Site

class test_sites(TestCase):

    def setUp(self):
        database.db_session = mock.Mock()
        self.log_patch = mock.patch('logging.Logger')
        self.mock_log = self.log_patch.start()

    def tearDown(self):
        self.log_patch.stop()

    def create_app(self):
        views.app.config['TESTING'] = True
        return views.app



    def test_method_get_on_edit_site_returns_200_ok_and_passes_mock_db_site_as_context_variables_using_correct_template(self):
        site_return = mock.Mock()
        site_return.name_long= 2
        site_return.name_short = 3
        database.db_session.query().filter().first.return_value = site_return

        result = self.client.get('/sites/10/edit')
        self.assert200(result)

        calls = database.db_session.query.call_args_list
        self.assertTrue(True in [Site in call[0] for call in calls], "'Site' class not called in a query")

        # Accessing context variable by name feels brittle, but it seems to be the only way
        context_site = self.get_context_variable('site')
        values = [value for key, value in context_site.iteritems()]
        self.assertTrue(2 in values, "Value '2' is not in the returned site dictionary")
        self.assertTrue(3 in values, "Value '3' is not in the returned site dictionary")

        self.assert_template_used('edit_site.html')