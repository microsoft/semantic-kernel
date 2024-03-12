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
"""Vertex AI index endpoints deploy-index command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.index_endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import index_endpoints_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES':
        """\
        To deploy index ``345'' to an index endpoint ``456'' with 2 min replica count and 10 max replica count under project ``example'' in region ``us-central1'', within reserved ip ranges
        ``vertex-ai-ip-range-1'' and ``vertex-ai-ip-range-2'' run:

          $ {command} 456 --project=example --region=us-central1 --index=345 --deployed-index-id=deployed-index-345 --display-name=deployed-index-345 --min-replica-count=2 --max-replica-count=10 --reserved-ip-ranges=vertex-ai-ip-range-1,vertex-ai-ip-range-2
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DeployIndexV1(base.Command):
  """Deploy an index to a Vertex AI index endpoint."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddIndexEndpointResourceArg(parser, 'to deploy an index')
    flags.GetDeployedIndexId().AddToParser(parser)
    flags.GetIndexIdArg().AddToParser(parser)
    flags.GetDisplayNameArg('deployed index').AddToParser(parser)
    flags.AddDeploymentResourcesArgs(parser, 'deployed index')
    flags.AddReservedIpRangesArgs(parser, 'deployed index')
    flags.AddDeploymentGroupArg(parser)
    flags.AddAuthConfigArgs(parser, 'deployed index')
    flags.GetEnableAccessLoggingArg().AddToParser(parser)

  def _Run(self, args, version):
    validation.ValidateDisplayName(args.display_name)
    index_endpoint_ref = args.CONCEPTS.index_endpoint.Parse()
    project_id = index_endpoint_ref.AsDict()['projectsId']
    region = index_endpoint_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      index_endpoint_client = client.IndexEndpointsClient(version=version)
      if version == constants.GA_VERSION:
        operation = index_endpoint_client.DeployIndex(index_endpoint_ref, args)
      else:
        operation = index_endpoint_client.DeployIndexBeta(
            index_endpoint_ref, args)

      op_ref = index_endpoints_util.ParseIndexEndpointOperation(operation.name)
      # TODO(b/208506223): Support `--async` flag.
      index_endpoint_id = op_ref.AsDict()['indexEndpointsId']
      log.status.Print(
          constants.OPERATION_CREATION_DISPLAY_MESSAGE.format(
              name=operation.name,
              verb='deploy index',
              id=op_ref.Name(),
              sub_commands='--index-endpoint={} --region={} [--project={}]'
              .format(index_endpoint_id, region, project_id)))
      return operation

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeployIndexV1Beta1(DeployIndexV1):
  """Deploy an index to a Vertex AI index endpoint."""

  detailed_help = DETAILED_HELP

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
