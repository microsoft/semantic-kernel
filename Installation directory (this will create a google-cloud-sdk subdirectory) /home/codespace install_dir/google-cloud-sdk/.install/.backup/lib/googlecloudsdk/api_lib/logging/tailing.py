# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""A library for logs tailing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import datetime

# pylint: disable=unused-import, type imports needed for gRPC
import google.appengine.logging.v1.request_log_pb2
import google.cloud.appengine_v1.proto.audit_data_pb2
import google.cloud.appengine_v1alpha.proto.audit_data_pb2
import google.cloud.appengine_v1beta.proto.audit_data_pb2
import google.cloud.bigquery_logging_v1.proto.audit_data_pb2
import google.cloud.cloud_audit.proto.audit_log_pb2
import google.cloud.iam_admin_v1.proto.audit_data_pb2
import google.iam.v1.logging.audit_data_pb2
import google.type.money_pb2
# pylint: enable=unused-import

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import gapic_util
from googlecloudsdk.core import log

import grpc


_SUPPRESSION_INFO_FLUSH_PERIOD_SECONDS = 2

_HELP_PAGE_LINK = 'https://cloud.google.com/logging/docs/reference/tools/gcloud-logging#tailing.'


def _HandleGrpcRendezvous(rendezvous, output_debug, output_warning):
  """Handles _MultiThreadedRendezvous errors."""
  error_messages_by_code = {
      grpc.StatusCode.INVALID_ARGUMENT:
          'Invalid argument.',
      grpc.StatusCode.RESOURCE_EXHAUSTED:
          'There are too many tail sessions open.',
      grpc.StatusCode.INTERNAL:
          'Internal error.',
      grpc.StatusCode.PERMISSION_DENIED:
          'Access is denied or has changed for resource.',
      grpc.StatusCode.OUT_OF_RANGE:
          ('The maximum duration for tail has been met. '
           'The command may be repeated to continue.')
  }

  # grpc calls cancelled by application should not warn
  if rendezvous.code() == grpc.StatusCode.CANCELLED:
    return

  output_debug(rendezvous)
  output_warning('{} ({})'.format(
      error_messages_by_code.get(rendezvous.code(),
                                 'Unknown error encountered.'),
      rendezvous.details()))


def _HandleSuppressionCounts(counts_by_reason, handler):
  """Handles supression counts."""
  client_class = apis.GetGapicClientClass('logging', 'v2')
  suppression_info = (client_class.types.TailLogEntriesResponse.SuppressionInfo)

  suppression_reason_strings = {
      suppression_info.Reason.RATE_LIMIT:
          'Logging API backend rate limit',
      suppression_info.Reason.NOT_CONSUMED:
          'client not consuming messages quickly enough',
  }
  for reason, count in counts_by_reason.items():
    reason_string = suppression_reason_strings.get(
        reason, 'UNKNOWN REASON: {}'.format(reason))
    handler(reason_string, count)


class _SuppressionInfoAccumulator(object):
  """Accumulates and outputs information about suppression for the tail session."""

  def __init__(self, get_now, output_warning, output_error):
    self._get_now = get_now
    self._warning = output_warning
    self._error = output_error
    self._count_by_reason_delta = collections.Counter()
    self._count_by_reason_cumulative = collections.Counter()
    self._last_flush = get_now()

  def _OutputSuppressionHelpMessage(self):
    self._warning(
        'Find guidance for suppression at {}.'.format(_HELP_PAGE_LINK))

  def _ShouldFlush(self):
    return (self._get_now() - self._last_flush
           ).total_seconds() > _SUPPRESSION_INFO_FLUSH_PERIOD_SECONDS

  def _OutputSuppressionDeltaMessage(self, reason_string, count):
    self._error('Suppressed {} entries due to {}.'.format(count, reason_string))

  def _OutputSuppressionCumulativeMessage(self, reason_string, count):
    self._warning('In total, suppressed {} messages due to {}.'.format(
        count, reason_string))

  def _Flush(self):
    self._last_flush = self._get_now()
    _HandleSuppressionCounts(self._count_by_reason_delta,
                             self._OutputSuppressionDeltaMessage)
    self._count_by_reason_cumulative += self._count_by_reason_delta
    self._count_by_reason_delta.clear()

  def Finish(self):
    self._Flush()
    _HandleSuppressionCounts(self._count_by_reason_cumulative,
                             self._OutputSuppressionCumulativeMessage)
    if self._count_by_reason_cumulative:
      self._OutputSuppressionHelpMessage()

  def Add(self, suppression_info):
    self._count_by_reason_delta += collections.Counter(
        {info.reason: info.suppressed_count for info in suppression_info})
    if self._ShouldFlush():
      self._Flush()


def _StreamEntries(get_now, output_warning, output_error, output_debug,
                   tail_stub):
  """Streams entries back from the Logging API.

  Args:
    get_now: A callable that returns the current time.
    output_warning: A callable that outputs the argument as a warning.
    output_error: A callable that outputs the argument as an error.
    output_debug: A callable that outputs the argument as debug info.
    tail_stub: The `BidiRpc` stub to use.

  Yields:
    Entries included in the tail session.
  """

  tail_stub.open()
  suppression_info_accumulator = _SuppressionInfoAccumulator(
      get_now, output_warning, output_error)
  error = None
  while tail_stub.is_active:
    try:
      response = tail_stub.recv()
    except grpc.RpcError as e:
      error = e
      break
    suppression_info_accumulator.Add(response.suppression_info)
    for entry in response.entries:
      yield entry

  if error:
    # The `grpc.RpcError` that are raised by `recv()` are actually gRPC
    # `_MultiThreadedRendezvous` objects.
    _HandleGrpcRendezvous(error, output_debug, output_warning)
  suppression_info_accumulator.Finish()
  tail_stub.close()


class LogTailer(object):
  """Streams logs using gRPC."""

  def __init__(self):
    self.client = apis.GetGapicClientInstance('logging', 'v2')
    self.tail_stub = None

  def TailLogs(self,
               resource_names,
               logs_filter,
               buffer_window_seconds=None,
               output_warning=log.err.Print,
               output_error=log.error,
               output_debug=log.debug,
               get_now=datetime.datetime.now):
    """Tails log entries from the Cloud Logging API.

    Args:
      resource_names: The resource names to tail.
      logs_filter: The Cloud Logging filter identifying entries to include in
        the session.
      buffer_window_seconds: The amount of time that Cloud Logging should buffer
        entries to get correct ordering, or None if the backend should use its
        default.
      output_warning: A callable that outputs the argument as a warning.
      output_error: A callable that outputs the argument as an error.
      output_debug: A callable that outputs the argument as debug.
      get_now: A callable that returns the current time.

    Yields:
      Entries for the tail session.
    """
    request = self.client.types.TailLogEntriesRequest()
    request.resource_names.extend(resource_names)
    request.filter = logs_filter

    self.tail_stub = gapic_util.MakeBidiRpc(
        self.client, self.client.logging.transport.tail_log_entries,
        initial_request=request)
    if buffer_window_seconds:
      request.buffer_window = datetime.timedelta(seconds=buffer_window_seconds)
    for entry in _StreamEntries(get_now, output_warning, output_error,
                                output_debug, self.tail_stub):
      yield entry

  def Stop(self):
    if self.tail_stub:
      self.tail_stub.close()
