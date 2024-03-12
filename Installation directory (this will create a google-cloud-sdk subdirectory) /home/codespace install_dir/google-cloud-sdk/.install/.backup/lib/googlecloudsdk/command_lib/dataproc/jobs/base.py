# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Utilities for building the dataproc clusters CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import os

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

import six
import six.moves.urllib.parse


class JobBase(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for Jobs."""

  def __init__(self, *args, **kwargs):
    super(JobBase, self).__init__(*args, **kwargs)
    self.files_by_type = {}
    self.files_to_stage = []
    self._staging_dir = None

  def _GetStagedFile(self, file_str):
    """Validate file URI and register it for uploading if it is local."""
    drive, _ = os.path.splitdrive(file_str)
    uri = six.moves.urllib.parse.urlsplit(file_str, allow_fragments=False)
    # Determine the file is local to this machine if no scheme besides a drive
    # is passed. file:// URIs are interpreted as living on VMs.
    is_local = drive or not uri.scheme
    if not is_local:
      # Non-local files are already staged.
      # TODO(b/36057257): Validate scheme.
      return file_str

    if not os.path.exists(file_str):
      raise files.Error('File Not Found: [{0}].'.format(file_str))
    if self._staging_dir is None:
      # we raise this exception only if there are files to stage but the staging
      # location couldn't be determined. In case where files are already staged
      # this exception is not raised
      raise exceptions.ArgumentError(
          'Could not determine where to stage local file {0}. When submitting '
          'a job to a cluster selected via --cluster-labels, either\n'
          '- a staging bucket must be provided via the --bucket argument, or\n'
          '- all provided files must be non-local.'.format(file_str))

    basename = os.path.basename(file_str)
    self.files_to_stage.append(file_str)
    staged_file = six.moves.urllib.parse.urljoin(self._staging_dir, basename)
    return staged_file

  def ValidateAndStageFiles(self):
    """Validate file URIs and upload them if they are local."""
    for file_type, file_or_files in six.iteritems(self.files_by_type):
      # TODO(b/36049793): Validate file suffixes.
      if not file_or_files:
        continue
      elif isinstance(file_or_files, six.string_types):
        self.files_by_type[file_type] = self._GetStagedFile(file_or_files)
      else:
        staged_files = [self._GetStagedFile(f) for f in file_or_files]
        self.files_by_type[file_type] = staged_files

    if self.files_to_stage:
      log.info('Staging local files {0} to {1}.'.format(self.files_to_stage,
                                                        self._staging_dir))
      storage_helpers.Upload(self.files_to_stage, self._staging_dir)

  def GetStagingDir(self, cluster, job_id, bucket=None):
    """Determine the GCS directory to stage job resources in."""
    if bucket is None and cluster is None:
      return None
    if bucket is None:
      # If bucket is not provided, fall back to cluster's staging bucket.
      if cluster.config:
        bucket = cluster.config.configBucket
      elif cluster.virtualClusterConfig:
        bucket = cluster.virtualClusterConfig.stagingBucket
      else:
        # This is only needed if the request needs to stage files. If it doesn't
        # everything will work. If it does need to stage files, then it will
        # fail with a message saying --bucket should be specified.
        return None
    cluster_id = 'unresolved'
    if cluster is not None:
      cluster_id = cluster.clusterUuid

    staging_dir = (
        'gs://{bucket}/{prefix}/{cluster_id}/jobs/{job_id}/staging/'.format(
            bucket=bucket,
            prefix=constants.GCS_METADATA_PREFIX,
            cluster_id=cluster_id,
            job_id=job_id))
    return staging_dir

  def BuildLoggingConfig(self, messages, driver_logging):
    """Build LoggingConfig from parameters."""
    if not driver_logging:
      return None

    value_enum = (messages.LoggingConfig.DriverLogLevelsValue.
                  AdditionalProperty.ValueValueValuesEnum)
    config = collections.OrderedDict(
        [(key, value_enum(value)) for key, value in driver_logging.items()])
    return messages.LoggingConfig(
        driverLogLevels=encoding.DictToAdditionalPropertyMessage(
            config,
            messages.LoggingConfig.DriverLogLevelsValue))

  def PopulateFilesByType(self, args):
    self.files_by_type.update(self.GetFilesByType(args))
