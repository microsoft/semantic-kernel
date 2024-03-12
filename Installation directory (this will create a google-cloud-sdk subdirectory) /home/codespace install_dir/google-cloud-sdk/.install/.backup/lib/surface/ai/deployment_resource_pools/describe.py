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
"""Vertex AI deployment resource pools describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.deployment_resource_pools import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util


def _ArgsBeta(parser):
  flags.AddDeploymentResourcePoolArg(
      parser,
      'to describe',
      prompt_func=region_util.PromptForDeploymentResourcePoolSupportedRegion)


def _RunBeta(args):
  """Describe a Vertex AI deployment resource pool."""
  version = constants.BETA_VERSION
  deployment_resource_pool_ref = args.CONCEPTS.deployment_resource_pool.Parse()
  args.region = deployment_resource_pool_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    deployment_resource_pools_client = client.DeploymentResourcePoolsClient(
        version=version)

    describe_response = deployment_resource_pools_client.DescribeBeta(
        deployment_resource_pool_ref)

    return describe_response


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DescribeV1Beta1(base.DescribeCommand):
  """Describe a Vertex AI deployment resource pool.

  This command describes a deployment resource pool with a provided deployment
  resource pool.

  ## EXAMPLES

  To describe a deployment resource pool with name ''example'' in region
  ''us-central1'', run:

    $ {command} example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    return _ArgsBeta(parser)

  def Run(self, args):
    return _RunBeta(args)
