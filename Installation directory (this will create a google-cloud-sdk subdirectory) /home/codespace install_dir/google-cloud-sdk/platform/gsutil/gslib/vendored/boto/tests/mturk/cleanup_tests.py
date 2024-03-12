import itertools

from ._init_environment import SetHostMTurkConnection
from ._init_environment import config_environment

def description_filter(substring):
  return lambda hit: substring in hit.Title

def disable_hit(hit):
  return conn.disable_hit(hit.HITId)

def dispose_hit(hit):
  # assignments must be first approved or rejected
  for assignment in conn.get_assignments(hit.HITId):
    if assignment.AssignmentStatus == 'Submitted':
      conn.approve_assignment(assignment.AssignmentId)
  return conn.dispose_hit(hit.HITId)

def cleanup():
  """Remove any boto test related HIT's"""
  config_environment()

  global conn

  conn = SetHostMTurkConnection()


  is_boto = description_filter('Boto')
  print('getting hits...')
  all_hits = list(conn.get_all_hits())
  is_reviewable = lambda hit: hit.HITStatus == 'Reviewable'
  is_not_reviewable = lambda hit: not is_reviewable(hit)
  hits_to_process = filter(is_boto, all_hits)
  hits_to_disable = filter(is_not_reviewable, hits_to_process)
  hits_to_dispose = filter(is_reviewable, hits_to_process)
  print('disabling/disposing %d/%d hits' % (len(hits_to_disable), len(hits_to_dispose)))
  map(disable_hit, hits_to_disable)
  map(dispose_hit, hits_to_dispose)

  total_hits = len(all_hits)
  hits_processed = len(hits_to_process)
  skipped = total_hits - hits_processed
  fmt = 'Processed: %(total_hits)d HITs, disabled/disposed: %(hits_processed)d, skipped: %(skipped)d'
  print(fmt % vars())

if __name__ == '__main__':
  cleanup()
