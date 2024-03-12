# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Progress Tracker for Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import os
import signal
import sys
import threading
import time

import enum
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import multiline
from googlecloudsdk.core.console.style import parser

import six

collections_abc = collections
if sys.version_info > (3, 8):
  collections_abc = collections.abc


def ProgressTracker(
    message=None,
    autotick=True,
    detail_message_callback=None,
    done_message_callback=None,
    tick_delay=0.2,
    interruptable=True,
    screen_reader=False,
    aborted_message=console_io.OperationCancelledError.DEFAULT_MESSAGE,
    no_spacing=False):
  """A context manager for telling the user about long-running progress.

  Args:
    message: str, The message to show next to the spinner.
    autotick: bool, True to have the spinner tick on its own. Otherwise, you
      need to call Tick() explicitly to move the spinner.
    detail_message_callback: func, A no argument function that will be called
      and the result appended to message each time it needs to be printed.
    done_message_callback: func, A no argument function whose result will be
      appended to message if the progress tracker successfully exits.
    tick_delay: float, The amount of time to wait between ticks, in second.
    interruptable: boolean, True if the user can ctrl-c the operation. If so,
      it will stop and will report as aborted. If False, a message will be
      displayed saying that it cannot be cancelled.
    screen_reader: boolean, override for screen reader accessibility property
      toggle.
    aborted_message: str, A custom message to put in the exception when it is
      cancelled by the user.
    no_spacing: boolean, Removes ellipses and other spacing between text.

  Returns:
    The progress tracker.
  """
  style = properties.VALUES.core.interactive_ux_style.Get()
  if style == properties.VALUES.core.InteractiveUXStyles.OFF.name:
    return NoOpProgressTracker(interruptable, aborted_message)
  elif style == properties.VALUES.core.InteractiveUXStyles.TESTING.name:
    return _StubProgressTracker(message, interruptable, aborted_message)
  else:
    is_tty = console_io.IsInteractive(error=True)
    tracker_cls = (_NormalProgressTracker if is_tty
                   else _NonInteractiveProgressTracker)
    screen_reader = (screen_reader or
                     properties.VALUES.accessibility.screen_reader.GetBool())
    spinner_override_message = None
    if screen_reader:
      tick_delay = 1
      spinner_override_message = 'working'

    return tracker_cls(message, autotick, detail_message_callback,
                       done_message_callback, tick_delay, interruptable,
                       aborted_message, spinner_override_message, no_spacing)


class _BaseProgressTracker(six.with_metaclass(abc.ABCMeta, object)):
  """A context manager for telling the user about long-running progress."""

  def __init__(self, message, autotick, detail_message_callback,
               done_message_callback, tick_delay, interruptable,
               aborted_message, spinner_override_message, no_spacing):
    self._stream = sys.stderr
    if message is None:
      self._spinner_only = True
      self._message = ''
      self._prefix = ''
    else:
      self._spinner_only = False
      self._message = message
      self._prefix = message + ('' if no_spacing else '...')
    self._detail_message_callback = detail_message_callback
    self.spinner_override_message = spinner_override_message
    self._done_message_callback = done_message_callback
    self._ticks = 0
    self._done = False
    self._lock = threading.Lock()
    self._tick_delay = tick_delay
    self._ticker = None
    console_width = console_attr.ConsoleAttr().GetTermSize()[0]
    if console_width < 0:
      # This can happen if we're on a pseudo-TTY. Set it to 0 and also
      # turn off output to prevent it from stopping responding.
      console_width = 0
    self._output_enabled = log.IsUserOutputEnabled() and console_width != 0
    # Don't bother autoticking if we aren't going to print anything.
    self.__autotick = autotick and self._output_enabled
    self._interruptable = interruptable
    self._aborted_message = aborted_message
    self._old_signal_handler = None
    self._symbols = console_attr.GetConsoleAttr().GetProgressTrackerSymbols()
    self._no_spacing = no_spacing
    self._is_tty = console_io.IsInteractive(error=True)

  @property
  def _autotick(self):
    return self.__autotick

  def _GetPrefix(self):
    if self._is_tty and self._detail_message_callback:
      detail_message = self._detail_message_callback()
      if detail_message:
        if self._no_spacing:
          return self._prefix + detail_message
        return self._prefix + ' ' + detail_message + '...'
    return self._prefix

  def _SetUpSignalHandler(self):
    """Sets up a signal handler for handling SIGINT."""
    def _CtrlCHandler(unused_signal, unused_frame):
      if self._interruptable:
        raise console_io.OperationCancelledError(self._aborted_message)
      else:
        with self._lock:
          sys.stderr.write('\n\nThis operation cannot be cancelled.\n\n')
    try:
      self._old_signal_handler = signal.signal(signal.SIGINT, _CtrlCHandler)
      self._restore_old_handler = True
    except ValueError:
      # Only works in the main thread. Gcloud does not run in the main thread
      # in gcloud interactive.
      self._restore_old_handler = False

  def _TearDownSignalHandler(self):
    if self._restore_old_handler:
      try:
        signal.signal(signal.SIGINT, self._old_signal_handler)
      except ValueError:
        pass  # only works in main thread

  def __enter__(self):
    # Setup signal handlers
    self._SetUpSignalHandler()

    log.file_only_logger.info(self._GetPrefix())
    self._Print()
    if self._autotick:
      def Ticker():
        while True:
          _SleepSecs(self._tick_delay)
          if self.Tick():
            return
      self._ticker = threading.Thread(target=Ticker)
      self._ticker.start()
    return self

  def __exit__(self, unused_ex_type, exc_value, unused_traceback):
    with self._lock:
      self._done = True
      # If an exception was raised during progress tracking, exit silently here
      # and let the appropriate exception handler tell the user what happened.
      if exc_value:
        # This is to prevent the tick character from appearing before 'failed.'
        # (ex. 'message...failed' instead of 'message.../failed.')
        if isinstance(exc_value, console_io.OperationCancelledError):
          self._Print('aborted by ctrl-c.\n')
        else:
          self._Print('failed.\n')
      elif not self._spinner_only:
        if self._done_message_callback:
          self._Print(self._done_message_callback())
        else:
          self._Print('done.\n')
    if self._ticker:
      self._ticker.join()
    self._TearDownSignalHandler()

  @abc.abstractmethod
  def Tick(self):
    """Give a visual indication to the user that some progress has been made.

    Output is sent to sys.stderr. Nothing is shown if output is not a TTY.

    Returns:
      Whether progress has completed.
    """
    pass

  @abc.abstractmethod
  def _Print(self, message=''):
    """Prints an update containing message to the output stream."""
    pass


