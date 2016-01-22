from unittest import TestCase
from selenium import webdriver


class TestBasicFunctionality(TestCase):
    self.warno_url = 'yggdrasil.pnl.gov'

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()


    def test_index_has_title(self):
        self.browser.get(warno_url)
