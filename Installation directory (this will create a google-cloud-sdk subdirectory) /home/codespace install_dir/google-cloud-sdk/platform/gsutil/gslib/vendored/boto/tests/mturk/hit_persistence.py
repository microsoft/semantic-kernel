import unittest
import pickle

from .common import MTurkCommon

class TestHITPersistence(MTurkCommon):
	def create_hit_result(self):
		return self.conn.create_hit(
			question=self.get_question(), **self.get_hit_params()
			)

	def test_pickle_hit_result(self):
		result = self.create_hit_result()
		new_result = pickle.loads(pickle.dumps(result))

	def test_pickle_deserialized_version(self):
		"""
		It seems the technique used to store and reload the object must
		result in an equivalent object, or subsequent pickles may fail.
		This tests a double-pickle to elicit that error.
		"""
		result = self.create_hit_result()
		new_result = pickle.loads(pickle.dumps(result))
		pickle.dumps(new_result)

if __name__ == '__main__':
	unittest.main()
