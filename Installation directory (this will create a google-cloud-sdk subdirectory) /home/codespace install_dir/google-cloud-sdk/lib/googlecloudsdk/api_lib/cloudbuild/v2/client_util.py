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
"""Utilities for the cloudbuild v2 API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

_API_NAME = 'cloudbuild'
GA_API_VERSION = 'v2'

RELEASE_TRACK_TO_API_VERSION = {
    base.ReleaseTrack.GA: GA_API_VERSION,
    base.ReleaseTrack.BETA: GA_API_VERSION,
    base.ReleaseTrack.ALPHA: GA_API_VERSION,
}

CLUSTER_NAME_SELECTOR = r'projects/.*/locations/.*/memberships/(.*)'


def GetMessagesModule(release_track=base.ReleaseTrack.GA):
  """Returns the messages module for Cloud Build.

  Args:
    release_track: The desired value of the enum
      googlecloudsdk.calliope.base.ReleaseTrack.

  Returns:
    Module containing the definitions of messages for Cloud Build.
  """
  return apis.GetMessagesModule(_API_NAME,
                                RELEASE_TRACK_TO_API_VERSION[release_track])


def GetClientInstance(release_track=base.ReleaseTrack.GA, use_http=True):
  """Returns an instance of the Cloud Build client.

  Args:
    release_track: The desired value of the enum
      googlecloudsdk.calliope.base.ReleaseTrack.
    use_http: bool, True to create an http object for this client.

  Returns:
    base_api.BaseApiClient, An instance of the Cloud Build client.
  """
  return apis.GetClientInstance(
      _API_NAME,
      RELEASE_TRACK_TO_API_VERSION[release_track],
      no_http=(not use_http))


def GetRun(project, region, run_id, run_type):
  """Get a PipelineRun/TaskRun."""
  client = GetClientInstance()
  messages = GetMessagesModule()
  if run_type == 'pipelinerun':
    pipeline_run_resource = resources.REGISTRY.Parse(
        run_id,
        collection='cloudbuild.projects.locations.pipelineRuns',
        api_version='v2',
        params={
            'projectsId': project,
            'locationsId': region,
            'pipelineRunsId': run_id,
        })
    pipeline_run = client.projects_locations_pipelineRuns.Get(
        messages.CloudbuildProjectsLocationsPipelineRunsGetRequest(
            name=pipeline_run_resource.RelativeName(),))
    return pipeline_run
  elif run_type == 'taskrun':
    task_run_resource = resources.REGISTRY.Parse(
        run_id,
        collection='cloudbuild.projects.locations.taskRuns',
        api_version='v2',
        params={
            'projectsId': project,
            'locationsId': region,
            'taskRunsId': run_id,
        })
    task_run = client.projects_locations_taskRuns.Get(
        messages.CloudbuildProjectsLocationsTaskRunsGetRequest(
            name=task_run_resource.RelativeName(),))
    return task_run


def ClusterShortName(resource_name):
  """Get the name part of a cluster membership's full resource name.

  For example, "projects/123/locations/global/memberships/cluster2" returns
  "cluster2".

  Args:
    resource_name: A cluster's full resource name.

  Raises:
    ValueError: If the full resource name was not well-formatted.

  Returns:
    The cluster's short name.
  """
  match = re.search(CLUSTER_NAME_SELECTOR, resource_name)
  if match:
    return match.group(1)
  raise ValueError('The cluster membership resource name must match "%s"' %
                   (CLUSTER_NAME_SELECTOR,))


def ListLocations(project):
  """Get the list of supported Cloud Build locations.

  Args:
    project: The project to search.

  Returns:
    A CloudbuildProjectsLocationsListRequest object.
  """
  client = GetClientInstance()
  messages = GetMessagesModule()

  return client.projects_locations.List(
      messages.CloudbuildProjectsLocationsListRequest(
          name='projects/{}'.format(project)
      )
  )