class _NormalProgressTracker(_BaseProgressTracker):
  """A context manager for telling the user about long-running progress."""

  def __enter__(self):
    self._SetupOutput()
    return super(_NormalProgressTracker, self).__enter__()

  def _SetupOutput(self):
    def _FormattedCallback():
      if self._detail_message_callback:
        detail_message = self._detail_message_callback()
        if detail_message:
          if self._no_spacing:
            return detail_message
          return ' ' + detail_message + '...'
      return None

    self._console_output = multiline.SimpleSuffixConsoleOutput(self._stream)
    self._console_message = self._console_output.AddMessage(
        self._prefix, detail_message_callback=_FormattedCallback)

  def Tick(self):
    """Give a visual indication to the user that some progress has been made.

    Output is sent to sys.stderr. Nothing is shown if output is not a TTY.

    Returns:
      Whether progress has completed.
    """
    with self._lock:
      if not self._done:
        self._ticks += 1
        self._Print(self._GetSuffix())
    self._stream.flush()
    return self._done

  def _GetSuffix(self):
    if self.spinner_override_message:
      num_dots = self._ticks % 4  # 3 dots max.
      return self.spinner_override_message + '.' * num_dots
    else:
      return self._symbols.spin_marks[
          self._ticks % len(self._symbols.spin_marks)]

  def _Print(self, message=''):
    """Reprints the prefix followed by an optional message.

    If there is a multiline message, we print the full message and every
    time the Prefix Message is the same, we only reprint the last line to
    account for a different 'message'. If there is a new message, we print
    on a new line.

    Args:
      message: str, suffix of message
    """
    if self._spinner_only or not self._output_enabled:
      return

    self._console_output.UpdateMessage(self._console_message, message)
    self._console_output.UpdateConsole()


class _NonInteractiveProgressTracker(_BaseProgressTracker):
  """A context manager for telling the user about long-running progress."""

  def Tick(self):
    """Give a visual indication to the user that some progress has been made.

    Output is sent to sys.stderr. Nothing is shown if output is not a TTY.

    Returns:
      Whether progress has completed.
    """
    with self._lock:
      if not self._done:
        self._Print('.')
    return self._done

  def _Print(self, message=''):
    """Reprints the prefix followed by an optional message.

    If there is a multiline message, we print the full message and every
    time the Prefix Message is the same, we only reprint the last line to
    account for a different 'message'. If there is a new message, we print
    on a new line.

    Args:
      message: str, suffix of message
    """
    if self._spinner_only or not self._output_enabled:
      return

    # Since we are not in a tty, print will be called twice outside of normal
    # ticking. The first time during __enter__, where the tracker message should
    # be outputted. The second time is during __exit__, where a status updated
    # contained in message will be outputted.
    display_message = self._GetPrefix()
    self._stream.write(message or display_message + '\n')
    return


class NoOpProgressTracker(object):
  """A Progress tracker that doesn't do anything."""

  def __init__(self, interruptable, aborted_message):
    self._interruptable = interruptable
    self._aborted_message = aborted_message
    self._done = False

  def __enter__(self):
    def _CtrlCHandler(unused_signal, unused_frame):
      if self._interruptable:
        raise console_io.OperationCancelledError(self._aborted_message)
    self._old_signal_handler = signal.signal(signal.SIGINT, _CtrlCHandler)
    return self

  def Tick(self):
    return self._done

  def __exit__(self, exc_type, exc_val, exc_tb):
    self._done = True
    signal.signal(signal.SIGINT, self._old_signal_handler)


class _StubProgressTracker(NoOpProgressTracker):
  """A Progress tracker that only prints deterministic start and end points.

  No UX about tracking should be exposed here. This is strictly for being able
  to tell that the tracker ran, not what it actually looks like.
  """

  def __init__(self, message, interruptable, aborted_message):
    super(_StubProgressTracker, self).__init__(interruptable, aborted_message)
    self._message = message or ''
    self._stream = sys.stderr

  def __exit__(self, exc_type, exc_val, exc_tb):
    if not exc_val:
      status = 'SUCCESS'
    elif isinstance(exc_val, console_io.OperationCancelledError):
      status = 'INTERRUPTED'
    else:
      status = 'FAILURE'

    if log.IsUserOutputEnabled():
      self._stream.write(console_io.JsonUXStub(
          console_io.UXElementType.PROGRESS_TRACKER,
          message=self._message, status=status) + '\n')
    return super(_StubProgressTracker, self).__exit__(exc_type, exc_val, exc_tb)


