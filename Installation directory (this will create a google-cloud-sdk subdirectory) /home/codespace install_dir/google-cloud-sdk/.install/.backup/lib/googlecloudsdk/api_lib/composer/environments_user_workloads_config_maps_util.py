# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Utilities for calling the Composer UserWorkloads ConfigMaps API."""

import typing
from typing import Mapping, Tuple

from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import yaml

if typing.TYPE_CHECKING:
  from googlecloudsdk.core.resources import Resource
  from googlecloudsdk.generated_clients.apis.composer.v1alpha2 import composer_v1alpha2_messages
  from googlecloudsdk.generated_clients.apis.composer.v1beta1 import composer_v1beta1_messages
  from googlecloudsdk.generated_clients.apis.composer.v1 import composer_v1_messages


def GetService(release_track=base.ReleaseTrack.GA):
  return api_util.GetClientInstance(
      release_track
  ).projects_locations_environments_userWorkloadsConfigMaps


def CreateUserWorkloadsConfigMap(
    environment_ref: 'Resource',
    config_map_file_path: str,
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
) -> typing.Union[
    'composer_v1alpha2_messages.UserWorkloadsConfigMap',
    'composer_v1beta1_messages.UserWorkloadsConfigMap',
    'composer_v1_messages.UserWorkloadsConfigMap',
]:
  """Calls the Composer Environments.CreateUserWorkloadsConfigMap method.

  Args:
    environment_ref: Resource, the Composer environment resource to create a
      user workloads ConfigMap for.
    config_map_file_path: string, path to a local file with a Kubernetes
      ConfigMap in yaml format.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.

  Returns:
    UserWorkloadsConfigMap: the created user workloads ConfigMap.

  Raises:
    command_util.InvalidUserInputError: if metadata.name was absent from the
    file.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)

  config_map_name, config_map_data = _ReadConfigMapFromFile(
      config_map_file_path
  )
  user_workloads_config_map_name = f'{environment_ref.RelativeName()}/userWorkloadsConfigMaps/{config_map_name}'
  user_workloads_config_map_data = api_util.DictToMessage(
      config_map_data,
      message_module.UserWorkloadsConfigMap.DataValue,
  )
  request_message = message_module.ComposerProjectsLocationsEnvironmentsUserWorkloadsConfigMapsCreateRequest(
      parent=environment_ref.RelativeName(),
      userWorkloadsConfigMap=message_module.UserWorkloadsConfigMap(
          name=user_workloads_config_map_name,
          data=user_workloads_config_map_data,
      ),
  )

  return GetService(release_track=release_track).Create(request_message)


def GetUserWorkloadsConfigMap(
    environment_ref: 'Resource',
    config_map_name: str,
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
) -> typing.Union[
    'composer_v1alpha2_messages.UserWorkloadsConfigMap',
    'composer_v1beta1_messages.UserWorkloadsConfigMap',
    'composer_v1_messages.UserWorkloadsConfigMap',
]:
  """Calls the Composer Environments.GetUserWorkloadsConfigMap method.

  Args:
    environment_ref: Resource, the Composer environment resource to get a user
      workloads ConfigMap for.
    config_map_name: string, name of the Kubernetes ConfigMap.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.

  Returns:
    UserWorkloadsConfigMap: user workloads ConfigMap.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  user_workloads_config_map_name = f'{environment_ref.RelativeName()}/userWorkloadsConfigMaps/{config_map_name}'
  request_message = message_module.ComposerProjectsLocationsEnvironmentsUserWorkloadsConfigMapsGetRequest(
      name=user_workloads_config_map_name,
  )

  return GetService(release_track=release_track).Get(request_message)


