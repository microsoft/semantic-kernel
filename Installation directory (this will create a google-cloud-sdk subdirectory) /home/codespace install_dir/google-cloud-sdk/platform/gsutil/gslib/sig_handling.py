# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Signal handling functions."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import os
import re
import signal
import sys
import traceback

from gslib import metrics
from gslib.exception import ControlCException
from gslib.utils.constants import UTF8
from gslib.utils.system_util import IS_WINDOWS

if IS_WINDOWS:
  import ctypes  # pylint: disable=g-import-not-at-top

# Maps from signal_num to list of signal handlers to call.
_non_final_signal_handlers = {}
# Maps from signal_num to the final signal handler (if any) that should be
# called for that signal.
_final_signal_handlers = {}


def RegisterSignalHandler(signal_num, handler, is_final_handler=False):
  """Registers a handler for signal signal_num.

  Unlike calling signal.signal():
    - This function can be called from any thread (and will cause the handler to
      be run by the main thread when the signal is received).
    - Handlers are cumulative: When a given signal is received, all registered
      handlers will be executed (with the exception that only the last handler
      to register with is_final_handler=True will be called).

  Handlers should make no ordering assumptions, other than that the last handler
  to register with is_final_handler=True will be called after all the other
  handlers.

  Args:
    signal_num: The signal number with which to associate handler.
    handler: The handler.
    is_final_handler: Bool indicator whether handler should be called last among
                      all the handlers for this signal_num. The last handler to
                      register this way survives; other handlers registered with
                      is_final_handler=True will not be called when the signal
                      is received.
  Raises:
    RuntimeError: if attempt is made to register a signal_num not in
        GetCaughtSignals.
  """
  if signal_num not in GetCaughtSignals():
    raise RuntimeError('Attempt to register handler (%s) for signal %d, which '
                       'is not in GetCaughtSignals' % (handler, signal_num))
  if is_final_handler:
    _final_signal_handlers[signal_num] = handler
  else:
    _non_final_signal_handlers[signal_num].append(handler)


def _SignalHandler(signal_num, cur_stack_frame):
  """Global signal handler.

  When a signal is caught we execute each registered handler for that signal.

  Args:
    signal_num: Signal that was caught.
    cur_stack_frame: Unused.
  """
  if signal_num in _non_final_signal_handlers:
    for handler in _non_final_signal_handlers[signal_num]:
      handler(signal_num, cur_stack_frame)
  if signal_num in _final_signal_handlers:
    _final_signal_handlers[signal_num](signal_num, cur_stack_frame)


def InitializeSignalHandling():
  """Initializes global signal handling.

  Sets up global signal handler for each signal we handle.
  """
  for signal_num in GetCaughtSignals():
    _non_final_signal_handlers[signal_num] = []
    # Make main signal handler catch the signal.
    signal.signal(signal_num, _SignalHandler)


def GetCaughtSignals():
  """Returns terminating signals that can be caught on this OS platform."""
  signals = [signal.SIGINT, signal.SIGTERM]
  if not IS_WINDOWS:
    # Windows doesn't have SIGQUIT.
    signals.append(signal.SIGQUIT)
  return signals


def KillProcess(pid):
  """Make best effort to kill the given process.

  We ignore all exceptions so a caller looping through a list of processes will
  continue attempting to kill each, even if one encounters a problem.

  Args:
    pid: The process ID.
  """
  try:
    # os.kill doesn't work in Python3 versions before 3.2.
    if IS_WINDOWS and ((3, 0) <= sys.version_info[:3] < (3, 2)):
      kernel32 = ctypes.windll.kernel32
      handle = kernel32.OpenProcess(1, 0, pid)
      kernel32.TerminateProcess(handle, 0)
    else:
      os.kill(pid, signal.SIGKILL)
  except:  # pylint: disable=bare-except
    pass


# pylint: disable=unused-argument
def MultithreadedMainSignalHandler(signal_num, cur_stack_frame):
  """Final signal handler for multi-threaded main process."""
  if signal_num == signal.SIGINT:
    if logging.getLogger().isEnabledFor(logging.DEBUG):
      stack_trace = ''.join(traceback.format_list(traceback.extract_stack()))
      err = ('DEBUG: Caught CTRL-C (signal %d) - Exception stack trace:\n'
             '    %s' % (signal_num, re.sub('\\n', '\n    ', stack_trace)))
      try:
        sys.stderr.write(err.encode(UTF8))
      except (UnicodeDecodeError, TypeError) as e:
        # Can happen when outputting invalid Unicode filenames.
        # or in python3, where stderr only accepts arguments of type
        # str, not bytes.
        sys.stderr.write(err)
    else:
      sys.stderr.write('Caught CTRL-C (signal %d) - exiting\n' % signal_num)

  metrics.LogFatalError(exception=ControlCException())
  metrics.Shutdown()
  KillProcess(os.getpid())


def ChildProcessSignalHandler(signal_num, cur_stack_frame):
  """Final signal handler for child processes."""
  KillProcess(os.getpid())


# pylint: enable=unused-argument