def _SleepSecs(seconds):
  """Sleep int or float seconds. For mocking sleeps in this module."""
  time.sleep(seconds)


def CompletionProgressTracker(ofile=None, timeout=4.0, tick_delay=0.1,
                              background_ttl=60.0, autotick=True):
  """A context manager for visual feedback during long-running completions.

  A completion that exceeds the timeout is assumed to be refreshing the cache.
  At that point the progress tracker displays '?', forks the cache operation
  into the background, and exits.  This gives the background cache update a
  chance finish.  After background_ttl more seconds the update is forcibly
  exited (forced to call exit rather than killed by signal) to prevent not
  responding updates from proliferating in the background.

  Args:
    ofile: The stream to write to.
    timeout: float, The amount of time in second to show the tracker before
      backgrounding it.
    tick_delay: float, The time in second between ticks of the spinner.
    background_ttl: float, The number of seconds to allow the completion to
      run in the background before killing it.
    autotick: bool, True to tick the spinner automatically.

  Returns:
    The completion progress tracker.
  """

  style = properties.VALUES.core.interactive_ux_style.Get()
  if (style == properties.VALUES.core.InteractiveUXStyles.OFF.name or
      style == properties.VALUES.core.InteractiveUXStyles.TESTING.name):
    return _NoOpCompletionProgressTracker()
  else:
    return _NormalCompletionProgressTracker(
        ofile, timeout, tick_delay, background_ttl, autotick)


class _NormalCompletionProgressTracker(object):
  """A context manager for visual feedback during long-running completions.

  A completion that exceeds the timeout is assumed to be refreshing the cache.
  At that point the progress tracker displays '?', forks the cache operation
  into the background, and exits.  This gives the background cache update a
  chance finish.  After background_ttl more seconds the update is forcibly
  exited (forced to call exit rather than killed by signal) to prevent not
  responding updates from proliferating in the background.
  """

  _COMPLETION_FD = 9

  def __init__(self, ofile, timeout, tick_delay, background_ttl, autotick):
    self._ofile = ofile or self._GetStream()
    self._timeout = timeout
    self._tick_delay = tick_delay
    self.__autotick = autotick
    self._background_ttl = background_ttl
    self._ticks = 0
    self._symbols = console_attr.GetConsoleAttr().GetProgressTrackerSymbols()

  def __enter__(self):
    if self._autotick:
      self._old_handler = signal.signal(signal.SIGALRM, self._Spin)
      self._old_itimer = signal.setitimer(
          signal.ITIMER_REAL, self._tick_delay, self._tick_delay)
    return self

  def __exit__(self, unused_type=None, unused_value=True,
               unused_traceback=None):
    if self._autotick:
      signal.setitimer(signal.ITIMER_REAL, *self._old_itimer)
      signal.signal(signal.SIGALRM, self._old_handler)
    if not self._TimedOut():
      self._WriteMark(' ')

  def _TimedOut(self):
    """True if the tracker has timed out."""
    return self._timeout < 0

  def _Spin(self, unused_sig=None, unused_frame=None):
    """Rotates the spinner one tick and checks for timeout."""
    self._ticks += 1
    self._WriteMark(self._symbols.spin_marks[
        self._ticks % len(self._symbols.spin_marks)])
    self._timeout -= self._tick_delay
    if not self._TimedOut():
      return
    # Timed out.
    self._WriteMark('?')
    # Exit the parent process.
    if os.fork():
      os._exit(1)  # pylint: disable=protected-access
    # Allow the child to run in the background for up to self._background_ttl
    # more seconds before being forcefully exited.
    signal.signal(signal.SIGALRM, self._ExitBackground)
    signal.setitimer(
        signal.ITIMER_REAL, self._background_ttl, self._background_ttl)
    # Suppress the explicit completion status channel.  stdout and stderr have
    # already been suppressed.
    self._ofile = None

  def _WriteMark(self, mark):
    """Writes one mark to self._ofile."""
    if self._ofile:
      self._ofile.write(mark + '\b')
      self._ofile.flush()

  @staticmethod
  def _ExitBackground():
    """Unconditionally exits the background completer process after timeout."""
    os._exit(1)  # pylint: disable=protected-access

  @property
  def _autotick(self):
    return self.__autotick

  @staticmethod
  def _GetStream():
    """Returns the completer output stream."""
    return os.fdopen(
        os.dup(_NormalCompletionProgressTracker._COMPLETION_FD), 'w')


class _NoOpCompletionProgressTracker(object):
  """A Progress tracker that prints nothing."""

  def __init__(self):
    pass

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    pass


