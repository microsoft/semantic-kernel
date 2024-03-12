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
"""Code for making shared messages between commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from typing import Optional

from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.command_lib.run.integrations import integration_printer
from googlecloudsdk.command_lib.run.integrations.formatters import base
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages as runapps


def GetSuccessMessage(integration_type, integration_name, action='deployed'):
  """Returns a user message for a successful integration deploy.

  Args:
    integration_type: str, type of the integration
    integration_name: str, name of the integration
    action: str, the action that succeeded
  """
  return (
      '[{{bold}}{}{{reset}}] integration [{{bold}}{}{{reset}}] '
      'has been {} successfully.'
  ).format(integration_type, integration_name, action)


def GetCallToAction(
    metadata: Optional[types_utils.TypeMetadata],
    resource: runapps.Resource,
    resource_status: Optional[runapps.ResourceStatus] = None,
):
  """Print the call to action message for the given integration.

  Args:
    metadata: the type metadata
    resource: the integration resource object
    resource_status: status of the integration

  Returns:
    A formatted string of the call to action message.
  """
  formatter = integration_printer.GetFormatter(metadata)
  return formatter.CallToAction(base.Record(
      name=None,
      metadata=metadata,
      region=None,
      resource=resource,
      status=resource_status,
      latest_deployment=None
  ))


def GetDeleteErrorMessage(integration_name):
  """Returns message when delete command fails.

  Args:
    integration_name: str, name of the integration.

  Returns:
    A formatted string of the error message.
  """
  return ('Deleting Integration [{}] failed, please rerun the delete command to'
          ' try again.').format(integration_name)


def CheckStatusMessage(release_track, integration_name):
  """Message about check status with describe command.

  Args:
    release_track: Release track of the command being run.
    integration_name: str, name of the integration.

  Returns:
    A formatted string of the message.
  """
  return (
      'You can check the status with `gcloud {}run integrations describe {}`'
      .format(_ReleaseCommandPrefix(release_track), integration_name))


def RetryDeploymentMessage(release_track, integration_name):
  """Message about retry deployment using update command.

  Args:
    release_track: Release track of the command being run.
    integration_name: str, name of the integration.

  Returns:
    A formatted string of the message.
  """
  return (
      'To retry the deployment, use update command ' +
            '`gcloud {}run integrations update {}`'
      .format(_ReleaseCommandPrefix(release_track), integration_name))


def _ReleaseCommandPrefix(release_track):
  """Prefix for release track for printing commands.

  Args:
    release_track: Release track of the command being run.

  Returns:
    A formatted string of the release track prefix
  """
  track = release_track.prefix
  if track:
    track += ' '
  return track


def IntegrationAlreadyExists(name):
  """Generates a message when an integration already exists during create.

  Args:
    name: name of the integration.

  Returns:
    A string message.
  """
  return ('Integration with name [{}] already exists. '
          'Update it with `gcloud run integrations update`.').format(name)


def IntegrationNotFound(name):
  """Generates a message when an integration is not found.

  Args:
    name: name of the integration.

  Returns:
    A string message.
  """
  return ('Integration [{}] cannot be found. '
          'First create an integration with `gcloud run integrations create`.'
         ).format(name)
