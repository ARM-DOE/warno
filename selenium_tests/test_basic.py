from unittest import TestCase
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from random import randint


class TestIndexFunctionality(TestCase):
    warno_url = 'http://127.0.0.1:8080'

    def setUp(self):
        self.browser = webdriver.Firefox()
        # self.browser.implicitly_wait(1)

    def tearDown(self):
        self.browser.quit()

    def test_index_has_WARNO_in_title(self):
        self.browser.get(self.warno_url)
        self.assertTrue('WARNO' in self.browser.title, 'WARNO is not in index title.')

    def test_sites_has_sites_in_title(self):
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Sites").click()
        self.assertTrue('Site' in self.browser.title, 'Sites did not have sites in title.')


    def test_instrument_add_button_redirects_to_new_instrument_page(self):
        """
        Test instrument add adds instrument to database, and then makes the instrument
        visible in instrument listing with correct elements.
        -------

        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Instruments').click()
        self.browser.find_element_by_id('new-instrument-redirect-button').click()
        contents = self.browser.find_element_by_class_name('sub-title')
        print(contents)
        self.assertTrue('New Instrument' in contents.text)

    def test_instrument_add_adds_instrument(self):
        test_instrument = {'abbv': 'TEST',
                           'name': 'SELENIUM TEST INSTRUMENT',
                           'type': 'TEST_RADAR',
                           'vendor': 'SELENIUM',
                           'description': 'Selenium Injected Instrument',
                           'frequency_band': 'Y'}

        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Instruments').click()
        self.browser.find_element_by_id('new-instrument-redirect-button').click()

        for key in test_instrument.keys():
            element = self.browser.find_element_by_name(key)
            element.send_keys(test_instrument[key])

        site_select = Select(self.browser.find_element_by_name('site'))

        site_select.select_by_visible_text('OLI')

        self.browser.find_element_by_id('submit').click()
        ## Should insert instrument, and returns us to instruments page.

        self.assertTrue('instruments' in self.browser.current_url, 'Did not return to instruments page after instrument insert')

        table_id = self.browser.find_element_by_id('instrument-table')
        rows = table_id.find_elements_by_tag_name('tr')
        test_row = []
        for row in rows[1:]:
            if row.find_elements_by_tag_name("td")[0].text == 'TEST':
                test_row = row

        ## Now we make sure we get back out what we put in
        test_values = [td.text for td in test_row.find_elements_by_tag_name('td')]
        for key in test_instrument.keys():
            self.assertIn(test_instrument[key], test_values,'Missing Value %s' %test_instrument[key])


    def test_site_add_shows_up_in_table(self):
        test_site = {'abbv': 'TEST%d' % randint(0,100),
                           'name': 'SELENIUM TEST SITE',
                           'lat': '12.3',
                           'lon': '45.6',
                           'facility': 'SELENIUM',
                           'location_name': 'Selenium Injected Site'
                           }


        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Sites').click()
        self.browser.find_element_by_id('new-site-redirect-button').click()

        for key in test_site.keys():
            element = self.browser.find_element_by_name(key)
            element.send_keys(test_site[key])



        self.browser.find_element_by_id('submit').click()

        self.assertTrue('sites' in self.browser.current_url, 'Did not return to sites page after instrument insert')

        table_id = self.browser.find_element_by_id('site-table')
        rows = table_id.find_elements_by_tag_name('tr')
        test_row = []
        for row in rows[1:]:
            if row.find_elements_by_tag_name("td")[0].text ==test_site['abbv']:
                test_row = row

        self.assertFalse(test_row == [],'Did not find test row at all')

        ## Now we make sure we get back out what we put in
        test_values = [td.text for td in test_row.find_elements_by_tag_name('td')]
        for key in test_site.keys():
            self.assertIn(test_site[key], test_values,'Missing Value %s' %test_site[key])






