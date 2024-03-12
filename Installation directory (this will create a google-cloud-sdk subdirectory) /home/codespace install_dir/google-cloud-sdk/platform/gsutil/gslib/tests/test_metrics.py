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
# pylint:mode=test
"""Unit tests for analytics data collection."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import os
import pickle
import re
import socket
import subprocess
import sys
import tempfile
import pprint

import six
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import http_wrapper
from boto.storage_uri import BucketStorageUri

from gslib import metrics
from gslib import VERSION
from gslib.cs_api_map import ApiSelector
import gslib.exception
from gslib.gcs_json_api import GcsJsonApi
from gslib.metrics import MetricsCollector
from gslib.metrics_tuple import Metric
from gslib.tests.mock_logging_handler import MockLoggingHandler
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import HAS_S3_CREDS
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SkipForParFile
from gslib.tests.util import unittest
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.thread_message import FileMessage
from gslib.thread_message import RetryableErrorMessage
from gslib.utils.constants import START_CALLBACK_PER_BYTES
from gslib.utils.retry_util import LogAndHandleRetries
from gslib.utils.system_util import IS_LINUX
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils.unit_util import ONE_KIB
from gslib.utils.unit_util import ONE_MIB

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock

# A piece of the URL logged for all of the tests.
GLOBAL_DIMENSIONS_URL_PARAMS = (
    'a=b&c=d&cd1=cmd1+action1&cd10=0&cd2=x%2Cy%2Cz&cd3=opta%2Coptb&'
    'cd6=CommandException&cm1=0')

GLOBAL_PARAMETERS = [
    'a=b', 'c=d', 'cd1=cmd1 action1', 'cd2=x,y,z', 'cd3=opta,optb',
    'cd6=CommandException', 'cm1=0', 'ev=0', 'el={0}'.format(VERSION)
]
COMMAND_AND_ERROR_TEST_METRICS = set([
    Metric(
        'https://example.com', 'POST',
        '{0}&cm2=3&ea=cmd1+action1&ec={1}&el={2}&ev=0'.format(
            GLOBAL_DIMENSIONS_URL_PARAMS, metrics._GA_COMMANDS_CATEGORY,
            VERSION), 'user-agent-007'),
    Metric(
        'https://example.com', 'POST',
        '{0}&cm2=2&ea=Exception&ec={1}&el={2}&ev=0'.format(
            GLOBAL_DIMENSIONS_URL_PARAMS, metrics._GA_ERRORRETRY_CATEGORY,
            VERSION), 'user-agent-007'),
    Metric(
        'https://example.com', 'POST',
        '{0}&cm2=1&ea=ValueError&ec={1}&el={2}&ev=0'.format(
            GLOBAL_DIMENSIONS_URL_PARAMS, metrics._GA_ERRORRETRY_CATEGORY,
            VERSION), 'user-agent-007'),
    Metric(
        'https://example.com', 'POST',
        '{0}&ea=CommandException&ec={1}&el={2}&ev=0'.format(
            GLOBAL_DIMENSIONS_URL_PARAMS, metrics._GA_ERRORFATAL_CATEGORY,
            VERSION), 'user-agent-007')
])

# A regex to find the list of metrics in log output.
METRICS_LOG_RE = re.compile(r'(\[Metric.*\])')


def _TryExceptAndPass(func, *args, **kwargs):
  """Calls the given function with the arguments and ignores exceptions.

  In these tests, we often force a failure that doesn't matter in order to
  check that a metric was collected.

  Args:
    func: The function to call.
    *args: Any arguments to call the function with.
    **kwargs: Any named arguments to call the function with.
  """
  try:
    func(*args, **kwargs)
  except:  # pylint: disable=bare-except
    pass


def _LogAllTestMetrics():
  """Logs all the common metrics for a test."""
  metrics.LogCommandParams(command_name='cmd1',
                           subcommands=['action1'],
                           global_opts=[('-y', 'value'), ('-z', ''),
                                        ('-x', '')],
                           sub_opts=[('optb', ''), ('opta', '')])
  retry_msg_1 = RetryableErrorMessage(Exception(), 0)
  retry_msg_2 = RetryableErrorMessage(ValueError(), 0)
  metrics.LogRetryableError(retry_msg_1)
  metrics.LogRetryableError(retry_msg_1)
  metrics.LogRetryableError(retry_msg_2)
  metrics.LogFatalError(gslib.exception.CommandException('test'))


class RetryableErrorsQueue(object):
  """Emulates Cloud API status queue, processes only RetryableErrorMessages."""

  def put(self, status_item):  # pylint: disable=invalid-name
    if isinstance(status_item, RetryableErrorMessage):
      metrics.LogRetryableError(status_item)


@SkipForParFile('Do not try spawning the interpreter nested in the archive.')
@mock.patch('time.time', new=mock.MagicMock(return_value=0))
class TestMetricsUnitTests(testcase.GsUtilUnitTestCase):
  """Unit tests for analytics data collection."""

  def setUp(self):
    super(TestMetricsUnitTests, self).setUp()

    # Save the original state of the collector.
    self.original_collector_instance = MetricsCollector.GetCollector()

    # Set dummy attributes for the collector.
    MetricsCollector.StartTestCollector('https://example.com', 'user-agent-007',
                                        {
                                            'a': 'b',
                                            'c': 'd'
                                        })
    self.collector = MetricsCollector.GetCollector()

    self.log_handler = MockLoggingHandler()
    # Use metrics logger to avoid impacting the root logger which may
    # interfere with other tests.
    logging.getLogger('metrics').setLevel(logging.DEBUG)
    logging.getLogger('metrics').addHandler(self.log_handler)

  def tearDown(self):
    super(TestMetricsUnitTests, self).tearDown()

    # Reset to default collection settings.
    MetricsCollector.StopTestCollector(
        original_instance=self.original_collector_instance)

  def testDisabling(self):
    """Tests enabling/disabling of metrics collection."""
    self.assertEqual(self.collector, MetricsCollector.GetCollector())

    # Test when gsutil is part of the Cloud SDK and the user opted in there.
    with mock.patch.dict(os.environ,
                         values={
                             'CLOUDSDK_WRAPPER': '1',
                             'GA_CID': '555'
                         }):
      MetricsCollector._CheckAndSetDisabledCache()
      self.assertFalse(MetricsCollector._disabled_cache)
      self.assertEqual(self.collector, MetricsCollector.GetCollector())

    # Test that when using the shim analytics are disabled.
    with mock.patch('boto.config.getbool', return_value=True):
      MetricsCollector._CheckAndSetDisabledCache()
      self.assertTrue(MetricsCollector._disabled_cache)
      self.assertEqual(None, MetricsCollector.GetCollector())

    # Test when gsutil is part of the Cloud SDK and the user did not opt in
    # there.
    with mock.patch.dict(os.environ,
                         values={
                             'CLOUDSDK_WRAPPER': '1',
                             'GA_CID': ''
                         }):
      MetricsCollector._CheckAndSetDisabledCache()
      self.assertTrue(MetricsCollector._disabled_cache)
      self.assertEqual(None, MetricsCollector.GetCollector())

    # Test when gsutil is not part of the Cloud SDK and there is no UUID file.
    with mock.patch.dict(os.environ, values={'CLOUDSDK_WRAPPER': ''}):
      with mock.patch('os.path.exists', return_value=False):
        MetricsCollector._CheckAndSetDisabledCache()
        self.assertTrue(MetricsCollector._disabled_cache)
        self.assertEqual(None, MetricsCollector.GetCollector())

    # Test when gsutil is not part of the Cloud SDK and there is a UUID file.
    with mock.patch.dict(os.environ, values={'CLOUDSDK_WRAPPER': ''}):
      with mock.patch('os.path.exists', return_value=True):
        # Mock the contents of the file.
        if six.PY2:
          builtin_open = '__builtin__.open'
        else:
          builtin_open = 'builtins.open'
        with mock.patch(builtin_open) as mock_open:
          mock_open.return_value.__enter__ = lambda s: s

          # Set the file.read() method to return the disabled text.
          mock_open.return_value.read.return_value = metrics._DISABLED_TEXT
          MetricsCollector._CheckAndSetDisabledCache()
          self.assertTrue(MetricsCollector._disabled_cache)
          self.assertEqual(None, MetricsCollector.GetCollector())

          # Set the file.read() method to return a mock cid (analytics enabled).
          mock_open.return_value.read.return_value = 'mock_cid'
          MetricsCollector._CheckAndSetDisabledCache()
          self.assertFalse(MetricsCollector._disabled_cache)
          self.assertEqual(self.collector, MetricsCollector.GetCollector())

          # Check that open/read was called twice.
          self.assertEqual(2, len(mock_open.call_args_list))
          self.assertEqual(2, len(mock_open.return_value.read.call_args_list))

  def testConfigValueValidation(self):
    """Tests the validation of potentially PII config values."""
    string_and_bool_categories = [
        'check_hashes', 'content_language', 'disable_analytics_prompt',
        'https_validate_certificates', 'json_api_version',
        'parallel_composite_upload_component_size',
        'parallel_composite_upload_threshold', 'prefer_api',
        'sliced_object_download_component_size',
        'sliced_object_download_threshold', 'tab_completion_time_logs',
        'token_cache', 'use_magicfile'
    ]
    int_categories = [
        'debug', 'default_api_version', 'http_socket_timeout',
        'max_retry_delay', 'num_retries', 'oauth2_refresh_retries',
        'parallel_process_count', 'parallel_thread_count',
        'resumable_threshold', 'rsync_buffer_lines',
        'sliced_object_download_max_components', 'software_update_check_period',
        'tab_completion_timeout', 'task_estimation_threshold'
    ]
    all_categories = sorted(string_and_bool_categories + int_categories)

    # Test general invalid values.
    with mock.patch('boto.config.get_value', return_value=None):
      self.assertEqual('', self.collector._ValidateAndGetConfigValues())

    with mock.patch('boto.config.get_value', return_value='invalid string'):
      self.assertEqual(
          ','.join([category + ':INVALID' for category in all_categories]),
          self.collector._ValidateAndGetConfigValues())

    # Test that non-ASCII characters are invalid.
    with mock.patch('boto.config.get_value', return_value='£'):
      self.assertEqual(
          ','.join([category + ':INVALID' for category in all_categories]),
          self.collector._ValidateAndGetConfigValues())

    # Mock valid return values for specific string validations.
    def MockValidStrings(section, category):
      if section == 'GSUtil':
        if category == 'check_hashes':
          return 'if_fast_else_skip'
        if category == 'content_language':
          return 'chi'
        if category == 'json_api_version':
          return 'v3'
        if category == 'prefer_api':
          return 'xml'
        if category in ('disable_analytics_prompt', 'use_magicfile',
                        'tab_completion_time_logs'):
          return 'True'
      if section == 'OAuth2' and category == 'token_cache':
        return 'file_system'
      if section == 'Boto' and category == 'https_validate_certificates':
        return 'True'
      return ''

    with mock.patch('boto.config.get_value', side_effect=MockValidStrings):
      self.assertEqual(
          'check_hashes:if_fast_else_skip,content_language:chi,'
          'disable_analytics_prompt:True,https_validate_certificates:True,'
          'json_api_version:v3,prefer_api:xml,tab_completion_time_logs:True,'
          'token_cache:file_system,use_magicfile:True',
          self.collector._ValidateAndGetConfigValues())

    # Test that "small" and "large" integers are appropriately validated.
    def MockValidSmallInts(_, category):
      if category in int_categories:
        return '1999'
      return ''

    with mock.patch('boto.config.get_value', side_effect=MockValidSmallInts):
      self.assertEqual(
          'debug:1999,default_api_version:1999,http_socket_timeout:1999,'
          'max_retry_delay:1999,num_retries:1999,oauth2_refresh_retries:1999,'
          'parallel_process_count:1999,parallel_thread_count:1999,'
          'resumable_threshold:1999,rsync_buffer_lines:1999,'
          'sliced_object_download_max_components:1999,'
          'software_update_check_period:1999,tab_completion_timeout:1999,'
          'task_estimation_threshold:1999',
          self.collector._ValidateAndGetConfigValues())

    def MockValidLargeInts(_, category):
      if category in int_categories:
        return '2001'
      return ''

    with mock.patch('boto.config.get_value', side_effect=MockValidLargeInts):
      self.assertEqual(
          'debug:INVALID,default_api_version:INVALID,'
          'http_socket_timeout:INVALID,max_retry_delay:INVALID,'
          'num_retries:INVALID,oauth2_refresh_retries:INVALID,'
          'parallel_process_count:INVALID,parallel_thread_count:INVALID,'
          'resumable_threshold:2001,rsync_buffer_lines:2001,'
          'sliced_object_download_max_components:INVALID,'
          'software_update_check_period:INVALID,'
          'tab_completion_timeout:INVALID,task_estimation_threshold:2001',
          self.collector._ValidateAndGetConfigValues())

      # Test that a non-integer return value is invalid.
      def MockNonIntegerValue(_, category):
        if category in int_categories:
          return '10.28'
        return ''

      with mock.patch('boto.config.get_value', side_effect=MockNonIntegerValue):
        self.assertEqual(
            ','.join([category + ':INVALID' for category in int_categories]),
            self.collector._ValidateAndGetConfigValues())

      # Test data size validation.
      def MockDataSizeValue(_, category):
        if category in ('parallel_composite_upload_component_size',
                        'parallel_composite_upload_threshold',
                        'sliced_object_download_component_size',
                        'sliced_object_download_threshold'):
          return '10MiB'
        return ''

      with mock.patch('boto.config.get_value', side_effect=MockDataSizeValue):
        self.assertEqual(
            'parallel_composite_upload_component_size:10485760,'
            'parallel_composite_upload_threshold:10485760,'
            'sliced_object_download_component_size:10485760,'
            'sliced_object_download_threshold:10485760',
            self.collector._ValidateAndGetConfigValues())

  def testCommandAndErrorEventsCollection(self):
    """Tests the collection of command and error GA events."""
    self.assertEqual([], self.collector._metrics)

    _LogAllTestMetrics()
    # Only the first command should be logged.
    metrics.LogCommandParams(command_name='cmd2')

    # Commands and errors should not be collected until we explicitly collect
    # them.
    self.assertEqual([], self.collector._metrics)
    self.collector._CollectCommandAndErrorMetrics()
    self.assertEqual(COMMAND_AND_ERROR_TEST_METRICS,
                     set(self.collector._metrics))

  def testPerformanceSummaryEventCollection(self):
    """Test the collection of PerformanceSummary GA events."""
    # PerformanceSummaries are only collected for cp and rsync.
    self.collector.ga_params[metrics._GA_LABEL_MAP['Command Name']] = 'cp'
    # GetDiskCounters is called at initialization of _PerformanceSummaryParams,
    # which occurs during the first call to LogPerformanceSummaryParams.
    with mock.patch('gslib.metrics.system_util.GetDiskCounters',
                    return_value={'fake-disk': (0, 0, 0, 0, 0, 0)}):
      metrics.LogPerformanceSummaryParams(uses_fan=True,
                                          uses_slice=True,
                                          avg_throughput=10,
                                          is_daisy_chain=True,
                                          has_file_dst=False,
                                          has_cloud_dst=True,
                                          has_file_src=False,
                                          has_cloud_src=True,
                                          total_bytes_transferred=100,
                                          total_elapsed_time=10,
                                          thread_idle_time=40,
                                          thread_execution_time=10,
                                          num_processes=2,
                                          num_threads=3,
                                          num_objects_transferred=3,
                                          provider_types=['gs'])

    # Log a retryable service error and two retryable network errors.
    service_retry_msg = RetryableErrorMessage(
        apitools_exceptions.CommunicationError(), 0)
    network_retry_msg = RetryableErrorMessage(socket.error(), 0)
    metrics.LogRetryableError(service_retry_msg)
    metrics.LogRetryableError(network_retry_msg)
    metrics.LogRetryableError(network_retry_msg)

    # Log some thread throughput.
    start_file_msg = FileMessage('src', 'dst', 0, size=100)
    end_file_msg = FileMessage('src', 'dst', 10, finished=True)
    start_file_msg.thread_id = end_file_msg.thread_id = 1
    start_file_msg.process_id = end_file_msg.process_id = 1
    metrics.LogPerformanceSummaryParams(file_message=start_file_msg)
    metrics.LogPerformanceSummaryParams(file_message=end_file_msg)
    self.assertEqual(
        self.collector.perf_sum_params.thread_throughputs[(1,
                                                           1)].GetThroughput(),
        10)

    # GetDiskCounters is called a second time during collection.
    with mock.patch('gslib.metrics.system_util.GetDiskCounters',
                    return_value={'fake-disk': (0, 0, 0, 0, 10, 10)}):
      self.collector._CollectPerformanceSummaryMetric()

    # Check for all the expected parameters.
    metric_body = self.collector._metrics[0].body
    label_and_value_pairs = [
        ('Event Category', metrics._GA_PERFSUM_CATEGORY),
        ('Event Action', 'CloudToCloud%2CDaisyChain'),
        ('Execution Time', '10'),
        ('Parallelism Strategy', 'both'),
        ('Source URL Type', 'cloud'),
        ('Provider Types', 'gs'),
        ('Num Processes', '2'),
        ('Num Threads', '3'),
        ('Number of Files/Objects Transferred', '3'),
        ('Size of Files/Objects Transferred', '100'),
        ('Average Overall Throughput', '10'),
        ('Num Retryable Service Errors', '1'),
        ('Num Retryable Network Errors', '2'),
        ('Thread Idle Time Percent', '0.8'),
        ('Slowest Thread Throughput', '10'),
        ('Fastest Thread Throughput', '10'),
    ]
    if IS_LINUX:  # Disk I/O time is only available on Linux.
      label_and_value_pairs.append(('Disk I/O Time', '20'))
    for label, exp_value in label_and_value_pairs:
      self.assertIn('{0}={1}'.format(metrics._GA_LABEL_MAP[label], exp_value),
                    metric_body)

  def testCommandCollection(self):
    """Tests the collection of command parameters."""
    _TryExceptAndPass(self.command_runner.RunNamedCommand,
                      'acl', ['set', '-a'],
                      collect_analytics=True)
    self.assertEqual(
        'acl set',
        self.collector.ga_params.get(metrics._GA_LABEL_MAP['Command Name']))
    self.assertEqual(
        'a',
        self.collector.ga_params.get(
            metrics._GA_LABEL_MAP['Command-Level Options']))

    # Reset the ga_params, which store the command info.
    self.collector.ga_params.clear()

    self.command_runner.RunNamedCommand('list', collect_analytics=True)
    self.assertEqual(
        'ls',
        self.collector.ga_params.get(metrics._GA_LABEL_MAP['Command Name']))
    self.assertEqual(
        'list',
        self.collector.ga_params.get(metrics._GA_LABEL_MAP['Command Alias']))

    self.collector.ga_params.clear()
    _TryExceptAndPass(self.command_runner.RunNamedCommand,
                      'iam', ['get', 'dummy_bucket'],
                      collect_analytics=True)
    self.assertEqual(
        'iam get',
        self.collector.ga_params.get(metrics._GA_LABEL_MAP['Command Name']))

  # We only care about the error logging, not the actual exceptions handling.
  @mock.patch.object(http_wrapper, 'HandleExceptionsAndRebuildHttpConnections')
  def testRetryableErrorCollection(self, mock_default_retry):
    """Tests the collection of a retryable error in the retry function."""
    # A DiscardMessagesQueue has the same retryable error-logging code as the
    # UIThread and the MainThreadUIQueue.
    mock_queue = RetryableErrorsQueue()
    value_error_retry_args = http_wrapper.ExceptionRetryArgs(
        None, None, ValueError(), None, None, None)
    socket_error_retry_args = http_wrapper.ExceptionRetryArgs(
        None, None, socket.error(), None, None, None)
    metadata_retry_func = LogAndHandleRetries(is_data_transfer=False,
                                              status_queue=mock_queue)
    media_retry_func = LogAndHandleRetries(is_data_transfer=True,
                                           status_queue=mock_queue)

    metadata_retry_func(value_error_retry_args)
    self.assertEqual(self.collector.retryable_errors['ValueError'], 1)
    metadata_retry_func(value_error_retry_args)
    self.assertEqual(self.collector.retryable_errors['ValueError'], 2)
    metadata_retry_func(socket_error_retry_args)
    if six.PY2:
      self.assertEqual(self.collector.retryable_errors['SocketError'], 1)
    else:
      self.assertEqual(self.collector.retryable_errors['OSError'], 1)

    # The media retry function raises an exception after logging because
    # the GcsJsonApi handles retryable errors for media transfers itself.
    _TryExceptAndPass(media_retry_func, value_error_retry_args)
    _TryExceptAndPass(media_retry_func, socket_error_retry_args)
    self.assertEqual(self.collector.retryable_errors['ValueError'], 3)
    if six.PY2:
      self.assertEqual(self.collector.retryable_errors['SocketError'], 2)
    else:
      self.assertEqual(self.collector.retryable_errors['OSError'], 2)

  def testExceptionCatchingDecorator(self):
    """Tests the exception catching decorator CaptureAndLogException."""

    # A wrapped function with an exception should not stop the process.
    mock_exc_fn = mock.MagicMock(__name__=str('mock_exc_fn'),
                                 side_effect=Exception())
    wrapped_fn = metrics.CaptureAndLogException(mock_exc_fn)
    wrapped_fn()

    debug_messages = self.log_handler.messages['debug']
    self.assertIn('Exception captured in mock_exc_fn during metrics collection',
                  debug_messages[0])
    self.log_handler.reset()

    self.assertEqual(1, mock_exc_fn.call_count)

    mock_err_fn = mock.MagicMock(__name__=str('mock_err_fn'),
                                 side_effect=TypeError())
    wrapped_fn = metrics.CaptureAndLogException(mock_err_fn)
    wrapped_fn()
    self.assertEqual(1, mock_err_fn.call_count)

    debug_messages = self.log_handler.messages['debug']
    self.assertIn('Exception captured in mock_err_fn during metrics collection',
                  debug_messages[0])
    self.log_handler.reset()

    # Test that exceptions in the unprotected metrics functions are caught.
    with mock.patch.object(MetricsCollector,
                           'GetCollector',
                           return_value='not a collector'):
      # These calls should all fail, but the exceptions shouldn't propagate up.
      metrics.Shutdown()
      metrics.LogCommandParams()
      metrics.LogRetryableError()
      metrics.LogFatalError()
      metrics.LogPerformanceSummaryParams()
      metrics.CheckAndMaybePromptForAnalyticsEnabling('invalid argument')

      debug_messages = self.log_handler.messages['debug']
      message_index = 0
      for func_name in ('Shutdown', 'LogCommandParams', 'LogRetryableError',
                        'LogFatalError', 'LogPerformanceSummaryParams',
                        'CheckAndMaybePromptForAnalyticsEnabling'):
        self.assertIn(
            'Exception captured in %s during metrics collection' % func_name,
            debug_messages[message_index])
        message_index += 1

      self.log_handler.reset()


# Mock callback handlers to throw errors in integration tests, based on handlers
# from test_cp.py.
class _JSONForceHTTPErrorCopyCallbackHandler(object):
  """Test callback handler that raises an arbitrary HTTP error exception."""

  def __init__(self, startover_at_byte, http_error_num):
    self._startover_at_byte = startover_at_byte
    self._http_error_num = http_error_num
    self.started_over_once = False

  # pylint: disable=invalid-name
  def call(self, total_bytes_transferred, unused_total_size):
    """Forcibly exits if the transfer has passed the halting point."""
    if (total_bytes_transferred >= self._startover_at_byte and
        not self.started_over_once):
      self.started_over_once = True
      raise apitools_exceptions.HttpError({'status': self._http_error_num},
                                          None, None)


class _ResumableUploadRetryHandler(object):
  """Test callback handler for causing retries during a resumable transfer."""

  def __init__(self,
               retry_at_byte,
               exception_to_raise,
               exc_args,
               num_retries=1):
    self._retry_at_byte = retry_at_byte
    self._exception_to_raise = exception_to_raise
    self._exception_args = exc_args
    self._num_retries = num_retries

    self._retries_made = 0

  # pylint: disable=invalid-name
  def call(self, total_bytes_transferred, unused_total_size):
    """Cause a single retry at the retry point."""
    if (total_bytes_transferred >= self._retry_at_byte and
        self._retries_made < self._num_retries):
      self._retries_made += 1
      raise self._exception_to_raise(*self._exception_args)


@SkipForParFile('Do not try spawning the interpreter nested in the archive.')
class TestMetricsIntegrationTests(testcase.GsUtilIntegrationTestCase):
  """Integration tests for analytics data collection."""

  def setUp(self):
    super(TestMetricsIntegrationTests, self).setUp()

    # Save the original state of the collector.
    self.original_collector_instance = MetricsCollector.GetCollector()

    # Set dummy attributes for the collector.
    MetricsCollector.StartTestCollector('https://example.com', 'user-agent-007',
                                        {
                                            'a': 'b',
                                            'c': 'd'
                                        })
    self.collector = MetricsCollector.GetCollector()

  def tearDown(self):
    super(TestMetricsIntegrationTests, self).tearDown()

    # Reset to default collection settings.
    MetricsCollector.StopTestCollector(
        original_instance=self.original_collector_instance)

  def _RunGsUtilWithAnalyticsOutput(self, cmd, expected_status=0):
    """Runs the gsutil command to check for metrics log output.

    The env value is set so that the metrics collector in the subprocess will
    use testing parameters and output the metrics collected to the debugging
    log, which lets us check for proper collection in the stderr.

    Args:
      cmd: The command to run, as a list.
      expected_status: The expected return code.

    Returns:
      The string of metrics output.
    """
    stderr = self.RunGsUtil(['-d'] + cmd,
                            return_stderr=True,
                            expected_status=expected_status,
                            env_vars={'GSUTIL_TEST_ANALYTICS': '2'})
    return METRICS_LOG_RE.search(stderr).group()

  def _StartObjectPatch(self, *args, **kwargs):
    """Runs mock.patch.object with the given args, and returns the mock object.

    This starts the patcher, returns the mock object, and registers the patcher
    to stop on test teardown.

    Args:
      *args: The args to pass to mock.patch.object()
      **kwargs: The kwargs to pass to mock.patch.object()

    Returns:
      Mock, The result of starting the patcher.
    """
    patcher = mock.patch.object(*args, **kwargs)
    self.addCleanup(patcher.stop)
    return patcher.start()

  def _CheckParameterValue(self, param_name, exp_value, metrics_to_search):
    """Checks for a correct key=value pair in a log output string."""
    self.assertIn(
        '{0}={1}'.format(metrics._GA_LABEL_MAP[param_name], exp_value),
        metrics_to_search)

  @mock.patch('time.time', new=mock.MagicMock(return_value=0))
  def testMetricsReporting(self):
    """Tests the subprocess creation by Popen in metrics.py."""
    popen_mock = self._StartObjectPatch(subprocess, 'Popen')

    # Set up the temp file for pickle dumping metrics into.
    metrics_file = tempfile.NamedTemporaryFile()
    metrics_file.close()
    temp_file_mock = self._StartObjectPatch(tempfile, 'NamedTemporaryFile')
    temp_file_mock.return_value = open(metrics_file.name, 'wb')

    # If there are no metrics, Popen should not be called.
    self.collector.ReportMetrics()
    self.assertEqual(0, popen_mock.call_count)

    _LogAllTestMetrics()

    # Report the metrics and check Popen calls.
    metrics.Shutdown()
    call_list = popen_mock.call_args_list
    self.assertEqual(1, len(call_list))
    # Check to make sure that we have the proper PYTHONPATH in the subprocess.
    args = call_list[0]
    self.assertIn('PYTHONPATH', args[1]['env'])
    # Ensure that we can access the same modules as the main process from
    # PYTHONPATH.
    missing_paths = (set(sys.path) -
                     set(args[1]['env']['PYTHONPATH'].split(os.pathsep)))
    self.assertEqual(set(), missing_paths)

    # Check that the metrics were correctly dumped into the temp file.
    with open(metrics_file.name, 'rb') as metrics_file:
      reported_metrics = pickle.load(metrics_file)
    self.assertEqual(COMMAND_AND_ERROR_TEST_METRICS, set(reported_metrics))

  @mock.patch('time.time', new=mock.MagicMock(return_value=0))
  def testMetricsPosting(self):
    """Tests the metrics posting process as performed in metrics_reporter.py."""
    # Windows has odd restrictions about attempting to open a named tempfile
    # while it's open. Regardless of platform, we don't need the file to be open
    # or even exist; we only need a valid file path to create a log file at.
    metrics_file = tempfile.NamedTemporaryFile()
    metrics_file_name = metrics_file.name
    metrics_file.close()

    # Logging statements will create a file at the path we just fetched. Make
    # sure we clean up the file afterward.
    def MetricsTempFileCleanup(file_path):
      try:
        os.unlink(file_path)
      except OSError:
        # Don't fail if the file was already cleaned up.
        pass

    self.addCleanup(MetricsTempFileCleanup, metrics_file_name)

    # Collect a metric and set log level for the metrics_reporter subprocess.
    def CollectMetricAndSetLogLevel(log_level, log_file_path):
      metrics.LogCommandParams(command_name='cmd1',
                               subcommands=['action1'],
                               sub_opts=[('optb', ''), ('opta', '')])
      metrics.LogFatalError(gslib.exception.CommandException('test'))

      # Wait for report to make sure the log is written before we check it.
      self.collector.ReportMetrics(wait_for_report=True,
                                   log_level=log_level,
                                   log_file_path=log_file_path)
      self.assertEqual([], self.collector._metrics)

    metrics.LogCommandParams(global_opts=[('-y', 'value'), ('-z', ''), ('-x',
                                                                        '')])

    # The log file should be empty unless the debug option is specified.
    CollectMetricAndSetLogLevel(logging.DEBUG, metrics_file.name)
    with open(metrics_file.name, 'rb') as metrics_log:
      log_text = metrics_log.read()
    if six.PY2:
      expected_response = (
          b'Metric(endpoint=u\'https://example.com\', method=u\'POST\', '
          b'body=\'{0}&cm2=0&ea=cmd1+action1&ec={1}&el={2}&ev=0\', '
          b'user_agent=u\'user-agent-007\')'.format(
              GLOBAL_DIMENSIONS_URL_PARAMS, metrics._GA_COMMANDS_CATEGORY,
              VERSION))
    else:
      expected_response = (
          'Metric(endpoint=\'https://example.com\', method=\'POST\', '
          'body=\'{0}&cm2=0&ea=cmd1+action1&ec={1}&el={2}&ev=0\', '
          'user_agent=\'user-agent-007\')'.format(GLOBAL_DIMENSIONS_URL_PARAMS,
                                                  metrics._GA_COMMANDS_CATEGORY,
                                                  VERSION)).encode('utf_8')
    self.assertIn(expected_response, log_text)
    self.assertIn(b'RESPONSE: 200', log_text)

    CollectMetricAndSetLogLevel(logging.INFO, metrics_file.name)
    with open(metrics_file.name, 'rb') as metrics_log:
      log_text = metrics_log.read()
    self.assertEqual(log_text, b'')

    CollectMetricAndSetLogLevel(logging.WARN, metrics_file.name)
    with open(metrics_file.name, 'rb') as metrics_log:
      log_text = metrics_log.read()
    self.assertEqual(log_text, b'')

  def testMetricsReportingWithFail(self):
    """Tests that metrics reporting error does not throw an exception."""
    popen_mock = self._StartObjectPatch(subprocess, 'Popen')
    popen_mock.side_effect = OSError()

    self.collector._metrics.append('dummy metric')
    # Shouldn't raise an exception.
    self.collector.ReportMetrics()

    self.assertTrue(popen_mock.called)

  def testCommandCollection(self):
    """Tests the collection of commands."""
    metrics_list = self._RunGsUtilWithAnalyticsOutput(
        ['-m', 'acl', 'set', '-a'], expected_status=1)
    self._CheckParameterValue('Event Category', metrics._GA_COMMANDS_CATEGORY,
                              metrics_list)
    self._CheckParameterValue('Event Action', 'acl+set', metrics_list)
    # Check that the options were collected.
    self._CheckParameterValue('Global Options', 'd%2Cm', metrics_list)
    self._CheckParameterValue('Command-Level Options', 'a', metrics_list)

    metrics_list = self._RunGsUtilWithAnalyticsOutput(['ver'])
    self._CheckParameterValue('Event Category', metrics._GA_COMMANDS_CATEGORY,
                              metrics_list)
    self._CheckParameterValue('Event Action', 'version', metrics_list)
    # Check the recording of the command alias.
    self._CheckParameterValue('Command Alias', 'ver', metrics_list)

  def testRetryableErrorMetadataCollection(self):
    """Tests that retryable errors are collected on JSON metadata operations."""
    # Retryable errors will only be collected with the JSON API.
    if self.test_api != ApiSelector.JSON:
      return unittest.skip('Retryable errors are only collected in JSON')

    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'bar')
    # Set the command name to rsync in order to collect PerformanceSummary info.
    self.collector.ga_params[metrics._GA_LABEL_MAP['Command Name']] = 'rsync'
    # Generate a JSON API instance to test with, because the RunGsUtil method
    # may use the XML API.
    gsutil_api = GcsJsonApi(BucketStorageUri, logging.getLogger(),
                            RetryableErrorsQueue(), self.default_provider)
    # Don't wait for too many retries or for long periods between retries to
    # avoid long tests.
    gsutil_api.api_client.num_retries = 2
    gsutil_api.api_client.max_retry_wait = 1

    # Throw an error when transferring metadata.
    key = object_uri.get_key()
    src_obj_metadata = apitools_messages.Object(name=key.name,
                                                bucket=key.bucket.name,
                                                contentType=key.content_type)
    dst_obj_metadata = apitools_messages.Object(
        bucket=src_obj_metadata.bucket,
        name=self.MakeTempName('object'),
        contentType=src_obj_metadata.contentType)
    with mock.patch.object(http_wrapper,
                           '_MakeRequestNoRetry',
                           side_effect=socket.error()):
      _TryExceptAndPass(gsutil_api.CopyObject, src_obj_metadata,
                        dst_obj_metadata)
    if six.PY2:
      self.assertEqual(self.collector.retryable_errors['SocketError'], 1)
    else:
      # In PY3, socket.* errors are deprecated aliases for OSError
      self.assertEqual(self.collector.retryable_errors['OSError'], 1)

    # Throw an error when removing a bucket.
    with mock.patch.object(http_wrapper,
                           '_MakeRequestNoRetry',
                           side_effect=apitools_exceptions.HttpError(
                               'unused', 'unused', 'unused')):
      _TryExceptAndPass(gsutil_api.DeleteObject, bucket_uri.bucket_name,
                        object_uri.object_name)
    self.assertEqual(self.collector.retryable_errors['HttpError'], 1)

    # Check that the number of each kind of retryable error was logged.
    self.assertEqual(
        self.collector.perf_sum_params.num_retryable_network_errors, 1)
    self.assertEqual(
        self.collector.perf_sum_params.num_retryable_service_errors, 1)

  def testRetryableErrorMediaCollection(self):
    """Tests that retryable errors are collected on JSON media operations."""
    # Retryable errors will only be collected with the JSON API.
    if self.test_api != ApiSelector.JSON:
      return unittest.skip('Retryable errors are only collected in JSON')

    boto_config_for_test = [('GSUtil', 'resumable_threshold', str(ONE_KIB))]
    bucket_uri = self.CreateBucket()
    # For the resumable upload exception, we need to ensure at least one
    # callback occurs.
    halt_size = START_CALLBACK_PER_BYTES * 2
    fpath = self.CreateTempFile(contents=b'a' * halt_size)

    # Test that the retry function for data transfers catches and logs an error.
    test_callback_file = self.CreateTempFile(contents=pickle.dumps(
        _ResumableUploadRetryHandler(5, apitools_exceptions.BadStatusCodeError,
                                     ('unused', 'unused', 'unused'))))
    with SetBotoConfigForTest(boto_config_for_test):
      metrics_list = self._RunGsUtilWithAnalyticsOutput([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ])
      self._CheckParameterValue('Event Category',
                                metrics._GA_ERRORRETRY_CATEGORY, metrics_list)
      self._CheckParameterValue('Event Action', 'BadStatusCodeError',
                                metrics_list)
      self._CheckParameterValue('Retryable Errors', '1', metrics_list)
      self._CheckParameterValue('Num Retryable Service Errors', '1',
                                metrics_list)

    # Test that the ResumableUploadStartOverException in copy_helper is caught.
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(_JSONForceHTTPErrorCopyCallbackHandler(5, 404)))
    with SetBotoConfigForTest(boto_config_for_test):
      metrics_list = self._RunGsUtilWithAnalyticsOutput([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ])
      self._CheckParameterValue('Event Category',
                                metrics._GA_ERRORRETRY_CATEGORY, metrics_list)
      self._CheckParameterValue('Event Action',
                                'ResumableUploadStartOverException',
                                metrics_list)
      self._CheckParameterValue('Retryable Errors', '1', metrics_list)
      self._CheckParameterValue('Num Retryable Service Errors', '1',
                                metrics_list)

    # Test retryable error collection in a multithread/multiprocess situation.
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(_JSONForceHTTPErrorCopyCallbackHandler(5, 404)))
    with SetBotoConfigForTest(boto_config_for_test):
      metrics_list = self._RunGsUtilWithAnalyticsOutput([
          '-m', 'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ])
      self._CheckParameterValue('Event Category',
                                metrics._GA_ERRORRETRY_CATEGORY, metrics_list)
      self._CheckParameterValue('Event Action',
                                'ResumableUploadStartOverException',
                                metrics_list)
      self._CheckParameterValue('Retryable Errors', '1', metrics_list)
      self._CheckParameterValue('Num Retryable Service Errors', '1',
                                metrics_list)

  def testFatalErrorCollection(self):
    """Tests that fatal errors are collected."""

    def CheckForCommandException(log_output):
      self._CheckParameterValue('Event Category',
                                metrics._GA_ERRORFATAL_CATEGORY, log_output)
      self._CheckParameterValue('Event Action', 'CommandException', log_output)

    metrics_list = self._RunGsUtilWithAnalyticsOutput(['invalid-command'],
                                                      expected_status=1)
    CheckForCommandException(metrics_list)

    metrics_list = self._RunGsUtilWithAnalyticsOutput(['mb', '-invalid-option'],
                                                      expected_status=1)
    CheckForCommandException(metrics_list)

    bucket_uri = self.CreateBucket()
    metrics_list = self._RunGsUtilWithAnalyticsOutput(
        ['cp', suri(bucket_uri), suri(bucket_uri)], expected_status=1)
    CheckForCommandException(metrics_list)

  def _GetAndCheckAllNumberMetrics(self, metrics_to_search, multithread=True):
    """Checks number metrics for PerformanceSummary tests.

    Args:
      metrics_to_search: The string of metrics to search.
      multithread: False if the the metrics were collected in a non-multithread
                   situation.

    Returns:
      (slowest_throughput, fastest_throughput, io_time) as floats.
    """

    def _ExtractNumberMetric(param_name):
      extracted_match = re.search(
          metrics._GA_LABEL_MAP[param_name] + r'=(\d+\.?\d*)&',
          metrics_to_search)
      if not extracted_match:
        self.fail(
            'Could not find %s (%s) in metrics string %s' %
            (metrics._GA_LABEL_MAP[param_name], param_name, metrics_to_search))
      return float(extracted_match.group(1))

    # Thread idle time will only be recorded in a multithread situation.
    if multithread:
      thread_idle_time = _ExtractNumberMetric('Thread Idle Time Percent')
      # This should be a decimal between 0 and 1.
      self.assertGreaterEqual(thread_idle_time, 0)
      self.assertLessEqual(thread_idle_time, 1)

    throughput = _ExtractNumberMetric('Average Overall Throughput')
    self.assertGreater(throughput, 0)

    slowest_throughput = _ExtractNumberMetric('Slowest Thread Throughput')
    fastest_throughput = _ExtractNumberMetric('Fastest Thread Throughput')
    self.assertGreaterEqual(fastest_throughput, slowest_throughput)
    self.assertGreater(slowest_throughput, 0)
    self.assertGreater(fastest_throughput, 0)

    io_time = None
    if IS_LINUX:
      io_time = _ExtractNumberMetric('Disk I/O Time')
      self.assertGreaterEqual(io_time, 0)

    # Return some metrics to run tests in more specific scenarios.
    return (slowest_throughput, fastest_throughput, io_time)

  def testPerformanceSummaryFileToFile(self):
    """Tests PerformanceSummary collection in a file-to-file transfer."""
    tmpdir1 = self.CreateTempDir()
    tmpdir2 = self.CreateTempDir()
    file_size = ONE_MIB
    self.CreateTempFile(tmpdir=tmpdir1, contents=b'a' * file_size)

    # Run an rsync file-to-file command with fan parallelism, without slice
    # parallelism.
    process_count = 1 if IS_WINDOWS else 6
    with SetBotoConfigForTest([('GSUtil', 'parallel_process_count',
                                str(process_count)),
                               ('GSUtil', 'parallel_thread_count', '7')]):
      metrics_list = self._RunGsUtilWithAnalyticsOutput(
          ['-m', 'rsync', tmpdir1, tmpdir2])
      self._CheckParameterValue('Event Category', metrics._GA_PERFSUM_CATEGORY,
                                metrics_list)
      self._CheckParameterValue('Event Action', 'FileToFile', metrics_list)
      self._CheckParameterValue('Parallelism Strategy', 'fan', metrics_list)
      self._CheckParameterValue('Source URL Type', 'file', metrics_list)
      self._CheckParameterValue('Num Processes', str(process_count),
                                metrics_list)
      self._CheckParameterValue('Num Threads', '7', metrics_list)
      self._CheckParameterValue('Provider Types', 'file', metrics_list)
      self._CheckParameterValue('Size of Files/Objects Transferred', file_size,
                                metrics_list)
      self._CheckParameterValue('Number of Files/Objects Transferred', 1,
                                metrics_list)

      (_, _, io_time) = self._GetAndCheckAllNumberMetrics(metrics_list)
      if IS_LINUX:  # io_time will be None on other platforms.
        # We can't guarantee that the file read/write will consume a
        # reportable amount of disk I/O, but it should be reported as >= 0.
        self.assertGreaterEqual(io_time, 0)

  @SkipForS3('No slice parallelism support for S3.')
  def testPerformanceSummaryFileToCloud(self):
    """Tests PerformanceSummary collection in a file-to-cloud transfer."""
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()
    file_size = 6
    self.CreateTempFile(tmpdir=tmpdir, contents=b'a' * file_size)
    self.CreateTempFile(tmpdir=tmpdir, contents=b'b' * file_size)

    process_count = 1 if IS_WINDOWS else 2
    # Run a parallel composite upload without fan parallelism.
    with SetBotoConfigForTest([
        ('GSUtil', 'parallel_process_count', str(process_count)),
        ('GSUtil', 'parallel_thread_count', '3'),
        ('GSUtil', 'parallel_composite_upload_threshold', '1')
    ]):
      metrics_list = self._RunGsUtilWithAnalyticsOutput(
          ['rsync', tmpdir, suri(bucket_uri)])
      self._CheckParameterValue('Event Category', metrics._GA_PERFSUM_CATEGORY,
                                metrics_list)
      self._CheckParameterValue('Event Action', 'FileToCloud', metrics_list)
      self._CheckParameterValue('Parallelism Strategy', 'slice', metrics_list)
      self._CheckParameterValue('Num Processes', str(process_count),
                                metrics_list)
      self._CheckParameterValue('Num Threads', '3', metrics_list)
      self._CheckParameterValue('Provider Types', 'file%2C' + bucket_uri.scheme,
                                metrics_list)
      self._CheckParameterValue('Size of Files/Objects Transferred',
                                2 * file_size, metrics_list)
      self._CheckParameterValue('Number of Files/Objects Transferred', 2,
                                metrics_list)
      (_, _, io_time) = self._GetAndCheckAllNumberMetrics(metrics_list)
      if IS_LINUX:  # io_time will be None on other platforms.
        # We can't guarantee that the file read will consume a
        # reportable amount of disk I/O, but it should be reported as >= 0.
        self.assertGreaterEqual(io_time, 0)

  @SkipForS3('No slice parallelism support for S3.')
  def testPerformanceSummaryCloudToFile(self):
    """Tests PerformanceSummary collection in a cloud-to-file transfer."""
    bucket_uri = self.CreateBucket()
    file_size = 6
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   contents=b'a' * file_size)

    fpath = self.CreateTempFile()
    # Run a sliced object download with fan parallelism.
    process_count = 1 if IS_WINDOWS else 4
    with SetBotoConfigForTest([
        ('GSUtil', 'parallel_process_count', str(process_count)),
        ('GSUtil', 'parallel_thread_count', '5'),
        ('GSUtil', 'sliced_object_download_threshold', '1'),
        ('GSUtil', 'test_assume_fast_crcmod', 'True')
    ]):
      metrics_list = self._RunGsUtilWithAnalyticsOutput(
          ['-m', 'cp', suri(object_uri), fpath])
      self._CheckParameterValue('Event Category', metrics._GA_PERFSUM_CATEGORY,
                                metrics_list)
      self._CheckParameterValue('Event Action', 'CloudToFile', metrics_list)
      self._CheckParameterValue('Parallelism Strategy', 'both', metrics_list)
      self._CheckParameterValue('Num Processes', str(process_count),
                                metrics_list)
      self._CheckParameterValue('Num Threads', '5', metrics_list)
      self._CheckParameterValue('Provider Types', 'file%2C' + bucket_uri.scheme,
                                metrics_list)
      self._CheckParameterValue('Number of Files/Objects Transferred', '1',
                                metrics_list)
      self._CheckParameterValue('Size of Files/Objects Transferred', file_size,
                                metrics_list)
      (_, _, io_time) = self._GetAndCheckAllNumberMetrics(metrics_list)
      if IS_LINUX:  # io_time will be None on other platforms.
        # We can't guarantee that the file write will consume a
        # reportable amount of disk I/O, but it should be reported as >= 0.
        self.assertGreaterEqual(io_time, 0)

  def testPerformanceSummaryCloudToCloud(self):
    """Tests PerformanceSummary collection in a cloud-to-cloud transfer."""
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    file_size = 6
    key_uri = self.CreateObject(bucket_uri=bucket1_uri,
                                contents=b'a' * file_size)

    # Run a daisy-chain cloud-to-cloud copy without parallelism.
    metrics_list = self._RunGsUtilWithAnalyticsOutput(
        ['cp', '-D', suri(key_uri),
         suri(bucket2_uri)])

    (slowest_throughput, fastest_throughput,
     _) = self._GetAndCheckAllNumberMetrics(metrics_list, multithread=False)
    # Since there's a single thread, this must be the case.
    self.assertEqual(slowest_throughput, fastest_throughput)

    self._CheckParameterValue('Event Category', metrics._GA_PERFSUM_CATEGORY,
                              metrics_list)
    self._CheckParameterValue('Event Action', 'CloudToCloud%2CDaisyChain',
                              metrics_list)
    self._CheckParameterValue('Parallelism Strategy', 'none', metrics_list)
    self._CheckParameterValue('Source URL Type', 'cloud', metrics_list)
    self._CheckParameterValue('Num Processes', '1', metrics_list)
    self._CheckParameterValue('Num Threads', '1', metrics_list)
    self._CheckParameterValue('Provider Types', bucket1_uri.scheme,
                              metrics_list)
    self._CheckParameterValue('Number of Files/Objects Transferred', '1',
                              metrics_list)
    self._CheckParameterValue('Size of Files/Objects Transferred', file_size,
                              metrics_list)

  @unittest.skipUnless(HAS_S3_CREDS, 'Test requires both S3 and GS credentials')
  def testCrossProviderDaisyChainCollection(self):
    """Tests the collection of daisy-chain operations."""
    s3_bucket = self.CreateBucket(provider='s3')
    gs_bucket = self.CreateBucket(provider='gs')
    unused_s3_key = self.CreateObject(bucket_uri=s3_bucket, contents=b'foo')
    gs_key = self.CreateObject(bucket_uri=gs_bucket, contents=b'bar')

    metrics_list = self._RunGsUtilWithAnalyticsOutput(
        ['rsync', suri(s3_bucket), suri(gs_bucket)])
    self._CheckParameterValue('Event Action', 'CloudToCloud%2CDaisyChain',
                              metrics_list)
    self._CheckParameterValue('Provider Types', 'gs%2Cs3', metrics_list)

    metrics_list = self._RunGsUtilWithAnalyticsOutput(
        ['cp', suri(gs_key), suri(s3_bucket)])
    self._CheckParameterValue('Event Action', 'CloudToCloud%2CDaisyChain',
                              metrics_list)
    self._CheckParameterValue('Provider Types', 'gs%2Cs3', metrics_list)
