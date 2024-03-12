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
"""Utilities for querying custom jobs in AI Platform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io


class CustomJobsClient(object):
  """Client used for interacting with CustomJob endpoint."""

  def __init__(self, version=constants.GA_VERSION):
    client = apis.GetClientInstance(constants.AI_PLATFORM_API_NAME,
                                    constants.AI_PLATFORM_API_VERSION[version])
    self._messages = client.MESSAGES_MODULE
    self._version = version
    self._service = client.projects_locations_customJobs
    self._message_prefix = constants.AI_PLATFORM_MESSAGE_PREFIX[version]

  def GetMessage(self, message_name):
    """Returns the API message class by name."""

    return getattr(
        self._messages,
        '{prefix}{name}'.format(prefix=self._message_prefix,
                                name=message_name), None)

  def CustomJobMessage(self):
    """Retures the CustomJob resource message."""

    return self.GetMessage('CustomJob')

  def Create(self,
             parent,
             job_spec,
             display_name=None,
             kms_key_name=None,
             labels=None):
    """Constructs a request and sends it to the endpoint to create a custom job instance.

    Args:
      parent: str, The project resource path of the custom job to create.
      job_spec: The CustomJobSpec message instance for the job creation request.
      display_name: str, The display name of the custom job to create.
      kms_key_name: A customer-managed encryption key to use for the custom job.
      labels: LabelValues, map-like user-defined metadata to organize the custom
        jobs.

    Returns:
      A CustomJob message instance created.
    """
    custom_job = self.CustomJobMessage()(
        displayName=display_name, jobSpec=job_spec)

    if kms_key_name is not None:
      custom_job.encryptionSpec = self.GetMessage('EncryptionSpec')(
          kmsKeyName=kms_key_name)

    if labels:
      custom_job.labels = labels

    if self._version == constants.BETA_VERSION:
      return self._service.Create(
          self._messages.AiplatformProjectsLocationsCustomJobsCreateRequest(
              parent=parent, googleCloudAiplatformV1beta1CustomJob=custom_job))
    else:
      return self._service.Create(
          self._messages.AiplatformProjectsLocationsCustomJobsCreateRequest(
              parent=parent, googleCloudAiplatformV1CustomJob=custom_job))

  def List(self, limit=None, region=None):
    return list_pager.YieldFromList(
        self._service,
        self._messages.AiplatformProjectsLocationsCustomJobsListRequest(
            parent=region),
        field='customJobs',
        batch_size_attribute='pageSize',
        limit=limit)

  def Get(self, name):
    request = self._messages.AiplatformProjectsLocationsCustomJobsGetRequest(
        name=name)
    return self._service.Get(request)

  def Cancel(self, name):
    request = self._messages.AiplatformProjectsLocationsCustomJobsCancelRequest(
        name=name)
    return self._service.Cancel(request)

  def CheckJobComplete(self, name):
    """Returns a function to decide if log fetcher should continue polling.

    Args:
      name: String id of job.

    Returns:
      A one-argument function decides if log fetcher should continue.
    """
    request = self._messages.AiplatformProjectsLocationsCustomJobsGetRequest(
        name=name)
    response = self._service.Get(request)

    def ShouldContinue(periods_without_logs):
      if periods_without_logs <= 1:
        return True
      return response.endTime is None

    return ShouldContinue

  def ImportResourceMessage(self, yaml_file, message_name):
    """Import a messages class instance typed by name from a YAML file."""
    data = console_io.ReadFromFileOrStdin(yaml_file, binary=False)
    message_type = self.GetMessage(message_name)
    return export_util.Import(message_type=message_type, stream=data)
