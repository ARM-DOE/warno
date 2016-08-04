from selenium.webdriver.support.ui import Select
from selenium import webdriver
from unittest import TestCase
from random import randint


class TestIndexFunctionality(TestCase):
    """
    Tests basic page functionality, such as page existence, redirects, database element creation and editing.
    """
    warno_url = 'http://127.0.0.1:8080'

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_index_has_WARNO_in_title(self):
        """
        Test that visiting the home url displays the landing page.
        """
        self.browser.get(self.warno_url)
        self.assertTrue('WARNO' in self.browser.title, '"WARNO" is not in index title.')

    def test_sites_has_sites_in_title(self):
        """
        Test that clicking 'Sites' button redirects to the correct page.
        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Sites").click()
        self.assertTrue('Site' in self.browser.title, 'Sites did not have "Site" in title.')

    def test_pulses_has_pulses_in_title(self):
        """
        Test that clicking 'Pulses' button redirects to the correct page.
        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Pulses").click()
        self.assertTrue('Pulse' in self.browser.title, 'Pulses did not have "Pulse" in title')

    def test_instruments_has_instruments_in_title(self):
        """
        Test that clicking 'Instruments' button redirects to the correct page.
        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Instruments").click()
        self.assertTrue('Instrument' in self.browser.title, 'Instruments did not have "Instrument" in title')

    def test_users_has_users_in_title(self):
        """
        Test that clicking 'Users' button redirects to the correct page.
        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Users").click()
        self.assertTrue('User' in self.browser.title, 'Users did not have "User" in title')

    def test_dashboard_has_dashboard_in_title(self):
        """
        Test that clicking 'Dashboard' button redirects to the correct page.
        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Dashboard").click()
        self.assertTrue('Dashboard' in self.browser.title, 'Dashboard did not have "Dashboard" in title')

    def test_submit_log_has_submit_log_in_title(self):
        """
        Test that clicking 'Submit Log' button redirects to the correct page.
        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Submit Log").click()
        self.assertTrue('Submit Log' in self.browser.title, 'Submit Log did not have "Submit Log" in title')

    def test_query_has_query_in_title(self):
        """
        Test that visiting '/query' redirects to the correct page.
        """
        query_url = self.warno_url + '/query'
        self.browser.get(query_url)
        self.assertTrue('Query' in self.browser.title, 'Query did not have "Query" in title')

    def test_ena_site_has_ena_in_title_and_is_accessible_through_sites_list(self):
        """
        Test that clicking on a site name in the list of sites takes you to that site's details page.
        """
        site_name = "ENA"
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Sites").click()
        self.browser.find_element_by_link_text(site_name).click()
        sub_title = self.browser.find_element_by_class_name("sub-title")
        self.assertTrue(site_name in sub_title.text, 'Site %s did not have "%s" in sub-title' % (site_name, site_name))

    def test_kazr_instrument_has_kazr_in_title_and_is_accessible_through_instruments_list(self):
        """
        Test that clicking on an instrument name in the list of instruments takes you to that instrument's details page.
        """
        instrument_name = "KAZR"
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Instruments").click()
        self.browser.find_element_by_link_text(instrument_name).click()
        sub_title = self.browser.find_element_by_class_name("sub-title")
        self.assertTrue(instrument_name in sub_title.text,
                        'Instrument %s did not have "%s" in sub-title' % (instrument_name, instrument_name))

    def test_ena_site_has_ena_in_title_and_is_accessible_through_instruments_list(self):
        """
        Test that clicking on a site name in the list of instruments takes you to that site's details page.
        """
        site_name = "ENA"
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Instruments").click()
        self.browser.find_element_by_link_text(site_name).click()
        sub_title = self.browser.find_element_by_class_name("sub-title")
        self.assertTrue(site_name in sub_title.text, 'Site %s did not have "%s" in sub-title' % (site_name, site_name))

    def test_submit_log_redirects_to_instrument_the_log_is_for_and_shows_log(self):
        """
        Test that submitting a log for a particular instrument both redirects the user to the instrument details page
        for that instrument and displays the log.
        """
        test_log = {'user': 'John J. Technician',
                    'instrument': 'ENA:KAZR',
                    'instrument_name_only': 'KAZR',
                    'date': '2030-01-01 22:22:22',
                    'status': 'NOT WORKING',
                    'contents': 'TESTLOGCONTENTS'}
        # Navigate to the Submit Log page
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text("Submit Log").click()

        # Fill out the form using the test data
        user_select = Select(self.browser.find_element_by_name('user-id'))
        user_select.select_by_visible_text(test_log['user'])

        instrument_select = Select(self.browser.find_element_by_name('instrument'))
        instrument_select.select_by_visible_text(test_log['instrument'])

        date_element = self.browser.find_element_by_id("datetime-input")
        date_element.clear()
        date_element.send_keys(test_log['date'])

        status_select = Select(self.browser.find_element_by_name('status'))
        status_select.select_by_visible_text(test_log['status'])

        contents_element = self.browser.find_element_by_name('contents')
        contents_element.send_keys(test_log['contents'])

        # Should insert a new log and redirect to the instrument details page the log was submitted for
        self.browser.find_element_by_id("submit").click()

        sub_title = self.browser.find_element_by_class_name('sub-title')
        self.assertTrue(test_log['instrument_name_only'] in sub_title.text,
                        "Redirected page's subtitle did not contain the instrument name %s" %
                        test_log['instrument_name_only'])

        info_boxes = self.browser.find_elements_by_class_name("info")
        # Asserts that the test_log['status'] is in any element with the class name "info"
        self.assertTrue(True in [test_log['status'] in box.text for box in info_boxes],
                        "Log's status '%s' is not in the first info box" % test_log['status'])

        # No id's or names for log entries displayed, so just do a general search for the div containing the author
        # TODO Figure out a way to test for time, even though it switches from local at input to utc at display
        possible_divs = self.browser.find_elements_by_tag_name("div")
        test_div = []
        for div in possible_divs:
            if test_log['user'] in div.text:
                test_div = div

        self.assertTrue(test_log['contents'] in test_div.text,
                        "Log's contents not displayed in %s's log" % test_log['user'])
        self.assertTrue(test_log['status'] in test_div.text,
                        "Log's status %s not displayed in %s's log" % (test_log['status'], test_log['user']))

    def test_user_add_button_redirects_to_new_user_page(self):
        """
        Test that clicking on the new user button redirects to the new user form page.
        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Users').click()
        self.browser.find_element_by_id('new-user-redirect-button').click()
        contents = self.browser.find_element_by_class_name('sub-title')
        self.assertTrue('New User' in contents.text, "Redirected page's subtitle did not contain 'New User'")

    def test_user_add_adds_user(self):
        """
        Test user add adds user to database, and then makes the user visible in user listing with correct elements.
        """
        test_user = {'name': 'TESTNAME',
                     'email': 'TESTEMAIL@TESTHOST.com',
                     'location': 'TESTLOCATION',
                     'position': 'TESTPOSITION',
                     'password': 'TESTPASSWORD'}

        # Navigate to the new user form
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Users').click()
        self.browser.find_element_by_id('new-user-redirect-button').click()

        # Fill in the new user form
        for key in test_user.keys():
            element = self.browser.find_element_by_name(key)
            element.send_keys(test_user[key])

        # Should insert user and redirect to users page
        self.browser.find_element_by_id('submit').click()

        self.assertTrue('users' in self.browser.current_url, 'Did not redirect to users page after user insert')

        table_id = self.browser.find_element_by_id('user-table')
        rows = table_id.find_elements_by_tag_name('tr')
        test_row = []
        for row in rows[1:]:
            if row.find_elements_by_tag_name("td")[0].text == test_user['name']:
                test_row = row

        # Now assert that the entered information is displayed
        test_values = [td.text for td in test_row.find_elements_by_tag_name('td')]
        for key in test_user.keys():
            # You pretty much never display a password, so don't expect to see one
            if key != 'password':
                self.assertIn(test_user[key], test_values, 'Missing Value %s' % test_user[key])

    def test_creating_a_user_and_editing_the_name_results_in_a_user_with_the_edited_name_in_the_user_list(self):
        """
        Test that editing an user name successfully edits the database entry by showing the edited user
        in the users list.
        """
        test_user = {'name': 'TESTNAME%d' % randint(0, 100),
                     'email': 'TESTEMAIL@TESTHOST.com',
                     'location': 'TESTLOCATION',
                     'position': 'TESTPOSITION',
                     'password': 'TESTPASSWORD'}
        new_name = "EDITEDNAME%d" % randint(0, 100)

        # Navigate to the new user form
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Users').click()
        self.browser.find_element_by_id('new-user-redirect-button').click()

        # Fill in the new user form
        for key in test_user.keys():
            element = self.browser.find_element_by_name(key)
            element.send_keys(test_user[key])

        # Should insert user and redirect to users page
        self.browser.find_element_by_id('submit').click()

        self.assertTrue('users' in self.browser.current_url, 'Did not redirect to users page after user insert')

        # Find the row with the new user
        table_id = self.browser.find_element_by_id('user-table')
        rows = table_id.find_elements_by_tag_name('tr')
        test_row = []
        for row in rows[1:]:
            if row.find_elements_by_tag_name("td")[0].text == test_user["name"]:
                test_row = row

        # In the row with the new user, find the 'Edit' link and click it
        test_row_tds = test_row.find_elements_by_tag_name('td')

        for td in test_row_tds:
            if td.text == "Edit":
                td.find_elements_by_tag_name('a')[0].click()

        # It should redirect to the proper edit page
        self.assertTrue('edit' in self.browser.current_url, 'Did not redirect to edit page.')

        # Clear the name box and fill it with the edited name
        name_field = self.browser.find_element_by_id("userNameBox")
        name_field.clear()
        name_field.send_keys(new_name)

        # Submit the form.  Should redirect to the list of users
        self.browser.find_element_by_id('submit').click()

        self.assertTrue('users' in self.browser.current_url, 'Did not redirect to users page after user update')

        # Make sure that the edited user now displays in the list of users.
        test_values = [td.text for td in self.browser.find_elements_by_tag_name("td")]
        self.assertIn(new_name, test_values, "Edited name not in table cells on page.")

    def test_instrument_add_button_redirects_to_new_instrument_page(self):
        """
        Test that clicking on the new user button redirects to the new user form page.
        """
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Instruments').click()
        self.browser.find_element_by_id('new-instrument-redirect-button').click()
        contents = self.browser.find_element_by_class_name('sub-title')
        self.assertTrue('New Instrument' in contents.text,
                        "Redirected page's subtitle did not contain 'New Instrument'")

    def test_instrument_add_adds_instrument(self):
        """
        Test instrument add adds instrument to database, and then makes the instrument
        visible in instrument listing with correct elements.
        """
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
        # Should insert instrument, and returns us to instruments page.

        self.assertTrue('instruments' in self.browser.current_url,
                        'Did not redirect to instruments page after instrument insert')

        table_id = self.browser.find_element_by_id('instrument-table')
        rows = table_id.find_elements_by_tag_name('tr')
        test_row = []
        for row in rows[1:]:
            if row.find_elements_by_tag_name("td")[1].text == test_instrument['abbv']:
                test_row = row

        # Now we make sure we get back out what we put in
        test_values = [td.text for td in test_row.find_elements_by_tag_name('td')]
        for key in test_instrument.keys():
            self.assertIn(test_instrument[key], test_values, 'Missing Value %s' % test_instrument[key])

    def test_creating_an_instrument_and_editing_the_name_results_in_a_properly_updated_instrument_list(self):
        """
        Test that editing an instrument abbreviation successfully edits the database entry by showing the edited
        instrument in the instruments list.
        """
        test_instrument = {'abbv': 'TEST%d' % randint(0, 100),
                           'name': 'SELENIUM TEST INSTRUMENT',
                           'type': 'TEST_RADAR',
                           'vendor': 'SELENIUM',
                           'description': 'Selenium Injected Instrument',
                           'frequency_band': 'Y'}
        new_name = "EDIT%d" % randint(0, 100)

        # Navigate to the new instrument form
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Instruments').click()
        self.browser.find_element_by_id('new-instrument-redirect-button').click()

        # Fill in the new instrument form
        for key in test_instrument.keys():
            element = self.browser.find_element_by_name(key)
            element.send_keys(test_instrument[key])

        # Should insert instrument and redirect to instruments page
        self.browser.find_element_by_id('submit').click()

        self.assertTrue('instruments' in self.browser.current_url,
                        'Did not redirect to instruments page after instrument insert')

        # Find the row with the new instrument
        table_id = self.browser.find_element_by_id('instrument-table')
        rows = table_id.find_elements_by_tag_name('tr')
        test_row = None
        for row in rows[1:]:
            if row.find_elements_by_tag_name("td")[1].text == test_instrument["abbv"]:
                test_row = row

        # In the row with the new instrument, find the 'Edit' link and click it
        test_row_tds = test_row.find_elements_by_tag_name('td')

        for td in test_row_tds:
            if td.text == "Edit":
                td.find_elements_by_tag_name('a')[0].click()

        # It should redirect to the proper edit page
        self.assertTrue('edit' in self.browser.current_url, 'Did not redirect to edit page.')

        # Clear the name box and fill it with the edited name
        name_field = self.browser.find_element_by_id("instrumentNameBox")
        name_field.clear()
        name_field.send_keys(new_name)

        # Submit the form.  Should redirect to the list of instruments
        self.browser.find_element_by_id('submit').click()

        self.assertTrue('instruments' in self.browser.current_url,
                        'Did not redirect to instruments page after instrument update')

        # Make sure that the edited instrument now displays in the list of instruments.
        test_values = [td.text for td in self.browser.find_elements_by_tag_name("td")]
        self.assertIn(new_name, test_values, "Edited abbreviation not in table cells on page.")

    def test_site_add_shows_up_in_table(self):
        test_site = {'abbv': 'TEST%d' % randint(0, 100),
                     'name': 'SELENIUM TEST SITE',
                     'lat': '12.3',
                     'lon': '45.6',
                     'facility': 'SELENIUM',
                     'location_name': 'Selenium Injected Site'}

        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Sites').click()
        self.browser.find_element_by_id('new-site-redirect-button').click()

        for key in test_site.keys():
            element = self.browser.find_element_by_name(key)
            element.send_keys(test_site[key])

        self.browser.find_element_by_id('submit').click()

        self.assertTrue('sites' in self.browser.current_url, 'Did not return to sites page after site insert')

        table_id = self.browser.find_element_by_id('site-table')
        rows = table_id.find_elements_by_tag_name('tr')
        test_row = []
        for row in rows[1:]:
            if row.find_elements_by_tag_name("td")[0].text == test_site['abbv']:
                test_row = row

        self.assertFalse(test_row == [], 'Did not find test row at all')

        # Now we make sure we get back out what we put in
        test_values = [td.text for td in test_row.find_elements_by_tag_name('td')]
        for key in test_site.keys():
            self.assertIn(test_site[key], test_values, 'Missing Value %s' % test_site[key])

    def test_creating_a_site_and_editing_the_name_results_in_a_site_with_the_edited_name_in_the_site_list(self):
        """
        Test that editing an site abbreviation successfully edits the database entry by showing the edited site
        in the sites list.
        """
        test_site = {'abbv': 'TEST%d' % randint(0, 100),
                     'name': 'SELENIUM TEST SITE',
                     'lat': '12.3',
                     'lon': '45.6',
                     'facility': 'SELENIUM',
                     'location_name': 'Selenium Injected Site'}

        new_name = "EDIT%d" % randint(0, 100)

        # Navigate to the new site form
        self.browser.get(self.warno_url)
        self.browser.find_element_by_link_text('Sites').click()
        self.browser.find_element_by_id('new-site-redirect-button').click()

        # Fill in the new site form
        for key in test_site.keys():
            element = self.browser.find_element_by_name(key)
            element.send_keys(test_site[key])

        # Should insert site and redirect to sites page
        self.browser.find_element_by_id('submit').click()

        self.assertTrue('sites' in self.browser.current_url,
                        'Did not redirect to sites page after site insert')

        # Find the row with the new site
        table_id = self.browser.find_element_by_id('site-table')
        rows = table_id.find_elements_by_tag_name('tr')
        test_row = []
        for row in rows[1:]:
            if row.find_elements_by_tag_name("td")[0].text == test_site["abbv"]:
                test_row = row

        # In the row with the new site, find the 'Edit' link and click it
        test_row_tds = test_row.find_elements_by_tag_name('td')

        for td in test_row_tds:
            if td.text == "Edit":
                td.find_elements_by_tag_name('a')[0].click()

        # It should redirect to the proper edit page
        self.assertTrue('edit' in self.browser.current_url, 'Did not redirect to edit page.')

        # Clear the name box and fill it with the edited name
        name_field = self.browser.find_element_by_id("siteNameBox")
        name_field.clear()
        name_field.send_keys(new_name)

        # Submit the form.  Should redirect to the list of sites
        self.browser.find_element_by_id('submit').click()

        self.assertTrue('sites' in self.browser.current_url,
                        'Did not redirect to sites page after site update')

        # Make sure that the edited site now displays in the list of sites.
        test_values = [td.text for td in self.browser.find_elements_by_tag_name("td")]
        self.assertIn(new_name, test_values, "Edited abbreviation not in table cells on page.")
