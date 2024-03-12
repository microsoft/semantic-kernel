# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility classes and methods for the parallelism framework."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import collections
import errno
import logging
import multiprocessing
import threading
import traceback

from gslib.utils import constants
from gslib.utils import system_util
from six.moves import queue as Queue

# pylint: disable=g-import-not-at-top
try:
  # This module doesn't necessarily exist on Windows.
  import resource
  _HAS_RESOURCE_MODULE = True
except ImportError as e:
  _HAS_RESOURCE_MODULE = False

# Maximum time to wait (join) on the SeekAheadThread after the ProducerThread
# completes, in seconds.
SEEK_AHEAD_JOIN_TIMEOUT = 60

# Timeout for puts/gets to the global status queue, in seconds.
STATUS_QUEUE_OP_TIMEOUT = 5

# Maximum time to wait (join) on the UIThread after the Apply
# completes, in seconds.
UI_THREAD_JOIN_TIMEOUT = 60

ZERO_TASKS_TO_DO_ARGUMENT = ('There were no', 'tasks to do')

# Multiprocessing manager used to coordinate across all processes. This
# attribute is only present if multiprocessing is available, which can be
# determined by calling CheckMultiprocessingAvailableAndInit().
global top_level_manager  # pylint: disable=global-at-module-level

# Cache the values from this check such that they're available to all callers
# without needing to run all the checks again (some of these, such as calling
# multiprocessing.Manager(), are expensive operations).
_cached_multiprocessing_is_available = None
_cached_multiprocessing_check_stack_trace = None
_cached_multiprocessing_is_available_message = None

# This must be defined at the module level for pickling across processes.
MultiprocessingIsAvailableResult = collections.namedtuple(
    'MultiprocessingIsAvailableResult', ['is_available', 'stack_trace'])

# Explicitly set start method to 'fork' since this isn't always the default
# in later versions of Python.
try:
  multiprocessing_context = multiprocessing.get_context('fork')
except (AttributeError, ValueError):
  multiprocessing_context = multiprocessing


class AtomicDict(object):
  """Thread-safe (and optionally process-safe) dictionary protected by a lock.

  If a multiprocessing.Manager is supplied on init, the dictionary is
  both process and thread safe. Otherwise, it is only thread-safe.
  """

  def __init__(self, manager=None):
    """Initializes the dict.

    Args:
      manager: (multiprocessing.Manager or None) Manager instance (required for
          cross-process safety), or none if cross-process safety is not needed.
    """
    if manager:
      self.lock = manager.Lock()
      self.dict = manager.dict()
    else:
      self.lock = threading.Lock()
      self.dict = {}

  def __getitem__(self, key):
    with self.lock:
      return self.dict[key]

  def __setitem__(self, key, value):
    with self.lock:
      self.dict[key] = value

  # pylint: disable=invalid-name
  def get(self, key, default_value=None):
    with self.lock:
      return self.dict.get(key, default_value)

  def delete(self, key):
    with self.lock:
      del self.dict[key]

  def values(self):
    with self.lock:
      return self.dict.values()

  def Increment(self, key, inc, default_value=0):
    """Atomically updates the stored value associated with the given key.

    Performs the atomic equivalent of
    dict[key] = dict.get(key, default_value) + inc.

    Args:
      key: lookup key for the value of the first operand of the "+" operation.
      inc: Second operand of the "+" operation.
      default_value: Default value if there is no existing value for the key.

    Returns:
      Incremented value.
    """
    with self.lock:
      val = self.dict.get(key, default_value) + inc
      self.dict[key] = val
      return val


class ProcessAndThreadSafeInt(object):
  """This class implements a process and thread-safe integer.

  It is backed either by a multiprocessing Value of type 'i' or an internal
  threading lock.  This simplifies the calling pattern for
  global variables that could be a Multiprocessing.Value or an integer.
  Without this class, callers need to write code like this:

  global variable_name
  if isinstance(variable_name, int):
    return variable_name
  else:
    return variable_name.value
  """

  def __init__(self, multiprocessing_is_available):
    self.multiprocessing_is_available = multiprocessing_is_available
    if self.multiprocessing_is_available:
      # Lock is implicit in multiprocessing.Value
      self.value = multiprocessing_context.Value('i', 0)
    else:
      self.lock = threading.Lock()
      self.value = 0

  def Reset(self, reset_value=0):
    if self.multiprocessing_is_available:
      self.value.value = reset_value
    else:
      with self.lock:
        self.value = reset_value

  def Increment(self):
    if self.multiprocessing_is_available:
      self.value.value += 1
    else:
      with self.lock:
        self.value += 1

  def Decrement(self):
    if self.multiprocessing_is_available:
      self.value.value -= 1
    else:
      with self.lock:
        self.value -= 1

  def GetValue(self):
    if self.multiprocessing_is_available:
      return self.value.value
    else:
      with self.lock:
        return self.value