def StagedProgressTracker(
    message, stages, tracker_id=None, autotick=True, tick_delay=0.1,
    interruptable=True, done_message_callback=None, success_message=None,
    warning_message=None, failure_message=None,
    aborted_message=console_io.OperationCancelledError.DEFAULT_MESSAGE,
    suppress_output=False):
  """A progress tracker for performing actions with multiple stages.

  The progress tracker is a context manager. To start displaying information
  about a running stage, call StartStage within the staged progress tracker
  context. To update the message of a stage, use UpdateStage. When a stage is
  completed/failed there are CompleteStage and FailStage methods on the
  tracker as well.

  Note that stages do not need to be started/completed in order. In
  non-multiline (the only supported mode) output mode, the displayed stage will
  be the earliest started stage that has not been completed.

  Example Usage:
    stages = [
      Stage('Getting bread...', key='bread'),
      Stage('Getting peanut butter...', key='pb'),
      Stage('Making sandwich...', key='make')]
    with StagedProgressTracker(
        'Making sandwich...',
        stages,
        success_message='Time to eat!',
        failure_message='Time to order delivery..!',
        tracker_id='meta.make_sandwich') as tracker:
      tracker.StartStage('bread')
      # Go to pantry
      tracker.UpdateStage('bread', 'Looking for bread in the pantry')
      # Get bread
      tracker.CompleteStage('bread', 'Got some whole wheat bread!')

      tracker.StartStage('pb')
      # Look for peanut butter
      if pb_not_found:
        error = exceptions.NoPeanutButterError('So sad!')
        tracker.FailStage('pb', error)
      elif pb_not_organic:
        tracker.CompleteStageWithWarning('pb', 'The pb is not organic!')
      else:
        tracker.CompleteStage('bread', 'Got some organic pb!')

  Args:
    message: str, The message to show next to the spinner.
    stages: list[Stage], A list of stages for the progress tracker to run. Once
      you pass the stages to a StagedProgressTracker, they're owned by the
      tracker and you should not mutate them.
    tracker_id: str The ID of this tracker that will be used for metrics.
    autotick: bool, True to have the spinner tick on its own. Otherwise, you
      need to call Tick() explicitly to move the spinner.
    tick_delay: float, The amount of time to wait between ticks, in second.
    interruptable: boolean, True if the user can ctrl-c the operation. If so,
      it will stop and will report as aborted. If False,
    done_message_callback: func, A callback to get a more detailed done message.
    success_message: str, A message to display on success of all tasks.
    warning_message: str, A message to display when no task fails but one or
      more tasks complete with a warning and none fail.
    failure_message: str, A message to display on failure of a task.
    aborted_message: str, A custom message to put in the exception when it is
      cancelled by the user.
    suppress_output: bool, True to suppress output from the tracker.

  Returns:
    The progress tracker.
  """
  style = properties.VALUES.core.interactive_ux_style.Get()
  if (suppress_output
      or style == properties.VALUES.core.InteractiveUXStyles.OFF.name):
    return NoOpStagedProgressTracker(stages, interruptable, aborted_message)
  elif style == properties.VALUES.core.InteractiveUXStyles.TESTING.name:
    return _StubStagedProgressTracker(
        message, stages, interruptable, aborted_message)
  else:
    is_tty = console_io.IsInteractive(error=True)
    if is_tty:
      if console_attr.ConsoleAttr().SupportsAnsi():
        tracker_cls = _MultilineStagedProgressTracker
      else:
        tracker_cls = _NormalStagedProgressTracker
    else:
      tracker_cls = _NonInteractiveStagedProgressTracker
    return tracker_cls(
        message, stages, success_message, warning_message, failure_message,
        autotick, tick_delay, interruptable, aborted_message, tracker_id,
        done_message_callback)


class Stage(object):
  """Defines a stage of a staged progress tracker."""

  def __init__(self, header, key=None, task_id=None):
    """Encapsulates a stage in a staged progress tracker.

    A task should contain a message about what it does.

    Args:
      header: (str) The header that describes what the task is doing.
        A high level description like 'Uploading files' would be appropriate.
      key: (str) A key which can be used to access/refer to this stage. Must be
        unique within a StagedProgressTracker. If not provided, the header will
        be used as the key.
      task_id: (str) The ID of this task that will be used for metrics.
      timing metrics. NOTE: Metrics are currently not implemented yet.
    """
    self._header = header
    self._key = key if key is not None else self._header
    self.message = ''
    self.task_id = task_id
    # TODO(b/109928970): Add support for progress bars.
    # TODO(b/109928025): Add support for timing metrics by task id.

    # Task attributes
    self._is_done = False
    self.status = StageCompletionStatus.NOT_STARTED

  @property
  def key(self):
    return self._key

  @property
  def header(self):
    return self._header

  @property
  def is_done(self):
    return self._is_done


class StageCompletionStatus(enum.Enum):
  """Indicates the completion status of a stage."""
  NOT_STARTED = 'not started'
  RUNNING = 'still running'
  SUCCESS = 'done'
  FAILED = 'failed'
  INTERRUPTED = 'interrupted'
  WARNING = 'warning'


