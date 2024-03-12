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
"""Utilities for interacting with streaming logs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import encoding
from googlecloudsdk.command_lib.logs import stream
import six

LOG_FORMAT = ('value('
              'severity,'
              'timestamp.date("%Y-%m-%d %H:%M:%S %z",tz="LOCAL"), '
              'task_name,'
              'message'
              ')')
_CONTINUE_INTERVAL = 10


def StreamLogs(name, continue_function, polling_interval, task_name,
               allow_multiline):
  """Returns the streaming log of the job by id.

  Args:
    name: string id of the entity.
    continue_function: One-arg function that takes in the number of empty polls
      and outputs a boolean to decide if we should keep polling or not. If not
      given, keep polling indefinitely.
    polling_interval: amount of time to sleep between each poll.
    task_name: String name of task.
    allow_multiline: Tells us if logs with multiline messages are okay or not.
  """
  log_fetcher = stream.LogFetcher(
      filters=_LogFilters(name, task_name=task_name),
      polling_interval=polling_interval,
      continue_interval=_CONTINUE_INTERVAL,
      continue_func=continue_function)
  return _SplitMultiline(log_fetcher.YieldLogs(), allow_multiline)


def _LogFilters(name, task_name):
  """Returns filters for log fetcher to use.

  Args:
    name: string id of the entity.
    task_name: String name of task.

  Returns:
    A list of filters to be passed to the logging API.
  """
  filters = [
      'resource.type="ml_job"', 'resource.labels.job_id="{0}"'.format(name)
  ]
  if task_name:
    filters.append('resource.labels.task_name="{0}"'.format(task_name))
  return filters


def _SplitMultiline(log_generator, allow_multiline=False):
  """Splits the dict output of logs into multiple lines.

  Args:
    log_generator: iterator that returns a an ml log in dict format.
    allow_multiline: Tells us if logs with multiline messages are okay or not.

  Yields:
    Single-line ml log dictionaries.
  """
  for log in log_generator:
    log_dict = _EntryToDict(log)
    messages = log_dict['message'].splitlines()
    if allow_multiline:
      yield log_dict
    else:
      if not messages:
        messages = ['']
      for message in messages:
        single_line_log = copy.deepcopy(log_dict)
        single_line_log['message'] = message
        yield single_line_log


def _EntryToDict(log_entry):
  """Converts a log entry to a dictionary."""
  output = {}
  output[
      'severity'] = log_entry.severity.name if log_entry.severity else 'DEFAULT'
  output['timestamp'] = log_entry.timestamp
  output['task_name'] = _GetTaskName(log_entry)
  message = []
  if log_entry.jsonPayload is not None:
    json_data = _ToDict(log_entry.jsonPayload)
    # 'message' contains a free-text message that we want to pull out of the
    # JSON.
    if 'message' in json_data:
      if json_data['message']:
        message.append(json_data['message'])
  elif log_entry.textPayload is not None:
    message.append(six.text_type(log_entry.textPayload))
  output['message'] = ''.join(message)
  return output


def _GetTaskName(log_entry):
  """Reads the label attributes of the given log entry."""
  resource_labels = {} if not log_entry.resource else _ToDict(
      log_entry.resource.labels)
  return 'unknown_task' if not resource_labels.get(
      'task_name') else resource_labels['task_name']


def _ToDict(message):
  if not message:
    return {}
  if isinstance(message, dict):
    return message
  else:
    return encoding.MessageToDict(message)
