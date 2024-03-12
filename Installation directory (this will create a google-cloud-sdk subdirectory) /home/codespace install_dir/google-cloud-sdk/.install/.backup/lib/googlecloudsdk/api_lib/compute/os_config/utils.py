# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Utility functions for GCE OS Config APIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


_API_CLIENT_NAME = 'osconfig'
_API_CLIENT_VERSION_MAP = {
    base.ReleaseTrack.BETA: 'v1beta',
    base.ReleaseTrack.GA: 'v1'
}


def GetApiVersion(release_track):
  return _API_CLIENT_VERSION_MAP[release_track]


def GetClientClass(release_track, api_version_override=None):
  return apis.GetClientClass(
      _API_CLIENT_NAME, api_version_override or
      _API_CLIENT_VERSION_MAP[release_track])


def GetClientInstance(release_track, api_version_override=None):
  return apis.GetClientInstance(
      _API_CLIENT_NAME, api_version_override or
      _API_CLIENT_VERSION_MAP[release_track])


def GetClientMessages(release_track, api_version_override=None):
  return apis.GetMessagesModule(
      _API_CLIENT_NAME, api_version_override or
      _API_CLIENT_VERSION_MAP[release_track])


def GetRegistry(release_track, api_version_override=None):
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName(
      _API_CLIENT_NAME, api_version_override or
      _API_CLIENT_VERSION_MAP[release_track])
  return registry


class Poller(waiter.OperationPoller):
  """Poller for synchronous patch job execution."""

  def __init__(self, client, messages):
    """Initializes poller for patch job execution.

    Args:
      client: API client of the OsConfig service.
      messages: API messages of the OsConfig service.
    """
    self.client = client
    self.messages = messages
    self.patch_job_terminal_states = [
        self.messages.PatchJob.StateValueValuesEnum.SUCCEEDED,
        self.messages.PatchJob.StateValueValuesEnum.COMPLETED_WITH_ERRORS,
        self.messages.PatchJob.StateValueValuesEnum.TIMED_OUT,
        self.messages.PatchJob.StateValueValuesEnum.CANCELED,
    ]

  def IsDone(self, patch_job):
    """Overrides."""
    return patch_job.state in self.patch_job_terminal_states

  def Poll(self, request):
    """Overrides."""
    return self.client.projects_patchJobs.Get(request)

  def GetResult(self, patch_job):
    """Overrides."""
    return patch_job
