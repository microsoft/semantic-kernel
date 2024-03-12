# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""CLI Utilities for cloud tpu commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.services import peering
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.projects import util as projects_command_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


_PROJECT_LOOKUP_ERROR = ('Error determining VPC peering status '
                         'for network [{}]: [{}]')
_PEERING_VALIDATION_ERROR = ('Network [{}] is invalid for use '
                             'with Service Networking')


class ServiceNetworkingException(core_exceptions.Error):
  """Exception for creation failures involving Service Networking/Peering."""


def GetMessagesModule(version='v1'):
  return apis.GetMessagesModule('tpu', version)


def StartRequestHook(ref, args, request):
  """Declarative request hook for TPU Start command."""
  del ref
  del args
  start_request = GetMessagesModule().StartNodeRequest()
  request.startNodeRequest = start_request
  return request


def StopRequestHook(ref, args, request):
  """Declarative request hook for TPU Stop command."""
  del ref
  del args
  stop_request = GetMessagesModule().StopNodeRequest()
  request.stopNodeRequest = stop_request
  return request


def _ParseProjectNumberFromNetwork(network, user_project):
  """Retrieves the project field from the provided network value."""
  try:
    registry = resources.REGISTRY.Clone()
    network_ref = registry.Parse(network,
                                 collection='compute.networks')
    project_identifier = network_ref.project
  except resources.Error:
    # If not a parseable resource string, then use user_project
    project_identifier = user_project

  return projects_command_util.GetProjectNumber(project_identifier)


def CreateValidateVPCHook(ref, args, request):
  """Validates that supplied network has been peered to a GoogleOrganization.

     Uses the Service Networking API to check if the network specified via
     --network flag has been peered to Google Organization. If it has, proceeds
     with TPU create operation otherwise will raise ServiceNetworking exception.
     Check is only valid if --use-service-networking has been specified
     otherwise check will return immediately.

  Args:
    ref: Reference to the TPU Node resource to be created.
    args: Argument namespace.
    request: TPU Create requests message.

  Returns:
    request: Passes requests through if args pass validation

  Raises:
    ServiceNetworkingException: if network is not properly peered
  """
  del ref
  service_networking_enabled = args.use_service_networking
  if service_networking_enabled:
    project = args.project or properties.VALUES.core.project.Get(required=True)
    try:
      network_project_number = _ParseProjectNumberFromNetwork(args.network,
                                                              project)

      lookup_result = peering.ListConnections(
          network_project_number, 'servicenetworking.googleapis.com',
          os.path.basename(args.network))
    except (exceptions.ListConnectionsPermissionDeniedException,
            apitools_exceptions.HttpError) as e:
      raise ServiceNetworkingException(
          _PROJECT_LOOKUP_ERROR.format(args.network, project, e))

    if not lookup_result:
      raise ServiceNetworkingException(
          _PEERING_VALIDATION_ERROR.format(args.network))

  return request


def ListTopologiesResponseHook(response, args):
  """Reformat to extract topologies and sort by acceleratorType."""
  del args
  results = []
  for accelerator_type in response:
    for accelerator_config in accelerator_type.acceleratorConfigs:
      results += [{
          'topology': accelerator_config.topology,
          'type': accelerator_config.type,
          'acceleratorType': accelerator_type.type
      }]
  results.sort(key=lambda x: (int(x['acceleratorType'].split('-')[1])))
  return results
