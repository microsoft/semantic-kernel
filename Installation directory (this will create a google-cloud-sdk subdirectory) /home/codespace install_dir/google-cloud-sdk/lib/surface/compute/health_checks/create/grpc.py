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
"""Command for creating gRPC health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.health_checks import flags


def _DetailedHelp():
  return {
      'brief':
          'Create a gRPC health check to monitor load balanced instances.',
      'DESCRIPTION':
          """\
      *{command}* is used to create a non-legacy health check using the gRPC
      protocol. You can use this health check for Google Cloud load
      balancers or for managed instance group autohealing. For more information,
      see the health checks overview at:
      [](https://cloud.google.com/load-balancing/docs/health-check-concepts)
      """,
  }


def _Args(parser, include_log_config):
  """Set up arguments to create a gRPC HealthCheck."""
  parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
  flags.HealthCheckArgument('gRPC').AddArgument(parser, operation_type='create')
  health_checks_utils.AddGrpcRelatedCreationArgs(parser)
  health_checks_utils.AddProtocolAgnosticCreationArgs(parser, 'gRPC')
  if include_log_config:
    health_checks_utils.AddHealthCheckLoggingRelatedArgs(parser)

  parser.display_info.AddCacheUpdater(completers.HealthChecksCompleterAlpha)


def _Run(args, holder, include_log_config):
  """Issues the request necessary for adding the health check."""
  client = holder.client
  messages = client.messages

  # Check that port related flags are set for gRPC health check.
  args_unset = not (args.port or args.use_serving_port)
  if args_unset:
    raise exceptions.OneOfArgumentsRequiredException([
        '--port', '--use-serving-port'
    ], 'Either --port or --use-serving-port must be set for gRPC health check.')

  health_check_ref = flags.HealthCheckArgument('gRPC').ResolveAsResource(
      args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
  grpc_health_check = messages.GRPCHealthCheck(
      port=args.port, grpcServiceName=args.grpc_service_name)

  health_checks_utils.ValidateAndAddPortSpecificationToGRPCHealthCheck(
      args, grpc_health_check)

  if health_checks_utils.IsRegionalHealthCheckRef(health_check_ref):
    request = messages.ComputeRegionHealthChecksInsertRequest(
        healthCheck=messages.HealthCheck(
            name=health_check_ref.Name(),
            description=args.description,
            type=messages.HealthCheck.TypeValueValuesEnum.GRPC,
            grpcHealthCheck=grpc_health_check,
            checkIntervalSec=args.check_interval,
            timeoutSec=args.timeout,
            healthyThreshold=args.healthy_threshold,
            unhealthyThreshold=args.unhealthy_threshold),
        project=health_check_ref.project,
        region=health_check_ref.region)
    collection = client.apitools_client.regionHealthChecks
  else:
    request = messages.ComputeHealthChecksInsertRequest(
        healthCheck=messages.HealthCheck(
            name=health_check_ref.Name(),
            description=args.description,
            type=messages.HealthCheck.TypeValueValuesEnum.GRPC,
            grpcHealthCheck=grpc_health_check,
            checkIntervalSec=args.check_interval,
            timeoutSec=args.timeout,
            healthyThreshold=args.healthy_threshold,
            unhealthyThreshold=args.unhealthy_threshold),
        project=health_check_ref.project)
    collection = client.apitools_client.healthChecks

  if include_log_config:
    request.healthCheck.logConfig = health_checks_utils.CreateLogConfig(
        client, args)

  return client.MakeRequests([(collection, 'Insert', request)])


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a gRPC health check."""

  detailed_help = _DetailedHelp()

  _include_log_config = True

  @classmethod
  def Args(cls, parser):
    _Args(parser, cls._include_log_config)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self._include_log_config)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):

  pass


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):

  pass
