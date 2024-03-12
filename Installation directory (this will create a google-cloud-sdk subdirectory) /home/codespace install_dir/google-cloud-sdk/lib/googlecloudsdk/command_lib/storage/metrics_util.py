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
"""Used to collect anonymous transfer-related metrics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task_util
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms


def fix_user_agent_for_gsutil_shim():
  """Transform the user agent when the gsutil shim is used to run gcloud.

  This transforms `gcloud.storage.command` to `gcloud.gsutil.command`.

  This needs to be called by every command, so the best place to put this is
  likely surface/storage/__init__.py, but if there's a better place it could be
  called there instead.
  """
  if properties.VALUES.storage.run_by_gsutil_shim.GetBool():
    command_path_string = properties.VALUES.metrics.command_name.Get().replace(
        'gcloud.storage.', 'gcloud.gslibshim.')
    properties.VALUES.SetInvocationValue(
        properties.VALUES.metrics.command_name, command_path_string, None)


class ParallelismStrategy(enum.Enum):
  SEQUENTIAL = 1
  PARALLEL = 2


PROVIDER_PREFIX_TO_METRICS_KEY = {
    storage_url.ProviderPrefix.FILE: 1,
    storage_url.ProviderPrefix.GCS: 2,
    storage_url.ProviderPrefix.HTTP: 3,
    storage_url.ProviderPrefix.HTTPS: 4,
    storage_url.ProviderPrefix.POSIX: 5,
    storage_url.ProviderPrefix.S3: 6,
}

# Used when either Parallelism Strategy or Provider Prefix is unset.
UNSET = 0


def _record_storage_event(metric, value=0):
  """Common code for processing an event.

  Args:
    metric (str): The metric being recorded.
    value (mixed): The value being recorded.
  """
  command_name = properties.VALUES.metrics.command_name.Get()
  metrics.CustomKeyValue(command_name, 'Storage-' + metric, value)


def _get_parallelism_strategy():
  if task_util.should_use_parallelism():
    return ParallelismStrategy.PARALLEL.value
  return ParallelismStrategy.SEQUENTIAL.value


def _get_run_by_gsutil_shim():
  return 1 if properties.VALUES.storage.run_by_gsutil_shim.GetBool() else 0


def report(source_scheme=UNSET, destination_scheme=UNSET, num_files=0,
           size=0, avg_speed=0, disk_io_time=0):
  """Reports metrics for a transfer.

  Args:
    source_scheme (int): The source scheme, i.e. 'gs' or 's3'.
    destination_scheme (int): The destination scheme i.e. 'gs' or 's3'.
    num_files (int): The number of files transferred.
    size (int): The size of the files transferred, in bytes.
    avg_speed (int): The average throughput of a transfer in bytes/sec.
    disk_io_time (int): The time spent on disk of a transfer in ms.
  """
  _record_storage_event('ParallelismStrategy', _get_parallelism_strategy())
  _record_storage_event('RunByGsutilShim', _get_run_by_gsutil_shim())
  _record_storage_event('SourceScheme', source_scheme)
  _record_storage_event('DestinationScheme', destination_scheme)
  _record_storage_event('NumberOfFiles', num_files)
  _record_storage_event('SizeOfFilesBytes', size)
  _record_storage_event('AverageSpeedBytesPerSec', avg_speed)
  _record_storage_event('DiskIoTimeMs', disk_io_time)


def _get_partitions():
  """Retrieves a list of disk partitions.

  Returns:
    An array of partition names as strings.
  """
  partitions = []

  try:
    with files.FileReader('/proc/partitions') as f:
      lines = f.readlines()[2:]
      for line in lines:
        _, _, _, name = line.split()
        if name[-1].isdigit():
          partitions.append(name)
  # This will catch access denied and file not found errors, which is expected
  # on non-Linux/limited access systems. All other errors will raise as normal.
  except files.Error:
    pass

  return partitions


def get_disk_counters():
  """Retrieves disk I/O statistics for all disks.

  Adapted from the psutil module's psutil._pslinux.disk_io_counters:
    http://code.google.com/p/psutil/source/browse/trunk/psutil/_pslinux.py

  Originally distributed under under a BSD license.
  Original Copyright (c) 2009, Jay Loden, Dave Daeschler, Giampaolo Rodola.

  Returns:
    A dictionary containing disk names mapped to the disk counters from
    /disk/diskstats.
  """
  # iostat documentation states that sectors are equivalent with blocks and
  # have a size of 512 bytes since 2.4 kernels. This value is needed to
  # calculate the amount of disk I/O in bytes.
  sector_size = 512

  partitions = _get_partitions()

  retdict = {}
  try:
    with files.FileReader('/proc/diskstats') as f:
      lines = f.readlines()
      for line in lines:
        values = line.split()[:11]
        _, _, name, reads, _, rbytes, rtime, writes, _, wbytes, wtime = values
        if name in partitions:
          rbytes = int(rbytes) * sector_size
          wbytes = int(wbytes) * sector_size
          reads = int(reads)
          writes = int(writes)
          rtime = int(rtime)
          wtime = int(wtime)
          retdict[name] = (reads, writes, rbytes, wbytes, rtime, wtime)
  # This will catch access denied and file not found errors, which is expected
  # on non-Linux/limited access systems. All other errors will raise as normal.
  except files.Error:
    pass

  return retdict


class MetricsReporter():
  """Mix-in for tracking metrics during task status reporting."""

  def __init__(self):
    # For source/destination types
    self._source_scheme = UNSET
    self._destination_scheme = UNSET
    # For calculating disk I/O.
    self._disk_counters_start = get_disk_counters()

  def _get_scheme_value(self, url):
    """Extracts the scheme as an integer value from a storage_url."""
    if url:
      return PROVIDER_PREFIX_TO_METRICS_KEY[url.scheme]
    return UNSET

  def _set_source_and_destination_schemes(self, status_message):
    """Sets source and destination schemes, if available.

    Args:
      status_message (thread_messages.*): Message to process.
    """
    if self._source_scheme == UNSET:
      self._source_scheme = self._get_scheme_value(status_message.source_url)
    if self._destination_scheme == UNSET:
      self._destination_scheme = self._get_scheme_value(
          status_message.destination_url)

  def _calculate_disk_io(self):
    """Calculate deltas of time spent on I/O."""
    current_os = platforms.OperatingSystem.Current()
    if current_os == platforms.OperatingSystem.LINUX:
      disk_start = self._disk_counters_start
      disk_end = get_disk_counters()
      # Read and write time are the 5th and 6th elements of the stat tuple.
      return (sum([stat[4] + stat[5] for stat in disk_end.values()]) -
              sum([stat[4] + stat[5] for stat in disk_start.values()]))
    return UNSET

  def _report_metrics(self, total_bytes, time_delta, num_files):
    """Reports back all tracked events via report method.

    Args:
      total_bytes (int): Amount of data transferred in bytes.
      time_delta (int): Time elapsed during the transfer in seconds.
      num_files (int): Number of files processed
    """
    # This recreates the gsutil throughput calculation so that metrics are 1:1.
    avg_speed = round(float(total_bytes) / float(time_delta))
    report(
        source_scheme=self._source_scheme,
        destination_scheme=self._destination_scheme,
        num_files=num_files,
        size=total_bytes,
        avg_speed=avg_speed,
        disk_io_time=self._calculate_disk_io())
