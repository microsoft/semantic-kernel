import unittest
import uuid
import datetime
from boto.mturk.question import ExternalQuestion

from ._init_environment import SetHostMTurkConnection, external_url, \
        config_environment

class Test(unittest.TestCase):
        def setUp(self):
                config_environment()

        def test_create_hit_external(self):
                q = ExternalQuestion(external_url=external_url, frame_height=800)
                conn = SetHostMTurkConnection()
                keywords=['boto', 'test', 'doctest']
                create_hit_rs = conn.create_hit(question=q, lifetime=60*65, max_assignments=2, title="Boto External Question Test", keywords=keywords, reward = 0.05, duration=60*6, approval_delay=60*60, annotation='An annotation from boto external question test', response_groups=['Minimal', 'HITDetail', 'HITQuestion', 'HITAssignmentSummary',])
                assert(create_hit_rs.status == True)

if __name__ == "__main__":
        unittest.main()
