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
"""Utility function for OS Config Troubleshooter to check cloud logs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import os
import re

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.app import logs_util
from googlecloudsdk.api_lib.logging import common
from googlecloudsdk.api_lib.logging import util as logging_util
from googlecloudsdk.core import log as logging
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
import six

_NUM_SERIAL_PORTS = 4


def _PayloadToJSON(payload, is_json_payload=False):
  """Converts the property into a JSON string.

  This is mainly used for properties that have additional properties under them.
  For example, the resource and split properties of LogEntry store objects
  containing additional fields. These fields must be elementary and have no
  nested objects within.

  Args:
    payload: the property to serialize to JSON.
    is_json_payload: only used for the jsonPayload property since the values
                     values are nested in an additional string_value attribute.

  Returns:
    The JSON string representation of the provided property of a LogEntry.
  """
  payload_string = '{\n'
  properties = payload.additionalProperties
  length = len(properties)
  for i in range(length):
    field = properties[i]
    payload_string += '"{}": "{}"'.format(
        field.key,
        (field.value.string_value if is_json_payload else field.value)
    ) + ('\n' if i == length - 1 else ',\n')
  payload_string += '}'
  return payload_string


def _PayloadFormatter(log):
  """Used as a formatter for logs_util.LogPrinter.

  If the log has a JSON payload or a proto payload, the payloads will be
  JSON-ified. The text payload will be returned as-is.

  Args:
    log: the log entry to serialize to json

  Returns:
    A JSON serialization of a log's payload.
  """
  if hasattr(log, 'protoPayload') and log.protoPayload:
    return _PayloadToJSON(log.protoPayload)
  elif hasattr(log, 'textPayload') and log.textPayload:
    return log.textPayload
  elif hasattr(log, 'jsonPayload') and log.jsonPayload:
    return _PayloadToJSON(log.jsonPayload, is_json_payload=True)
  return 'No contents found.'


def _GenerateLogFilePath(dest, instance_id, serial_port_num=None):
  """Gets the full path of the destination file to which to download logs."""
  base_dir = None
  if dest.startswith('~'):
    base_dir = files.ExpandHomeDir(dest)
  elif os.path.isabs(dest):
    base_dir = dest
  else:
    base_dir = files.GetCWD()
  date_str = _GetDateStr()

  file_name = ''
  if serial_port_num:
    file_name = '{}_serial_port_{}_logs_{}.txt'.format(instance_id,
                                                       serial_port_num,
                                                       date_str)
  else:
    file_name = '{}_cloud_logging_logs_{}.txt'.format(instance_id, date_str)
  return os.path.join(base_dir, file_name)


def DownloadInstanceLogs(instance,
                         logs,
                         dest,
                         serial_port_num=None):
  """Downloads the logs and puts them in the specified destination.

  Args:
    instance: the instance from which to download the logs.
    logs: the list of logs from the instance.
    dest: the destination folder.
    serial_port_num: The serial port from which the logs came
  """
  dest_file = _GenerateLogFilePath(dest, instance.id, serial_port_num)

  if serial_port_num:
    contents = logs.contents.split('\n')
    lines_to_download = []
    for line in contents:
      if 'OSConfigAgent' in line:
        lines_to_download.append(line)
    files.WriteFileContents(dest_file, '\n'.join(lines_to_download))
  else:
    formatter = logs_util.LogPrinter()
    formatter.RegisterFormatter(_PayloadFormatter)
    files.WriteFileContents(
        dest_file,
        formatter.Format(logs[0]) + '\n')
    with files.FileWriter(dest_file, append=True) as f:
      for log in logs[1:]:
        f.write(formatter.Format(log) + '\n')
  logging.Print('Logs downloaded to {}.'.format(dest_file))


def _GetDateStr():
  date = datetime.datetime.now()
  return date.strftime('%Y-%m-%d-%H-%M-%S')


def _GetSerialLogOutput(client, project, instance, zone, port):
  request = (client.apitools_client.instances,
             'GetSerialPortOutput',
             client.messages.ComputeInstancesGetSerialPortOutputRequest(
                 instance=instance.name,
                 project=project.name,
                 port=port,
                 start=0,
                 zone=zone))
  return client.MakeRequests(requests=[request])[0]


def CheckCloudLogs(project, instance):
  """Checks the Cloud logs created by this instance for errors."""
  logging.Print('The troubleshooter is now fetching and analyzing logs...\n')

  # Check if the service account has the desired scope.
  cloud_logging_enabled = False
  for account in instance.serviceAccounts:
    if 'https://www.googleapis.com/auth/logging.write' in account.scopes:
      cloud_logging_enabled = True
      break

  if not cloud_logging_enabled:
    logging.Print('Cloud logging is not enabled for this project.')
    return False

  filter_str = ('resource.type="gce_instance" AND '
                'resource.labels.instance_id="{}" AND '
                'log_name="projects/{}/logs/OSConfigAgent"').format(
                    instance.id, project.name)
  logs = list(common.FetchLogs(filter_str, limit=1000,
                               order_by='DESC'))
  logs.reverse()  # Make the logs be in ascending order by timestamp.

  severity_enum = logging_util.GetMessages().LogEntry.SeverityValueValuesEnum
  # Find error logs
  error_log_counter = 0
  earliest_timestamp = None
  for log in logs:
    if log.severity >= severity_enum.ERROR:
      error_log_counter += 1
    if not earliest_timestamp:
      earliest_timestamp = log.timestamp

  if logs:
    response_message = ('The troubleshooter analyzed Cloud Logging logs and '
                        'found:\n')
    response_message += '> {} OSConfigAgent log entries.\n'.format(len(logs))
    response_message += '> Among them, {} {} errors.\n'.format(
        error_log_counter, 'has' if error_log_counter == 1 else 'have')
    response_message += '> The earliest timestamp is ' + (
        earliest_timestamp if earliest_timestamp else 'N/A') + '.'
    logging.Print(response_message)

    # Prompt user to keep logs for each error log.
    cont = console_io.PromptContinue(
        prompt_string='Download all OSConfigAgent logs?')

    if cont:
      dest = console_io.PromptWithDefault(
          message='Destination folder for log download',
          default='~/Downloads/osconfig-logs/')
      logging.Print('Downloading log entries...')

      DownloadInstanceLogs(instance, logs, six.text_type(dest))
  else:
    logging.Print('The troubleshooter analyzed Cloud Logging logs and found '
                  'no logs.')
    return False
  return True


def CheckSerialLogOutput(client, project, instance, zone):
  """Checks the serial log output of the given instance for errors."""
  logging.Print('The troubleshooter is now checking serial log output.')

  logs_to_download = []
  serial_logs = []
  for port in range(1, _NUM_SERIAL_PORTS + 1):
    serial_log = None
    num_errors = 0
    try:
      serial_log = _GetSerialLogOutput(client, project, instance, zone, port)
      num_errors = len(re.findall(r'OSConfigAgent Error', serial_log.contents))
    except exceptions.Error:
      num_errors = None
    serial_logs.append(serial_log)

    if num_errors is not None:
      logging.Print('Port {}: {} OSConfigAgent error(s)'.format(port,
                                                                num_errors))
      if num_errors:
        logs_to_download.append(port)
    else:
      logging.Print('Port {}: N/A'.format(port))

  if logs_to_download:
    cont = console_io.PromptContinue(
        prompt_string='Download all OSConfigAgent logs?')
    if cont:
      dest = console_io.PromptWithDefault(
          message='Destination folder for log download (default is ~/Downloads/osconfig-logs):',
          default='~/Downloads/osconfig-logs')
      logging.Print('Downloading serial log entries...')
      for port in logs_to_download:
        DownloadInstanceLogs(
            instance,
            serial_logs[port - 1],
            six.text_type(dest),
            serial_port_num=port)