class _BaseStagedProgressTracker(collections_abc.Mapping):
  """Base class for staged progress trackers.

  During each tick, the tracker checks if there is a stage being displayed by
  checking if _stage_being_displayed is not None. If it is not none and stage
  has not completed, then the tracker will print an update. If the stage is
  done, then the tracker will write out the status of all completed stages
  in _running_stages_queue.
  """

  def __init__(self, message, stages, success_message, warning_message,
               failure_message, autotick, tick_delay, interruptable,
               aborted_message, tracker_id, done_message_callback,
               console=None):
    self._stages = collections.OrderedDict()
    for stage in stages:
      if stage.key in self._stages:
        raise ValueError('Duplicate stage key: {}'.format(stage.key))
      self._stages[stage.key] = stage
    self._stream = sys.stderr
    self._message = message
    self._success_message = success_message
    self._warning_message = warning_message
    self._failure_message = failure_message
    self._aborted_message = aborted_message
    self._done_message_callback = done_message_callback
    self._tracker_id = tracker_id
    if console is None:
      console = console_attr.GetConsoleAttr()
    console_width = console.GetTermSize()[0]
    if not isinstance(console_width, int) or console_width < 0:
      # This can happen if we're on a pseudo-TTY. Set it to 0 and also
      # turn off output to prevent it from stopping responding.
      console_width = 0
    self._output_enabled = log.IsUserOutputEnabled() and console_width != 0
    # Don't bother autoticking if we aren't going to print anything.
    self.__autotick = autotick and self._output_enabled
    self._interruptable = interruptable
    self._tick_delay = tick_delay

    self._symbols = console.GetProgressTrackerSymbols()
    self._done = False
    self._exception_is_uncaught = True
    self._ticks = 0
    self._ticker = None
    self._running_stages = set()
    self._completed_stages = []
    self._completed_with_warnings_stages = []
    self._exit_output_warnings = []
    self._lock = threading.Lock()

  def __getitem__(self, key):
    return self._stages[key]

  def __iter__(self):
    return iter(self._stages)

  def __len__(self):
    return len(self._stages)

  @property
  def _autotick(self):
    return self.__autotick

  def IsComplete(self, stage):
    """Returns True if the stage is complete."""
    return not (self.IsRunning(stage) or self.IsWaiting(stage))

  def IsRunning(self, stage):
    """Returns True if the stage is running."""
    stage = self._ValidateStage(stage, allow_complete=True)
    return stage.status == StageCompletionStatus.RUNNING

  def HasWarning(self):
    """Returns True if this tracker has encountered at least one warning."""
    return bool(self._exit_output_warnings)

  def IsWaiting(self, stage):
    """Returns True if the stage is not yet started."""
    stage = self._ValidateStage(stage, allow_complete=True)
    return stage.status == StageCompletionStatus.NOT_STARTED

  def _SetUpSignalHandler(self):
    """Sets up a signal handler for handling SIGINT."""
    def _CtrlCHandler(unused_signal, unused_frame):
      if self._interruptable:
        raise console_io.OperationCancelledError(self._aborted_message)
      else:
        self._NotifyUninterruptableError()
    try:
      self._old_signal_handler = signal.signal(signal.SIGINT, _CtrlCHandler)
      self._restore_old_handler = True
    except ValueError:
      # Only works in the main thread. Gcloud does not run in the main thread
      # in gcloud interactive.
      self._restore_old_handler = False

  def _NotifyUninterruptableError(self):
    with self._lock:
      sys.stderr.write('\n\nThis operation cannot be cancelled.\n\n')

  def _TearDownSignalHandler(self):
    if self._restore_old_handler:
      try:
        signal.signal(signal.SIGINT, self._old_signal_handler)
      except ValueError:
        pass  # only works in main thread

  def __enter__(self):
    self._SetupOutput()
    # Setup signal handlers
    self._SetUpSignalHandler()

    log.file_only_logger.info(self._message)
    self._Print()
    if self._autotick:
      def Ticker():
        while True:
          _SleepSecs(self._tick_delay)
          if self.Tick():
            return
      self._ticker = threading.Thread(target=Ticker)
      self._ticker.daemon = True
      self._ticker.start()
    return self

  def __exit__(self, unused_ex_type, exc_value, unused_traceback):
    with self._lock:
      self._done = True
      # If an exception was raised during progress tracking, exit silently here
      # and let the appropriate exception handler tell the user what happened.
      if exc_value:
        if self._exception_is_uncaught:
          self._HandleUncaughtException(exc_value)
      else:
        self._PrintExitOutput(warned=self.HasWarning())
    if self._ticker:
      self._ticker.join()
    self._TearDownSignalHandler()
    for warning_message in self._exit_output_warnings:
      log.status.Print('  %s' %  warning_message)

  def _HandleUncaughtException(self, exc_value):
    # The first print is to signal exiting the stage. The second print
    # handles the output for exiting the progress tracker.
    if isinstance(exc_value, console_io.OperationCancelledError):
      self._PrintExitOutput(aborted=True)
    else:
      # This means this was an uncaught exception. This ideally
      # should be handled by the implementer
      self._PrintExitOutput(failed=True)

  @abc.abstractmethod
  def _SetupOutput(self):
    """Sets up the output for the tracker. Gets called during __enter__."""
    pass

  def UpdateHeaderMessage(self, message):
    """Updates the header messsage if supported."""
    pass

  @abc.abstractmethod
  def Tick(self):
    """Give a visual indication to the user that some progress has been made.

    Output is sent to sys.stderr. Nothing is shown if output is not a TTY.

    Returns:
      Whether progress has completed.
    """
    pass

  def _GetTickMark(self, ticks):
    """Returns the next tick mark."""
    return self._symbols.spin_marks[self._ticks % len(self._symbols.spin_marks)]

  def _GetStagedCompletedSuffix(self, status):
    return status.value

  def _ValidateStage(self, key, allow_complete=False):
    """Validates the stage belongs to the tracker.

    Args:
      key: the key of the stage to validate.
      allow_complete: whether to error on an already-complete stage

    Returns:
      The validated Stage object, even if we were passed a key.
    """
    if key not in self:
      raise ValueError('This stage does not belong to this progress tracker.')
    stage = self.get(key)
    if not allow_complete and stage.status not in {
        StageCompletionStatus.NOT_STARTED, StageCompletionStatus.RUNNING}:
      raise ValueError('This stage has already completed.')
    return stage

  def StartStage(self, key):
    """Informs the progress tracker that this stage has started."""
    stage = self._ValidateStage(key)
    with self._lock:
      self._running_stages.add(key)
      stage.status = StageCompletionStatus.RUNNING
      self._StartStage(stage)
    self.Tick()

  def _StartStage(self, stage):
    """Override to customize behavior on starting a stage."""
    return

  def _FailStage(self, stage, failure_exception, message):
    """Override to customize behavior on failing a stage."""
    pass

  def _PrintExitOutput(self, aborted=False, warned=False, failed=False):
    """Override to customize behavior on printing exit output."""
    pass

  def UpdateStage(self, key, message):
    """Updates a stage in the progress tracker."""
    # TODO(b/109928970): Add support for progress bars.
    stage = self._ValidateStage(key)
    with self._lock:
      stage.message = message
    self.Tick()

  def CompleteStage(self, key, message=None):
    """Informs the progress tracker that this stage has completed."""
    stage = self._ValidateStage(key)
    with self._lock:
      stage.status = StageCompletionStatus.SUCCESS
      stage._is_done = True  # pylint: disable=protected-access
      self._running_stages.discard(key)
      if message is not None:
        stage.message = message
      self._CompleteStage(stage)
    self.Tick()  # This ensures output is properly flushed out.

  def _CompleteStage(self, stage):
    return

  def CompleteStageWithWarning(self, key, warning_message):
    self.CompleteStageWithWarnings(key, [warning_message])

  def CompleteStageWithWarnings(self, key, warning_messages):
    """Informs the progress tracker that this stage completed with warnings.

    Args:
      key: str, key for the stage to fail.
      warning_messages: list of str, user visible warning messages.
    """
    stage = self._ValidateStage(key)
    with self._lock:
      stage.status = StageCompletionStatus.WARNING
      stage._is_done = True  # pylint: disable=protected-access
      self._running_stages.discard(key)
      self._exit_output_warnings.extend(warning_messages)
      self._completed_with_warnings_stages.append(stage.key)
      self._CompleteStageWithWarnings(stage, warning_messages)
    self.Tick()  # This ensures output is properly flushed out.

  def _CompleteStageWithWarnings(self, stage, warning_messages):
    """Override to customize behavior on completing a stage with warnings."""
    pass

  def FailStage(self, key, failure_exception, message=None):
    """Informs the progress tracker that this stage has failed.

    Args:
      key: str, key for the stage to fail.
      failure_exception: Exception, raised by __exit__.
      message: str, user visible message for failure.
    """
    stage = self._ValidateStage(key)
    with self._lock:
      stage.status = StageCompletionStatus.FAILED
      stage._is_done = True  # pylint: disable=protected-access
      self._running_stages.discard(key)
      if message is not None:
        stage.message = message
      self._FailStage(stage, failure_exception, message)
    self.Tick()  # This ensures output is properly flushed out.
    if failure_exception:
      self._PrintExitOutput(failed=True)
      self._exception_is_uncaught = False
      raise failure_exception  # pylint: disable=raising-bad-type

  def AddWarning(self, warning_message):
    """Add a warning message independent of any particular stage.

    This warning message will be printed on __exit__.

    Args:
      warning_message: str, user visible warning message.
    """
    with self._lock:
      self._exit_output_warnings.append(warning_message)