def ListUserWorkloadsConfigMaps(
    environment_ref: 'Resource',
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
) -> typing.Union[
    typing.List['composer_v1alpha2_messages.UserWorkloadsConfigMap'],
    typing.List['composer_v1beta1_messages.UserWorkloadsConfigMap'],
    typing.List['composer_v1_messages.UserWorkloadsConfigMap'],
]:
  """Calls the Composer Environments.ListUserWorkloadsConfigMaps method.

  Args:
    environment_ref: Resource, the Composer environment resource to list user
      workloads ConfigMaps for.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.

  Returns:
    list of user workloads ConfigMaps.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)

  page_token = ''
  user_workloads_config_maps = []
  while True:
    request_message = message_module.ComposerProjectsLocationsEnvironmentsUserWorkloadsConfigMapsListRequest(
        pageToken=page_token,
        parent=environment_ref.RelativeName(),
    )
    response = GetService(release_track=release_track).List(request_message)
    user_workloads_config_maps.extend(response.userWorkloadsConfigMaps)

    if not response.nextPageToken:
      break
    # Set page_token for the next request.
    page_token = response.nextPageToken

  return user_workloads_config_maps


def UpdateUserWorkloadsConfigMap(
    environment_ref: 'Resource',
    config_map_file_path: str,
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
) -> typing.Union[
    'composer_v1alpha2_messages.UserWorkloadsConfigMap',
    'composer_v1beta1_messages.UserWorkloadsConfigMap',
    'composer_v1_messages.UserWorkloadsConfigMap',
]:
  """Calls the Composer Environments.UpdateUserWorkloadsConfigMap method.

  Args:
    environment_ref: Resource, the Composer environment resource to update a
      user workloads ConfigMap for.
    config_map_file_path: string, path to a local file with a Kubernetes
      ConfigMap in yaml format.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.

  Returns:
    UserWorkloadsConfigMap: the updated user workloads ConfigMap.

  Raises:
    command_util.InvalidUserInputError: if metadata.name was absent from the
    file.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)

  config_map_name, config_map_data = _ReadConfigMapFromFile(
      config_map_file_path
  )
  user_workloads_config_map_name = f'{environment_ref.RelativeName()}/userWorkloadsConfigMaps/{config_map_name}'
  user_workloads_config_map_data = api_util.DictToMessage(
      config_map_data,
      message_module.UserWorkloadsConfigMap.DataValue,
  )
  request_message = message_module.UserWorkloadsConfigMap(
      name=user_workloads_config_map_name,
      data=user_workloads_config_map_data,
  )

  return GetService(release_track=release_track).Update(request_message)


def DeleteUserWorkloadsConfigMap(
    environment_ref: 'Resource',
    config_map_name: str,
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
):
  """Calls the Composer Environments.DeleteUserWorkloadsConfigMap method.

  Args:
    environment_ref: Resource, the Composer environment resource to delete a
      user workloads ConfigMap for.
    config_map_name: string, name of the Kubernetes ConfigMap.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  user_workloads_config_map_name = f'{environment_ref.RelativeName()}/userWorkloadsConfigMaps/{config_map_name}'
  request_message = message_module.ComposerProjectsLocationsEnvironmentsUserWorkloadsConfigMapsDeleteRequest(
      name=user_workloads_config_map_name,
  )

  GetService(release_track=release_track).Delete(request_message)


def _ReadConfigMapFromFile(
    config_map_file_path: str,
) -> Tuple[str, Mapping[str, str]]:
  """Reads ConfigMap object from yaml file.

  Args:
    config_map_file_path: path to the file.

  Returns:
    tuple with name and data of the ConfigMap.

  Raises:
    command_util.InvalidUserInputError: if the content of the file is invalid.
  """
  config_map_file_content = yaml.load_path(config_map_file_path)
  if not isinstance(config_map_file_content, dict):
    raise command_util.InvalidUserInputError(
        f'Invalid content of the {config_map_file_path}'
    )

  kind = config_map_file_content.get('kind')
  metadata_name = config_map_file_content.get('metadata', {}).get('name', '')
  data = config_map_file_content.get('data', {})
  if kind != 'ConfigMap':
    raise command_util.InvalidUserInputError(
        f'Incorrect "kind" attribute value. Found: {kind}, should be: ConfigMap'
    )
  if not metadata_name:
    raise command_util.InvalidUserInputError(
        f'Empty metadata.name in {config_map_file_path}'
    )

  return metadata_name, data
