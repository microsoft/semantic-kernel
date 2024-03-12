from tests.mturk.support import unittest

from .common import MTurkCommon
from boto.mturk.connection import MTurkRequestError

class TestDisableHITs(MTurkCommon):
	def test_disable_invalid_hit(self):
		self.assertRaises(MTurkRequestError, self.conn.disable_hit, 'foo')

if __name__ == '__main__':
	unittest.main()
