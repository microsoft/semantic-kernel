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
"""Vertex AI deployment resource pools create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.deployment_resource_pools import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import deployment_resource_pools_util
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.core import log


def _AddArgsBeta(parser):
  """Adding deployment resource pool arguments from CLI.

  Args:
    parser: argparse.ArgumentParser, cli argument parser

  Returns:
    None
  """
  version = constants.BETA_VERSION
  parser.add_argument(
      'deployment_resource_pool_id',
      help='The ID to use for the DeploymentResourcePool, which will become ' +
      'the final component of the DeploymentResourcePool\'s resource name. ' +
      'The maximum length is 63 characters, and valid characters are ' +
      '/^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$/.')
  flags.AddPredictionResourcesArgs(parser, version)
  flags.GetAutoscalingMetricSpecsArg().AddToParser(parser)
  flags.AddRegionResourceArg(
      parser,
      'to create deployment resource pool',
      prompt_func=region_util.PromptForDeploymentResourcePoolSupportedRegion)


def _RunBeta(args):
  """Create a new Vertex AI deployment resource pool."""
  version = constants.BETA_VERSION
  region_ref = args.CONCEPTS.region.Parse()
  args.region = region_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    deployment_resource_pools_client = client.DeploymentResourcePoolsClient(
        version=version)
    op = deployment_resource_pools_client.CreateBeta(
        region_ref,
        args.deployment_resource_pool_id,
        autoscaling_metric_specs=args.autoscaling_metric_specs,
        accelerator_dict=args.accelerator,
        min_replica_count=args.min_replica_count,
        max_replica_count=args.max_replica_count,
        machine_type=args.machine_type)
    response_msg = operations_util.WaitForOpMaybe(
        operations.OperationsClient(), op,
        deployment_resource_pools_util.ParseOperation(op.name))
    if response_msg is not None:
      response = encoding.MessageToPyValue(response_msg)
      if 'name' in response:
        log.status.Print(
            ('Created Vertex AI deployment resource pool: {}.')
            .format(response['name']))
  return response_msg


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateV1Beta1(base.CreateCommand):
  """Create a new Vertex AI deployment resource pool.

  This command creates a new deployment resource pool with a provided deployment
  resource pool id (name) in a provided region (assuming that region provides
  support for this api). You can choose to simply provide the resource pool
  name and create an instance with default arguments, or you can pass in your
  own preferences, such as the accelerator and machine specs. Please note this
  functionality is not yet available in the GA track and is currently only
  part of the v1beta1 API version.

  ## EXAMPLES

  To create a deployment resource pool with name ``example'' in region
  ``us-central1'', run:

    $ {command} example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    return _AddArgsBeta(parser)

  def Run(self, args):
    return _RunBeta(args)
