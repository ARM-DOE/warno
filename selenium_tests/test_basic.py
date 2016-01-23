from unittest import TestCase
from selenium import webdriver


class TestIndexFunctionality(TestCase):
    warno_url = 'http://yggdrasil.pnl.gov:8080'

    def setUp(self):
        self.browser = webdriver.Firefox()
        # self.browser.implicitly_wait(1)

    def tearDown(self):
        self.browser.quit()

    def test_index_has_WARNOin_title(self):
        self.browser.get(self.warno_url)
        self.assertTrue('WARNO' in self.browser.title, 'WARNO is not in index title.')