def _IncreaseSoftLimitForResource(resource_name, fallback_value):
  """Sets a new soft limit for the maximum number of open files.

  The soft limit is used for this process (and its children), but the
  hard limit is set by the system and cannot be exceeded.

  We will first try to set the soft limit to the hard limit's value; if that
  fails, we will try to set the soft limit to the fallback_value iff this would
  increase the soft limit.

  Args:
    resource_name: Name of the resource to increase the soft limit for.
    fallback_value: Fallback value to be used if we couldn't set the
                    soft value to the hard value (e.g., if the hard value
                    is "unlimited").

  Returns:
    Current soft limit for the resource (after any changes we were able to
    make), or -1 if the resource doesn't exist.
  """

  # Get the value of the resource.
  try:
    (soft_limit, hard_limit) = resource.getrlimit(resource_name)
  except (resource.error, ValueError):
    # The resource wasn't present, so we can't do anything here.
    return -1

  # Try to set the value of the soft limit to the value of the hard limit.
  if hard_limit > soft_limit:  # Some OS's report 0 for "unlimited".
    try:
      resource.setrlimit(resource_name, (hard_limit, hard_limit))
      return hard_limit
    except (resource.error, ValueError):
      # We'll ignore this and try the fallback value.
      pass

  # Try to set the value of the soft limit to the fallback value.
  if soft_limit < fallback_value:
    try:
      resource.setrlimit(resource_name, (fallback_value, hard_limit))
      return fallback_value
    except (resource.error, ValueError):
      # We couldn't change the soft limit, so just report the current
      # value of the soft limit.
      return soft_limit
  else:
    return soft_limit


def ShouldProhibitMultiprocessing():
  """Determines if the OS doesn't support multiprocessing.

  There are two cases we currently know about:
    - Multiple processes are not supported on Windows.
    - If an error is encountered while using multiple processes on Alpine Linux
      gsutil hangs. For this case it's possible we could do more work to find
      the root cause but after a fruitless initial attempt we decided instead
      to fall back on multi-threading w/o multiprocesing.

  Returns:
    (bool indicator if multiprocessing should be prohibited, OS name)
  """
  if system_util.IS_WINDOWS:
    # Issues have been observed while trying to use multi-processing in Windows
    return (True, 'Windows')
  if system_util.IS_OSX:
    # macOS does not contain /etc/os-release, used in this method. This
    # shortcuts raising an exception and returning 'Unknown' as an OS.
    return (False, 'macOS')
  try:
    with open('/etc/os-release', 'r') as f:
      # look for line that contains 'NAME=' both PRETTY_NAME and NAME should
      # be acceptable to try to find if alpine linux is being used.
      for line in f.read().splitlines():
        if 'NAME=' in line:
          os_name = line.split('=')[1].strip('"')
          return ('alpine linux' in os_name.lower(), os_name)
      # Unable to determine OS. NAME line not found in /etc/os-release file.
      return (False, 'Unknown')
  except IOError as e:
    if e.errno == errno.ENOENT:
      logging.debug('Unable to open /etc/os-release to determine whether OS '
                    'supports multiprocessing: errno=%d, message=%s' %
                    (e.errno, str(e)))
      return (False, 'Unknown')
    else:
      raise
  except Exception as exc:
    logging.debug('Something went wrong while trying to determine '
                  'multiprocessing capabilities.\nMessage: {0}'.format(
                      str(exc)))
    return (False, 'Unknown')


