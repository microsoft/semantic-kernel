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
"""Vertex AI index endpoints create command."""

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
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateV1(base.CreateCommand):
  """Create a new Vertex AI index endpoint.

  ## EXAMPLES

  To create an index endpoint under project `example` with network
  `projects/123/global/networks/test-network` in region
  `us-central1`, run:

    $ {command} --display-name=index-endpoint --description=test
    --network=projects/123/global/networks/test-network
    --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddRegionResourceArg(
        parser,
        'to create index endpoint',
        prompt_func=region_util.GetPromptForRegionFunc(
            constants.SUPPORTED_OP_REGIONS
        ),
    )
    flags.GetDisplayNameArg('index endpoint').AddToParser(parser)
    flags.GetDescriptionArg('index endpoint').AddToParser(parser)
    flags.GetNetworkArg().AddToParser(parser)
    flags.GetPublicEndpointEnabledArg().AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddPrivateServiceConnectConfig(parser)
    flags.GetEncryptionKmsKeyNameArg().AddToParser(parser)

  def _Run(self, args, version):
    validation.ValidateDisplayName(args.display_name)
    validation.ValidateEndpointArgs(args.network, args.public_endpoint_enabled)
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(version, region=region):
      index_endpoint_client = client.IndexEndpointsClient(version=version)
      if version == constants.GA_VERSION:
        operation = index_endpoint_client.Create(region_ref, args)
      else:
        operation = index_endpoint_client.CreateBeta(region_ref, args)

      response_msg = operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(version=version),
          op=operation,
          op_ref=index_endpoints_util.ParseIndexEndpointOperation(
              operation.name))
      if response_msg is not None:
        response = encoding.MessageToPyValue(response_msg)
        if 'name' in response:
          log.status.Print(('Created Vertex AI index endpoint: {}.').format(
              response['name']))
      return response_msg

  def Run(self, args):
    return self._Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateV1Beta1(CreateV1):
  """Create a new Vertex AI index endpoint.

  ## EXAMPLES

  To create an index endpoint under project `example` with network
  `projects/123/global/networks/test-network` in region
  `us-central1`, run:

    $ {command} --display-name=index-endpoint --description=test
    --network=projects/123/global/networks/test-network
    --project=example --region=us-central1
  """

  def Run(self, args):
    return self._Run(args, constants.BETA_VERSION)
