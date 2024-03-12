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
"""Vertex AI deployment resource pools delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.deployment_resource_pools import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import deployment_resource_pools_util
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.core.console import console_io


def _ArgsBeta(parser):
  """Adding deployment resource pool arguments from CLI.

  Args:
    parser: argparse.ArgumentParser, cli argument parser

  Returns:
    None
  """
  flags.AddDeploymentResourcePoolArg(
      parser,
      'to delete',
      prompt_func=region_util.PromptForDeploymentResourcePoolSupportedRegion)


def _RunBeta(args):
  """Delete a Vertex AI deployment resource pool."""
  version = constants.BETA_VERSION
  deployment_resource_pool_ref = args.CONCEPTS.deployment_resource_pool.Parse()
  args.region = deployment_resource_pool_ref.AsDict()['locationsId']
  deployment_resource_pool_id = deployment_resource_pool_ref.AsDict(
  )['deploymentResourcePoolsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    deployment_resource_pools_client = client.DeploymentResourcePoolsClient(
        version=version)
    operation_client = operations.OperationsClient()
    console_io.PromptContinue(
        'This will delete deployment resource pool [{}]...'.format(
            deployment_resource_pool_id),
        cancel_on_no=True)
    op = deployment_resource_pools_client.DeleteBeta(
        deployment_resource_pool_ref)
    return operations_util.WaitForOpMaybe(
        operation_client,
        op,
        deployment_resource_pools_util.ParseOperation(op.name),
        log_method='delete')


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeleteV1Beta1(base.DeleteCommand):
  """Delete an existing Vertex AI deployment resource pool.

  ## EXAMPLES

  To delete a deployment resource pool ``123'' under project ``example'' in
  region ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    return _ArgsBeta(parser)

  def Run(self, args):
    return _RunBeta(args)
