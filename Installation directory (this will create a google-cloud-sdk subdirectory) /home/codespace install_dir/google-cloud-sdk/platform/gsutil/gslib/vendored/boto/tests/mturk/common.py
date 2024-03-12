import unittest
import uuid
import datetime

from boto.mturk.question import (
        Question, QuestionContent, AnswerSpecification, FreeTextAnswer,
)
from ._init_environment import SetHostMTurkConnection, config_environment

class MTurkCommon(unittest.TestCase):
        def setUp(self):
                config_environment()
                self.conn = SetHostMTurkConnection()

        @staticmethod
        def get_question():
                # create content for a question
                qn_content = QuestionContent()
                qn_content.append_field('Title', 'Boto no hit type question content')
                qn_content.append_field('Text', 'What is a boto no hit type?')

                # create the question specification
                qn = Question(
                        identifier=str(uuid.uuid4()),
                        content=qn_content,
                        answer_spec=AnswerSpecification(FreeTextAnswer()))
                return qn

        @staticmethod
        def get_hit_params():
                return dict(
                        lifetime=datetime.timedelta(minutes=65),
                        max_assignments=2,
                        title='Boto create_hit title',
                        description='Boto create_hit description',
                        keywords=['boto', 'test'],
                        reward=0.23,
                        duration=datetime.timedelta(minutes=6),
                        approval_delay=60*60,
                        annotation='An annotation from boto create_hit test',
                        response_groups=['Minimal',
                                'HITDetail',
                                'HITQuestion',
                                'HITAssignmentSummary',],
                        )

