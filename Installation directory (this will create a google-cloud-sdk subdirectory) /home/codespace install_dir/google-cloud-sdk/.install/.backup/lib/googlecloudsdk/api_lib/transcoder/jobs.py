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
"""Utilities for Transcoder API Jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transcoder import util
from googlecloudsdk.command_lib.util.args import labels_util

VERSION_MAP = {base.ReleaseTrack.GA: 'v1'}


def _GetClientInstance(release_track=base.ReleaseTrack.GA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance('transcoder', api_version)


def _GetTranscoderMessages():
  """Get a resource reference to the transcoder proto."""
  return apis.GetMessagesModule('transcoder', 'v1')


class ProcessingMode(enum.Enum):
  PROCESSING_MODE_INTERACTIVE = 'PROCESSING_MODE_INTERACTIVE'
  PROCESSING_MODE_BATCH = 'PROCESSING_MODE_BATCH'


class OptimizationStrategy(enum.Enum):
  AUTODETECT = 'AUTODETECT'
  DISABLED = 'DISABLED'


class JobsClient(object):
  """Client for job service in the Transcoder API."""

  def __init__(self, release_track=base.ReleaseTrack.GA, client=None):
    self.client = client or _GetClientInstance(release_track)
    self.message = self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_jobs
    self._job_class = self.client.MESSAGES_MODULE.Job

  def Create(self, parent_ref, args):
    """Create a job.

    Args:
      parent_ref: a Resource reference to a transcoder.projects.locations
        resource for the parent of this template.
      args: arguments to create a job.

    Returns:
      Job: Job created, including configuration and name.
    """

    labels = labels_util.ParseCreateArgs(args, self.message.Job.LabelsValue)
    input_uri = args.input_uri
    output_uri = args.output_uri
    template_id = args.template_id
    mode = None
    if args.mode is not None:
      msg = _GetTranscoderMessages()
      mode = msg.Job.ModeValueValuesEnum(args.mode)
    batch_mode_priority = 0
    if args.batch_mode_priority is not None:
      batch_mode_priority = args.batch_mode_priority
    optimization = None
    if args.optimization is not None:
      msg = _GetTranscoderMessages()
      optimization = msg.Job.OptimizationValueValuesEnum(args.optimization)
    job_json = None
    if template_id is None:
      job_json = util.GetContent(args.file, args.json)

    if job_json is None:
      job = self.message.Job(
          inputUri=input_uri,
          outputUri=output_uri,
          templateId=template_id,
          labels=labels,
          mode=mode,
          batchModePriority=batch_mode_priority,
          optimization=optimization,
      )
    else:
      job = encoding.JsonToMessage(self._job_class, job_json)
      job.inputUri = input_uri or job.inputUri
      job.outputUri = output_uri or job.outputUri
      job.labels = labels or job.labels
      job.mode = mode or job.mode
      job.optimization = optimization or job.optimization
      job.batchModePriority = batch_mode_priority or job.batchModePriority
    req = self.message.TranscoderProjectsLocationsJobsCreateRequest(
        parent=parent_ref.RelativeName(), job=job
    )
    return self._service.Create(req)

  def Delete(self, job_ref):
    """Delete a job.

    Args:
      job_ref: a resource reference to a transcoder.projects.locations.jobs
        resource to delete

    Returns:
      Empty: An empty response message.
    """
    req = self.message.TranscoderProjectsLocationsJobsDeleteRequest(
        name=job_ref.RelativeName()
    )
    return self._service.Delete(req)

  def Get(self, job_ref):
    """Get a job.

    Args:
      job_ref: a resource reference to a transcoder.projects.locations.jobs
        resource to get

    Returns:
      Job: if available, return the full job information.
    """
    req = self.message.TranscoderProjectsLocationsJobsGetRequest(
        name=job_ref.RelativeName()
    )
    return self._service.Get(req)

  def List(self, parent_ref, page_size=100):
    """List jobs.

    Args:
      parent_ref: a Resource reference to a transcoder.projects.locations
        resource to list job for.
      page_size (optional): the number of jobs to fetch in each request (affects
        requests made, but not the yielded results).

    Returns:
      Jobs: a list of jobs in the specified location
    """
    req = self.message.TranscoderProjectsLocationsJobsListRequest(
        parent=parent_ref.RelativeName(), pageSize=page_size
    )
    resp = list_pager.YieldFromList(
        service=self._service,
        request=req,
        batch_size=page_size,
        field='jobs',
        batch_size_attribute='pageSize',
    )
    return resp
