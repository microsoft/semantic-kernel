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
"""Command for updating health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.health_checks import exceptions
from googlecloudsdk.command_lib.compute.health_checks import flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log


def _DetailedHelp():
  return {
      'brief':
          'Update a gRPC health check.',
      'DESCRIPTION':
          """\
      *{command}* is used to update an existing gRPC health check. Only
      arguments passed in will be updated on the health check. Other
      attributes will remain unaffected.
      """,
  }


def _Args(parser, include_log_config):
  health_check_arg = flags.HealthCheckArgument('gRPC')
  health_check_arg.AddArgument(parser, operation_type='update')
  health_checks_utils.AddGrpcRelatedUpdateArgs(parser)
  health_checks_utils.AddProtocolAgnosticUpdateArgs(parser, 'gRPC')
  if include_log_config:
    health_checks_utils.AddHealthCheckLoggingRelatedArgs(parser)


def _GetGetRequest(client, health_check_ref):
  """Returns a request for fetching the existing health check."""
  return (client.apitools_client.healthChecks, 'Get',
          client.messages.ComputeHealthChecksGetRequest(
              healthCheck=health_check_ref.Name(),
              project=health_check_ref.project))


def _GetSetRequest(client, health_check_ref, replacement):
  """Returns a request for updating the health check."""
  return (client.apitools_client.healthChecks, 'Update',
          client.messages.ComputeHealthChecksUpdateRequest(
              healthCheck=health_check_ref.Name(),
              healthCheckResource=replacement,
              project=health_check_ref.project))


def _GetRegionalGetRequest(client, health_check_ref):
  """Returns a request for fetching the existing health check."""
  return (client.apitools_client.regionHealthChecks, 'Get',
          client.messages.ComputeRegionHealthChecksGetRequest(
              healthCheck=health_check_ref.Name(),
              project=health_check_ref.project,
              region=health_check_ref.region))


def _GetRegionalSetRequest(client, health_check_ref, replacement):
  """Returns a request for updating the health check."""
  return (client.apitools_client.regionHealthChecks, 'Update',
          client.messages.ComputeRegionHealthChecksUpdateRequest(
              healthCheck=health_check_ref.Name(),
              healthCheckResource=replacement,
              project=health_check_ref.project,
              region=health_check_ref.region))


def _Modify(client, args, existing_check, include_log_config):
  """Returns a modified HealthCheck message."""
  # We do not support using 'update grpc' with a health check of a
  # different protocol.
  if (existing_check.type !=
      client.messages.HealthCheck.TypeValueValuesEnum.GRPC):
    raise core_exceptions.Error(
        'update grpc subcommand applied to health check with protocol ' +
        existing_check.type.name)

  # Description, PortName, and GrpcServiceName are the only attributes that can
  # be cleared by passing in an empty string (but we don't want to set it to
  # an empty string).
  if args.description:
    description = args.description
  elif args.description is None:
    description = existing_check.description
  else:
    description = None

  if args.grpc_service_name:
    grpc_service_name = args.grpc_service_name
  elif args.grpc_service_name is None:
    grpc_service_name = existing_check.grpcHealthCheck.grpcServiceName
  else:
    grpc_service_name = None

  port, port_specification = health_checks_utils.\
    HandlePortRelatedFlagsForGRPCUpdate(
        args, existing_check.grpcHealthCheck)

  new_health_check = client.messages.HealthCheck(
      name=existing_check.name,
      description=description,
      type=client.messages.HealthCheck.TypeValueValuesEnum.GRPC,
      grpcHealthCheck=client.messages.GRPCHealthCheck(
          port=port,
          portSpecification=port_specification,
          grpcServiceName=grpc_service_name),
      checkIntervalSec=(args.check_interval or existing_check.checkIntervalSec),
      timeoutSec=args.timeout or existing_check.timeoutSec,
      healthyThreshold=(args.healthy_threshold or
                        existing_check.healthyThreshold),
      unhealthyThreshold=(args.unhealthy_threshold or
                          existing_check.unhealthyThreshold),
  )

  if include_log_config:
    new_health_check.logConfig = health_checks_utils.ModifyLogConfig(
        client, args, existing_check.logConfig)
  return new_health_check


def _ValidateArgs(args, include_log_config):
  """Validates given args and raises exception if any args are invalid."""
  health_checks_utils.CheckProtocolAgnosticArgs(args)

  args_unset = not (args.port or args.check_interval or args.timeout or
                    args.healthy_threshold or args.unhealthy_threshold or
                    args.use_serving_port)

  if include_log_config:
    args_unset = (args.enable_logging is None and args_unset)

  if (args.description is None and args.grpc_service_name is None and
      args_unset):
    raise exceptions.ArgumentError('At least one property must be modified.')


def _Run(args, holder, include_log_config):
  """Issues the requests necessary for updating the health check."""
  client = holder.client

  _ValidateArgs(args, include_log_config)

  health_check_arg = flags.HealthCheckArgument('gRPC')

  health_check_ref = health_check_arg.ResolveAsResource(
      args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)

  if health_checks_utils.IsRegionalHealthCheckRef(health_check_ref):
    get_request = _GetRegionalGetRequest(client, health_check_ref)
  else:
    get_request = _GetGetRequest(client, health_check_ref)

  objects = client.MakeRequests([get_request])

  new_object = _Modify(client, args, objects[0], include_log_config)

  # If existing object is equal to the proposed object or if
  # _Modify() returns None, then there is no work to be done, so we
  # print the resource and return.
  if objects[0] == new_object:
    log.status.Print('No change requested; skipping update for [{0}].'.format(
        objects[0].name))
    return objects

  if health_checks_utils.IsRegionalHealthCheckRef(health_check_ref):
    set_request = _GetRegionalSetRequest(client, health_check_ref, new_object)
  else:
    set_request = _GetSetRequest(client, health_check_ref, new_object)
  return client.MakeRequests([set_request])


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a gRPC health check."""

  _include_log_config = True
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    _Args(parser, cls._include_log_config)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self._include_log_config)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):

  pass


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):

  pass
