import unittest
import os
from boto.mturk.question import QuestionForm

from .common import MTurkCommon

class TestHITCreation(MTurkCommon):
	def testCallCreateHitWithOneQuestion(self):
		create_hit_rs = self.conn.create_hit(
			question=self.get_question(),
			**self.get_hit_params()
			)

	def testCallCreateHitWithQuestionForm(self):
		create_hit_rs = self.conn.create_hit(
			questions=QuestionForm([self.get_question()]),
			**self.get_hit_params()
			)

if __name__ == '__main__':
	unittest.main()
