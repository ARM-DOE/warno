from unittest import TestCase

from .. import utility


class TestStaticEventCodes(TestCase):

    def test_static_event_codes_has_site_id_request_equal_to_2(self):
        """Test that static event codes are properly accessible, testing that the SITE_ID_REQUEST is equal to 2"""
        self.assertEqual(utility.SITE_ID_REQUEST, 2, 'Site ID request was not 2')

