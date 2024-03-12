#!/usr/bin/env python
# Copyright 2005 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A useful class for digesting, on a high-level, where time in a program goes.

Usage:

sw = StopWatch()
sw.start()
sw.start('foo')
foo()
sw.stop('foo')
args = overhead_code()
sw.start('bar')
bar(args)
sw.stop('bar')
sw.dump()

If you start a new timer when one is already running, then the other one will
stop running, and restart when you stop this timer.  This behavior is very
useful for when you want to try timing for a subcall without remembering
what is already running.  For instance:

sw.start('all_this')
do_some_stuff()
sw.start('just_that')
small_but_expensive_function()
sw.stop('just_that')
cleanup_code()
sw.stop('all_this')

In this case, the output will be what you want:  the time spent in
small_but_expensive function will show up in the timer for just_that and not
all_this.
"""

import StringIO
import time


__owner__ = 'dbentley@google.com (Dan Bentley)'


class StopWatch(object):
  """Class encapsulating a timer; see above for example usage.

  Instance variables:
    timers: map of stopwatch name -> time for each currently running stopwatch,
            where time is seconds from the epoch of when this stopwatch was
            started.
    accum: map of stopwatch name -> accumulated time, in seconds, it has
            already been run for.
    stopped: map of timer name -> list of timer names that are blocking it.
    counters: map of timer name -> number of times it has been started.
  """

  def __init__(self):
    self.timers = {}
    self.accum = {}
    self.stopped = {}
    self.counters = {}

  def start(self, timer='total', stop_others=True):
    """Start a timer.

    Args:
      timer: str; name of the timer to start, defaults to the overall timer.
      stop_others: bool; if True, stop all other running timers.  If False, then
                   you can have time that is spent inside more than one timer
                   and there's a good chance that the overhead measured will be
                   negative.
    """
    if stop_others:
      stopped = []
      for other in list(self.timers):
        if not other == 'total':
          self.stop(other)
          stopped.append(other)
      self.stopped[timer] = stopped
    self.counters[timer] = self.counters.get(timer, 0) + 1
    self.timers[timer] = time.time()

  def stop(self, timer='total'):
    """Stop a running timer.

    This includes restarting anything that was stopped on behalf of this timer.

    Args:
      timer: str; name of the timer to stop, defaults to the overall timer.

    Raises:
      RuntimeError: if timer refers to a timer that was never started.
    """
    if timer not in self.timers:
      raise RuntimeError(
          'Tried to stop timer that was never started: %s' % timer)
    self.accum[timer] = self.timervalue(timer)
    del self.timers[timer]
    for stopped in self.stopped.get(timer, []):
      self.start(stopped, stop_others=0)

  def timervalue(self, timer='total', now=None):
    """Return the value seen by this timer so far.

    If the timer is stopped, this will be the accumulated time it has seen.
    If the timer is running, this will be the time it has seen up to now.
    If the timer has never been started, this will be zero.

    Args:
      timer: str; the name of the timer to report on.
      now: long; if provided, the time to use for 'now' for running timers.
    """
    if not now:
      now = time.time()

    if timer in self.timers:
      # Timer is running now.
      return self.accum.get(timer, 0.0) + (now - self.timers[timer])
    elif timer in self.accum:
      # Timer is stopped.
      return self.accum[timer]
    else:
      # Timer is never started.
      return 0.0

  def overhead(self, now=None):
    """Calculate the overhead.

    Args:
      now: (optional) time to use as the current time.

    Returns:
      The overhead, that is, time spent in total but not in any sub timer.  This
      may be negative if time was counted in two sub timers.  Avoid this by
      always using stop_others.
    """
    total = self.timervalue('total', now)
    if total == 0.0:
      return 0.0

    all_timers = sum(self.accum.itervalues())
    return total - (all_timers - total)

  def results(self, verbose=False):
    """Get the results of this stopwatch.

    Args:
      verbose: bool; if True, show all times; otherwise, show only the total.

    Returns:
      A list of tuples showing the output of this stopwatch, of the form
      (name, value, num_starts) for each timer.  Note that if the total timer
      is not used, non-verbose results will be the empty list.
    """
    now = time.time()

    all_names = self.accum.keys()
    names = []

    if 'total' in all_names:
      all_names.remove('total')
    all_names.sort()
    if verbose:
      names = all_names

    results = [(name, self.timervalue(name, now=now), self.counters[name])
               for name in names]
    if verbose:
      results.append(('overhead', self.overhead(now=now), 1))
    if 'total' in self.accum or 'total' in self.timers:
      results.append(('total', self.timervalue('total', now=now),
                      self.counters['total']))
    return results

  def dump(self, verbose=False):
    """Describes where time in this stopwatch was spent.

    Args:
      verbose: bool; if True, show all timers; otherwise, show only the total.

    Returns:
      A string describing the stopwatch.
    """
    output = StringIO.StringIO()
    results = self.results(verbose=verbose)
    maxlength = max([len(result[0]) for result in results])
    for result in results:
      output.write('%*s: %6.2fs\n' % (maxlength, result[0], result[1]))
    return output.getvalue()

# Create a stopwatch to be publicly used.
sw = StopWatch()
