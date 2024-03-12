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
"""For managing the copy manifest feature (manifest = a file with copy info)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import csv
import datetime
import enum
import os

from googlecloudsdk.command_lib.storage import thread_messages
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


class ResultStatus(enum.Enum):
  ERROR = 'error'
  OK = 'OK'
  SKIP = 'skip'


class ManifestManager:
  """Handles writing copy statuses to manifest."""

  def __init__(self, manifest_path):
    """Creates manifest file with correct headers."""
    # UploadId is never populated and kept around for compatibility with gsutil.
    self._manifest_column_headers = [
        'Source',
        'Destination',
        'Start',
        'End',
        'Md5',
    ] + (['UploadId']
         if properties.VALUES.storage.run_by_gsutil_shim.GetBool() else []) + [
             'Source Size',
             'Bytes Transferred',
             'Result',
             'Description',
         ]

    self._manifest_path = manifest_path
    if os.path.exists(manifest_path) and os.path.getsize(manifest_path) > 0:
      return
    with files.FileWriter(manifest_path, newline='\n') as file_writer:
      csv.DictWriter(file_writer, self._manifest_column_headers).writeheader()

  def write_row(self, manifest_message, file_progress=None):
    """Writes data to manifest file."""
    if file_progress and manifest_message.result_status is ResultStatus.OK:
      bytes_copied = file_progress.total_bytes_copied
    else:
      bytes_copied = 0

    end_time = manifest_message.end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    if file_progress:
      start_time = file_progress.start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    else:
      start_time = end_time
    if manifest_message.description:
      # Print raw newlines and carriage returns in CSV.
      description = manifest_message.description.replace('\n', '\\n').replace(
          '\r', '\\r')
    else:
      description = ''

    row_dictionary = {
        'Source': manifest_message.source_url.url_string,
        'Destination': manifest_message.destination_url.versionless_url_string,
        'Start': start_time,
        'End': end_time,
        'Md5': manifest_message.md5_hash or '',
        'Source Size': manifest_message.size,
        'Bytes Transferred': bytes_copied,
        'Result': manifest_message.result_status.value,
        'Description': description,
    }
    if properties.VALUES.storage.run_by_gsutil_shim.GetBool():
      row_dictionary['UploadId'] = None
    with files.FileWriter(
        self._manifest_path, append=True, newline='\n') as file_writer:
      csv.DictWriter(file_writer,
                     self._manifest_column_headers).writerow(row_dictionary)


def parse_for_completed_sources(manifest_path):
  """Extracts set of completed or skipped copies from manifest CSV."""
  if not (manifest_path and os.path.exists(manifest_path)):
    return set()
  res = set()
  with files.FileReader(manifest_path) as file_reader:
    csv_reader = csv.DictReader(file_reader)
    for row in csv_reader:
      if row['Result'] in (ResultStatus.OK.value, ResultStatus.SKIP.value):
        res.add(row['Source'])
  return res


def _send_manifest_message(task_status_queue,
                           source_resource,
                           destination_resource,
                           result_status,
                           md5_hash=None,
                           description=None):
  """Send ManifestMessage to task_status_queue for processing."""
  task_status_queue.put(
      thread_messages.ManifestMessage(
          source_url=source_resource.storage_url,
          destination_url=destination_resource.storage_url,
          end_time=datetime.datetime.utcnow(),
          # Ignores transforms that change file size at destination, like STET.
          size=source_resource.size,
          result_status=result_status,
          # Will be None if a multi-component copy (they use CRC32C hashing)
          # or if the "storage/check_hashes" property is set to "never".
          md5_hash=md5_hash,
          description=description,
      ))


def send_error_message(task_status_queue, source_resource, destination_resource,
                       error):
  """Send ManifestMessage for failed copy to central processing."""
  _send_manifest_message(
      task_status_queue,
      source_resource,
      destination_resource,
      ResultStatus.ERROR,
      md5_hash=None,
      description=str(error))


def send_skip_message(task_status_queue, source_resource, destination_resource,
                      message):
  """Send ManifestMessage for skipped copy to central processing."""
  _send_manifest_message(
      task_status_queue,
      source_resource,
      destination_resource,
      ResultStatus.SKIP,
      md5_hash=None,
      description=message)


def send_success_message(task_status_queue,
                         source_resource,
                         destination_resource,
                         md5_hash=None):
  """Send ManifestMessage for successful copy to central processing."""
  _send_manifest_message(task_status_queue, source_resource,
                         destination_resource, ResultStatus.OK, md5_hash)
