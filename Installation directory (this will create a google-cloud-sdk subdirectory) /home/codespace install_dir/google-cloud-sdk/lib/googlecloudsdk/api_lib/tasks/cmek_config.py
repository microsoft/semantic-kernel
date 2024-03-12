# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""API Library for `gcloud tasks cmek-config`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class RequiredFieldsMissingError(exceptions.Error):
  """Error for when calling a method when a required field is unspecified."""


class CmekConfig(object):
  """Client for cmekConfig resource in the Cloud Tasks API."""

  def __init__(self, messages, cmek_config_service):
    self.messages = messages
    self.cmek_config_service = cmek_config_service

  def UpdateCmekConfig(
      self, project_id, location_id, full_kms_key_name, clear=False
  ):
    """Prepares and sends a UpdateCmekConfig request for the given CmekConfig."""
    # When clearing, the location and project must be set.
    if clear and (location_id is None or project_id is None):
      raise RequiredFieldsMissingError(
          'The location or project are undefined.'
          ' Please set these flags properly.'
      )
    # When updating, flags combination must be set properly.
    # Either a full KMS key name is provided, or all of the flags are provided.
    elif (not clear) and (
        full_kms_key_name is None or location_id is None or project_id is None
    ):
      raise RequiredFieldsMissingError(
          'One or more of the --kms-key-name, --kms-keyring, --location, or'
          ' --project are invalid. Please set these flags properly or make sure'
          ' the full KMS key name is valid. (args: kms_key={}, location={},'
          ' project={})'.format(full_kms_key_name, location_id, project_id)
      )
    cmek_config_name = (
        'projects/{project_id}/locations/{location_id}/cmekConfig'.format(
            project_id=project_id, location_id=location_id
        )
    )

    cmek_config = self.messages.CmekConfig(
        name=cmek_config_name,
        kmsKey=full_kms_key_name,
    )
    request = self.messages.CloudtasksProjectsLocationsUpdateCmekConfigRequest(
        cmekConfig=cmek_config,
        name=cmek_config_name
    )

    return self.cmek_config_service.UpdateCmekConfig(request)

  def GetCmekConfig(self, project_id, location_id):
    """Prepares and sends a GetCmekConfig request for the given CmekConfig."""
    if project_id is None:
      raise RequiredFieldsMissingError(
          'Project ({project_id}) is invalid. Must specify --project'
          ' properly.'.format(project_id=project_id)
      )
    if location_id is None:
      raise RequiredFieldsMissingError(
          'Location path ({location_id}) is invalid. Must specify --location'
          ' properly.'.format(location_id=location_id)
      )

    cmek_config_name = (
        'projects/{project_id}/locations/{location_id}/cmekConfig'.format(
            project_id=project_id, location_id=location_id
        )
    )
    request = self.messages.CloudtasksProjectsLocationsGetCmekConfigRequest(
        name=cmek_config_name,
    )

    return self.cmek_config_service.GetCmekConfig(request)
