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
"""Vertex AI endpoints deploy-model command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import endpoints_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import log


def _AddArgs(parser, version):
  """Prepares for the arguments of the command."""
  flags.GetModelIdArg().AddToParser(parser)
  flags.GetDisplayNameArg('deployed model').AddToParser(parser)
  flags.GetTrafficSplitArg().AddToParser(parser)
  flags.AddPredictionResourcesArgs(parser, version)
  flags.GetEnableAccessLoggingArg().AddToParser(parser)
  flags.GetServiceAccountArg().AddToParser(parser)
  flags.GetUserSpecifiedIdArg('deployed-model').AddToParser(parser)
  flags.GetAutoscalingMetricSpecsArg().AddToParser(parser)
  flags.AddEndpointResourceArg(
      parser,
      'to deploy a model to',
      prompt_func=region_util.PromptForOpRegion)
  if version != constants.GA_VERSION:
    flags.AddSharedResourcesArg(
        parser,
        'to co-host a model on')


def _Run(args, version):
  """Deploy a model to an existing Vertex AI endpoint."""
  validation.ValidateDisplayName(args.display_name)
  validation.ValidateAutoscalingMetricSpecs(args.autoscaling_metric_specs)
  endpoint_ref = args.CONCEPTS.endpoint.Parse()
  args.region = endpoint_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    endpoints_client = client.EndpointsClient(version=version)
    operation_client = operations.OperationsClient()
    if version == constants.GA_VERSION:
      op = endpoints_client.DeployModel(
          endpoint_ref,
          args.model,
          args.region,
          args.display_name,
          machine_type=args.machine_type,
          accelerator_dict=args.accelerator,
          min_replica_count=args.min_replica_count,
          max_replica_count=args.max_replica_count,
          autoscaling_metric_specs=args.autoscaling_metric_specs,
          enable_access_logging=args.enable_access_logging,
          disable_container_logging=args.disable_container_logging,
          service_account=args.service_account,
          traffic_split=args.traffic_split,
          deployed_model_id=args.deployed_model_id)
    else:
      shared_resources_ref = args.CONCEPTS.shared_resources.Parse()
      validation.ValidateSharedResourceArgs(
          shared_resources_ref=shared_resources_ref,
          machine_type=args.machine_type,
          accelerator_dict=args.accelerator,
          min_replica_count=args.min_replica_count,
          max_replica_count=args.max_replica_count,
          autoscaling_metric_specs=args.autoscaling_metric_specs)
      op = endpoints_client.DeployModelBeta(
          endpoint_ref,
          args.model,
          args.region,
          args.display_name,
          machine_type=args.machine_type,
          accelerator_dict=args.accelerator,
          min_replica_count=args.min_replica_count,
          max_replica_count=args.max_replica_count,
          autoscaling_metric_specs=args.autoscaling_metric_specs,
          enable_access_logging=args.enable_access_logging,
          enable_container_logging=args.enable_container_logging,
          service_account=args.service_account,
          traffic_split=args.traffic_split,
          deployed_model_id=args.deployed_model_id,
          shared_resources_ref=shared_resources_ref)
    response_msg = operations_util.WaitForOpMaybe(
        operation_client, op, endpoints_util.ParseOperation(op.name))
    if response_msg is not None:
      response = encoding.MessageToPyValue(response_msg)
      if 'deployedModel' in response and 'id' in response['deployedModel']:
        log.status.Print(('Deployed a model to the endpoint {}. '
                          'Id of the deployed model: {}.').format(
                              endpoint_ref.AsDict()['endpointsId'],
                              response['deployedModel']['id']))
    return response_msg


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DeployModelGa(base.Command):
  """Deploy a model to an existing Vertex AI endpoint.

  ## EXAMPLES

  To deploy a model ``456'' to an endpoint ``123'' under project ``example'' in
  region ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1 --model=456
    --display-name=my_deployed_model
  """

  @staticmethod
  def Args(parser):
    _AddArgs(parser, constants.GA_VERSION)
    flags.GetDisableContainerLoggingArg().AddToParser(parser)

  def Run(self, args):
    _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class DeployModelBeta(DeployModelGa):
  """Deploy a model to an existing Vertex AI endpoint.

  ## EXAMPLES

  To deploy a model ``456'' to an endpoint ``123'' under project ``example'' in
  region ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1 --model=456
    --display-name=my_deployed_model
  """

  @staticmethod
  def Args(parser):
    _AddArgs(parser, constants.BETA_VERSION)
    flags.GetEnableContainerLoggingArg().AddToParser(parser)

  def Run(self, args):
    _Run(args, constants.BETA_VERSION)
