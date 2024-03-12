# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for updating health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.health_checks import exceptions
from googlecloudsdk.command_lib.compute.health_checks import flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a UDP health check.

  *{command}* is used to update an existing UDP health check. Only
  arguments passed in will be updated on the health check. Other
  attributes will remain unaffected.
  """

  HEALTH_CHECK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.HEALTH_CHECK_ARG = flags.HealthCheckArgument('UDP')
    cls.HEALTH_CHECK_ARG.AddArgument(parser, operation_type='update')
    health_checks_utils.AddUdpRelatedArgs(
        parser, request_and_response_required=False)
    health_checks_utils.AddProtocolAgnosticUpdateArgs(parser, 'UDP')

  def _GetGetRequest(self, client, health_check_ref):
    """Returns a request for fetching the existing health check."""
    return (client.apitools_client.healthChecks, 'Get',
            client.messages.ComputeHealthChecksGetRequest(
                healthCheck=health_check_ref.Name(),
                project=health_check_ref.project))

  def _GetSetRequest(self, client, health_check_ref, replacement):
    """Returns a request for updating the health check."""
    return (client.apitools_client.healthChecks, 'Update',
            client.messages.ComputeHealthChecksUpdateRequest(
                healthCheck=health_check_ref.Name(),
                healthCheckResource=replacement,
                project=health_check_ref.project))

  def _GetRegionalGetRequest(self, client, health_check_ref):
    """Returns a request for fetching the existing health check."""
    return (client.apitools_client.regionHealthChecks, 'Get',
            client.messages.ComputeRegionHealthChecksGetRequest(
                healthCheck=health_check_ref.Name(),
                project=health_check_ref.project,
                region=health_check_ref.region))

  def _GetRegionalSetRequest(self, client, health_check_ref, replacement):
    """Returns a request for updating the health check."""
    return (client.apitools_client.regionHealthChecks, 'Update',
            client.messages.ComputeRegionHealthChecksUpdateRequest(
                healthCheck=health_check_ref.Name(),
                healthCheckResource=replacement,
                project=health_check_ref.project,
                region=health_check_ref.region))

  def Modify(self, client, args, existing_check):
    """Returns a modified HealthCheck message."""
    # We do not support using 'update udp' with a health check of a
    # different protocol.
    if (existing_check.type !=
        client.messages.HealthCheck.TypeValueValuesEnum.UDP):
      raise core_exceptions.Error(
          'update udp subcommand applied to health check with protocol ' +
          existing_check.type.name)

    # Description and PortName are the only attributes that can be cleared by
    # passing in an empty string (but we don't want to set it to empty string).
    if args.description:
      description = args.description
    elif args.description is None:
      description = existing_check.description
    else:
      description = None

    if args.port_name:
      port_name = args.port_name
    elif args.port_name is None:
      port_name = existing_check.udpHealthCheck.portName
    else:
      port_name = None

    new_health_check = client.messages.HealthCheck(
        name=existing_check.name,
        description=description,
        type=client.messages.HealthCheck.TypeValueValuesEnum.UDP,
        udpHealthCheck=client.messages.UDPHealthCheck(
            request=args.request or existing_check.udpHealthCheck.request,
            response=args.response or existing_check.udpHealthCheck.response,
            port=args.port or existing_check.udpHealthCheck.port,
            portName=port_name),
        checkIntervalSec=(args.check_interval or
                          existing_check.checkIntervalSec),
        timeoutSec=args.timeout or existing_check.timeoutSec,
        healthyThreshold=(args.healthy_threshold or
                          existing_check.healthyThreshold),
        unhealthyThreshold=(args.unhealthy_threshold or
                            existing_check.unhealthyThreshold),
    )
    return new_health_check

  def Run(self, args):
    """Issues requests necessary to update UDP Health Checks."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    health_checks_utils.CheckProtocolAgnosticArgs(args)

    args_unset = not (args.port or args.check_interval or args.timeout or
                      args.healthy_threshold or args.unhealthy_threshold or
                      args.request or args.response)
    if args.description is None and args.port_name is None and args_unset:
      raise exceptions.ArgumentError('At least one property must be modified.')

    # Check that request and response are not empty. It is acceptable for it to
    # be None.
    if args.request is not None and not args.request:
      raise exceptions.ArgumentError(
          '"request" field for UDP can not be empty.')
    if args.response is not None and not args.response:
      raise exceptions.ArgumentError(
          '"response" field for UDP can not be empty.')

    health_check_ref = self.HEALTH_CHECK_ARG.ResolveAsResource(
        args, holder.resources)
    if health_checks_utils.IsRegionalHealthCheckRef(health_check_ref):
      get_request = self._GetRegionalGetRequest(client, health_check_ref)
    else:
      get_request = self._GetGetRequest(client, health_check_ref)

    objects = client.MakeRequests([get_request])

    new_object = self.Modify(client, args, objects[0])

    # If existing object is equal to the proposed object or if
    # Modify() returns None, then there is no work to be done, so we
    # print the resource and return.
    if objects[0] == new_object:
      log.status.Print('No change requested; skipping update for [{0}].'.format(
          objects[0].name))
      return objects

    if health_checks_utils.IsRegionalHealthCheckRef(health_check_ref):
      set_request = self._GetRegionalSetRequest(client, health_check_ref,
                                                new_object)
    else:
      set_request = self._GetSetRequest(client, health_check_ref, new_object)

    return client.MakeRequests([set_request])
