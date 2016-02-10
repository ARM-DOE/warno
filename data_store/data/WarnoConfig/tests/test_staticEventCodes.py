from unittest import TestCase

from .. import utility


class TestStaticEventCodes(TestCase):

    def test_static_event_codes_has_site_id_request(self):
        self.assertEqual(utility.SITE_ID_REQUEST, 2, 'Site ID request was not 2')