def CheckMultiprocessingAvailableAndInit(logger=None):
  """Checks if multiprocessing is available, and if so performs initialization.

  There are some environments in which there is no way to use multiprocessing
  logic that's built into Python (e.g., if /dev/shm is not available, then
  we can't create semaphores). This simply tries out a few things that will be
  needed to make sure the environment can support the pieces of the
  multiprocessing module that we need.

  See gslib.command.InitializeMultiprocessingVariables for
  an explanation of why this is necessary.

  Args:
    logger: (logging.Logger) Logger to use for debug output.

  Returns:
    (MultiprocessingIsAvailableResult) A namedtuple with the following attrs:
      - multiprocessing_is_available: True iff the multiprocessing module is
            available for use.
      - stack_trace: The stack trace generated by the call we tried that
            failed.
  """
  # pylint: disable=global-variable-undefined
  global _cached_multiprocessing_is_available
  global _cached_multiprocessing_check_stack_trace
  global _cached_multiprocessing_is_available_message
  if _cached_multiprocessing_is_available is not None:
    if logger:
      logger.debug(_cached_multiprocessing_check_stack_trace)
      logger.warn(_cached_multiprocessing_is_available_message)
    return MultiprocessingIsAvailableResult(
        is_available=_cached_multiprocessing_is_available,
        stack_trace=_cached_multiprocessing_check_stack_trace)

  should_prohibit_multiprocessing, os_name = ShouldProhibitMultiprocessing()
  if should_prohibit_multiprocessing:
    message = """
Multiple processes are not supported on %s. Operations requesting
parallelism will be executed with multiple threads in a single process only.
""" % os_name
    if logger:
      logger.warn(message)
    return MultiprocessingIsAvailableResult(is_available=False,
                                            stack_trace=None)

  stack_trace = None
  multiprocessing_is_available = True
  message = """
You have requested multiple processes for an operation, but the
required functionality of Python\'s multiprocessing module is not available.
Operations requesting parallelism will be executed with multiple threads in a
single process only.
"""
  try:
    # Fails if /dev/shm (or some equivalent thereof) is not available for use
    # (e.g., there's no implementation, or we can't write to it, etc.).
    try:
      multiprocessing_context.Value('i', 0)
    except:
      message += """
Please ensure that you have write access to both /dev/shm and /run/shm.
"""
      raise  # We'll handle this in one place below.

    global top_level_manager  # pylint: disable=global-variable-undefined
    top_level_manager = multiprocessing_context.Manager()

    # Check that the max number of open files is reasonable. Always check this
    # after we're sure that the basic multiprocessing functionality is
    # available, since this won't matter unless that's true.
    limit = -1
    if _HAS_RESOURCE_MODULE:
      # Try to set this with both resource names - RLIMIT_NOFILE for most Unix
      # platforms, and RLIMIT_OFILE for BSD. Ignore AttributeError because the
      # "resource" module is not guaranteed to know about these names.
      try:
        limit = max(
            limit,
            _IncreaseSoftLimitForResource(
                resource.RLIMIT_NOFILE,
                constants.MIN_ACCEPTABLE_OPEN_FILES_LIMIT))
      except AttributeError:
        pass

      try:
        limit = max(
            limit,
            _IncreaseSoftLimitForResource(
                resource.RLIMIT_OFILE,
                constants.MIN_ACCEPTABLE_OPEN_FILES_LIMIT))
      except AttributeError:
        pass

    if limit < constants.MIN_ACCEPTABLE_OPEN_FILES_LIMIT:
      message += ("""
Your max number of open files, %s, is too low to allow safe multiprocessing.
On Linux you can fix this by adding something like "ulimit -n 10000" to your
~/.bashrc or equivalent file and opening a new terminal.

On macOS, you may also need to run a command like this once (in addition to the
above instructions), which might require a restart of your system to take
effect:
  launchctl limit maxfiles 10000

Alternatively, edit /etc/launchd.conf with something like:
  limit maxfiles 10000 10000

""" % limit)
      raise Exception('Max number of open files, %s, is too low.' % limit)
  except:  # pylint: disable=bare-except
    stack_trace = traceback.format_exc()
    multiprocessing_is_available = False
    if logger is not None:
      logger.debug(stack_trace)
      logger.warn(message)

  # Set the cached values so that we never need to do this check again.
  _cached_multiprocessing_is_available = multiprocessing_is_available
  _cached_multiprocessing_check_stack_trace = stack_trace
  _cached_multiprocessing_is_available_message = message
  return MultiprocessingIsAvailableResult(
      is_available=_cached_multiprocessing_is_available,
      stack_trace=_cached_multiprocessing_check_stack_trace)


def CreateLock():
  """Returns either a multiprocessing lock or a threading lock.

  Use Multiprocessing lock iff we have access to the parts of the
  multiprocessing module that are necessary to enable parallelism in operations.

  Returns:
    Multiprocessing or threading lock.
  """
  if CheckMultiprocessingAvailableAndInit().is_available:
    return top_level_manager.Lock()
  else:
    return threading.Lock()


# Pylint gets confused by the mixed lower and upper-case method names in
# AtomicDict.
# pylint: disable=invalid-name
def PutToQueueWithTimeout(queue, msg, timeout=STATUS_QUEUE_OP_TIMEOUT):
  """Puts an item to the status queue.

  If the queue is full, this function will timeout periodically and repeat
  until success. This avoids deadlock during shutdown by never making a fully
  blocking call to the queue, since Python signal handlers cannot execute
  in between instructions of the Python interpreter (see
  https://docs.python.org/2/library/signal.html for details).

  Args:
    queue: Queue class (typically the global status queue)
    msg: message to post to the queue.
    timeout: (optional) amount of time to wait before repeating put request.
  """
  put_success = False
  while not put_success:
    try:
      queue.put(msg, timeout=timeout)
      put_success = True
    except Queue.Full:
      pass


# pylint: enable=invalid-name
