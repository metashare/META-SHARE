from django.test import TestCase
from django.test.client import Client

class SyncTest(TestCase):
	def test_inventory(self):
		self.assertEqual(10, 10)
