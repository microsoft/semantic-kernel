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
"""Vertex AI deployment resource pools list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.deployment_resource_pools import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.core import resources

_DEFAULT_FORMAT = """
        table(
            name.basename():label=DEPLOYMENT_RESOURCE_POOL_ID
        )
    """


def _GetUri(deployment_resource_pool):
  ref = resources.REGISTRY.ParseRelativeName(
      deployment_resource_pool.name,
      constants.DEPLOYMENT_RESOURCE_POOLS_COLLECTION)
  return ref.SelfLink()


def _AddArgsBeta(parser):
  """Adding deployment resource pool arguments from CLI.

  Args:
    parser: argparse.ArgumentParser, cli argument parser

  Returns:
    None
  """
  parser.display_info.AddFormat(_DEFAULT_FORMAT)
  parser.display_info.AddUriFunc(_GetUri)
  flags.AddRegionResourceArg(
      parser,
      'to list deployment resource pools',
      prompt_func=region_util.PromptForDeploymentResourcePoolSupportedRegion)


def _RunBeta(args):
  """List Vertex AI deployment resource pools."""
  version = constants.BETA_VERSION
  region_ref = args.CONCEPTS.region.Parse()
  args.region = region_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    return client.DeploymentResourcePoolsClient(
        version=version).ListBeta(region_ref)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListV1Beta1(base.ListCommand):
  """List existing Vertex AI deployment resource pools.

  ## EXAMPLES

  To list the deployment resource pools under project ``example'' in region
  ``us-central1'', run:

    $ {command} --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    return _AddArgsBeta(parser)

  def Run(self, args):
    return _RunBeta(args)
