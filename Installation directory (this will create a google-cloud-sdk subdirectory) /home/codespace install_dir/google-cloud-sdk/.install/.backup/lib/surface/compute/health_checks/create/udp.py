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
"""Command for creating UDP health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.health_checks import exceptions
from googlecloudsdk.command_lib.compute.health_checks import flags


def _DetailedHelp():
  return {
      'brief':
          'Create a UDP health check to monitor load balanced instances.',
      'DESCRIPTION':
          """\
          *{command}* is used to create a UDP health check. UDP health checks
        monitor instances in a load balancer controlled by a target pool. All
        arguments to the command are optional except for the name of the health
        check, request and response. For more information on load balancing, see
        [](https://cloud.google.com/compute/docs/load-balancing-and-autoscaling/)
          """,
  }


def _Args(parser):
  parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
  flags.HealthCheckArgument('UDP').AddArgument(parser, operation_type='create')
  health_checks_utils.AddUdpRelatedArgs(parser)
  health_checks_utils.AddProtocolAgnosticCreationArgs(parser, 'UDP')


def _Run(args, holder):
  """Issues the request necessary for adding the health check."""
  client = holder.client

  health_check_ref = flags.HealthCheckArgument('UDP').ResolveAsResource(
      args, holder.resources)

  # Check that request and response are not None and empty.
  if not args.request:
    raise exceptions.ArgumentError('"request" field for UDP can not be empty.')
  if not args.response:
    raise exceptions.ArgumentError('"response" field for UDP can not be empty.')

  if health_checks_utils.IsRegionalHealthCheckRef(health_check_ref):
    request = client.messages.ComputeRegionHealthChecksInsertRequest(
        healthCheck=client.messages.HealthCheck(
            name=health_check_ref.Name(),
            description=args.description,
            type=client.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=client.messages.UDPHealthCheck(
                request=args.request,
                response=args.response,
                port=args.port,
                portName=args.port_name),
            checkIntervalSec=args.check_interval,
            timeoutSec=args.timeout,
            healthyThreshold=args.healthy_threshold,
            unhealthyThreshold=args.unhealthy_threshold,
        ),
        project=health_check_ref.project,
        region=health_check_ref.region)
    collection = client.apitools_client.regionHealthChecks
  else:
    request = client.messages.ComputeHealthChecksInsertRequest(
        healthCheck=client.messages.HealthCheck(
            name=health_check_ref.Name(),
            description=args.description,
            type=client.messages.HealthCheck.TypeValueValuesEnum.UDP,
            udpHealthCheck=client.messages.UDPHealthCheck(
                request=args.request,
                response=args.response,
                port=args.port,
                portName=args.port_name),
            checkIntervalSec=args.check_interval,
            timeoutSec=args.timeout,
            healthyThreshold=args.healthy_threshold,
            unhealthyThreshold=args.unhealthy_threshold,
        ),
        project=health_check_ref.project)
    collection = client.apitools_client.healthChecks

  return client.MakeRequests([(collection, 'Insert', request)])


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Create an Alpha UDP health check to monitor load balanced instances.

  Business logic should be put in helper functions. Classes annotated with
  @base.ReleaseTracks should only be concerned with calling helper functions
  with the correct feature parameters.
  """

  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    _Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder)
