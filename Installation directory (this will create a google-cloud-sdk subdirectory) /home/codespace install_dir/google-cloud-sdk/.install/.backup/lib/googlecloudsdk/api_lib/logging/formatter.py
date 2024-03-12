# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Formatter to parse logs into single lines."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from cloudsdk.google.protobuf import timestamp_pb2
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.privateca import text_utils


def FormatLog(log):
  """Format logs for a service."""
  is_log_entry = isinstance(log,
                            apis.GetMessagesModule('logging', 'v2').LogEntry)
  log_entry_line = GetAttributeFieldFromLog('log_name', is_log_entry, log)
  if not log_entry_line:
    return ''
  split_log = log_entry_line.split('%2F')
  if len(split_log) < 2:
    return ''
  log_type = split_log[1]
  log_output = [GetTimestampFromLogFormat(is_log_entry, log)]
  if log_type == 'requests':
    http_request = GetAttributeFieldFromLog('http_request', is_log_entry, log)
    http_method = GetAttributeFieldFromLog('request_method', is_log_entry,
                                           http_request)
    status = GetAttributeFieldFromLog('status', is_log_entry, http_request)
    url = GetAttributeFieldFromLog('request_url', is_log_entry, http_request)
    log_output.append(http_method)
    log_output.append(str(status))
    log_output.append(url)
  elif log_type == 'stderr' or log_type == 'stdout':
    text_payload = GetAttributeFieldFromLog('text_payload', is_log_entry, log)
    log_output.append(text_payload)
  else:
    return ''
  return ' '.join(log_output)


def GetTimestampFromLogFormat(is_log_entry, log):
  """Returns timestamp in 'YYYY-MM-DD HH:MM:SS' string format."""
  timestamp = GetAttributeFieldFromLog('timestamp', is_log_entry, log)
  if is_log_entry:
    ts = timestamp_pb2.Timestamp()
    ts.FromJsonString(timestamp)
    log_entry_timestamp = ts.ToDatetime()
    return datetime.datetime.strftime(log_entry_timestamp, '%Y-%m-%d %H:%M:%S')
  return datetime.datetime.strftime(timestamp, '%Y-%m-%d %H:%M:%S')


def GetAttributeFieldFromLog(field_name, is_log_entry, log_obj):
  return getattr(log_obj, GetProperField(field_name, is_log_entry), '')


def GetProperField(field_name, is_log_entry):
  """Retrieve the proper atrribute from LogEntry depending if it is in MessageModule or GapiClient format."""
  if not is_log_entry:
    return field_name
  return text_utils.SnakeCaseToCamelCase(field_name)