class _NormalStagedProgressTracker(_BaseStagedProgressTracker):
  """A context manager for telling the user about long-running progress.

  This class uses the core.console.multiline.ConsoleOutput interface for
  outputting. The header and each stage is defined as a message object
  contained by the ConsoleOutput message.
  """

  def __init__(self, *args, **kwargs):
    self._running_stages_queue = []
    self._stage_being_displayed = None
    super(_NormalStagedProgressTracker, self).__init__(*args, **kwargs)

  def _SetupOutput(self):
    # Console outputting objects
    self._console_output = multiline.SimpleSuffixConsoleOutput(self._stream)
    self._header_message = self._console_output.AddMessage(self._message)
    self._current_stage_message = self._header_message

  def _FailStage(self, stage, failure_exception, message=None):
    for running_stage in self._running_stages_queue:
      if stage != running_stage:
        running_stage.status = StageCompletionStatus.INTERRUPTED
      running_stage._is_done = True  # pylint: disable=protected-access

  def _StartStage(self, stage):
    """Informs the progress tracker that this stage has started."""
    self._running_stages_queue.append(stage)
    if self._stage_being_displayed is None:
      self._LoadNextStageForDisplay()

  def _LoadNextStageForDisplay(self):
    if self._running_stages_queue:
      self._stage_being_displayed = self._running_stages_queue[0]
      self._SetUpOutputForStage(self._stage_being_displayed)
      return True

  def Tick(self):
    """Give a visual indication to the user that some progress has been made.

    Output is sent to sys.stderr. Nothing is shown if output is not a TTY.
    This method also handles loading new stages and flushing out completed
    stages.

    Returns:
      Whether progress has completed.
    """
    with self._lock:
      if not self._done:
        self._ticks += 1

        # Flush output for any stages that may already be finished
        if self._stage_being_displayed is None:
          self._LoadNextStageForDisplay()
        else:
          while (self._running_stages_queue and
                 self._running_stages_queue[0].is_done):
            completed_stage = self._running_stages_queue.pop(0)
            self._completed_stages.append(completed_stage.key)
            completion_status = self._GetStagedCompletedSuffix(
                self._stage_being_displayed.status)
            self._Print(completion_status)
            if not self._LoadNextStageForDisplay():
              self._stage_being_displayed = None

        if self._stage_being_displayed:
          self._Print(self._GetTickMark(self._ticks))
    return self._done

  def _PrintExitOutput(self, aborted=False, warned=False, failed=False):
    """Handles the final output for the progress tracker."""
    self._SetupExitOutput()
    if aborted:
      msg = self._aborted_message or 'Aborted.'
    elif failed:
      msg = self._failure_message or 'Failed.'
    elif warned:
      msg = self._warning_message or 'Completed with warnings:'
    else:
      msg = self._success_message or 'Done.'
    if self._done_message_callback:
      msg += ' ' + self._done_message_callback()
    self._Print(msg + '\n')

  def _SetupExitOutput(self):
    """Sets up output to print out the closing line."""
    self._current_stage_message = self._console_output.AddMessage('')

  def _HandleUncaughtException(self, exc_value):
    # The first print is to signal exiting the stage. The second print
    # handles the output for exiting the progress tracker.
    if isinstance(exc_value, console_io.OperationCancelledError):
      self._Print('aborted by ctrl-c')
      self._PrintExitOutput(aborted=True)
    else:
      # This means this was an uncaught exception. This ideally
      # should be handled by the implementer
      self._Print(
          self._GetStagedCompletedSuffix(StageCompletionStatus.FAILED))
      self._PrintExitOutput(failed=True)

  def _SetUpOutputForStage(self, stage):
    def _FormattedCallback():
      if stage.message:
        return ' ' + stage.message + '...'
      return None
    self._current_stage_message = self._console_output.AddMessage(
        stage.header,
        indentation_level=1,
        detail_message_callback=_FormattedCallback)

  def _Print(self, message=''):
    """Prints an update containing message to the output stream.

    Args:
      message: str, suffix of message
    """
    if not self._output_enabled:
      return
    if self._current_stage_message:
      self._console_output.UpdateMessage(self._current_stage_message, message)
      self._console_output.UpdateConsole()


