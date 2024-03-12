from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement

def test():
    q = ExternalQuestion(external_url="http://websort.net/s/F3481C", frame_height=800)
    conn = MTurkConnection(host='mechanicalturk.sandbox.amazonaws.com')
    keywords=['boto', 'test', 'doctest']
    qualifications = Qualifications()
    qualifications.add(PercentAssignmentsApprovedRequirement(comparator="GreaterThan", integer_value="95"))
    create_hit_rs = conn.create_hit(question=q, lifetime=60*65, max_assignments=2, title="Boto External Question Test", keywords=keywords, reward = 0.05, duration=60*6, approval_delay=60*60, annotation='An annotation from boto external question test', qualifications=qualifications)
    assert(create_hit_rs.status == True)
    print(create_hit_rs.HITTypeId)

if __name__ == "__main__":
    test()
