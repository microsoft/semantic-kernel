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
"""AI Platform index endpoints mutate-deployed-index command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.index_endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import index_endpoints_util
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'EXAMPLES':
        """\
        To mutated a deployed index ``deployed-index-123'' from an index
        endpoint ``456'' with 2 min replica count and 10 max replica count under
        project ``example'' in region ``us-central1'', within
        ``vertex-ai-ip-ranges-1'' and ``vertex-ai-ip-ranges-2'', within
        deployment group ``test'', enabling access logging, with JWT audiences
        ``aud1'' and ``aud2'', JWT issuers ``issuer1'' and ``issuer2'' run:

          $ {command} 456 --project=example --region=us-central1 --deployed-index-id=deployed-index-123 --min-replica-count=2 --max-replica-count=10 --reserved-ip-ranges=vertex-ai-ip-ranges-1,vertex-ai-ip-ranges-2 --enable-access-logging --audiences=aud1,aud2 --allowed-issuers=issuer1,issuer2 --deployment-group=test
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class MutateDeployedIndexV1(base.Command):
  """Mutate an existing deployed index from a Vertex AI index endpoint."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddIndexEndpointResourceArg(parser, 'ID of the index endpoint.')
    flags.GetDeployedIndexId().AddToParser(parser)
    flags.AddMutateDeploymentResourcesArgs(parser, 'deployed index')
    flags.AddReservedIpRangesArgs(parser, 'deployed index')
    flags.AddDeploymentGroupArg(parser)
    flags.AddAuthConfigArgs(parser, 'deployed index')
    flags.GetEnableAccessLoggingArg().AddToParser(parser)

  def _Run(self, args, version):
    index_endpoint_ref = args.CONCEPTS.index_endpoint.Parse()
    region = index_endpoint_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      index_endpoint_client = client.IndexEndpointsClient(version=version)
      if version == constants.GA_VERSION:
        operation = index_endpoint_client.MutateDeployedIndex(
            index_endpoint_ref, args)
      else:
        operation = index_endpoint_client.MutateDeployedIndexBeta(
            index_endpoint_ref, args)

      response_msg = operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(version=version),
          op=operation,
          op_ref=index_endpoints_util.ParseIndexEndpointOperation(
              operation.name))
    if response_msg is not None:
      response = encoding.MessageToPyValue(response_msg)
      if 'deployedIndex' in response and 'id' in response['deployedIndex']:
        log.status.Print(('Id of the deployed index updated: {}.').format(
            response['deployedIndex']['id']))
    return response_msg

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class MutateDeployedIndexV1Beta1(MutateDeployedIndexV1):
  """Mutate an existing deployed index from a Vertex AI index endpoint."""

  detailed_help = DETAILED_HELP

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
