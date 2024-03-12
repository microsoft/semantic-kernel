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

"""Common stateful utilities for the gcloud dataproc tool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


class Dataproc(object):
  """Stateful utility for calling Dataproc APIs.

  While this currently could all be static. It is encapsulated in a class to
  support API version switching in future.
  """

  def __init__(self, release_track=base.ReleaseTrack.GA):
    super(Dataproc, self).__init__()
    self.release_track = release_track
    self.api_version = 'v1'
    self._client = None
    self._resources = None

  @property
  def client(self):
    if self._client is None:
      self._client = apis.GetClientInstance('dataproc', self.api_version)
    return self._client

  @property
  def messages(self):
    return apis.GetMessagesModule('dataproc', self.api_version)

  @property
  def resources(self):
    if self._resources is None:
      self._resources = resources.REGISTRY.Clone()
      self._resources.RegisterApiByName('dataproc', self.api_version)
    return self._resources

  @property
  def terminal_job_states(self):
    return [
        self.messages.JobStatus.StateValueValuesEnum.CANCELLED,
        self.messages.JobStatus.StateValueValuesEnum.DONE,
        self.messages.JobStatus.StateValueValuesEnum.ERROR,
    ]

  def GetCreateClusterRequest(self,
                              cluster,
                              project_id,
                              region,
                              request_id,
                              action_on_failed_primary_workers=None):
    """Gets the CreateClusterRequest for the appropriate api version.

    Args :
      cluster : Dataproc cluster to be created.
      project_id: The ID of the Google Cloud Platform project that the cluster
      belongs to.
      region : The Dataproc region in which to handle the request.
      request_id : A unique ID used to identify the request.
      action_on_failed_primary_workers : Supported only for v1 api.

    Raises :
      ValueError : if non-None action_on_failed_primary_workers is passed for
      v1beta2 api.

    Returns :
      DataprocProjectsRegionsClustersCreateRequest
    """
    if action_on_failed_primary_workers is None:
      return self.messages.DataprocProjectsRegionsClustersCreateRequest(
          cluster=cluster,
          projectId=project_id,
          region=region,
          requestId=request_id)

    if self.api_version == 'v1beta2':
      raise ValueError(
          'action_on_failed_primary_workers is not supported for v1beta2 api')

    return self.messages.DataprocProjectsRegionsClustersCreateRequest(
        cluster=cluster,
        projectId=project_id,
        region=region,
        requestId=request_id,
        actionOnFailedPrimaryWorkers=action_on_failed_primary_workers)

  def GetRegionsWorkflowTemplate(self, template, version=None):
    """Gets workflow template from dataproc.

    Args:
      template: workflow template resource that contains template name and id.
      version: version of the workflow template to get.

    Returns:
      WorkflowTemplate object that contains the workflow template info.

    Raises:
      ValueError: if version cannot be converted to a valid integer.
    """
    messages = self.messages
    get_request = messages.DataprocProjectsRegionsWorkflowTemplatesGetRequest(
        name=template.RelativeName())
    if version:
      get_request.version = int(version)
    return self.client.projects_regions_workflowTemplates.Get(get_request)