class _NonInteractiveStagedProgressTracker(_NormalStagedProgressTracker):
  """A context manager for telling the user about long-running progress."""

  def _SetupExitOutput(self):
    """Sets up output to print out the closing line."""
    # Not necessary for non-interactive implementation
    return

  def _SetupOutput(self):
    self._Print(self._message + '\n')

  def _GetTickMark(self, ticks):
    """Returns the next tick mark."""
    return '.'

  def _GetStagedCompletedSuffix(self, status):
    return status.value + '\n'

  def _SetUpOutputForStage(self, stage):
    message = stage.header
    if stage.message:
      message += ' ' + stage.message + '...'
    self._Print(message)

  def _Print(self, message=''):
    """Prints an update containing message to the output stream.

    Args:
      message: str, suffix of message
    """
    if not self._output_enabled:
      return
    self._stream.write(message)


class _MultilineStagedProgressTracker(_BaseStagedProgressTracker):
  """A context manager for telling the user about long-running progress.

  This class uses the core.console.multiline.ConsoleOutput interface for
  outputting. The header and each stage is defined as a message object
  contained by the ConsoleOutput message.
  """

  def __init__(self, *args, **kwargs):
    self._parser = parser.GetTypedTextParser()
    super(_MultilineStagedProgressTracker, self).__init__(*args, **kwargs)

  def UpdateHeaderMessage(self, message):
    # Next tick will handle actually updating the message. Using tick here to
    # update the message will cause a deadlock when _NotifyUninterruptableError
    # is called.
    self._header_stage.message = message

  def _UpdateHeaderMessage(self, prefix):
    message = prefix + self._message
    if self._header_stage.message:
      message += ' ' + self._header_stage.message
    self._UpdateMessage(self._header_message, message)

  def _UpdateStageTickMark(self, stage, tick_mark=''):
    prefix = self._GenerateStagePrefix(stage.status, tick_mark)
    message = stage.header
    if stage.message:
      message += ' ' + stage.message
    self._UpdateMessage(self._stage_messages[stage], prefix + message)

  def _UpdateMessage(self, stage, message):
    message = self._parser.ParseTypedTextToString(message)
    self._console_output.UpdateMessage(stage, message)

  def _AddMessage(self, message, indentation_level=0):
    message = self._parser.ParseTypedTextToString(message)
    return self._console_output.AddMessage(message,
                                           indentation_level=indentation_level)

  def _NotifyUninterruptableError(self):
    with self._lock:
      self.UpdateHeaderMessage('This operation cannot be cancelled.')
    self.Tick()

  def _SetupExitOutput(self):
    """Sets up output to print out the closing line."""
    return self._console_output.AddMessage('')

  def _PrintExitOutput(self, aborted=False, warned=False, failed=False):
    """Handles the final output for the progress tracker."""
    output_message = self._SetupExitOutput()
    if aborted:
      msg = self._aborted_message or 'Aborted.'
      # Aborted is the same as overall failed progress.
      self._header_stage.status = StageCompletionStatus.FAILED
    elif failed:
      msg = self._failure_message or 'Failed.'
      self._header_stage.status = StageCompletionStatus.FAILED
    elif warned:
      msg = self._warning_message or 'Completed with warnings:'
      self._header_stage.status = StageCompletionStatus.FAILED
    else:
      msg = self._success_message or 'Done.'
      self._header_stage.status = StageCompletionStatus.SUCCESS
    if self._done_message_callback:
      msg += ' ' + self._done_message_callback()
    self._UpdateMessage(output_message, msg)
    # If for some reason some stage did not complete, mark it as interrupted.
    self._Print(self._symbols.interrupted)

  def _SetupOutput(self):
    # Console outputting objects
    self._maintain_queue = False
    self._console_output = multiline.MultilineConsoleOutput(self._stream)
    self._header_message = self._AddMessage(self._message)
    self._header_stage = Stage('')  # Use a Stage object to hold header state.
    self._header_stage.status = StageCompletionStatus.RUNNING
    self._stage_messages = dict()
    for stage in self._stages.values():
      self._stage_messages[stage] = self._AddMessage(stage.header,
                                                     indentation_level=1)
      self._UpdateStageTickMark(stage)
    self._console_output.UpdateConsole()

  def _GenerateStagePrefix(self, stage_status, tick_mark):
    if stage_status == StageCompletionStatus.NOT_STARTED:
      tick_mark = self._symbols.not_started
    elif stage_status == StageCompletionStatus.SUCCESS:
      tick_mark = self._symbols.success
    elif stage_status == StageCompletionStatus.FAILED:
      tick_mark = self._symbols.failed
    elif stage_status == StageCompletionStatus.INTERRUPTED:
      tick_mark = self._symbols.interrupted
    return tick_mark + ' ' * (self._symbols.prefix_length - len(tick_mark))

  def _FailStage(self, stage, exception, message=None):
    """Informs the progress tracker that this stage has failed."""
    self._UpdateStageTickMark(stage)
    if exception:
      for other_stage in self._stages.values():
        if (other_stage != stage and
            other_stage.status == StageCompletionStatus.RUNNING):
          other_stage.status = StageCompletionStatus.INTERRUPTED
        other_stage._is_done = True  # pylint: disable=protected-access

  def _CompleteStage(self, stage):
    self._UpdateStageTickMark(stage)

  def _CompleteStageWithWarnings(self, stage, warning_messages):
    self._UpdateStageTickMark(stage)

  def Tick(self):
    """Give a visual indication to the user that some progress has been made.

    Output is sent to sys.stderr. Nothing is shown if output is not a TTY.
    This method also handles loading new stages and flushing out completed
    stages.

    Returns:
      Whether progress has completed.
    """
    with self._lock:
      if not self._done:
        self._ticks += 1
        self._Print(self._GetTickMark(self._ticks))
    return self._done

  def _Print(self, tick_mark=''):
    """Prints an update containing message to the output stream.

    Args:
      tick_mark: str, suffix of message
    """
    if not self._output_enabled:
      return
    header_prefix = self._GenerateStagePrefix(
        self._header_stage.status, tick_mark)
    self._UpdateHeaderMessage(header_prefix)
    for key in self._running_stages:
      self._UpdateStageTickMark(self[key], tick_mark)
    self._console_output.UpdateConsole()


