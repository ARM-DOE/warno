from unittest import TestCase
from UserPortal import views

class test_views(TestCase):

  def test_is_number(self):
    self.assertTrue(views.is_number('1'), '"1 should be a number"')
    self.assertTrue(views.is_number('1.1'), '1.1 should be a number')
    self.assertTrue(views.is_number(' -5.1'), 'test_is_number failed')

    self.assertFalse(views.is_number('a'), 'a is not a number')
    self.assertFalse(views.is_number('1.1.1'), '1.1.1 is not a number')

  def test_two(self):
    self.assertTrue(True)
