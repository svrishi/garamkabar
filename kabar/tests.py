import unittest
from django.test.client import Client

class IndexViewTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def testViews(self):
        c = Client()
        resp = c.get('/')
        f = open("/tmp/test.html", "w")
        f.write(resp.content)
        f.close()