class NoOpStagedProgressTracker(_BaseStagedProgressTracker):
  """A staged progress tracker that doesn't do anything."""

  def __init__(self, stages, interruptable=False, aborted_message=''):
    super(NoOpStagedProgressTracker, self).__init__(
        message='',
        stages=stages,
        success_message='',
        warning_message='',
        failure_message='',
        autotick=False,
        tick_delay=0,
        interruptable=interruptable,
        aborted_message=aborted_message,
        tracker_id='',
        done_message_callback=None,
        console=console_attr.ConsoleAttr(
            encoding='ascii', suppress_output=True))
    self._aborted_message = aborted_message
    self._done = False

  def __enter__(self):
    def _CtrlCHandler(unused_signal, unused_frame):
      if self._interruptable:
        raise console_io.OperationCancelledError(self._aborted_message)
    self._old_signal_handler = signal.signal(signal.SIGINT, _CtrlCHandler)
    return self

  def _Print(self, message=''):
    # Non-interactive progress tracker should not print anything.
    return

  def Tick(self):
    return self._done

  def __exit__(self, exc_type, exc_val, exc_tb):
    self._done = True
    signal.signal(signal.SIGINT, self._old_signal_handler)

  def _SetupOutput(self):
    pass

  def UpdateHeaderMessage(self, message):
    pass


class _StubStagedProgressTracker(NoOpStagedProgressTracker):
  """Staged tracker that only prints deterministic start and end points.

  No UX about tracking should be exposed here. This is strictly for being able
  to tell that the tracker ran, not what it actually looks like.
  """

  def __init__(self, message, stages, interruptable, aborted_message):
    super(_StubStagedProgressTracker, self).__init__(
        stages, interruptable, aborted_message)
    self._message = message
    self._succeeded_stages = []
    self._failed_stage = None
    self._stream = sys.stderr

  def _CompleteStage(self, stage):
    self._succeeded_stages.append(stage.header)

  def _FailStage(self, stage, exception, message=None):
    self._failed_stage = stage.header
    raise exception

  def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_val and isinstance(exc_val, console_io.OperationCancelledError):
      status_message = 'INTERRUPTED'
    elif exc_val:
      status_message = 'FAILURE'
    elif self.HasWarning():
      status_message = 'WARNING'
    else:
      status_message = 'SUCCESS'

    if log.IsUserOutputEnabled():
      self._stream.write(console_io.JsonUXStub(
          console_io.UXElementType.STAGED_PROGRESS_TRACKER,
          message=self._message,
          status=status_message,
          succeeded_stages=self._succeeded_stages,
          failed_stage=self._failed_stage) + '\n')
    return super(
        _StubStagedProgressTracker, self).__exit__(exc_type, exc_val, exc_tb)
