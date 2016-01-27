import flask
import mock
import requests
from unittest import TestCase
from UserPortal import views

class test_views(TestCase):

  def substring_in_call_args(self, substring, call_list):
    print [call[0] for call in call_list]
    print u'1' == call_list[2][0][1][0]
    print "DELETE" in call_list[2][0]
    print "DELETE" in call_list[2][0][0]

  @mock.patch('psycopg2.connect')
  def test_get_instruments_1(self, connect):
    with views.app.test_client() as c:
      connection = connect.return_value
      cursor = connection.cursor.return_value
      result = c.get("/instruments/1")
      execute_calls = cursor.execute.call_args_list
      # cursor.execute.assert_called_with("SELECT i.instrument_id, i.name_short,"
      #           + " i.name_long, i.type, i.vendor, i.description, i.frequency_band,"
      #           + " s.name_short, s.latitude, s.longitude, s.site_id FROM instruments"
      #           + " i JOIN sites s ON (i.site_id = s.site_id) WHERE i.instrument_id = 1")
      self.assertTrue(mock.call("SELECT special, description FROM instrument_data_references WHERE instrument_id = %s",(u'1',)) in execute_calls)
      self.assertEqual(result.status, '200 OK')
      # self.assertEqual(True, False)

  @mock.patch('psycopg2.connect')
  def test_delete_instruments_1(self, connect):
    with views.app.test_client() as c:
      connection = connect.return_value
      cursor = connection.cursor.return_value
      result = c.delete("/instruments/1")
      execute_calls = cursor.execute.call_args_list
      ec = cursor.execute.call_args
      print execute_calls
      print "\nOne Call\n"
      print execute_calls[2]
      print execute_calls[2][0]
      print execute_calls[2][0][0]
      print execute_calls[2][0][1]
      print execute_calls[2][0][1][0]
      print "\nNext Set\n"
      #print execute_calls[0][0]
      #self.assertTrue("COMM" in ec)
      self.substring_in_call_args("DELETE", execute_calls)
      self.assertTrue(mock.call("DELETE FROM instruments WHERE instrument_id = %s",(u'1',)) in execute_calls)
      self.assertEqual(result.status, '200 OK')
      self.assertEqual(True, False)




  def test_is_number(self):
    self.assertTrue(views.is_number('1'), '"1 should be a number"')
    self.assertTrue(views.is_number('1.1'), '1.1 should be a number')
    self.assertTrue(views.is_number(' -5.1'), 'test_is_number failed')

    self.assertFalse(views.is_number('a'), 'a is not a number')
    self.assertFalse(views.is_number('1.1.1'), '1.1.1 is not a number')

  def test_two(self):
    self.assertTrue(True)
