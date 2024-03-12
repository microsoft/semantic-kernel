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
"""Utilities for calling the Composer UserWorkloads Secrets API."""

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
  ).projects_locations_environments_userWorkloadsSecrets


def CreateUserWorkloadsSecret(
    environment_ref: 'Resource',
    secret_file_path: str,
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
) -> typing.Union[
    'composer_v1alpha2_messages.UserWorkloadsSecret',
    'composer_v1beta1_messages.UserWorkloadsSecret',
    'composer_v1_messages.UserWorkloadsSecret',
]:
  """Calls the Composer Environments.CreateUserWorkloadsSecret method.

  Args:
    environment_ref: Resource, the Composer environment resource to create a
      user workloads Secret for.
    secret_file_path: string, path to a local file with a Kubernetes Secret in
      yaml format.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.

  Returns:
    UserWorkloadsSecret: the created user workloads Secret.

  Raises:
    command_util.InvalidUserInputError: if metadata.name was absent from the
    file.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)

  secret_name, secret_data = _ReadSecretFromFile(secret_file_path)
  user_workloads_secret_name = (
      f'{environment_ref.RelativeName()}/userWorkloadsSecrets/{secret_name}'
  )
  user_workloads_secret_data = api_util.DictToMessage(
      secret_data,
      message_module.UserWorkloadsSecret.DataValue,
  )
  request_message = message_module.ComposerProjectsLocationsEnvironmentsUserWorkloadsSecretsCreateRequest(
      parent=environment_ref.RelativeName(),
      userWorkloadsSecret=message_module.UserWorkloadsSecret(
          name=user_workloads_secret_name,
          data=user_workloads_secret_data,
      ),
  )

  return GetService(release_track=release_track).Create(request_message)


def GetUserWorkloadsSecret(
    environment_ref: 'Resource',
    secret_name: str,
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
) -> typing.Union[
    'composer_v1alpha2_messages.UserWorkloadsSecret',
    'composer_v1beta1_messages.UserWorkloadsSecret',
    'composer_v1_messages.UserWorkloadsSecret',
]:
  """Calls the Composer Environments.GetUserWorkloadsSecret method.

  Args:
    environment_ref: Resource, the Composer environment resource to get a user
      workloads Secret for.
    secret_name: string, name of the Kubernetes Secret.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.

  Returns:
    UserWorkloadsSecret: user workloads Secret.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  user_workloads_secret_name = (
      f'{environment_ref.RelativeName()}/userWorkloadsSecrets/{secret_name}'
  )
  request_message = message_module.ComposerProjectsLocationsEnvironmentsUserWorkloadsSecretsGetRequest(
      name=user_workloads_secret_name,
  )

  return GetService(release_track=release_track).Get(request_message)


def ListUserWorkloadsSecrets(
    environment_ref: 'Resource',
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
) -> typing.Union[
    typing.List['composer_v1alpha2_messages.UserWorkloadsSecret'],
    typing.List['composer_v1beta1_messages.UserWorkloadsSecret'],
    typing.List['composer_v1_messages.UserWorkloadsSecret'],
]:
  """Calls the Composer Environments.ListUserWorkloadsSecrets method.

  Args:
    environment_ref: Resource, the Composer environment resource to list user
      workloads Secrets for.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.

  Returns:
    list of user workloads Secrets.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)

  page_token = ''
  user_workloads_secrets = []
  while True:
    request_message = message_module.ComposerProjectsLocationsEnvironmentsUserWorkloadsSecretsListRequest(
        pageToken=page_token,
        parent=environment_ref.RelativeName(),
    )
    response = GetService(release_track=release_track).List(request_message)
    user_workloads_secrets.extend(response.userWorkloadsSecrets)

    if not response.nextPageToken:
      break
    # Set page_token for the next request.
    page_token = response.nextPageToken

  return user_workloads_secrets


def UpdateUserWorkloadsSecret(
    environment_ref: 'Resource',
    secret_file_path: str,
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
) -> typing.Union[
    'composer_v1alpha2_messages.UserWorkloadsSecret',
    'composer_v1beta1_messages.UserWorkloadsSecret',
    'composer_v1_messages.UserWorkloadsSecret',
]:
  """Calls the Composer Environments.UpdateUserWorkloadsSecret method.

  Args:
    environment_ref: Resource, the Composer environment resource to update a
      user workloads Secret for.
    secret_file_path: string, path to a local file with a Kubernetes Secret in
      yaml format.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.

  Returns:
    UserWorkloadsSecret: the updated user workloads Secret.

  Raises:
    command_util.InvalidUserInputError: if metadata.name was absent from the
    file.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)

  secret_name, secret_data = _ReadSecretFromFile(secret_file_path)
  user_workloads_secret_name = (
      f'{environment_ref.RelativeName()}/userWorkloadsSecrets/{secret_name}'
  )
  user_workloads_secret_data = api_util.DictToMessage(
      secret_data,
      message_module.UserWorkloadsSecret.DataValue,
  )
  request_message = message_module.UserWorkloadsSecret(
      name=user_workloads_secret_name,
      data=user_workloads_secret_data,
  )

  return GetService(release_track=release_track).Update(request_message)


def DeleteUserWorkloadsSecret(
    environment_ref: 'Resource',
    secret_name: str,
    release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
):
  """Calls the Composer Environments.DeleteUserWorkloadsSecret method.

  Args:
    environment_ref: Resource, the Composer environment resource to delete a
      user workloads Secret for.
    secret_name: string, name of the Kubernetes Secret.
    release_track: base.ReleaseTrack, the release track of the command. Will
      dictate which Composer client library will be used.
  """
  message_module = api_util.GetMessagesModule(release_track=release_track)
  user_workloads_secret_name = (
      f'{environment_ref.RelativeName()}/userWorkloadsSecrets/{secret_name}'
  )
  request_message = message_module.ComposerProjectsLocationsEnvironmentsUserWorkloadsSecretsDeleteRequest(
      name=user_workloads_secret_name,
  )

  GetService(release_track=release_track).Delete(request_message)


def _ReadSecretFromFile(secret_file_path: str) -> Tuple[str, Mapping[str, str]]:
  """Reads Secret object from yaml file.

  Args:
    secret_file_path: path to the file.

  Returns:
    tuple with name and data of the Secret.

  Raises:
    command_util.InvalidUserInputError: if the content of the file is invalid.
  """
  secret_file_content = yaml.load_path(secret_file_path)
  if not isinstance(secret_file_content, dict):
    raise command_util.InvalidUserInputError(
        f'Invalid content of the {secret_file_path}'
    )

  kind = secret_file_content.get('kind')
  metadata_name = secret_file_content.get('metadata', {}).get('name', '')
  data = secret_file_content.get('data', {})
  if kind != 'Secret':
    raise command_util.InvalidUserInputError(
        f'Incorrect "kind" attribute value. Found: {kind}, should be: Secret'
    )
  if not metadata_name:
    raise command_util.InvalidUserInputError(
        f'Empty metadata.name in {secret_file_path}'
    )

  return metadata_name, data
