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

"""Used to collect anonymous SDK metrics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import json
import os
import pickle
import platform
import socket
import subprocess
import sys
import tempfile
import time

from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms

import six
import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request


_INSTALLS_CATEGORY = 'Installs'
_COMMANDS_CATEGORY = 'Commands'
_HELP_CATEGORY = 'Help'
_ERROR_CATEGORY = 'Error'
_EXECUTIONS_CATEGORY = 'Executions'
_TEST_EXECUTIONS_CATEGORY = 'TestExecutions'
_CUSTOM_CATEGORY = 'Custom'

_LOAD_EVENT = 'load'
_RUN_EVENT = 'run'
_TOTAL_EVENT = 'total'
_REMOTE_EVENT = 'remote'
_LOCAL_EVENT = 'local'
_START_EVENT = 'start'

_CLEARCUT_ENDPOINT = 'https://play.googleapis.com/log'
_CLEARCUT_EVENT_METADATA_KEY = 'event_metadata'
_CLEARCUT_ERROR_TYPE_KEY = 'error_type'


class _Event(object):

  def __init__(self, category, action, label, value):
    self.category = category
    self.action = action
    self.label = label
    self.value = value


class CommonParams(object):
  """Parameters common to all metrics reporters."""

  def __init__(self):
    hostname = socket.gethostname()
    install_type = 'Google' if hostname.endswith('.google.com') else 'External'

    current_platform = platforms.Platform.Current()

    self.client_id = config.GetCID()
    self.current_platform = current_platform
    self.user_agent = GetUserAgent(current_platform)
    self.release_channel = config.INSTALLATION_CONFIG.release_channel
    self.install_type = install_type
    self.metrics_environment = properties.GetMetricsEnvironment()
    self.is_interactive = console_io.IsInteractive(error=True, heuristic=True)
    self.python_version = platform.python_version()
    self.metrics_environment_version = (properties.VALUES
                                        .metrics.environment_version.Get())
    self.is_run_from_shell_script = console_io.IsRunFromShellScript()
    self.term_identifier = console_attr.GetConsoleAttr().GetTermIdentifier()


def GetTimeMillis(time_secs=None):
  return int(round((time_secs or time.time()) * 1000))


def GetUserAgent(current_platform=None):
  """Constructs a user agent string from config and platform fragments.

  Args:
    current_platform: Optional platforms.Platform for pulling
      platform-specific user agent details.

  Returns:
    str, The user agent for the current client.
  """
  current_platform = current_platform or platforms.Platform.Current()

  return 'CloudSDK/{version} {fragment}'.format(
      version=config.CLOUD_SDK_VERSION,
      fragment=current_platform.UserAgentFragment())


class _TimedEvent(object):

  def __init__(self, name, time_millis):
    self.name = name
    self.time_millis = time_millis


class _CommandTimer(object):
  """A class for timing the execution of a command."""

  def __init__(self):
    self.__start = 0
    self.__events = []
    self.__total_rpc_duration = 0
    self.__total_local_duration = 0
    self.__category = 'unknown'
    self.__action = 'unknown'
    self.__label = None
    self.__flag_names = None

  def SetContext(self, category, action, label, flag_names):
    self.__category = category
    self.__action = action
    self.__label = label
    self.__flag_names = flag_names

  def GetContext(self):
    return self.__category, self.__action, self.__label, self.__flag_names

  def Event(self, name, event_time=None):
    time_millis = GetTimeMillis(event_time)

    if name is _START_EVENT:
      self.__start = time_millis
      return

    self.__events.append(_TimedEvent(name, time_millis))

    if name is _TOTAL_EVENT:
      self.__total_local_duration = time_millis - self.__start
      self.__total_local_duration -= self.__total_rpc_duration

  def AddRPCDuration(self, duration_in_ms):
    self.__total_rpc_duration += duration_in_ms

  def GetTimings(self):
    """Returns the timings for the recorded events."""
    timings = []
    for event in self.__events:
      timings.append((event.name, event.time_millis - self.__start))

    timings.extend([
        (_LOCAL_EVENT, self.__total_local_duration),
        (_REMOTE_EVENT, self.__total_rpc_duration),
    ])
    return timings


class _ClearcutMetricsReporter(object):
  """A class for handling reporting metrics to Clearcut."""

  def __init__(self, common_params):
    self._user_agent = common_params.user_agent
    self._clearcut_request_params = {
        'client_info': {
            'client_type': 'DESKTOP',
            'desktop_client_info': {
                'os': common_params.current_platform.operating_system.id
            }
        },
        'log_source_name': 'CONCORD',
        'zwieback_cookie': common_params.client_id,
    }

    event_metadata = [
        ('release_channel', common_params.release_channel),
        ('install_type', common_params.install_type),
        ('environment', common_params.metrics_environment),
        ('interactive', common_params.is_interactive),
        ('python_version', common_params.python_version),
        ('environment_version', common_params.metrics_environment_version),
        ('from_script', common_params.is_run_from_shell_script),
        ('term', common_params.term_identifier),
    ]

    self._clearcut_concord_event_metadata = [{
        'key': param[0], 'value': six.text_type(param[1])
    } for param in event_metadata]

    cloud_sdk_version = config.CLOUD_SDK_VERSION
    self._clearcut_concord_event_params = {
        'release_version': cloud_sdk_version,
        'console_type': 'CloudSDK',
        'client_install_id': common_params.client_id,
    }

    self._clearcut_concord_timed_events = []

  @property
  def event_metadata(self):
    return self._clearcut_concord_event_metadata

  @property
  def event_params(self):
    return self._clearcut_concord_event_params

  @property
  def request_params(self):
    return self._clearcut_request_params

  def Record(self,
             event,
             flag_names=None,
             error=None,
             error_extra_info_json=None):
    """Records the given event.

    Args:
      event: _Event, The event to process.
      flag_names: str, Comma separated list of flag names used with the action.
      error: class, The class (not the instance) of the Exception if a user
        tried to run a command that produced an error.
      error_extra_info_json: {str: json-serializable}, A json serializable dict
        of extra info that we want to log with the error. This enables us to
        write queries that can understand the keys and values in this dict.
    """
    concord_event = dict(self.event_params)
    concord_event['event_type'] = event.category
    concord_event['event_name'] = event.action

    concord_event[_CLEARCUT_EVENT_METADATA_KEY] = list(
        self.event_metadata)

    event_metadata = []

    if flag_names is not None:
      event_metadata.append({
          'key': 'flag_names',
          'value': six.text_type(flag_names)
      })
    if error is not None:
      event_metadata.append({'key': _CLEARCUT_ERROR_TYPE_KEY, 'value': error})
    if error_extra_info_json is not None:
      event_metadata.append({'key': 'extra_error_info',
                             'value': error_extra_info_json})

    if event.category is _EXECUTIONS_CATEGORY:
      event_metadata.append({'key': 'binary_version', 'value': event.label})
    elif event.category is _HELP_CATEGORY:
      event_metadata.append({'key': 'help_mode', 'value': event.label})
    elif event.category is _ERROR_CATEGORY:
      event_metadata.append(
          {'key': _CLEARCUT_ERROR_TYPE_KEY, 'value': event.label})
    elif event.category is _INSTALLS_CATEGORY:
      event_metadata.append({'key': 'component_version', 'value': event.label})
    elif event.category is _CUSTOM_CATEGORY:
      event_metadata.append({'key': event.label, 'value': event.value})

    concord_event[_CLEARCUT_EVENT_METADATA_KEY].extend(event_metadata)
    self._clearcut_concord_timed_events.append((concord_event,
                                                GetTimeMillis()))

  def Timings(self, timer):
    """Extracts relevant data from timer."""
    total_latency = None
    timings = timer.GetTimings()

    sub_event_latencies = []
    for timing in timings:
      if not total_latency and timing[0] == _TOTAL_EVENT:
        total_latency = timing[1]

      sub_event_latencies.append({
          'key': timing[0],
          'latency_ms': timing[1]
      })

    return total_latency, sub_event_latencies

  def ToHTTPBeacon(self, timer):
    """Collect the required clearcut HTTP beacon."""
    clearcut_request = dict(self.request_params)
    clearcut_request['request_time_ms'] = GetTimeMillis()

    event_latency, sub_event_latencies = self.Timings(timer)
    command_latency_set = False
    for concord_event, _ in self._clearcut_concord_timed_events:
      if (concord_event['event_type'] is _COMMANDS_CATEGORY and
          command_latency_set):
        continue
      concord_event['latency_ms'] = event_latency
      concord_event['sub_event_latency_ms'] = sub_event_latencies
      command_latency_set = concord_event['event_type'] is _COMMANDS_CATEGORY

    clearcut_request['log_event'] = []
    for concord_event, event_time_ms in self._clearcut_concord_timed_events:
      clearcut_request['log_event'].append({
          'source_extension_json': json.dumps(concord_event, sort_keys=True),
          'event_time_ms': event_time_ms
      })

    data = json.dumps(clearcut_request, sort_keys=True)
    headers = {'user-agent': self._user_agent}
    return (_CLEARCUT_ENDPOINT, 'POST', data, headers)


class _MetricsCollector(object):
  """A singleton class to handle metrics reporting."""

  _disabled_cache = None
  _instance = None
  test_group = None

  @staticmethod
  def GetCollectorIfExists():
    return _MetricsCollector._instance

  @staticmethod
  def GetCollector():
    """Returns the singleton _MetricsCollector instance or None if disabled."""
    if _MetricsCollector._IsDisabled():
      return None

    if not _MetricsCollector._instance:
      _MetricsCollector._instance = _MetricsCollector()
    return _MetricsCollector._instance

  @staticmethod
  def ResetCollectorInstance(disable_cache=None):
    """Reset the singleton _MetricsCollector and reinitialize it.

    This should only be used for tests, where we want to collect some metrics
    but not others, and we have to reinitialize the collector with a different
    Google Analytics tracking id.

    Args:
      disable_cache: Metrics collector keeps an internal cache of the disabled
          state of metrics. This controls the value to reinitialize the cache.
          None means we will refresh the cache with the default values.
          True/False forces a specific value.
    """
    _MetricsCollector._disabled_cache = disable_cache
    if _MetricsCollector._IsDisabled():
      _MetricsCollector._instance = None
    else:
      _MetricsCollector._instance = _MetricsCollector()

  @staticmethod
  def _IsDisabled():
    """Returns whether metrics collection should be disabled."""
    if _MetricsCollector._disabled_cache is None:
      # Don't collect metrics for completions.
      if '_ARGCOMPLETE' in os.environ:
        _MetricsCollector._disabled_cache = True
      elif not properties.IsDefaultUniverse():
        _MetricsCollector._disabled_cache = True
      else:
        # Don't collect metrics if the user has opted out.
        disabled = properties.VALUES.core.disable_usage_reporting.GetBool()
        if disabled is None:
          # There is no preference set, fall back to the installation default.
          disabled = config.INSTALLATION_CONFIG.disable_usage_reporting
        _MetricsCollector._disabled_cache = disabled
    return _MetricsCollector._disabled_cache

  def __init__(self):
    """Initialize a new MetricsCollector.

    This should only be invoked through the static GetCollector() function or
    the static ResetCollectorInstance() function.
    """
    common_params = CommonParams()

    self._metrics_reporters = [
        _ClearcutMetricsReporter(common_params)
    ]

    self._timer = _CommandTimer()
    self._metrics = []

    # Tracking the level so we can only report metrics for the top level action
    # (and not other actions executed within an action). Zero is the top level.
    self._action_level = 0

    current_platform = platforms.Platform.Current()
    self._async_popen_args = current_platform.AsyncPopenArgs()
    log.debug('Metrics collector initialized...')

  def IncrementActionLevel(self):
    self._action_level += 1

  def DecrementActionLevel(self):
    self._action_level -= 1

  def RecordTimedEvent(self, name, record_only_on_top_level=False,
                       event_time=None):
    """Records the time when a particular event happened.

    Args:
      name: str, Name of the event.
      record_only_on_top_level: bool, Whether to record only on top level.
      event_time: float, Time when the event happened in secs since epoch.
    """
    if self._action_level == 0 or not record_only_on_top_level:
      self._timer.Event(name, event_time=event_time)

  def RecordRPCDuration(self, duration_in_ms):
    """Records the time when a particular event happened.

    Args:
      duration_in_ms: int, Duration of the RPC in milli seconds.
    """
    self._timer.AddRPCDuration(duration_in_ms)

  def SetTimerContext(self, category, action, label=None, flag_names=None):
    """Sets the context for which the timer is collecting timed events.

    Args:
      category: str, Category of the action being timed.
      action: str, Name of the action being timed.
      label: str, Additional information about the action being timed.
      flag_names: str, Comma separated list of flag names used with the action.
    """
    # We only want to time top level commands
    if category is _COMMANDS_CATEGORY and self._action_level != 0:
      return

    # We want to report error times against the top level action
    if category is _ERROR_CATEGORY and self._action_level != 0:
      _, action, _, _ = self._timer.GetContext()

    self._timer.SetContext(category, action, label, flag_names)

  def Record(self,
             event,
             flag_names=None,
             error=None,
             error_extra_info_json=None):
    """Records the given event.

    Args:
      event: _Event, The event to process.
      flag_names: str, Comma separated list of flag names used with the action.
      error: class, The class (not the instance) of the Exception if a user
        tried to run a command that produced an error.
      error_extra_info_json: {str: json-serializable}, A json serializable dict
        of extra info that we want to log with the error. This enables us to
        write queries that can understand the keys and values in this dict.
    """
    for metrics_reporter in self._metrics_reporters:
      metrics_reporter.Record(
          event,
          flag_names=flag_names,
          error=error,
          error_extra_info_json=error_extra_info_json)

  def CollectMetrics(self):
    for metrics_reporter in self._metrics_reporters:
      http_beacon = metrics_reporter.ToHTTPBeacon(self._timer)
      self.CollectHTTPBeacon(*http_beacon)

  def CollectHTTPBeacon(self, url, method, body, headers):
    """Record a custom event to an arbitrary endpoint.

    Args:
      url: str, The full url of the endpoint to hit.
      method: str, The HTTP method to issue.
      body: str, The body to send with the request.
      headers: {str: str}, A map of headers to values to include in the request.
    """
    self._metrics.append((url, method, body, headers))

  def ReportMetrics(self, wait_for_report=False):
    """Reports the collected metrics using a separate async process."""
    if not self._metrics:
      return

    temp_metrics_file = tempfile.NamedTemporaryFile(delete=False)
    with temp_metrics_file:
      pickle.dump(self._metrics, temp_metrics_file)
      self._metrics = []

    this_file = encoding.Decode(__file__)
    reporting_script_path = os.path.realpath(
        os.path.join(os.path.dirname(this_file), 'metrics_reporter.py'))
    execution_args = execution_utils.ArgsForPythonTool(
        reporting_script_path, temp_metrics_file.name)
    # On Python 2.x on Windows, the first arg can't be unicode. We encode
    # encode it anyway because there is really nothing else we can do if
    # that happens.
    # https://bugs.python.org/issue19264
    execution_args = [encoding.Encode(a) for a in execution_args]

    exec_env = os.environ.copy()
    encoding.SetEncodedValue(exec_env, 'PYTHONPATH', os.pathsep.join(sys.path))

    try:
      p = subprocess.Popen(execution_args, env=exec_env,
                           **self._async_popen_args)
      log.debug('Metrics reporting process started...')
    except OSError:
      # This can happen specifically if the Python executable moves between the
      # start of this process and now.
      log.debug('Metrics reporting process failed to start.')
    if wait_for_report:
      # NOTE: p.wait() can cause a deadlock. p.communicate() is recommended.
      # See python docs for more information.
      p.communicate()
      log.debug('Metrics reporting process finished.')


def _RecordEventAndSetTimerContext(
    category, action, label, value=0, flag_names=None,
    error=None, error_extra_info_json=None):
  """Common code for processing an event."""
  collector = _MetricsCollector.GetCollector()
  if not collector:
    return

  # Override label for tests. This way we can filter by test group.
  if _MetricsCollector.test_group and category is not _ERROR_CATEGORY:
    label = _MetricsCollector.test_group

  event = _Event(category=category, action=action, label=label, value=value)

  collector.Record(
      event,
      flag_names=flag_names,
      error=error,
      error_extra_info_json=error_extra_info_json)

  if category in [_COMMANDS_CATEGORY, _EXECUTIONS_CATEGORY]:
    collector.SetTimerContext(category, action, flag_names=flag_names)
  elif category in [_ERROR_CATEGORY, _HELP_CATEGORY,
                    _TEST_EXECUTIONS_CATEGORY]:
    collector.SetTimerContext(category, action, label, flag_names=flag_names)
  # Ignoring installs for now since there could be multiple per cmd execution.
  # Custom events only record a key/value pair, and don't require timer context.


def _GetFlagNameString(flag_names):
  if flag_names is None:
    # We have no information on the flags that were used.
    return ''
  if not flag_names:
    # We explicitly know that no flags were used.
    return '==NONE=='
  # One or more flags were used.
  return ','.join(sorted(flag_names))


def CaptureAndLogException(func):
  """Function decorator to capture and log any exceptions."""
  def Wrapper(*args, **kwds):
    try:
      return func(*args, **kwds)
    # pylint:disable=bare-except
    except:
      log.debug('Exception captured in %s', func.__name__, exc_info=True)
  return Wrapper


def StartTestMetrics(test_group_id, test_method):
  _MetricsCollector.ResetCollectorInstance(False)
  _MetricsCollector.test_group = test_group_id
  _RecordEventAndSetTimerContext(
      _TEST_EXECUTIONS_CATEGORY,
      test_method,
      test_group_id,
      value=0)


def StopTestMetrics():
  collector = _MetricsCollector.GetCollectorIfExists()
  if collector:
    collector.ReportMetrics(wait_for_report=True)
  _MetricsCollector.test_group = None
  _MetricsCollector.ResetCollectorInstance(True)


def GetCIDIfMetricsEnabled():
  """Gets the client id if metrics collection is enabled.

  Returns:
    str, The hex string of the client id if metrics is enabled, else an empty
    string.
  """
  # pylint: disable=protected-access
  if _MetricsCollector._IsDisabled():
    # We directly set an environment variable with the return value of this
    # function, and so return the empty string rather than None.
    return ''
  return config.GetCID()
  # pylint: enable=protected-access


def GetUserAgentIfMetricsEnabled():
  """Gets the user agent if metrics collection is enabled.

  Returns:
    The complete user agent string if metrics is enabled, else None.
  """
  # pylint: disable=protected-access
  if not _MetricsCollector._IsDisabled():
    return GetUserAgent()
  return None
  # pylint: enable=protected-access


@CaptureAndLogException
def Shutdown():
  """Reports the metrics that were collected."""
  collector = _MetricsCollector.GetCollectorIfExists()
  if collector:
    collector.RecordTimedEvent(_TOTAL_EVENT)
    collector.CollectMetrics()
    collector.ReportMetrics()


def _GetExceptionName(error):
  """Gets a friendly exception name for the given error.

  Args:
    error: An exception class.

  Returns:
    str, The name of the exception to log.
  """
  if error:
    try:
      return '{0}.{1}'.format(error.__module__, error.__name__)
    # pylint:disable=bare-except, Never want to fail on metrics reporting.
    except:
      return 'unknown'
  return None


def _GetErrorExtraInfo(error_extra_info):
  """Serializes the extra info into a json string for logging.

  Args:
    error_extra_info: {str: json-serializable}, A json serializable dict of
      extra info that we want to log with the error. This enables us to write
      queries that can understand the keys and values in this dict.

  Returns:
    str, The value to pass to Clearcut or None.
  """
  if error_extra_info:
    return json.dumps(error_extra_info, sort_keys=True)
  return None


@CaptureAndLogException
def Installs(component_id, version_string):
  """Logs that an SDK component was installed.

  Args:
    component_id: str, The component id that was installed.
    version_string: str, The version of the component.
  """
  _RecordEventAndSetTimerContext(
      _INSTALLS_CATEGORY, component_id, version_string)


@CaptureAndLogException
def Commands(command_path, version_string='unknown', flag_names=None,
             error=None, error_extra_info=None):
  """Logs that a gcloud command was run.

  Args:
    command_path: [str], The '.' separated name of the calliope command.
    version_string: [str], The version of the command.
    flag_names: [str], The names of the flags that were used during this
      execution.
    error: class, The class (not the instance) of the Exception if a user
      tried to run a command that produced an error.
    error_extra_info: {str: json-serializable}, A json serializable dict of
      extra info that we want to log with the error. This enables us to write
      queries that can understand the keys and values in this dict.
  """
  _RecordEventAndSetTimerContext(
      _COMMANDS_CATEGORY, command_path, version_string,
      flag_names=_GetFlagNameString(flag_names),
      error=_GetExceptionName(error),
      error_extra_info_json=_GetErrorExtraInfo(error_extra_info))


@CaptureAndLogException
def Help(command_path, mode):
  """Logs that help for a gcloud command was run.

  Args:
    command_path: str, The '.' separated name of the calliope command.
    mode: str, The way help was invoked (-h, --help, help).
  """
  _RecordEventAndSetTimerContext(_HELP_CATEGORY, command_path, mode)


@CaptureAndLogException
def Error(command_path, error, flag_names=None, error_extra_info=None):
  """Logs that a top level Exception was caught for a gcloud command.

  Args:
    command_path: str, The '.' separated name of the calliope command.
    error: class, The class (not the instance) of the exception that was
      caught.
    flag_names: [str], The names of the flags that were used during this
      execution.
    error_extra_info: {str: json-serializable}, A json serializable dict of
      extra info that we want to log with the error. This enables us to write
      queries that can understand the keys and values in this dict.
  """
  _RecordEventAndSetTimerContext(
      _ERROR_CATEGORY, command_path, _GetExceptionName(error),
      flag_names=_GetFlagNameString(flag_names),
      error_extra_info_json=_GetErrorExtraInfo(error_extra_info))


@CaptureAndLogException
def Executions(command_name, version_string='unknown'):
  """Logs that a top level SDK script was run.

  Args:
    command_name: str, The script name.
    version_string: str, The version of the command.
  """
  _RecordEventAndSetTimerContext(
      _EXECUTIONS_CATEGORY, command_name, version_string)


@CaptureAndLogException
def CustomKeyValue(command_path, key, value):
  """Record a custom key/value metric for a given command.

  Args:
    command_path: str, The '.' separated name of the calliope command.
    key: str, The key recorded for the event.
    value: str. The value recorded for the event.
  """
  _RecordEventAndSetTimerContext(_CUSTOM_CATEGORY, command_path, key, value)


@CaptureAndLogException
def Started(start_time):
  """Record the time when the command was started.

  Args:
    start_time: float, The start time in seconds since epoch.
  """
  collector = _MetricsCollector.GetCollector()
  if collector:
    collector.RecordTimedEvent(name=_START_EVENT,
                               record_only_on_top_level=True,
                               event_time=start_time)


@CaptureAndLogException
def Loaded():
  """Record the time when command loading was completed."""
  collector = _MetricsCollector.GetCollector()
  if collector:
    collector.RecordTimedEvent(name=_LOAD_EVENT,
                               record_only_on_top_level=True)
    collector.IncrementActionLevel()


@CaptureAndLogException
def Ran():
  """Record the time when command running was completed."""
  collector = _MetricsCollector.GetCollector()
  if collector:
    collector.DecrementActionLevel()
    collector.RecordTimedEvent(name=_RUN_EVENT,
                               record_only_on_top_level=True)


@CaptureAndLogException
def CustomTimedEvent(event_name):
  """Record the time when a custom event was completed.

  Args:
    event_name: The name of the event. This must match the pattern
      "[a-zA-Z0-9_]+".
  """
  collector = _MetricsCollector.GetCollector()
  if collector:
    collector.RecordTimedEvent(event_name)


@contextlib.contextmanager
def RecordDuration(span_name):
  """Record duration of a span of time.

  Two timestamps will be sent, and the duration in between will be considered as
  the client side latency of this span.

  Args:
    span_name: str, The name of the span to time.

  Yields:
    None
  """
  CustomTimedEvent(span_name + '_start')
  yield
  CustomTimedEvent(span_name)


@CaptureAndLogException
def RPCDuration(duration_in_secs):
  """Record the time taken to perform an RPC.

  Args:
    duration_in_secs: float, The duration of the RPC in seconds.
  """
  collector = _MetricsCollector.GetCollector()
  if collector:
    collector.RecordRPCDuration(GetTimeMillis(duration_in_secs))


@CaptureAndLogException
def CustomBeacon(url, method, body, headers):
  """Record a custom event to an arbitrary endpoint.

  Args:
    url: str, The full url of the endpoint to hit.
    method: str, The HTTP method to issue.
    body: str, The body to send with the request.
    headers: {str: str}, A map of headers to values to include in the request.
  """
  collector = _MetricsCollector.GetCollector()
  if collector:
    collector.CollectHTTPBeacon(url, method, body, headers)
